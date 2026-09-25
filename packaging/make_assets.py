# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Build-time assets: the .ico (drawn by the app itself) and the Windows version resource."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from PySide6.QtGui import QGuiApplication  # noqa: E402

from gametalk import APP_NAME, AUTHOR, __version__  # noqa: E402

app = QGuiApplication([])
from gametalk.tray import make_icon  # noqa: E402

make_icon(True).pixmap(256, 256).save(str(HERE / "gametalk.ico"), "ICO")

parts = [int(x) for x in __version__.split(".")] + [0] * (4 - len(__version__.split(".")))
ver = tuple(parts[:4])
(HERE / "version_info.txt").write_text(
    f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={ver}, prodvers={ver}, mask=0x3f, flags=0x0, OS=0x40004,
                    fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', '{AUTHOR}'),
      StringStruct('FileDescription', '{APP_NAME}'),
      StringStruct('FileVersion', '{__version__}'),
      StringStruct('InternalName', 'GameTalk'),
      StringStruct('LegalCopyright', '(c) 2026 {AUTHOR}. MIT License.'),
      StringStruct('OriginalFilename', 'GameTalk.exe'),
      StringStruct('ProductName', '{APP_NAME}'),
      StringStruct('ProductVersion', '{__version__}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""",
    encoding="utf-8",
)
print("assets ok:", HERE / "gametalk.ico")
