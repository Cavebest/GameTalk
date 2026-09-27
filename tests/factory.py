"""A Controller wired to fakes (no mic, hotkeys, model or overlay), for window/backend tests."""

from test_controller import FakeHotkey, FakeOverlay, FakeRecorder, FakeSpeech

from gametalk.app import Controller
from gametalk.config import ConfigStore, Settings, validate


def make_controller(tmp_path):
    c = Controller(
        ConfigStore(tmp_path / "c.json"),
        validate(Settings()),
        speech=FakeSpeech(),
        recorder=FakeRecorder(),
        hotkey=FakeHotkey(),
        overlay=FakeOverlay(),
    )
    c.hotkey.captures = []
    c.hotkey.begin_capture = lambda: c.hotkey.captures.append("begin")
    c.hotkey.cancel_capture = lambda: c.hotkey.captures.append("cancel")
    c.start()
    return c
