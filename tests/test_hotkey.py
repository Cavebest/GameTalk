import pytest

from gametalk import win32
from gametalk.hotkey import (
    SUPPORTED_HOTKEYS,
    hotkey_name,
    mouse_button_events,
    parse_hotkey,
)


def test_required_keys_supported():
    required = [f"F{i}" for i in range(1, 13)] + [
        "Insert",
        "Home",
        "End",
        "PageUp",
        "PageDown",
        "Mouse4",
        "Mouse5",
    ]
    for key in required:
        assert key in SUPPORTED_HOTKEYS


@pytest.mark.parametrize(
    "name, parsed",
    [
        ("F1", ("key", 0x70)),
        ("F9", ("key", 0x78)),
        ("F12", ("key", 0x7B)),
        ("PageDown", ("key", 0x22)),
        ("Mouse4", ("mouse", 4)),
        ("Mouse5", ("mouse", 5)),
    ],
)
def test_parse_and_name_round_trip(name, parsed):
    assert parse_hotkey(name) == parsed
    assert hotkey_name(*parsed) == name


def test_unknown_hotkey():
    with pytest.raises(ValueError):
        parse_hotkey("Space")
    assert hotkey_name("key", 0x41) is None


def test_mouse_button_flags():
    assert mouse_button_events(win32.RI_MOUSE_BUTTON_4_DOWN) == [(4, True)]
    assert mouse_button_events(win32.RI_MOUSE_BUTTON_5_UP) == [(5, False)]
    assert mouse_button_events(0x0001) == []  # left button: ignored
    both = win32.RI_MOUSE_BUTTON_4_UP | win32.RI_MOUSE_BUTTON_5_DOWN
    assert mouse_button_events(both) == [(4, False), (5, True)]


def test_listener_ignores_autorepeat_and_other_keys(qapp):
    from gametalk.hotkey import HotkeyListener

    h = HotkeyListener()
    h.set_hotkey("F9")
    events = []
    h.pressed.connect(lambda: events.append("down"))
    h.released.connect(lambda: events.append("up"))
    for kind, code, down in [
        ("key", 0x78, True),
        ("key", 0x78, True),
        ("key", 0x41, True),
        ("key", 0x78, False),
        ("key", 0x78, False),
    ]:
        h._handle(kind, code, down)
    assert events == ["down", "up"]


def test_listener_capture_mode(qapp):
    from gametalk.hotkey import HotkeyListener

    h = HotkeyListener()
    got = []
    h.captured.connect(got.append)
    pressed = []
    h.pressed.connect(lambda: pressed.append(1))
    h._capturing = True
    h._handle("key", 0x41, True)  # unsupported key: ignored, still capturing
    h._handle("mouse", 5, True)
    assert got == ["Mouse5"] and not h._capturing and not pressed
    h._capturing = True
    h._handle("key", 0x1B, True)  # Esc cancels
    assert got == ["Mouse5", ""]
