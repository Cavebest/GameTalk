# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Entry point of the installed GameTalk.exe.

GameTalk.exe          -> launcher window
GameTalk.exe --app …  -> the tray app (hotkeys, overlay, speech)
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
