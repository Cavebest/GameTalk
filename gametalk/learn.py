# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Phrasebook & practice window (learning mode).

"My phrases": the English sentences you've used most, with the Arabic and how to pronounce
them; add any of them to your quick phrases. "Practice": flash cards — see the Arabic, say the
English out loud, reveal to check. Over time you need GameTalk less.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from . import APP_NAME, theme
from .i18n import is_rtl, tr

LRM = "‎"  # keeps English left-to-right inside the Arabic (right-to-left) UI
RLE, PDF = "‫", "‬"  # right-to-left embedding: Arabic with "B" or "." stays in order


def _rtl(text: str) -> str:
    return RLE + text + PDF if text else ""


def _pron(text: str) -> str:
    try:
        from .pronounce import to_arabic

        return to_arabic(text)
    except Exception:
        return ""


class LearnDialog(QDialog):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.c = controller
        self.book = controller.phrasebook
        self.setWindowTitle(tr("{app} — My phrasebook", app=tr(APP_NAME)))
        if is_rtl():
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        theme.apply(
            self,
            " QTableWidget { background: #1d2330; gridline-color: #2b3345;"
            " border: 1px solid #2b3345; border-radius: 6px; }"
            " QHeaderView::section { background: #161a22; color: #8b93a3; border: none;"
            " padding: 5px; }"
            " QLabel#card { font-size: 20pt; font-weight: 600; padding: 18px; }"
            " QLabel#answer { font-size: 17pt; color: #38bdf8; }"
            " QFrame#cardbox { background: #161a22; border: 1px solid #232937;"
            " border-radius: 10px; }",
        )
        self.resize(760, 520)
        root = QVBoxLayout(self)
        if not self.c.features.learning_enabled:
            warn = QLabel(
                tr(
                    "Learning mode is off: phrases are only kept until GameTalk closes. "
                    "Turn it on in Settings → Features to keep your phrasebook."
                )
            )
            warn.setObjectName("warn")
            warn.setWordWrap(True)
            root.addWidget(warn)
        tabs = QTabWidget()
        tabs.addTab(self._phrases_tab(), tr("My phrases"))
        tabs.addTab(self._practice_tab(), tr("Practice"))
        root.addWidget(tabs)
        self._fill()

    # ---- My phrases -------------------------------------------------------------------------

    def _phrases_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            [tr("English"), tr("Arabic"), tr("Pronunciation"), tr("Times")]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        header = self.table.horizontalHeader()
        for col in range(3):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        lay.addWidget(self.table)
        row = QHBoxLayout()
        add = QPushButton(tr("Add to quick phrases"))
        add.clicked.connect(self._add_selected)
        rem = QPushButton(tr("Remove selected"))
        rem.clicked.connect(self._remove_selected)
        clear = QPushButton(tr("Clear everything"))
        clear.clicked.connect(self._clear)
        row.addWidget(add)
        row.addWidget(rem)
        row.addStretch(1)
        row.addWidget(clear)
        lay.addLayout(row)
        return w

    def _fill(self) -> None:
        entries = self.book.most_used(500)
        self.table.setRowCount(len(entries))
        for r, e in enumerate(entries):
            for col, value in enumerate(
                (LRM + e.english, _rtl(e.arabic), _rtl(_pron(e.english)), str(e.count))
            ):
                item = QTableWidgetItem(value)
                if col in (1, 2):
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                self.table.setItem(r, col, item)
        self._cards = self.book.practice_order()
        self._card_index = 0
        self._show_card()

    def _selected_texts(self) -> list[str]:
        rows = sorted({i.row() for i in self.table.selectedIndexes()})
        return [self.table.item(r, 0).text().lstrip(LRM) for r in rows if self.table.item(r, 0)]

    def _add_selected(self) -> None:
        texts = self._selected_texts()
        for text in texts:
            self.c.add_quick_phrase(text)
        if texts:
            QMessageBox.information(
                self,
                tr(APP_NAME),
                tr("Added. Give them keys in Settings → Quick phrases."),
            )

    def _remove_selected(self) -> None:
        for text in self._selected_texts():
            self.book.remove(text)
        self.book.save()
        self._fill()

    def _clear(self) -> None:
        answer = QMessageBox.question(
            self, tr(APP_NAME), tr("Delete every saved phrase? This can't be undone.")
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.book.clear()
            self._fill()

    # ---- Practice -----------------------------------------------------------------------------

    def _practice_tab(self) -> QWidget:
        from PySide6.QtWidgets import QFrame

        w = QWidget()
        lay = QVBoxLayout(w)
        self.progress = QLabel("")
        self.progress.setObjectName("muted")
        lay.addWidget(self.progress)
        box = QFrame()
        box.setObjectName("cardbox")
        bl = QVBoxLayout(box)
        self.prompt = QLabel("")
        self.prompt.setObjectName("muted")
        self.prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card = QLabel("")
        self.card.setObjectName("card")
        self.card.setWordWrap(True)
        self.card.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.answer = QLabel("")
        self.answer.setObjectName("answer")
        self.answer.setWordWrap(True)
        self.answer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.answer_pron = QLabel("")
        self.answer_pron.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for wd in (self.prompt, self.card, self.answer, self.answer_pron):
            bl.addWidget(wd)
        lay.addWidget(box, 1)
        row = QHBoxLayout()
        self.reveal_btn = QPushButton(tr("Show answer"))
        self.reveal_btn.setObjectName("primary")
        self.reveal_btn.clicked.connect(self._reveal)
        self.knew_btn = QPushButton(tr("I knew it ✓"))
        self.knew_btn.clicked.connect(lambda: self._next(True))
        self.again_btn = QPushButton(tr("Again ↻"))
        self.again_btn.clicked.connect(lambda: self._next(False))
        row.addWidget(self.reveal_btn)
        row.addStretch(1)
        row.addWidget(self.again_btn)
        row.addWidget(self.knew_btn)
        lay.addLayout(row)
        return w

    def _show_card(self) -> None:
        cards = getattr(self, "_cards", [])
        has = bool(cards)
        for b in (self.reveal_btn, self.knew_btn, self.again_btn):
            b.setEnabled(has)
        self.answer.setText("")
        self.answer_pron.setText("")
        if not has:
            self.prompt.setText("")
            self.card.setText(tr("No phrases yet — use GameTalk and they'll appear here."))
            self.progress.setText("")
            return
        e = cards[self._card_index % len(cards)]
        known = sum(c.known for c in cards)
        self.progress.setText(tr("{known} of {total} phrases known", known=known, total=len(cards)))
        if e.arabic:
            self.prompt.setText(tr("How do you say this in English?"))
            self.card.setText(_rtl(e.arabic))
        else:
            self.prompt.setText(tr("Say this out loud, then check the pronunciation:"))
            self.card.setText(LRM + e.english)
        self.knew_btn.setEnabled(False)
        self.again_btn.setEnabled(False)

    def _reveal(self) -> None:
        cards = self._cards
        if not cards:
            return
        e = cards[self._card_index % len(cards)]
        self.answer.setText(LRM + e.english)
        self.answer_pron.setText(_rtl(_pron(e.english)))
        self.knew_btn.setEnabled(True)
        self.again_btn.setEnabled(True)

    def _next(self, knew: bool) -> None:
        cards = self._cards
        if not cards:
            return
        e = cards[self._card_index % len(cards)]
        self.book.set_known(e.english, knew)
        self._card_index += 1
        self._show_card()

    def closeEvent(self, e) -> None:  # noqa: N802 (Qt override)
        self.book.save()
        super().closeEvent(e)
