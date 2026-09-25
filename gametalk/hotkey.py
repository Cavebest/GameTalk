# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Global push-to-talk hotkey via Windows Raw Input.

Raw Input (RIDEV_INPUTSINK) is used instead of low-level hooks: messages are delivered
asynchronously to a hidden message-only window, so this process never sits in the game's
input chain (no added input latency, nothing injected, the key is never swallowed).
The mouse is only registered when a mouse-button hotkey is configured, so ordinary mouse
movement costs nothing otherwise.
"""

from __future__ import annotations

import ctypes
import logging
import threading
from ctypes import wintypes

from PySide6.QtCore import QObject, Signal

from . import win32

log = logging.getLogger(__name__)

KEYBOARD_KEYS = {
    **{f"F{i}": 0x6F + i for i in range(1, 25)},  # F1-F24 (F13+ exist on macro keyboards)
    "Insert": 0x2D,
    "Home": 0x24,
    "End": 0x23,
    "PageUp": 0x21,
    "PageDown": 0x22,
    "Pause": 0x13,
    "ScrollLock": 0x91,
    **{f"Numpad{i}": 0x60 + i for i in range(10)},  # NumLock on
    "NumpadMultiply": 0x6A,
    "NumpadAdd": 0x6B,
    "NumpadSubtract": 0x6D,
    "NumpadDecimal": 0x6E,
    "NumpadDivide": 0x6F,
}
MOUSE_BUTTONS = {"Mouse4": 4, "Mouse5": 5}
SUPPORTED_HOTKEYS = list(KEYBOARD_KEYS) + list(MOUSE_BUTTONS)
VK_ESCAPE = 0x1B

_VK_TO_NAME = {vk: name for name, vk in KEYBOARD_KEYS.items()}
_BTN_TO_NAME = {btn: name for name, btn in MOUSE_BUTTONS.items()}
_MOUSE_FLAGS = (
    (win32.RI_MOUSE_BUTTON_4_DOWN, 4, True),
    (win32.RI_MOUSE_BUTTON_4_UP, 4, False),
    (win32.RI_MOUSE_BUTTON_5_DOWN, 5, True),
    (win32.RI_MOUSE_BUTTON_5_UP, 5, False),
)
_WM_RECONFIGURE = win32.WM_APP + 1


def parse_hotkey(name: str) -> tuple[str, int]:
    """'F9' -> ('key', 0x78); 'Mouse4' -> ('mouse', 4). Raises ValueError."""
    if name in KEYBOARD_KEYS:
        return "key", KEYBOARD_KEYS[name]
    if name in MOUSE_BUTTONS:
        return "mouse", MOUSE_BUTTONS[name]
    raise ValueError(f"Unsupported hotkey: {name!r}")


def hotkey_name(kind: str, code: int) -> str | None:
    return (_VK_TO_NAME if kind == "key" else _BTN_TO_NAME).get(code)


def hotkey_vk(name: str) -> int | None:
    """Virtual-key code usable with GetAsyncKeyState ('Mouse4' -> VK_XBUTTON1)."""
    try:
        kind, code = parse_hotkey(name)
    except ValueError:
        return None
    return code if kind == "key" else {4: 0x05, 5: 0x06}[code]


def mouse_button_events(flags: int) -> list[tuple[int, bool]]:
    """Decode RAWMOUSE.usButtonFlags into [(button, is_down)] for buttons 4/5."""
    return [(btn, down) for bit, btn, down in _MOUSE_FLAGS if flags & bit]


class HotkeyListener(QObject):
    """Emits pressed(action)/released(action) for bound keys while any app (e.g. a game) has
    focus. Bindings map an action name ("ptt", "replay", "phrase:0", …) to a key name."""

    pressed = Signal(str)
    released = Signal(str)
    captured = Signal(str)  # next supported key pressed in capture mode ("" = cancelled)
    foreground_changed = Signal(str)  # exe name of the new foreground app
    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bindings: dict[tuple[str, int], str] = {("key", KEYBOARD_KEYS["F9"]): "ptt"}
        self._down: set[str] = set()
        self._capturing = False
        self._watch_foreground = False
        self._mouse_registered = False
        self._hwnd = None
        self._thread: threading.Thread | None = None
        self._thread_id = 0
        self._ready = threading.Event()
        self._last_exe = ""
        # Keep ctypes callbacks alive for the lifetime of the listener.
        self._wndproc = None
        self._eventproc = None
        self._event_hook = None
        self._class_name = f"GameTalkHotkey{id(self)}"

    # ---- public API (main thread) -------------------------------------------------------

    def start(self, bindings: dict[str, str] | str, watch_foreground: bool = False) -> None:
        if isinstance(bindings, str):
            bindings = {"ptt": bindings}
        self.set_bindings(bindings)
        self._watch_foreground = watch_foreground
        if not win32.IS_WINDOWS:
            self.failed.emit("Global hotkeys are only supported on Windows.")
            return
        self._thread = threading.Thread(target=self._run, name="gametalk-hotkey", daemon=True)
        self._thread.start()
        self._ready.wait(2.0)

    def stop(self) -> None:
        if self._thread and self._thread.is_alive():
            win32.PostThreadMessageW(self._thread_id, win32.WM_QUIT, 0, 0)
            self._thread.join(2.0)
        self._thread = None

    def set_hotkey(self, name: str) -> None:
        """Only the push-to-talk key (keeps other bindings)."""
        others = {a: k for a, k in self.bindings().items() if a != "ptt"}
        self.set_bindings({"ptt": name, **others})

    def set_bindings(self, bindings: dict[str, str]) -> None:
        """action -> key name. The first action claiming a key wins; bad names are skipped."""
        table: dict[tuple[str, int], str] = {}
        for action, name in bindings.items():
            if not name:
                continue
            try:
                key = parse_hotkey(name)
            except ValueError:
                log.warning("Unsupported hotkey %r for %s", name, action)
                if action == "ptt":
                    key = ("key", KEYBOARD_KEYS["F9"])
                else:
                    continue
            table.setdefault(key, action)
        self._bindings = table
        self._down = set()
        self._reconfigure()

    def bindings(self) -> dict[str, str]:
        return {a: hotkey_name(*k) or "" for k, a in self._bindings.items()}

    def set_watch_foreground(self, watch: bool) -> None:
        self._watch_foreground = watch
        self._reconfigure()

    def begin_capture(self) -> None:
        self._capturing = True
        self._reconfigure()

    def cancel_capture(self) -> None:
        self._capturing = False
        self._reconfigure()

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def reset_state(self) -> None:
        """Forget key-downs whose key-up was never delivered, so the next press registers."""
        self._down = set()

    # ---- listener thread -----------------------------------------------------------------

    def _reconfigure(self) -> None:
        if self._hwnd:
            win32.PostMessageW(self._hwnd, _WM_RECONFIGURE, 0, 0)

    def _run(self) -> None:
        try:
            self._thread_id = win32.GetCurrentThreadId()
            hinst = win32.GetModuleHandleW(None)
            self._wndproc = win32.WNDPROC(self._window_proc)
            wc = win32.WNDCLASSW()
            wc.lpfnWndProc = self._wndproc
            wc.hInstance = hinst
            wc.lpszClassName = self._class_name
            if not win32.RegisterClassW(ctypes.byref(wc)):
                raise OSError(ctypes.get_last_error(), "RegisterClassW failed")
            self._hwnd = win32.CreateWindowExW(
                0, self._class_name, "", 0, 0, 0, 0, 0, win32.HWND_MESSAGE, None, hinst, None
            )
            if not self._hwnd:
                raise OSError(ctypes.get_last_error(), "CreateWindowExW failed")
            self._register(win32.RAWINPUTDEVICE(1, 6, win32.RIDEV_INPUTSINK, self._hwnd))
            self._apply_config()
            log.info("Hotkey listener started")
        except OSError as e:
            log.error("Hotkey registration failed: %s", e)
            self.failed.emit("Couldn't register the push-to-talk hotkey.")
            self._ready.set()
            return
        self._ready.set()

        msg = wintypes.MSG()
        while win32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            win32.TranslateMessage(ctypes.byref(msg))
            win32.DispatchMessageW(ctypes.byref(msg))

        if self._event_hook:
            win32.UnhookWinEvent(self._event_hook)
            self._event_hook = None
        win32.DestroyWindow(self._hwnd)
        self._hwnd = None
        win32.UnregisterClassW(self._class_name, hinst)
        log.info("Hotkey listener stopped")

    @staticmethod
    def _register(device) -> None:
        if not win32.RegisterRawInputDevices(
            ctypes.byref(device), 1, ctypes.sizeof(win32.RAWINPUTDEVICE)
        ):
            raise OSError(ctypes.get_last_error(), "RegisterRawInputDevices failed")

    def _apply_config(self) -> None:
        """Runs on the listener thread: (un)register mouse input and the foreground hook."""
        want_mouse = self._capturing or any(k[0] == "mouse" for k in self._bindings)
        try:
            if want_mouse and not self._mouse_registered:
                self._register(win32.RAWINPUTDEVICE(1, 2, win32.RIDEV_INPUTSINK, self._hwnd))
                self._mouse_registered = True
            elif not want_mouse and self._mouse_registered:
                self._register(win32.RAWINPUTDEVICE(1, 2, win32.RIDEV_REMOVE, None))
                self._mouse_registered = False
        except OSError as e:
            log.error("Mouse hotkey registration failed: %s", e)
            self.failed.emit("Couldn't register the mouse-button hotkey.")

        if self._watch_foreground and not self._event_hook:
            self._eventproc = win32.WINEVENTPROC(self._on_foreground)
            self._event_hook = win32.SetWinEventHook(
                win32.EVENT_SYSTEM_FOREGROUND,
                win32.EVENT_SYSTEM_FOREGROUND,
                None,
                self._eventproc,
                0,
                0,
                win32.WINEVENT_OUTOFCONTEXT | win32.WINEVENT_SKIPOWNPROCESS,
            )
        elif not self._watch_foreground and self._event_hook:
            win32.UnhookWinEvent(self._event_hook)
            self._event_hook = None

    def _window_proc(self, hwnd, msg, wparam, lparam):
        try:
            if msg == win32.WM_INPUT:
                self._on_raw_input(lparam)
            elif msg == _WM_RECONFIGURE:
                self._apply_config()
                return 0
        except Exception:  # never let an exception escape into Win32
            log.exception("Hotkey window procedure error")
        return win32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _on_raw_input(self, handle) -> None:
        raw = win32.RAWINPUT()
        size = wintypes.UINT(ctypes.sizeof(raw))
        n = win32.GetRawInputData(
            handle,
            win32.RID_INPUT,
            ctypes.byref(raw),
            ctypes.byref(size),
            ctypes.sizeof(win32.RAWINPUTHEADER),
        )
        if n in (0, 0xFFFFFFFF):
            return
        if raw.header.dwType == win32.RIM_TYPEKEYBOARD:
            kb = raw.data.keyboard
            self._handle("key", kb.VKey, not (kb.Flags & win32.RI_KEY_BREAK))
        elif raw.header.dwType == win32.RIM_TYPEMOUSE:
            flags = raw.data.mouse.u.buttons.usButtonFlags
            if flags:
                for btn, down in mouse_button_events(flags):
                    self._handle("mouse", btn, down)

    def _handle(self, kind: str, code: int, down: bool) -> None:
        if self._capturing:
            if not down:
                return
            if kind == "key" and code == VK_ESCAPE:
                name = ""
            else:
                name = hotkey_name(kind, code)
                if name is None:
                    return
            self._capturing = False
            self._apply_config()
            self.captured.emit(name)
            return
        action = self._bindings.get((kind, code))
        if action is None:
            return
        if down and action not in self._down:  # ignore keyboard auto-repeat
            self._down.add(action)
            self.pressed.emit(action)
        elif not down and action in self._down:
            self._down.discard(action)
            self.released.emit(action)

    def _on_foreground(self, _hook, _event, hwnd, _obj, _child, _thread, _time) -> None:
        try:
            exe = win32.process_exe_for_window(hwnd)
            if exe and exe != self._last_exe:
                self._last_exe = exe
                self.foreground_changed.emit(exe)
        except Exception:
            log.exception("Foreground watcher error")
