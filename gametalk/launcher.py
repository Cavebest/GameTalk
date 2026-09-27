# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Open GameTalk: start the app with its main window, or bring the window of the already
running app to the front. Used by GameTalk.exe (no arguments), GameTalk.bat and shortcuts.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from gametalk import APP_NAME
from gametalk.config import default_config_dir
from gametalk.runtime import FROZEN, app_command, autostart_command, launcher_command

__all__ = ["app_command", "autostart_command", "create_desktop_shortcut", "main", "ps_quote"]


def ps_quote(value: str) -> str:
    """PowerShell single-quoted literal (an apostrophe in a path, e.g. O'Brien, can't break out)."""
    return "'" + value.replace("'", "''") + "'"


def make_ico() -> str:
    """Write the runtime-drawn icon to %APPDATA%\\GameTalk\\gametalk.ico for shortcuts."""
    from gametalk.tray import make_icon

    path = default_config_dir() / "gametalk.ico"
    path.parent.mkdir(parents=True, exist_ok=True)
    make_icon(True).pixmap(256, 256).save(str(path), "ICO")
    return str(path) if path.exists() else ""


def create_desktop_shortcut() -> Path:
    """Desktop .lnk that opens GameTalk (uses the WScript.Shell COM object)."""
    icon = make_ico()
    target, *args = launcher_command()
    script = (
        "$d=[Environment]::GetFolderPath('Desktop');"
        f'$s=(New-Object -ComObject WScript.Shell).CreateShortcut("$d\\{APP_NAME}.lnk");'
        f"$s.TargetPath={ps_quote(target)};"
        f"$s.Arguments={ps_quote(' '.join(args))};"
        f"$s.WorkingDirectory={ps_quote(str(Path.home()))};"
        f"$s.Description={ps_quote(APP_NAME)};"
        + (f"$s.IconLocation={ps_quote(icon + ',0')};" if icon and not FROZEN else "")
        + "$s.Save();Write-Output $d"
    )
    out = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        timeout=20,
    )
    if out.returncode != 0:
        raise OSError(out.stderr.strip() or "PowerShell failed")
    return Path(out.stdout.strip()) / f"{APP_NAME}.lnk"


def main() -> int:
    """GameTalk with its window. If it's already running (tray), that copy shows its window."""
    from gametalk.__main__ import main as app_main

    return app_main(["--show", *sys.argv[1:]])


if __name__ == "__main__":
    sys.exit(main())
