# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Transparent, click-through, never-focused overlay drawn above borderless/windowed games."""

from __future__ import annotations

import logging
import unicodedata
from enum import Enum, auto

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QRect,
    QRectF,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QColor, QFont, QFontMetrics, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import QWidget

from . import win32
from .config import NEVER_HIDE, OverlayStyle, Profile
from .i18n import tr

log = logging.getLogger(__name__)

PAD_X, PAD_Y = 16, 10
ERROR_SECONDS = 3
INFO_SECONDS = 3
SCREEN_MARGIN = 16  # never touch the screen edge
MAX_HEIGHT_FRACTION = 0.4  # long translations shrink/elide instead of covering the game
MIN_FONT_PT = 12
ELLIPSIS = "…"

ACCENT = QColor(56, 189, 248)  # cyan
DOT_COLORS = {
    "listening": QColor(255, 77, 94),
    "processing": QColor(255, 176, 32),
    "error": QColor(255, 107, 107),
    "info": QColor(56, 189, 248),
}


def reading_seconds(text: str, configured: int) -> int:
    """Keep long translations up long enough to read (about 0.3 s per word), max 15 s."""
    if configured == NEVER_HIDE:
        return NEVER_HIDE
    words = len(text.split())
    return int(min(15, max(configured, round(1.5 + 0.3 * words))))


def elide_to_lines(fm: QFontMetrics, text: str, width: int, max_lines: int) -> str:
    """Longest word-wrapped prefix of `text` that fits in `max_lines` lines, plus an ellipsis."""
    flags = int(Qt.TextFlag.TextWordWrap)
    limit = QRect(0, 0, width, 100_000)
    max_h = max_lines * fm.lineSpacing() + fm.descent()
    if fm.boundingRect(limit, flags, text).height() <= max_h:
        return text
    lo, hi = 0, len(text)
    while lo < hi:  # binary search on characters
        mid = (lo + hi + 1) // 2
        candidate = text[:mid].rstrip() + ELLIPSIS
        if fm.boundingRect(limit, flags, candidate).height() <= max_h:
            lo = mid
        else:
            hi = mid - 1
    cut = text[:lo]
    if " " in cut.strip():  # prefer ending on a word boundary
        cut = cut[: cut.rstrip().rfind(" ")]
    return cut.rstrip(" ,;:-") + ELLIPSIS


def is_rtl_text(text: str) -> bool:
    """True if the first strongly-directional character is Arabic/Hebrew."""
    for ch in text:
        kind = unicodedata.bidirectional(ch)
        if kind in ("R", "AL"):
            return True
        if kind == "L":
            return False
    return False


class State(Enum):
    HIDDEN = auto()
    LISTENING = auto()
    PROCESSING = auto()
    RESULT = auto()
    ERROR = auto()
    INFO = auto()


def anchor_point(
    position: str, screen: QRect, size: tuple[int, int], offset: tuple[int, int]
) -> QPoint:
    """Top-left for a widget of `size` at `position`, offsets measured inward from the edge."""
    w, h = size
    ox, oy = offset
    row, _, col = position.partition("-") if "-" in position else ("middle", "", "center")
    if col == "left":
        x = screen.left() + ox
    elif col == "right":
        x = screen.right() + 1 - w - ox
    else:
        x = screen.left() + (screen.width() - w) // 2 + ox
    if row == "top":
        y = screen.top() + oy
    elif row == "bottom":
        y = screen.bottom() + 1 - h - oy
    else:
        y = screen.top() + (screen.height() - h) // 2 + oy
    x = max(screen.left(), min(x, screen.right() + 1 - w))
    y = max(screen.top(), min(y, screen.bottom() + 1 - h))
    return QPoint(x, y)


def offset_for_point(position: str, screen: QRect, size: tuple[int, int], pt: QPoint):
    """Inverse of anchor_point (used after dragging the overlay in move mode)."""
    w, h = size
    row, _, col = position.partition("-") if "-" in position else ("middle", "", "center")
    if col == "left":
        ox = pt.x() - screen.left()
    elif col == "right":
        ox = screen.right() + 1 - w - pt.x()
    else:
        ox = pt.x() - (screen.left() + (screen.width() - w) // 2)
    if row == "top":
        oy = pt.y() - screen.top()
    elif row == "bottom":
        oy = screen.bottom() + 1 - h - pt.y()
    else:
        oy = pt.y() - (screen.top() + (screen.height() - h) // 2)
    return ox, oy


class Overlay(QWidget):
    moved = Signal(int, int)  # new offsets after a drag in move mode

    def __init__(self):
        super().__init__(None)
        self.setWindowTitle("GameTalk Overlay")
        self._click_through = True
        self.setWindowFlags(self._flags())
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.style_cfg = OverlayStyle()
        self.profile = Profile()
        self.state = State.HIDDEN
        self._text = ""
        self._secondary = ""
        self._shown_text = ""  # _text after elision
        self._badge = False  # "still recording" dot while a previous result is displayed
        self._pulse = 0
        self._drag_from: QPoint | None = None
        self._screen_geo = QRect()
        self._layout: dict = {}

        self._hide_timer = QTimer(self, singleShot=True, timeout=self._fade_out)
        self._pulse_timer = QTimer(self, interval=90, timeout=self._on_pulse)
        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade.finished.connect(self._on_fade_finished)
        self.winId()  # create the native window now so failures surface at startup
        self._apply_native_styles()

    # ---- configuration -------------------------------------------------------------------

    def _flags(self) -> Qt.WindowType:
        f = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.NoDropShadowWindowHint
        )
        if self._click_through:
            f |= Qt.WindowType.WindowTransparentForInput
        return f

    def _apply_native_styles(self) -> None:
        try:
            hwnd = int(self.winId())
            win32.make_overlay_window(hwnd, self._click_through)
            win32.raise_topmost(hwnd)
        except Exception as e:
            log.warning("Applying overlay window styles failed: %s", e)

    def apply(self, style: OverlayStyle, profile: Profile) -> None:
        self.style_cfg, self.profile = style, profile
        if self.state is not State.HIDDEN:
            self._relayout()
            self.update()

    def set_move_mode(self, enabled: bool) -> None:
        """Temporarily make the overlay draggable (settings > Overlay > Move overlay)."""
        if enabled == (not self._click_through):
            return
        self._click_through = not enabled
        visible = self.isVisible()
        self.setWindowFlags(self._flags())
        if enabled:
            self._set_content(State.INFO, tr("Drag me, then click Done"), "")
            self._hide_timer.stop()
        elif visible:
            self.show()
            self._apply_native_styles()
            self._fade_out()

    # ---- public state API ----------------------------------------------------------------

    def show_listening(self) -> None:
        self._set_content(State.LISTENING, tr("Listening..."), "")

    def show_processing(self) -> None:
        self._set_content(State.PROCESSING, tr("Processing..."), "")

    def show_result(self, text: str, secondary: str = "") -> None:
        self._set_content(State.RESULT, text, secondary)
        secs = reading_seconds(text, self.profile.display_seconds)
        if secs != NEVER_HIDE:
            self._hide_timer.start(secs * 1000)

    def set_recording_badge(self, on: bool) -> None:
        """Small pulsing red dot: the user is recording the next sentence while reading this."""
        self._badge = on
        if on:
            self._pulse_timer.start()
        elif self.state is not State.LISTENING:
            self._pulse_timer.stop()
        self.update()

    def show_error(self, message: str) -> None:
        self._set_content(State.ERROR, message, "")
        self._hide_timer.start(ERROR_SECONDS * 1000)

    def show_info(self, message: str, seconds: int = INFO_SECONDS) -> None:
        self._set_content(State.INFO, message, "")
        if seconds:
            self._hide_timer.start(seconds * 1000)

    def hide_now(self) -> None:
        self._hide_timer.stop()
        self._pulse_timer.stop()
        self._fade.stop()
        self.hide()
        self.state = State.HIDDEN

    # ---- internals -----------------------------------------------------------------------

    def _set_content(self, state: State, text: str, secondary: str) -> None:
        self._hide_timer.stop()
        self.state, self._text, self._secondary = state, text, secondary
        self._badge = False
        if state is State.LISTENING:
            self._pulse = 0
            self._pulse_timer.start()
        else:
            self._pulse_timer.stop()
        self._relayout()
        self.update()
        self._fade_in()

    def _fonts(self, size: int) -> tuple[QFont, QFont]:
        main = QFont(self.style_cfg.font_family or "Segoe UI", size)
        main.setWeight(QFont.Weight.DemiBold if self.state is State.RESULT else QFont.Weight.Medium)
        main.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        sub = QFont(self.style_cfg.font_family or "Segoe UI", max(9, int(size * 0.72)))
        return main, sub

    def _has_dot(self) -> bool:
        return self.state in (State.LISTENING, State.PROCESSING, State.ERROR, State.INFO)

    def _measure(self, size: int, text_w_limit: int):
        main_font, sub_font = self._fonts(size)
        fm = QFontMetrics(main_font)
        dot_d = max(8, fm.height() // 2)
        dot_area = dot_d + 10 if self._has_dot() else 0
        text_w = max(60, text_w_limit - dot_area)
        flags = int(Qt.TextFlag.TextWordWrap)
        main_rect = fm.boundingRect(QRect(0, 0, text_w, 100_000), flags, self._text)
        sub_rect = QRect()
        if self._secondary:
            sub_rect = QFontMetrics(sub_font).boundingRect(
                QRect(0, 0, text_w, 100_000), flags, self._secondary
            )
        return main_font, sub_font, fm, dot_d, dot_area, text_w, main_rect, sub_rect

    def _relayout(self) -> None:
        screen = self._target_screen()
        geo = screen.geometry() if screen is not None else QRect(0, 0, 1920, 1080)
        self._screen_geo = geo
        max_w = max(200, min(self.profile.max_width, geo.width() - 2 * SCREEN_MARGIN))
        max_h = max(60, int(geo.height() * MAX_HEIGHT_FRACTION))
        text_limit = max_w - 2 * PAD_X - 4

        # Long text: step the font down first, then elide, so it never covers the game.
        size = self.profile.font_size
        min_size = min(MIN_FONT_PT, size)
        while True:
            m = self._measure(size, text_limit)
            sub_h = m[7].height() + 4 if self._secondary else 0
            if m[6].height() + sub_h + 2 * PAD_Y <= max_h or size <= min_size:
                break
            size = max(min_size, size - 2)
        main_font, sub_font, fm, dot_d, dot_area, text_w, main_rect, sub_rect = m
        shown = self._text
        if main_rect.height() + sub_h + 2 * PAD_Y > max_h:
            lines = max(1, (max_h - 2 * PAD_Y - sub_h) // fm.lineSpacing())
            shown = elide_to_lines(fm, self._text, text_w, lines)
            main_rect = fm.boundingRect(
                QRect(0, 0, text_w, 100_000), int(Qt.TextFlag.TextWordWrap), shown
            )
        self._shown_text = shown

        content_w = max(main_rect.width(), sub_rect.width())
        w = min(max_w, content_w + 2 * PAD_X + dot_area + 4)
        h = main_rect.height() + 2 * PAD_Y + sub_h
        self._layout = {
            "main_font": main_font,
            "sub_font": sub_font,
            "dot_d": dot_d,
            "dot_area": dot_area,
            "main_h": main_rect.height(),
            "line_h": fm.height(),
        }
        if self._click_through or not self.isVisible():
            p = self.profile
            pos = anchor_point(
                p.overlay_position, geo, (w, h), (p.overlay_offset_x, p.overlay_offset_y)
            )
            self.setGeometry(pos.x(), pos.y(), w, h)  # one move+resize: no jump between states
        else:
            self.resize(w, h)  # being dragged in move mode: keep the user's position

    def _target_screen(self):
        screens = QGuiApplication.screens()
        primary = QGuiApplication.primaryScreen()
        if self.style_cfg.monitor != "game" or len(screens) < 2:
            return primary
        rect = win32.window_rect(win32.foreground_window())
        if not rect:
            return primary
        cx, cy = (rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2
        for s in screens:
            g, dpr = s.geometry(), s.devicePixelRatio()
            # Qt keeps each screen's native origin; only its size is scaled.
            if g.x() <= cx < g.x() + g.width() * dpr and g.y() <= cy < g.y() + g.height() * dpr:
                return s
        return primary

    def _fade_in(self) -> None:
        was_visible = self.isVisible() and self._fade.endValue() != 0.0
        self._fade.stop()
        if not self.isVisible():
            self.setWindowOpacity(0.0 if self.style_cfg.animation else 1.0)
            self.show()
            self._apply_native_styles()
        else:
            win32.raise_topmost(int(self.winId()))
        if self.style_cfg.animation and not was_visible:
            self._fade.setDuration(140)
            self._fade.setStartValue(self.windowOpacity())
            self._fade.setEndValue(1.0)
            self._fade.start()
        else:
            self.setWindowOpacity(1.0)

    def _fade_out(self) -> None:
        if not self._click_through:
            return  # stay visible while being positioned
        if not self._badge:
            self._pulse_timer.stop()
        if not self.style_cfg.animation:
            self.hide_now()
            return
        self._fade.stop()
        self._fade.setDuration(320)
        self._fade.setStartValue(self.windowOpacity())
        self._fade.setEndValue(0.0)
        self._fade.start()

    def _on_fade_finished(self) -> None:
        if self._fade.endValue() == 0.0:
            self.hide()
            self.state = State.HIDDEN

    def _on_pulse(self) -> None:
        self._pulse = (self._pulse + 1) % 20
        self.update()

    # ---- painting / dragging -------------------------------------------------------------

    def paintEvent(self, _event) -> None:
        if not self._layout:
            return
        s = self.style_cfg
        prof = self.profile
        lay = self._layout
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = min(s.corner_radius, r.height() / 2)

        bg = prof.background_opacity
        bg_color = QColor(s.background_color)
        bg_color.setAlpha(int(255 * bg))
        p.setPen(QPen(QColor(255, 255, 255, int(28 * max(bg, 0.3))), 1))
        p.setBrush(bg_color)
        p.drawRoundedRect(r, radius, radius)

        rtl = is_rtl_text(self._shown_text)
        if self.state is State.RESULT:  # thin accent bar marks a fresh translation
            p.setPen(Qt.PenStyle.NoPen)
            accent = QColor(s.accent_color)
            accent.setAlphaF(0.9 * prof.text_opacity)
            p.setBrush(accent)
            bar_h = max(8.0, r.height() - 2 * radius - 4) if radius else r.height() - 12
            bar_x = r.width() - 8 if rtl else 5
            p.drawRoundedRect(QRectF(bar_x, (r.height() - bar_h) / 2 + 0.5, 3, bar_h), 1.5, 1.5)

        x = PAD_X
        right = self.width() - PAD_X
        if self._has_dot():
            key = self.state.name.lower()
            color = QColor(DOT_COLORS.get(key, s.accent_color))
            alpha = 1.0
            if self.state is State.LISTENING:
                phase = self._pulse / 20
                alpha = 0.45 + 0.55 * (1 - abs(1 - 2 * phase))
            color.setAlphaF(alpha * prof.text_opacity)
            d = lay["dot_d"]
            cy = PAD_Y + lay["line_h"] / 2
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(color)
            dot_x = right - d if rtl else x  # the dot sits at the start of the reading direction
            p.drawEllipse(QRectF(dot_x, cy - d / 2, d, d))
            if rtl:
                right -= lay["dot_area"]
            else:
                x += lay["dot_area"]

        text_color = QColor(s.text_color)
        if self.state is State.ERROR:
            text_color = QColor(255, 196, 196)
        elif self.state in (State.LISTENING, State.PROCESSING, State.INFO):
            text_color = QColor(text_color).darker(115)
        text_color.setAlphaF(prof.text_opacity)
        outline = s.text_outline
        shadow = bg < 0.5  # thin background: keep text readable on bright scenes
        w = right - x
        align = Qt.AlignmentFlag.AlignRight if rtl else Qt.AlignmentFlag.AlignLeft
        flags = int(Qt.TextFlag.TextWordWrap | align)
        p.setFont(lay["main_font"])
        main_rect = QRect(x, PAD_Y, w, lay["main_h"])
        _draw_text(p, main_rect, flags, self._shown_text, text_color, shadow, outline)

        if self._secondary:
            sub = QColor(text_color)
            sub.setAlphaF(0.7 * prof.text_opacity)
            p.setFont(lay["sub_font"])
            top = PAD_Y + lay["main_h"] + 4
            sub_align = (
                Qt.AlignmentFlag.AlignRight
                if is_rtl_text(self._secondary)
                else Qt.AlignmentFlag.AlignLeft
            )
            sub_flags = int(Qt.TextFlag.TextWordWrap | sub_align)
            rect = QRect(x, top, w, self.height() - top - PAD_Y)
            _draw_text(p, rect, sub_flags, self._secondary, sub, shadow, outline)

        if self._badge and self.state is not State.LISTENING:
            red = QColor(DOT_COLORS["listening"])
            red.setAlphaF(0.45 + 0.55 * (1 - abs(1 - 2 * self._pulse / 20)))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(red)
            p.drawEllipse(QRectF(self.width() - 12, 6, 7, 7))
        p.end()

    def mousePressEvent(self, e) -> None:
        if not self._click_through and e.button() == Qt.MouseButton.LeftButton:
            self._drag_from = e.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, e) -> None:
        if self._drag_from is not None:
            self.move(e.globalPosition().toPoint() - self._drag_from)

    def mouseReleaseEvent(self, _e) -> None:
        if self._drag_from is None:
            return
        self._drag_from = None
        screen = self.screen() or QGuiApplication.primaryScreen()
        ox, oy = offset_for_point(
            self.profile.overlay_position,
            screen.geometry(),
            (self.width(), self.height()),
            self.pos(),
        )
        self.moved.emit(ox, oy)


def _draw_text(
    p: QPainter,
    rect: QRect,
    flags: int,
    text: str,
    color: QColor,
    shadow: bool,
    outline: bool = False,
):
    # Base direction follows the text itself, not the UI language: English stays left-to-right
    # ("Enemy spotted!") even in the Arabic UI, Arabic stays right-to-left.
    p.setLayoutDirection(
        Qt.LayoutDirection.RightToLeft if is_rtl_text(text) else Qt.LayoutDirection.LeftToRight
    )
    flags |= int(Qt.AlignmentFlag.AlignAbsolute)  # our Left/Right alignment is already explicit
    dark = QColor(0, 0, 0, int(210 * color.alphaF()))
    if outline:  # 1 px dark outline all around: readable over any scene
        p.setPen(dark)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            p.drawText(rect.translated(dx, dy), flags, text)
    elif shadow:
        p.setPen(dark)
        p.drawText(rect.translated(1, 1), flags, text)
    p.setPen(color)
    p.drawText(rect, flags, text)
