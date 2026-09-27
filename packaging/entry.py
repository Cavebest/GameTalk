# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Entry point of the installed GameTalk.exe.

GameTalk.exe          -> GameTalk with its main window (or brings it up if running)
GameTalk.exe --app …  -> GameTalk in the tray only (Windows startup)
"""

import sys


def run() -> int:
    if "--app" in sys.argv[1:]:
        from gametalk.__main__ import main

        return main(sys.argv[1:])
    from gametalk.launcher import main

    return main()


if __name__ == "__main__":
    sys.exit(run())
