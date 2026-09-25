# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""One dark theme for every window (launcher, settings, tray menu, dialogs).

Applied per window (never app-wide) so the transparent overlay is never touched. Pure Qt style
sheets: no extra dependency, nothing runs after the window is painted.
"""

from __future__ import annotations

BG = "#0f1218"
SURFACE = "#161a22"
CONTROL = "#1d2330"
CONTROL_HOVER = "#242c3c"
BORDER = "#2b3345"
TEXT = "#e6e9ef"
MUTED = "#8b93a3"
DISABLED = "#5b6272"
ACCENT = "#38bdf8"
ACCENT_DARK = "#0e7490"
OK = "#22c55e"
WARN = "#ffb020"

BASE = f"""
QWidget {{ background: {BG}; color: {TEXT}; font-family: 'Segoe UI'; font-size: 10pt; }}
QLabel, QRadioButton, QCheckBox {{ background: transparent; }}
QLabel#title {{ font-size: 16pt; font-weight: 600; }}
QLabel#muted, QLabel#desc {{ color: {MUTED}; }}
QLabel#desc {{ font-size: 9pt; margin-left: 24px; }}
QLabel#warn {{ color: {WARN}; }}
QLabel#ok {{ color: {OK}; }}
QLabel a {{ color: {ACCENT}; }}
QFrame#card {{ background: {SURFACE}; border: 1px solid #232937; border-radius: 10px; }}

QPushButton {{ background: {CONTROL}; border: 1px solid {BORDER}; border-radius: 8px;
              padding: 7px 12px; }}
QPushButton:hover {{ background: {CONTROL_HOVER}; border-color: {ACCENT}; }}
QPushButton:pressed {{ background: #10151d; }}
QPushButton:focus {{ border-color: {ACCENT}; }}
QPushButton:disabled {{ color: {DISABLED}; border-color: #232937; }}
QPushButton#primary, QPushButton:default {{ background: {ACCENT_DARK}; border-color: {ACCENT};
                                            font-weight: 600; }}
QPushButton#primary:hover, QPushButton:default:hover {{ background: #0891b2; }}
QPushButton#danger {{ background: #3a1d24; border-color: #7f2d3a; }}

QRadioButton, QCheckBox {{ spacing: 8px; }}
QRadioButton::indicator, QCheckBox::indicator {{
    width: 12px; height: 12px; border: 2px solid {DISABLED}; background: {BG}; }}
QRadioButton::indicator {{ border-radius: 8px; }}
QCheckBox::indicator {{ border-radius: 4px; }}
QRadioButton::indicator:hover, QCheckBox::indicator:hover,
QRadioButton:focus::indicator, QCheckBox:focus::indicator {{ border-color: {ACCENT}; }}
QRadioButton::indicator:checked {{ border: 4px solid {ACCENT}; width: 8px; height: 8px;
                                  background: #e6f7ff; }}
QCheckBox::indicator:checked {{ border-color: {ACCENT}; background: {ACCENT}; }}
QRadioButton:disabled, QCheckBox:disabled {{ color: {DISABLED}; }}

QComboBox, QLineEdit, QSpinBox, QPlainTextEdit {{
    background: {CONTROL}; border: 1px solid {BORDER}; border-radius: 6px; padding: 4px 8px;
    selection-background-color: {ACCENT_DARK}; }}
QComboBox:hover, QLineEdit:hover, QSpinBox:hover, QPlainTextEdit:hover {{ border-color: #3b4660; }}
QComboBox:focus, QLineEdit:focus, QSpinBox:focus, QPlainTextEdit:focus {{ border-color: {ACCENT}; }}
QComboBox:disabled, QLineEdit:disabled, QSpinBox:disabled, QPlainTextEdit:disabled {{
    color: {DISABLED}; background: #161a22; }}
QComboBox QAbstractItemView {{ background: {CONTROL}; border: 1px solid {BORDER};
                              selection-background-color: {ACCENT_DARK}; outline: 0; }}
QSpinBox::up-button, QSpinBox::down-button {{ width: 16px; border: none; background: transparent; }}

QSlider {{ min-height: 22px; background: transparent; }}
QSlider::groove:horizontal {{ height: 4px; background: {BORDER}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ height: 4px; background: {ACCENT}; border-radius: 2px; }}
QSlider::add-page:horizontal {{ height: 4px; background: {BORDER}; border-radius: 2px; }}
QSlider::handle:horizontal {{ width: 14px; margin: -6px 0; border-radius: 7px;
                             background: #e6f7ff; border: 2px solid {ACCENT}; }}
QSlider::handle:horizontal:hover {{ background: {ACCENT}; }}

QProgressBar {{ background: {CONTROL}; border: 1px solid {BORDER}; border-radius: 4px; }}
QProgressBar::chunk {{ background: {OK}; border-radius: 3px; }}

QTabWidget::pane {{ border: 1px solid #232937; border-radius: 8px; background: {SURFACE};
                   top: -1px; }}
QTabBar::tab {{ background: transparent; color: {MUTED}; padding: 7px 12px; margin-right: 2px;
               border-bottom: 2px solid transparent; }}
QTabBar::tab:hover {{ color: {TEXT}; }}
QTabBar::tab:selected {{ color: {TEXT}; border-bottom: 2px solid {ACCENT}; }}
QTabBar::tab:focus {{ color: {ACCENT}; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background: {SURFACE}; border: none; }}
QScrollBar:vertical {{ background: transparent; width: 10px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 4px; min-height: 24px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}

QMenu {{ background: {SURFACE}; border: 1px solid {BORDER}; padding: 4px; }}
QMenu::item {{ padding: 6px 22px 6px 14px; border-radius: 4px; }}
QMenu::item:selected {{ background: {CONTROL_HOVER}; }}
QMenu::item:disabled {{ color: {MUTED}; }}
QMenu::separator {{ height: 1px; background: #232937; margin: 4px 6px; }}
QMenu::indicator {{ width: 12px; height: 12px; }}
QToolTip {{ background: {SURFACE}; color: {TEXT}; border: 1px solid {BORDER}; padding: 4px; }}
"""


def apply(widget, extra: str = "") -> None:
    """Style one top-level window (and its children) with the shared theme."""
    widget.setStyleSheet(BASE + extra)
