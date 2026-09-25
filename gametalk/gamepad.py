# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Game controller button as push-to-talk (Xbox / XInput controllers).

XInput has no events, so a small background thread reads the controller 60 times a second —
only while this feature is enabled. Unplugged slots are re-checked every 2 s (querying an empty
slot is slow). PlayStation controllers work through Steam Input or DS4Windows (they appear as
XInput devices).
"""

from __future__ import annotations

import ctypes
import logging
import sys
import threading
import time
from ctypes import wintypes

from PySide6.QtCore import QObject, Signal

log = logging.getLogger(__name__)

BUTTON_MASKS = {
    "DPadUp": 0x0001,
    "DPadDown": 0x0002,
    "DPadLeft": 0x0004,
    "DPadRight": 0x0008,
    "Start": 0x0010,
    "Back": 0x0020,
    "LS": 0x0040,
    "RS": 0x0080,
    "LB": 0x0100,
    "RB": 0x0200,
    "A": 0x1000,
    "B": 0x2000,
    "X": 0x4000,
    "Y": 0x8000,
}
TRIGGER_THRESHOLD = 100  # 0-255
POLL_SECONDS = 1 / 60
RESCAN_SECONDS = 2.0
ERROR_SUCCESS = 0


class XINPUT_GAMEPAD(ctypes.Structure):  # noqa: N801 (Win32 name)
    _fields_ = [
        ("wButtons", wintypes.WORD),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


class XINPUT_STATE(ctypes.Structure):  # noqa: N801
    _fields_ = [("dwPacketNumber", wintypes.DWORD), ("Gamepad", XINPUT_GAMEPAD)]


def pressed_buttons(buttons: int, left_trigger: int, right_trigger: int) -> set[str]:
    """Decode an XInput state into button names ('LT'/'RT' for pulled triggers)."""
    names = {name for name, mask in BUTTON_MASKS.items() if buttons & mask}
    if left_trigger >= TRIGGER_THRESHOLD:
        names.add("LT")
    if right_trigger >= TRIGGER_THRESHOLD:
        names.add("RT")
    return names


def _load_xinput():
    if sys.platform != "win32":
        return None
    for dll in ("xinput1_4", "xinput1_3", "xinput9_1_0"):
        try:
            lib = ctypes.WinDLL(dll)
            fn = lib.XInputGetState
            fn.argtypes = [wintypes.DWORD, ctypes.POINTER(XINPUT_STATE)]
            fn.restype = wintypes.DWORD
            return fn
        except OSError:
            continue
    return None


class GamepadListener(QObject):
    """Emits pressed(action)/released(action) for bound controller buttons."""

    pressed = Signal(str)
    released = Signal(str)
    failed = Signal(str)

    def __init__(self, get_state=None, parent=None):
        super().__init__(parent)
        self._get_state = get_state  # injectable for tests
        self._bindings: dict[str, str] = {}  # button -> action
        self._down: set[str] = set()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def set_bindings(self, bindings: dict[str, str]) -> None:
        """action -> button name, e.g. {"ptt": "RB", "replay": "Y"}."""
        self._bindings = {
            b: a for a, b in bindings.items() if b in BUTTON_MASKS or b in ("LT", "RT")
        }

    def start(self) -> None:
        if self.running:
            return
        if self._get_state is None:
            self._get_state = _load_xinput()
            if self._get_state is None:
                self.failed.emit("Game controller support (XInput) isn't available.")
                return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="gametalk-gamepad", daemon=True)
        self._thread.start()
        log.info("Gamepad listener started")

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(1.0)
        self._thread = None
        self._release_all()

    def _release_all(self) -> None:
        for button in list(self._down):
            action = self._bindings.get(button)
            if action:
                self.released.emit(action)
        self._down.clear()

    def poll_once(self, slot: int) -> bool:
        """Read one controller and emit changes. Returns False if it's disconnected."""
        state = XINPUT_STATE()
        if self._get_state(slot, ctypes.byref(state)) != ERROR_SUCCESS:
            self._release_all()  # unplugged while held: don't leave PTT stuck
            return False
        g = state.Gamepad
        now = pressed_buttons(g.wButtons, g.bLeftTrigger, g.bRightTrigger)
        for button in now - self._down:
            action = self._bindings.get(button)
            if action:
                self.pressed.emit(action)
        for button in self._down - now:
            action = self._bindings.get(button)
            if action:
                self.released.emit(action)
        self._down = now
        return True

    def _find_slot(self) -> int | None:
        state = XINPUT_STATE()
        for slot in range(4):
            if self._get_state(slot, ctypes.byref(state)) == ERROR_SUCCESS:
                return slot
        return None

    def _run(self) -> None:
        slot: int | None = None
        next_scan = 0.0
        while not self._stop.is_set():
            try:
                if slot is None:
                    now = time.monotonic()
                    if now >= next_scan:
                        slot = self._find_slot()
                        next_scan = now + RESCAN_SECONDS
                    if slot is None:
                        self._stop.wait(0.25)
                        continue
                if not self.poll_once(slot):
                    slot = None
                    continue
            except Exception:
                log.exception("Gamepad polling error")
                slot = None
            self._stop.wait(POLL_SECONDS)
