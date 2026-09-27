# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""GameTalk's main window (Qt Quick), styled after gaming-gear apps.

It lives inside the running app. Closing it only hides GameTalk to the tray (hidden icons);
the window and its Qt Quick scene are destroyed so nothing is left using memory or the GPU
while you play. Double-click the tray icon (or start GameTalk again) to bring it back.
"""

from __future__ import annotations

import ctypes
import logging
import sys
import weakref

from PySide6.QtCore import QObject, QTimer, QUrl

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

# Page names used by commands like "settings:azure" (old tab names still work).
PAGES = {
    "home": 0,
    "engines": 1,
    "speech": 1,
    "translation": 1,
    "microphone": 2,
    "features": 3,
    "overlay": 4,
    "teammates": 5,
    "hotkeys": 6,
    "hotkey": 6,
    "gamepad": 6,
    "phrases": 7,
    "corrections": 7,
    "quicktext": 7,
    "profiles": 8,
    "games": 8,
    "keys": 9,
    "azure": 9,
    "google": 9,
    "settings": 10,
    "general": 10,
    "learning": 10,
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


class HubWindow(QObject):
    """Creates the window on demand and tears it down again when it's closed."""

    instances: weakref.WeakSet = weakref.WeakSet()

    def __init__(self, controller, poll: bool = True):
        super().__init__()
        self.c = controller
        self.poll = poll
        self.engine = None
        self.hub = None
        self._told_about_tray = False
        self._graveyard: list = []  # (engine, hub) waiting to be deleted on the next tick
        HubWindow.instances.add(self)

    @property
    def window(self):
        from shiboken6 import Shiboken

        if self.engine is None or not Shiboken.isValid(self.engine):
            return None  # never opened, closed, or already torn down with the app
        roots = self.engine.rootObjects()
        return roots[0] if roots else None

    def show(self, page: str | int | None = None) -> bool:
        index = PAGES.get(page, 0) if isinstance(page, str) else page
        win = self.window
        if win is None:
            if not self._build(index or 0):
                return False
            win = self.window
        elif index is not None:
            win.setProperty("page", index)
        if win.visibility() == win.Visibility.Minimized:
            win.showNormal()
        else:
            win.show()
        win.raise_()
        win.requestActivate()
        return True

    def _build(self, page: int, geometry=None) -> bool:
        from PySide6.QtGui import QFont
        from PySide6.QtQml import QQmlApplicationEngine
        from PySide6.QtWidgets import QApplication

        from ..i18n import apply_layout_direction
        from ..tray import make_icon
        from .backend import QML_DIR, Hub

        app = QApplication.instance()
        apply_layout_direction(app)
        # Plain QML Text uses the application font, not the window's: set it once here.
        app.setFont(QFont(THEME["font"], 10))
        if self.hub is None:
            self.hub = Hub(self.c, poll=self.poll)
            self.hub.languageChanged.connect(self._rebuild)
        engine = QQmlApplicationEngine()
        engine.warnings.connect(lambda ws: [log.warning("QML: %s", w.toString()) for w in ws])
        ctx = engine.rootContext()
        ctx.setContextProperty("hub", self.hub)
        ctx.setContextProperty("Theme", THEME)
        ctx.setContextProperty("startPage", page)
        engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
        roots = engine.rootObjects()
        if not roots:
            log.error("The main window couldn't load")
            self._retire(engine)
            return False
        win = roots[0]
        win.setIcon(make_icon(True))
        if geometry is not None:
            win.setGeometry(geometry)
        win.visibleChanged.connect(self._on_visible_changed)
        _round_corners(win)
        old, self.engine = self.engine, engine
        if old is not None:
            self._retire(old)
        return True

    def _rebuild(self) -> None:
        """New interface language: rebuild the window where it was, on the same page.

        Called from inside a QML click handler, so the swap happens on the next tick."""
        QTimer.singleShot(0, self._rebuild_now)

    def _rebuild_now(self) -> None:
        old = self.window
        if old is None:
            return
        page = int(old.property("page"))
        geometry = old.geometry()
        if self._build(page, geometry):
            self.window.show()

    def _on_visible_changed(self, visible: bool) -> None:
        win = self.window
        if visible or win is None or win.isVisible():
            return  # (an old window hidden during a language rebuild isn't self.window)
        # The X button hid the window: free everything once Qt has finished closing it.
        QTimer.singleShot(0, self.close)
        if not self._told_about_tray and self.c.tray is not None:
            self._told_about_tray = True
            from ..i18n import tr

            self.c.tray.notify(
                tr("GameTalk is still running here. Double-click the icon to open it again.")
            )

    def _retire(self, engine, hub=None) -> None:
        """Hide an interface now; delete it (and then its backend) on the next tick."""
        for w in engine.rootObjects():
            try:
                w.visibleChanged.disconnect()
            except (RuntimeError, TypeError):
                pass
            w.hide()
        self._graveyard.append((engine, hub))
        QTimer.singleShot(0, self._bury)

    def _bury(self) -> None:
        from shiboken6 import Shiboken

        graves, self._graveyard = self._graveyard, []
        for engine, hub in graves:
            if Shiboken.isValid(engine):
                Shiboken.delete(engine)  # the interface first: it reads the backend to the end
            if hub is not None and Shiboken.isValid(hub):
                Shiboken.delete(hub)

    def close(self) -> None:
        """Destroy the window and its backend (the app keeps running in the tray)."""
        engine, self.engine = self.engine, None
        hub, self.hub = self.hub, None
        if hub is not None:
            hub.close()  # stop polling and detach from the app right away
        if engine is not None:
            self._retire(engine, hub)
        elif hub is not None:
            self._graveyard.append((None, hub))
            QTimer.singleShot(0, self._bury)
