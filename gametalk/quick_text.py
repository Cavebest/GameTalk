# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Quick text box: press a key, type Arabic, press Enter — get English (for text chat).

This small window does take keyboard focus (you type into it); Esc closes it and gives focus
back to the game. Nothing is typed into the game: copy the result (or turn on "copy
translations to the clipboard") and paste it yourself.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from . import theme, win32
from .i18n import tr


class QuickTextBox(QDialog):
    submitted = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
        )
        theme.apply(
            self,
            "QDialog { background: #0f1218; border: 1px solid #38bdf8; border-radius: 10px; }"
            " QLineEdit { font-size: 13pt; padding: 8px; }"
            " QLabel#result { font-size: 13pt; font-weight: 600; color: #f5f7fa; }",
        )
        self._previous = 0
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        title = QLabel(tr("Type Arabic, press Enter — Esc closes"))
        title.setObjectName("muted")
        lay.addWidget(title)
        self.input = QLineEdit()
        self.input.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.input.setPlaceholderText("اكتب هنا بالعربي…")
        self.input.returnPressed.connect(self._submit)
        lay.addWidget(self.input)
        self.result = QLabel("")
        self.result.setObjectName("result")
        self.result.setWordWrap(True)
        self.result.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lay.addWidget(self.result)
        self.extra = QLabel("")
        self.extra.setObjectName("muted")
        self.extra.setWordWrap(True)
        self.extra.setAlignment(Qt.AlignmentFlag.AlignRight)
        lay.addWidget(self.extra)
        row = QHBoxLayout()
        self.copy_btn = QPushButton(tr("Copy"))
        self.copy_btn.clicked.connect(self._copy)
        self.copy_btn.setEnabled(False)
        close = QPushButton(tr("Close"))
        close.clicked.connect(self.close)
        row.addWidget(self.copy_btn)
        row.addStretch(1)
        row.addWidget(close)
        lay.addLayout(row)
        self.setFixedWidth(520)

    def open_box(self) -> None:
        """Show above the game and grab the keyboard (remembering who had it)."""
        self._previous = win32.foreground_window()
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.adjustSize()
        self.move(screen.center().x() - self.width() // 2, screen.top() + screen.height() // 4)
        self.show()
        self.raise_()
        self.activateWindow()
        win32.force_foreground(int(self.winId()))
        self.input.setFocus()
        self.input.selectAll()

    def _submit(self) -> None:
        text = self.input.text().strip()
        if not text:
            return
        self.result.setText(tr("Translating…"))
        self.extra.setText("")
        self.copy_btn.setEnabled(False)
        self.submitted.emit(text)

    def show_result(self, english: str, extra: str = "") -> None:
        self.result.setText(("‎" + english) if english else tr("Didn't catch that — try again."))
        self.extra.setText(extra)
        self.copy_btn.setEnabled(bool(english))
        self.input.selectAll()

    def show_error(self, message: str) -> None:
        self.result.setText(message)
        self.extra.setText("")
        self.copy_btn.setEnabled(False)

    def _copy(self) -> None:
        QApplication.clipboard().setText(self.result.text().lstrip("‎"))

    def keyPressEvent(self, e) -> None:  # noqa: N802 (Qt override)
        if e.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(e)

    def closeEvent(self, e) -> None:  # noqa: N802 (Qt override)
        super().closeEvent(e)
        win32.restore_foreground(self._previous)  # back to the game
