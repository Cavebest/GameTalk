# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""System tray icon and menu."""

from __future__ import annotations

from PySide6.QtCore import QObject, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPixmap,
    QPolygonF,
)
from PySide6.QtWidgets import QMenu, QMessageBox, QSystemTrayIcon

from . import APP_NAME, AUTHOR_URL, COPYRIGHT, __version__, theme
from .i18n import tr


def make_icon(enabled: bool = True) -> QIcon:
    """Draw the app icon at runtime (no binary assets to ship)."""
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 256):
        pm = QPixmap(size, size)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg = QColor(12, 12, 14) if enabled else QColor(70, 70, 76)
        fg = QColor(255, 90, 31) if enabled else QColor(170, 170, 176)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg)
        p.drawRoundedRect(QRectF(0, 0, size, size), size * 0.22, size * 0.22)
        # Speech bubble
        p.setBrush(fg)
        m = size * 0.16
        bubble = QRectF(m, m, size - 2 * m, size * 0.52)
        p.drawRoundedRect(bubble, size * 0.12, size * 0.12)
        tail = [
            (size * 0.30, bubble.bottom() - 1),
            (size * 0.26, size * 0.86),
            (size * 0.48, bubble.bottom() - 1),
        ]
        p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in tail]))
        p.setPen(QColor(255, 255, 255) if enabled else bg)
        f = QFont("Segoe UI", 1)
        f.setPixelSize(max(6, int(size * 0.30)))
        f.setBold(True)
        p.setFont(f)
        p.drawText(bubble, Qt.AlignmentFlag.AlignCenter, "EN")
        p.end()
        icon.addPixmap(pm)
    return icon


def about_html() -> str:
    link = AUTHOR_URL.removeprefix("https://")
    return (
        f"<h3>{tr(APP_NAME)}</h3>"
        f"<p>{tr('Version {version}', version=__version__)}</p>"
        f'<p>{COPYRIGHT}<br><a href="{AUTHOR_URL}" style="color:{theme.ACCENT}">{link}</a></p>'
        f"<p>{tr('Released under the MIT License.')}</p>"
    )


def show_about() -> None:
    box = QMessageBox()
    theme.apply(box)
    box.setWindowTitle(tr("About {app}", app=tr(APP_NAME)))
    box.setWindowIcon(make_icon(True))
    box.setIconPixmap(make_icon(True).pixmap(64, 64))
    box.setTextFormat(Qt.TextFormat.RichText)
    box.setText(about_html())
    box.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
    box.exec()


class Tray(QObject):
    enabled_toggled = Signal(bool)
    settings_requested = Signal()
    help_requested = Signal()
    test_requested = Signal()
    reload_requested = Signal()
    profile_selected = Signal(str)
    history_selected = Signal(int)
    selftest_requested = Signal()
    phrasebook_requested = Signal()
    quit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._icons = {True: make_icon(True), False: make_icon(False)}
        self.icon = QSystemTrayIcon(self._icons[True], self)
        self.icon.setToolTip(tr(APP_NAME))
        self._enabled_state = True
        self._profiles: tuple[list[str], str] = ([], "")
        self._history: list[str] = []
        self._build_menu()
        self.icon.activated.connect(self._on_activated)

    def _build_menu(self) -> None:
        menu = QMenu()
        open_app = menu.addAction(tr("Open GameTalk"), self.settings_requested.emit)
        menu.setDefaultAction(open_app)  # bold, like other apps' "open" item
        menu.addSeparator()
        self._enabled = QAction(tr("Enabled"), menu, checkable=True)
        self._enabled.setChecked(self._enabled_state)
        self._enabled.toggled.connect(self.enabled_toggled)
        menu.addAction(self._enabled)
        self._profiles_menu = menu.addMenu(tr("Profile"))
        self._profile_group = QActionGroup(self)
        self._profile_group.setExclusive(True)
        self._history_menu = menu.addMenu(tr("Recent translations"))
        menu.addSeparator()
        menu.addAction(tr("Test microphone"), self.test_requested.emit)
        menu.addAction(tr("Reload speech model"), self.reload_requested.emit)
        menu.addAction(tr("Self-test"), self.selftest_requested.emit)
        menu.addAction(tr("My phrasebook"), self.phrasebook_requested.emit)
        menu.addSeparator()
        menu.addAction(tr("Help"), self.help_requested.emit)
        menu.addAction(tr("About…"), show_about)
        menu.addAction(tr("Exit"), self.quit_requested.emit)
        theme.apply(menu)
        old = getattr(self, "_menu", None)
        self._menu = menu
        self.icon.setContextMenu(menu)
        if old is not None:
            old.deleteLater()
        self.set_profiles(*self._profiles)
        self.set_history(self._history)

    def retranslate(self) -> None:
        """Rebuild the menu in the current UI language."""
        self._build_menu()
        self.icon.setToolTip(tr(APP_NAME))

    @staticmethod
    def available() -> bool:
        return QSystemTrayIcon.isSystemTrayAvailable()

    def show(self) -> None:
        self.icon.show()

    def hide(self) -> None:
        self.icon.hide()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled_state = enabled
        self._enabled.blockSignals(True)
        self._enabled.setChecked(enabled)
        self._enabled.blockSignals(False)
        self.icon.setIcon(self._icons[enabled])

    def set_profiles(self, names: list[str], active: str) -> None:
        self._profiles = (list(names), active)
        self._profiles_menu.clear()
        for a in self._profile_group.actions():
            self._profile_group.removeAction(a)
        for name in names:
            act = QAction(name, self._profiles_menu, checkable=True, checked=name == active)
            act.triggered.connect(lambda _=False, n=name: self.profile_selected.emit(n))
            self._profile_group.addAction(act)
            self._profiles_menu.addAction(act)

    def set_history(self, items: list[str]) -> None:
        """Newest first; click shows it on the overlay again."""
        self._history = list(items)
        self._history_menu.clear()
        self._history_menu.setEnabled(bool(items))
        for index in reversed(range(len(items))):
            text = items[index]
            label = text if len(text) <= 60 else text[:57] + "…"
            act = self._history_menu.addAction(label)
            act.triggered.connect(lambda _=False, i=index: self.history_selected.emit(i))

    def set_status(self, text: str) -> None:
        self.icon.setToolTip((tr(APP_NAME) + "\n" + text)[:127])

    def notify(self, message: str, error: bool = False) -> None:
        kind = (
            QSystemTrayIcon.MessageIcon.Warning
            if error
            else QSystemTrayIcon.MessageIcon.Information
        )
        self.icon.showMessage(tr(APP_NAME), message, kind, 4000)

    def _on_activated(self, reason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.settings_requested.emit()
