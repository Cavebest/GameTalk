# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""GameTalk Hub: the main window (Qt Quick), styled after gaming-gear apps.

Started by GameTalk.exe / GameTalk.bat. If Qt Quick can't load for any reason the classic
launcher opens instead, so the user is never left without a window.
"""

from __future__ import annotations

import ctypes
import logging
import os
import sys

from PySide6.QtCore import QUrl

log = logging.getLogger(__name__)

THEME = {
    "bg": "#0c0c0e",
    "chrome": "#111114",
    "surface": "#161619",
    "surfaceDim": "#131316",
    "surface2": "#1d1d22",
    "raised": "#25252c",
    "border": "#27272d",
    "borderHover": "#3a3a44",
    "text": "#ededf0",
    "textSoft": "#c6c6cd",
    "muted": "#8c8c96",
    "faint": "#5e5e68",
    "accent": "#ff5a1f",
    "accentHover": "#ff6f3b",
    "accentPress": "#d9480f",
    "accentSoft": "#2b1710",
    "ok": "#3ddc84",
    "okSoft": "#0f2419",
    "okBorder": "#1f5c3b",
    "warn": "#ffb020",
    "warnSoft": "#2a2110",
    "warnBorder": "#6b5118",
    "danger": "#ff4d5e",
    "dangerSoft": "#2a1216",
    "dangerSoftHover": "#3a171d",
    "dangerBorder": "#6d2530",
    "track": "#2c2c33",
    "trackHover": "#36363f",
    "knob": "#9a9aa3",
    "keyBase": "#08080a",
    "keyFace": "#24242b",
    "keyHover": "#2d2d35",
    "azure": "#3b9cff",
    "google": "#5b8ff9",
    "font": "Segoe UI",
    "mono": "Consolas",
}


def _round_corners(window) -> None:
    """Windows 11: rounded corners and a native shadow even without a system frame."""
    if sys.platform != "win32":
        return
    try:
        hwnd = int(window.winId())
        dwm = ctypes.windll.dwmapi
        pref = ctypes.c_int(2)  # DWMWCP_ROUND
        dwm.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(pref), ctypes.sizeof(pref))
        dark = ctypes.c_int(1)  # DWMWA_USE_IMMERSIVE_DARK_MODE
        dwm.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(dark), ctypes.sizeof(dark))
    except (AttributeError, OSError):
        pass


class HubApp:
    """Owns the QML engine; rebuilds the window when the interface language changes."""

    def __init__(self, app, hub):
        from .backend import QML_DIR

        self.app = app
        self.hub = hub
        self.qml = QML_DIR / "Main.qml"
        self.engine = None
        hub.languageChanged.connect(self._rebuild)

    def build(self, page: int = 0, geometry=None) -> bool:
        from PySide6.QtGui import QFont
        from PySide6.QtQml import QQmlApplicationEngine

        from ..i18n import apply_layout_direction
        from ..tray import make_icon

        apply_layout_direction(self.app)
        # Plain QML Text uses the application font, not the window's: set it once here.
        self.app.setFont(QFont(THEME["font"], 10))
        engine = QQmlApplicationEngine()
        engine.warnings.connect(lambda ws: [log.warning("QML: %s", w.toString()) for w in ws])
        ctx = engine.rootContext()
        ctx.setContextProperty("hub", self.hub)
        ctx.setContextProperty("Theme", THEME)
        ctx.setContextProperty("startPage", page)
        engine.load(QUrl.fromLocalFile(str(self.qml)))
        roots = engine.rootObjects()
        if not roots:
            return False
        win = roots[0]
        win.setIcon(make_icon(True))
        if geometry is not None:
            win.setGeometry(geometry)
        _round_corners(win)
        old, self.engine = self.engine, engine
        if old is not None:
            for w in old.rootObjects():
                w.close()
            old.deleteLater()
        return True

    def _rebuild(self) -> None:
        old = self.engine.rootObjects()[0] if self.engine and self.engine.rootObjects() else None
        page = int(old.property("page")) if old is not None else 0
        geometry = old.geometry() if old is not None else None
        self.build(page, geometry)


def main() -> int:
    from PySide6.QtQuickControls2 import QQuickStyle
    from PySide6.QtWidgets import QApplication

    from ..config import ConfigStore
    from ..i18n import set_language
    from .backend import Hub

    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("GameTalk.Launcher")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    QQuickStyle.setStyle("Basic")
    app = QApplication(sys.argv[:1])
    app.setApplicationName("GameTalk")
    set_language(ConfigStore().load().features.ui_language)

    hub = Hub()
    ui = HubApp(app, hub)
    if not ui.build():
        log.error("The new window couldn't load; opening the classic launcher")
        hub.close()
        from ..launcher import run_classic

        return run_classic(app)
    code = app.exec()
    hub.close()
    ui.engine = None  # tear the interface down before the backend it talks to
    return code
