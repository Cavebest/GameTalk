# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Minimal ctypes Win32 bindings shared by the hotkey listener and the overlay."""

from __future__ import annotations

import ctypes
import os
import sys
from ctypes import wintypes

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    LRESULT = ctypes.c_ssize_t
    WNDPROC = ctypes.WINFUNCTYPE(
        LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
    )
    WINEVENTPROC = ctypes.WINFUNCTYPE(
        None,
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.HWND,
        wintypes.LONG,
        wintypes.LONG,
        wintypes.DWORD,
        wintypes.DWORD,
    )

    class WNDCLASSW(ctypes.Structure):
        _fields_ = [
            ("style", wintypes.UINT),
            ("lpfnWndProc", WNDPROC),
            ("cbClsExtra", ctypes.c_int),
            ("cbWndExtra", ctypes.c_int),
            ("hInstance", wintypes.HINSTANCE),
            ("hIcon", wintypes.HICON),
            ("hCursor", wintypes.HANDLE),
            ("hbrBackground", wintypes.HBRUSH),
            ("lpszMenuName", wintypes.LPCWSTR),
            ("lpszClassName", wintypes.LPCWSTR),
        ]

    class RAWINPUTDEVICE(ctypes.Structure):
        _fields_ = [
            ("usUsagePage", wintypes.USHORT),
            ("usUsage", wintypes.USHORT),
            ("dwFlags", wintypes.DWORD),
            ("hwndTarget", wintypes.HWND),
        ]

    class RAWINPUTHEADER(ctypes.Structure):
        _fields_ = [
            ("dwType", wintypes.DWORD),
            ("dwSize", wintypes.DWORD),
            ("hDevice", wintypes.HANDLE),
            ("wParam", wintypes.WPARAM),
        ]

    class RAWKEYBOARD(ctypes.Structure):
        _fields_ = [
            ("MakeCode", wintypes.USHORT),
            ("Flags", wintypes.USHORT),
            ("Reserved", wintypes.USHORT),
            ("VKey", wintypes.USHORT),
            ("Message", wintypes.UINT),
            ("ExtraInformation", wintypes.ULONG),
        ]

    class _RAWMOUSEBUTTONS(ctypes.Structure):
        _fields_ = [("usButtonFlags", wintypes.USHORT), ("usButtonData", wintypes.USHORT)]

    class _RAWMOUSEUNION(ctypes.Union):
        _fields_ = [("ulButtons", wintypes.ULONG), ("buttons", _RAWMOUSEBUTTONS)]

    class RAWMOUSE(ctypes.Structure):
        _fields_ = [
            ("usFlags", wintypes.USHORT),
            ("u", _RAWMOUSEUNION),
            ("ulRawButtons", wintypes.ULONG),
            ("lLastX", wintypes.LONG),
            ("lLastY", wintypes.LONG),
            ("ulExtraInformation", wintypes.ULONG),
        ]

    class _RAWINPUTDATA(ctypes.Union):
        _fields_ = [("mouse", RAWMOUSE), ("keyboard", RAWKEYBOARD)]

    class RAWINPUT(ctypes.Structure):
        _fields_ = [("header", RAWINPUTHEADER), ("data", _RAWINPUTDATA)]

    def _sig(fn, restype, *argtypes):
        fn.restype = restype
        fn.argtypes = argtypes
        return fn

    GetModuleHandleW = _sig(kernel32.GetModuleHandleW, wintypes.HMODULE, wintypes.LPCWSTR)
    GetCurrentThreadId = _sig(kernel32.GetCurrentThreadId, wintypes.DWORD)
    OpenProcess = _sig(
        kernel32.OpenProcess, wintypes.HANDLE, wintypes.DWORD, wintypes.BOOL, wintypes.DWORD
    )
    CloseHandle = _sig(kernel32.CloseHandle, wintypes.BOOL, wintypes.HANDLE)
    QueryFullProcessImageNameW = _sig(
        kernel32.QueryFullProcessImageNameW,
        wintypes.BOOL,
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    )

    RegisterClassW = _sig(user32.RegisterClassW, wintypes.ATOM, ctypes.POINTER(WNDCLASSW))
    UnregisterClassW = _sig(
        user32.UnregisterClassW, wintypes.BOOL, wintypes.LPCWSTR, wintypes.HINSTANCE
    )
    CreateWindowExW = _sig(
        user32.CreateWindowExW,
        wintypes.HWND,
        wintypes.DWORD,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.HWND,
        wintypes.HMENU,
        wintypes.HINSTANCE,
        wintypes.LPVOID,
    )
    DestroyWindow = _sig(user32.DestroyWindow, wintypes.BOOL, wintypes.HWND)
    DefWindowProcW = _sig(
        user32.DefWindowProcW,
        LRESULT,
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    )
    GetMessageW = _sig(
        user32.GetMessageW,
        wintypes.BOOL,
        ctypes.POINTER(wintypes.MSG),
        wintypes.HWND,
        wintypes.UINT,
        wintypes.UINT,
    )
    TranslateMessage = _sig(user32.TranslateMessage, wintypes.BOOL, ctypes.POINTER(wintypes.MSG))
    DispatchMessageW = _sig(user32.DispatchMessageW, LRESULT, ctypes.POINTER(wintypes.MSG))
    PostMessageW = _sig(
        user32.PostMessageW,
        wintypes.BOOL,
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    )
    PostThreadMessageW = _sig(
        user32.PostThreadMessageW,
        wintypes.BOOL,
        wintypes.DWORD,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    )
    RegisterRawInputDevices = _sig(
        user32.RegisterRawInputDevices,
        wintypes.BOOL,
        ctypes.POINTER(RAWINPUTDEVICE),
        wintypes.UINT,
        wintypes.UINT,
    )
    GetRawInputData = _sig(
        user32.GetRawInputData,
        wintypes.UINT,
        wintypes.HANDLE,
        wintypes.UINT,
        wintypes.LPVOID,
        ctypes.POINTER(wintypes.UINT),
        wintypes.UINT,
    )
    SetWinEventHook = _sig(
        user32.SetWinEventHook,
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HMODULE,
        WINEVENTPROC,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
    )
    UnhookWinEvent = _sig(user32.UnhookWinEvent, wintypes.BOOL, wintypes.HANDLE)
    GetForegroundWindow = _sig(user32.GetForegroundWindow, wintypes.HWND)
    GetWindowThreadProcessId = _sig(
        user32.GetWindowThreadProcessId,
        wintypes.DWORD,
        wintypes.HWND,
        ctypes.POINTER(wintypes.DWORD),
    )
    GetWindowRect = _sig(
        user32.GetWindowRect, wintypes.BOOL, wintypes.HWND, ctypes.POINTER(wintypes.RECT)
    )
    GetWindowLongPtrW = _sig(
        user32.GetWindowLongPtrW, ctypes.c_ssize_t, wintypes.HWND, ctypes.c_int
    )
    SetWindowLongPtrW = _sig(
        user32.SetWindowLongPtrW, ctypes.c_ssize_t, wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t
    )
    GetAsyncKeyState = _sig(user32.GetAsyncKeyState, ctypes.c_short, ctypes.c_int)
    AttachThreadInput = _sig(
        user32.AttachThreadInput, wintypes.BOOL, wintypes.DWORD, wintypes.DWORD, wintypes.BOOL
    )
    SetForegroundWindow = _sig(user32.SetForegroundWindow, wintypes.BOOL, wintypes.HWND)
    BringWindowToTop = _sig(user32.BringWindowToTop, wintypes.BOOL, wintypes.HWND)
    IsWindow = _sig(user32.IsWindow, wintypes.BOOL, wintypes.HWND)
    shell32 = ctypes.WinDLL("shell32")
    SHQueryUserNotificationState = _sig(
        shell32.SHQueryUserNotificationState, ctypes.c_long, ctypes.POINTER(ctypes.c_int)
    )
    SetWindowPos = _sig(
        user32.SetWindowPos,
        wintypes.BOOL,
        wintypes.HWND,
        wintypes.HWND,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.UINT,
    )

# Messages / constants
WM_INPUT = 0x00FF
WM_QUIT = 0x0012
WM_APP = 0x8000
HWND_MESSAGE = -3
HWND_TOPMOST = -1

RID_INPUT = 0x10000003
RIM_TYPEMOUSE = 0
RIM_TYPEKEYBOARD = 1
RIDEV_REMOVE = 0x00000001
RIDEV_INPUTSINK = 0x00000100
RI_KEY_BREAK = 0x01
RI_MOUSE_BUTTON_4_DOWN = 0x0040
RI_MOUSE_BUTTON_4_UP = 0x0080
RI_MOUSE_BUTTON_5_DOWN = 0x0100
RI_MOUSE_BUTTON_5_UP = 0x0200

EVENT_SYSTEM_FOREGROUND = 0x0003
WINEVENT_OUTOFCONTEXT = 0x0000
WINEVENT_SKIPOWNPROCESS = 0x0002

GWL_EXSTYLE = -20
WS_EX_TOPMOST = 0x00000008
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_LAYERED = 0x00080000
WS_EX_NOACTIVATE = 0x08000000

SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_NOOWNERZORDER = 0x0200

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
QUNS_RUNNING_D3D_FULL_SCREEN = 3


def foreground_window() -> int:
    if not IS_WINDOWS:
        return 0
    return GetForegroundWindow() or 0


def process_exe_for_window(hwnd: int) -> str:
    """Lower-case executable file name of the process owning hwnd, or ''."""
    if not IS_WINDOWS or not hwnd:
        return ""
    pid = wintypes.DWORD()
    GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        return ""
    handle = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not handle:
        return ""
    try:
        size = wintypes.DWORD(1024)
        buf = ctypes.create_unicode_buffer(size.value)
        if not QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            return ""
        return os.path.basename(buf.value).lower()
    finally:
        CloseHandle(handle)


def window_rect(hwnd: int) -> tuple[int, int, int, int] | None:
    """(left, top, right, bottom) in physical pixels."""
    if not IS_WINDOWS or not hwnd:
        return None
    r = wintypes.RECT()
    if not GetWindowRect(hwnd, ctypes.byref(r)):
        return None
    return r.left, r.top, r.right, r.bottom


def make_overlay_window(hwnd: int, click_through: bool) -> None:
    """Apply no-activate / tool-window / (optionally) click-through extended styles."""
    if not IS_WINDOWS or not hwnd:
        return
    style = GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
    style |= WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW | WS_EX_LAYERED | WS_EX_TOPMOST
    if click_through:
        style |= WS_EX_TRANSPARENT
    else:
        style &= ~WS_EX_TRANSPARENT
    SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style)


def raise_topmost(hwnd: int) -> None:
    """Re-assert topmost z-order without activating (games sometimes grab topmost)."""
    if IS_WINDOWS and hwnd:
        SetWindowPos(
            hwnd,
            HWND_TOPMOST,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOOWNERZORDER,
        )


def ex_style(hwnd: int) -> int:
    """Extended window style (diagnostics: verify the overlay is no-activate/click-through)."""
    return GetWindowLongPtrW(hwnd, GWL_EXSTYLE) if IS_WINDOWS and hwnd else 0


def key_is_down(vk: int) -> bool:
    """Physical state of a key/mouse button, independent of which app has focus."""
    if not IS_WINDOWS:
        return True  # can't check: never cut a recording short
    return bool(GetAsyncKeyState(vk) & 0x8000)


def exclusive_fullscreen() -> bool:
    """True when a Direct3D exclusive-fullscreen app is running (overlays can't draw on it)."""
    if not IS_WINDOWS:
        return False
    state = ctypes.c_int()
    try:
        if SHQueryUserNotificationState(ctypes.byref(state)) != 0:
            return False
    except OSError:
        return False
    return state.value == QUNS_RUNNING_D3D_FULL_SCREEN


def force_foreground(hwnd: int) -> bool:
    """Bring our window to the front even while a game has focus.

    Windows only lets the process that owns the foreground window hand it over, so we
    briefly attach to that window's input queue (the standard, documented technique).
    """
    if not IS_WINDOWS or not hwnd:
        return False
    fg = GetForegroundWindow()
    if fg == hwnd:
        return True
    fg_thread = GetWindowThreadProcessId(fg, None) if fg else 0
    me = GetCurrentThreadId()
    attached = bool(fg_thread and fg_thread != me and AttachThreadInput(me, fg_thread, True))
    try:
        BringWindowToTop(hwnd)
        return bool(SetForegroundWindow(hwnd))
    finally:
        if attached:
            AttachThreadInput(me, fg_thread, False)


def restore_foreground(hwnd: int) -> None:
    """Give focus back to the window that had it (e.g. the game) after our popup closes."""
    if IS_WINDOWS and hwnd and IsWindow(hwnd):
        SetForegroundWindow(hwnd)
