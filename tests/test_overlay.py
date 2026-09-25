import pytest
from PySide6.QtCore import QPoint, QRect

from gametalk.config import POSITIONS, OverlayStyle, Profile
from gametalk.overlay import anchor_point, offset_for_point

SCREEN = QRect(0, 0, 1920, 1080)


def test_top_center_default():
    assert anchor_point("top-center", SCREEN, (400, 50), (0, 48)) == QPoint(760, 48)


def test_bottom_right_offsets_are_inward():
    assert anchor_point("bottom-right", SCREEN, (400, 50), (20, 30)) == QPoint(1500, 1000)


def test_clamped_to_screen():
    assert anchor_point("top-left", SCREEN, (400, 50), (-500, -500)) == QPoint(0, 0)


@pytest.mark.parametrize("position", POSITIONS)
def test_offset_round_trip(position):
    size, off = (300, 60), (25, 40)
    pt = anchor_point(position, SCREEN, size, off)
    assert offset_for_point(position, SCREEN, size, pt) == off


def test_overlay_widget_states(qapp):
    from gametalk.overlay import Overlay, State

    o = Overlay()
    profile = Profile(display_seconds=2)
    o.apply(OverlayStyle(animation=False), profile)
    o.show_listening()
    assert o.state is State.LISTENING and o.isVisible()
    o.show_processing()
    assert o.state is State.PROCESSING
    o.show_result("Wait for me, I'm coming.")
    assert o.state is State.RESULT and o._hide_timer.isActive()
    assert o.width() <= Profile().max_width
    o.hide_now()
    assert o.state is State.HIDDEN and not o.isVisible()
    o.apply(OverlayStyle(animation=False), Profile(display_seconds=0))
    o.show_result("Stay behind me.")
    assert not o._hide_timer.isActive()  # never auto-hide
    o.hide_now()


LONG = " ".join(["Push B with me, rotate through mid, the sniper is on the roof"] * 12)


def test_long_translation_never_overflows_the_screen(qapp):
    from PySide6.QtGui import QGuiApplication

    from gametalk.overlay import MAX_HEIGHT_FRACTION, Overlay

    o = Overlay()
    o.apply(OverlayStyle(animation=False), Profile(font_size=28, max_width=5000))
    o.show_result(LONG)
    geo = QGuiApplication.primaryScreen().geometry()
    assert o.width() <= geo.width() - 32  # width clamped to the screen
    assert o.height() <= geo.height() * MAX_HEIGHT_FRACTION + 1
    assert geo.contains(o.geometry())
    o.hide_now()


def test_elide_to_lines(qapp):
    from PySide6.QtGui import QFont, QFontMetrics

    from gametalk.overlay import ELLIPSIS, elide_to_lines

    fm = QFontMetrics(QFont("Segoe UI", 14))
    short = "Stay behind me."
    assert elide_to_lines(fm, short, 400, 2) == short
    cut = elide_to_lines(fm, LONG, 400, 2)
    assert cut.endswith(ELLIPSIS) and len(cut) < len(LONG)
    assert LONG.startswith(cut[:-1].rstrip())  # a prefix, cut on a word boundary


def test_reading_time_grows_with_length():
    from gametalk.overlay import reading_seconds

    assert reading_seconds("Stay behind me.", 4) == 4
    assert reading_seconds(" ".join(["word"] * 30), 4) == 10  # 1.5 + 0.3 * 30
    assert reading_seconds(LONG, 4) == 15  # capped
    assert reading_seconds(LONG, 0) == 0  # "never auto-hide" untouched


def test_recording_badge_resets_on_next_state(qapp):
    from gametalk.overlay import Overlay

    o = Overlay()
    o.apply(OverlayStyle(animation=False), Profile())
    o.show_result("Wait for me.")
    o.set_recording_badge(True)
    assert o._badge and o._pulse_timer.isActive()
    o.show_processing()
    assert not o._badge and not o._pulse_timer.isActive()
    o.hide_now()
    assert not o._pulse_timer.isActive()  # nothing ticking while hidden
