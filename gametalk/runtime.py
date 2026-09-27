# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""How to start GameTalk, from source (python -m …) or the installed .exe.

Installed build: GameTalk.exe opens GameTalk with its window; "GameTalk.exe --app" starts it in
the tray only (Windows startup).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

FROZEN = bool(getattr(sys, "frozen", False))


def pythonw() -> str:
    exe = Path(sys.executable)
    candidate = exe.with_name("pythonw.exe")
    return str(candidate if candidate.exists() else exe)


def app_command(*args: str) -> list[str]:
    if FROZEN:
        return [sys.executable, "--app", *args]
    return [pythonw(), "-m", "gametalk", *args]


def launcher_command() -> list[str]:
    if FROZEN:
        return [sys.executable]
    return [pythonw(), "-m", "gametalk.launcher"]


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE = "GameTalk Translator"


def autostart_command() -> str:
    return subprocess.list2cmdline(app_command())


def autostart_enabled() -> bool:
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, RUN_VALUE)
            return True
    except OSError:
        return False


def set_autostart(enabled: bool) -> None:
    """Add/remove GameTalk from the current user's Windows startup (no admin needed)."""
    import winreg

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, RUN_VALUE, 0, winreg.REG_SZ, autostart_command())
        else:
            try:
                winreg.DeleteValue(key, RUN_VALUE)
            except FileNotFoundError:
                pass


def spawn(cmd: list[str]) -> None:
    """Start a detached process (no console window, survives the caller)."""
    flags = 0
    if sys.platform == "win32":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    subprocess.Popen(
        cmd,
        creationflags=flags,
        cwd=str(Path.home()),
        close_fds=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
