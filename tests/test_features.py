import ctypes

import numpy as np
import pytest

from gametalk.config import Correction, QuickPhrase, Settings, settings_from_dict, validate
from gametalk.translate import (
    TeamRequest,
    TranslationRequest,
    apply_corrections,
    run_pipeline,
    run_team_pipeline,
)

# ---------------------------------------------------------------- corrections


def test_corrections_whole_words_case_insensitive_no_loops():
    rules = (("Zafira", "ammo"), ("Shawa", "a bit"))
    assert apply_corrections("I need Zafira, wait Shawa.", rules) == "I need ammo, wait a bit."
    assert apply_corrections("ZAFIRA zafira Zafiras", rules[:1]) == "ammo ammo Zafiras"
    assert apply_corrections("a b ab", (("a", "b"), ("b", "a"))) == "b a ab"  # swap, no loop
    assert apply_corrections("ammonia ammo", (("ammo", "bullets"),)) == "ammonia bullets"
    assert apply_corrections("C4 on B", (("c4", "the bomb"),)) == "the bomb on B"
    assert apply_corrections("anything", ()) == "anything"


class Whisper:
    def decode(self, audio, task, language, prompt):
        return "i need zafira", "ar"


def test_corrections_and_pronunciation_in_pipeline():
    req = TranslationRequest("ar", corrections=(("zafira", "ammo"),), pronounce=True)
    r = run_pipeline(np.zeros(16000, np.float32), req, Whisper(), None)
    assert r.text == "I need ammo."
    assert r.pronunciation == "آي نيد أمو."


def test_config_cleans_phrases_and_corrections():
    s = settings_from_dict(
        {
            "features": {"replay_hotkey": "F10"},
            "profiles": [
                {
                    "hotkey": "F9",
                    "quick_phrases": [
                        {"key": "F9", "text": "steals the talk key"},
                        {"key": "Numpad1", "text": "  Enemy   spotted! "},
                        {"key": "Numpad1", "text": "duplicate key"},
                        {"key": "Numpad2", "text": ""},
                        "garbage",
                    ],
                    "corrections": [
                        {"find": "Zafira", "replace": "ammo"},
                        {"find": "zafira", "replace": "dup"},
                        {"find": "", "replace": "x"},
                    ],
                }
            ],
        }
    )
    p = s.profile
    assert [(q.key, q.text) for q in p.quick_phrases] == [
        ("", "steals the talk key"),
        ("Numpad1", "Enemy spotted!"),
        ("", "duplicate key"),
    ]
    assert p.corrections == [Correction("Zafira", "ammo")]


def test_features_and_teammates_validated():
    s = settings_from_dict(
        {
            "features": {"history_size": 999, "gamepad_button": "Z", "ui_language": "xx"},
            "teammates": {"translator": "local", "target_language": "fr", "sensitivity": 500},
            "overlay": {"text_color": "red", "background_color": "#123456"},
        }
    )
    assert s.features.history_size == 50
    assert s.features.gamepad_button == "RB"
    assert s.features.ui_language == "auto"
    assert s.teammates.target_language == "ar"  # offline model is EN->AR only
    assert s.teammates.sensitivity == 100
    assert s.overlay.text_color == "#f5f7fa" and s.overlay.background_color == "#123456"


# ---------------------------------------------------------------- pronunciation


def test_pronunciation_helper():
    from gametalk.pronounce import to_arabic

    assert to_arabic("Wait for me, I'm coming.") == "وايت فور مي، آيم كامينغ."
    assert to_arabic("Fall back, the tank is coming!") == "فول باك، ذا تانك إز كامينغ!"
    assert to_arabic("Reloading") == "ريلودينغ"  # not in the dictionary: suffix rule
    assert to_arabic("Is he 5v5?").endswith("؟")
    assert to_arabic("") == ""


# ---------------------------------------------------------------- teammates


def test_segmenter_cuts_speech_and_ignores_clicks():
    from gametalk.teammates import BLOCK, Segmenter

    seg = Segmenter(sensitivity=50)
    quiet = np.zeros(BLOCK, np.float32)
    loud = (0.1 * np.sin(np.arange(BLOCK) / 5)).astype(np.float32)
    out = [seg.feed(b) for b in [quiet] * 5 + [loud] * 10 + [quiet] * 6]
    segments = [o for o in out if o is not None]
    assert len(segments) == 1
    assert segments[0].size == BLOCK * (3 + 10 + 6)  # pre-roll + speech + trailing silence
    click = [seg.feed(b) for b in [loud] + [quiet] * 6]
    assert all(o is None for o in click)  # 0.1 s of noise isn't worth transcribing


def test_segmenter_caps_long_speech():
    from gametalk.teammates import BLOCK, MAX_SEGMENT_S, Segmenter

    seg = Segmenter(50)
    loud = (0.1 * np.ones(BLOCK)).astype(np.float32)
    outs = [seg.feed(loud) for _ in range(int(MAX_SEGMENT_S * 10) + 5)]
    assert sum(o is not None for o in outs) == 1


class Cloud:
    def __init__(self):
        self.calls = []

    def recognize(self, audio, locale, phrases=()):
        self.calls.append(("recognize", locale))
        return "Enemy on the roof"

    def translate(self, text, source, target):
        self.calls.append(("translate", source, target))
        return "العدو على السطح"


class EnglishWhisper:
    def decode(self, audio, task, language, prompt):
        assert (task, language) == ("transcribe", "en")
        return " Enemy on the roof ", "en"


class LocalMT:
    def translate(self, text):
        return "العدو على السطح"


AUDIO = (0.1 * np.sin(np.arange(16000) / 5)).astype(np.float32)


def test_team_pipeline_local_whisper_and_offline_model():
    r = run_team_pipeline(AUDIO, TeamRequest(show_original=True), EnglishWhisper(), None, LocalMT())
    assert r.text == "العدو على السطح" and r.source_text == "Enemy on the roof"


def test_team_pipeline_azure_both_ways_and_speech_gate():
    cloud = Cloud()
    req = TeamRequest(recognizer="azure", translator="azure", target_language="ar")
    r = run_team_pipeline(AUDIO, req, None, cloud, None, speech_check=lambda a: True)
    assert r.text == "العدو على السطح"
    assert cloud.calls == [("recognize", "en-US"), ("translate", "en", "ar")]
    cloud.calls.clear()
    r = run_team_pipeline(AUDIO, req, None, cloud, None, speech_check=lambda a: False)
    assert r.text == "" and cloud.calls == []  # gunfire never reaches Azure


def test_team_pipeline_no_translation_shows_english():
    r = run_team_pipeline(AUDIO, TeamRequest(translator="none"), EnglishWhisper(), None, None)
    assert r.text == "Enemy on the roof" and r.source_text == ""


# ---------------------------------------------------------------- gamepad


class FakeXInput:
    """Stand-in for XInputGetState: slot 0 connected, state set by the test."""

    def __init__(self):
        self.buttons = 0
        self.lt = self.rt = 0
        self.connected = True

    def __call__(self, slot, state_ptr):
        if slot != 0 or not self.connected:
            return 1167  # ERROR_DEVICE_NOT_CONNECTED
        from gametalk.gamepad import XINPUT_STATE

        st = ctypes.cast(state_ptr, ctypes.POINTER(XINPUT_STATE)).contents
        st.Gamepad.wButtons = self.buttons
        st.Gamepad.bLeftTrigger = self.lt
        st.Gamepad.bRightTrigger = self.rt
        return 0


def test_gamepad_press_release_and_unplug(qapp):
    from gametalk.gamepad import BUTTON_MASKS, GamepadListener, pressed_buttons

    assert pressed_buttons(BUTTON_MASKS["RB"] | BUTTON_MASKS["A"], 200, 0) == {"RB", "A", "LT"}
    x = FakeXInput()
    pad = GamepadListener(get_state=x)
    pad.set_bindings({"ptt": "RB", "replay": "Y"})
    events = []
    pad.pressed.connect(lambda a: events.append(("down", a)))
    pad.released.connect(lambda a: events.append(("up", a)))
    x.buttons = BUTTON_MASKS["RB"]
    pad.poll_once(0)
    pad.poll_once(0)  # held: no repeat
    x.buttons = BUTTON_MASKS["RB"] | BUTTON_MASKS["Y"]
    pad.poll_once(0)
    x.connected = False
    assert pad.poll_once(0) is False  # unplugged while held -> everything released
    assert events == [("down", "ptt"), ("down", "replay"), ("up", "ptt"), ("up", "replay")] or (
        events[:2] == [("down", "ptt"), ("down", "replay")] and len(events) == 4
    )


# ---------------------------------------------------------------- hotkey bindings


def test_hotkey_multiple_bindings(qapp):
    from gametalk.hotkey import KEYBOARD_KEYS, HotkeyListener

    h = HotkeyListener()
    h.set_bindings({"ptt": "F9", "replay": "F10", "phrase:0": "Numpad1", "phrase:1": "F9"})
    assert h.bindings() == {"ptt": "F9", "replay": "F10", "phrase:0": "Numpad1"}  # F9 kept by ptt
    events = []
    h.pressed.connect(lambda a: events.append(("down", a)))
    h.released.connect(lambda a: events.append(("up", a)))
    h._handle("key", KEYBOARD_KEYS["F10"], True)
    h._handle("key", KEYBOARD_KEYS["Numpad1"], True)
    h._handle("key", KEYBOARD_KEYS["Numpad1"], True)  # auto-repeat ignored
    h._handle("key", KEYBOARD_KEYS["F10"], False)
    assert events == [("down", "replay"), ("down", "phrase:0"), ("up", "replay")]


# ---------------------------------------------------------------- controller wiring


@pytest.fixture
def ctx(qapp, tmp_path):
    from test_controller import FakeHotkey, FakeOverlay, FakeRecorder, FakeSpeech

    from gametalk.app import Controller
    from gametalk.config import ConfigStore
    from gametalk.gamepad import GamepadListener
    from gametalk.teammates import TeammateListener

    class Team(TeammateListener):
        def start(self, device="", sensitivity=50):
            self.started = (device, sensitivity)

        def stop(self):
            self.started = None

    class Pad(GamepadListener):
        def start(self):
            self.on = True

        def stop(self):
            self.on = False

    settings = validate(Settings())
    hk, sp, rec, ov, subs = FakeHotkey(), FakeSpeech(), FakeRecorder(), FakeOverlay(), FakeOverlay()
    pad, team = Pad(), Team()
    c = Controller(
        ConfigStore(tmp_path / "c.json"),
        settings,
        speech=sp,
        recorder=rec,
        hotkey=hk,
        overlay=ov,
        gamepad=pad,
        teammates=team,
        subtitles=subs,
        key_is_down=lambda vk: True,
        exclusive_fullscreen=lambda: False,
    )
    c.start()
    return c, hk, sp, rec, ov, subs, pad, team


def test_replay_and_history(ctx):
    from gametalk.translate import TranslationResult

    c, hk, sp, rec, ov, *_ = ctx
    hk.pressed.emit("replay")
    assert ov.last[0] == "show_info"  # nothing yet
    hk.pressed.emit("ptt")
    hk.released.emit("ptt")
    c._release_timer.stop()
    c._finish_recording()
    sp.finished.emit("ptt", TranslationResult(text="Stay behind me.", pronunciation="ستاي"))
    hk.pressed.emit("replay")
    assert ov.last == ("show_result", "Stay behind me.", "ستاي")
    assert [h.text for h in c.history] == ["Stay behind me."]
    c.show_history_item(0)
    assert ov.last == ("show_result", "Stay behind me.", "ستاي")


def test_history_and_replay_can_be_switched_off(ctx):
    c, hk, sp, rec, ov, *_ = ctx
    new = c.settings.clone()
    new.features.replay_enabled = False
    new.features.history_enabled = False
    c.apply_settings(new)
    assert "replay" not in hk.bindings
    c._remember("x", "", "you")
    assert not c.history


def test_quick_phrases_bound_and_shown_instantly(ctx):
    c, hk, sp, rec, ov, *_ = ctx
    assert not any(a.startswith("phrase:") for a in hk.bindings)  # off by default
    new = c.settings.clone()
    new.features.quick_phrases_enabled = True
    new.profile.quick_phrases = [QuickPhrase("Numpad7", "Rotate B!")]
    c.apply_settings(new)
    assert hk.bindings["phrase:0"] == "Numpad7"
    hk.pressed.emit("phrase:0")
    assert ov.last == ("show_result", "Rotate B!", "")
    assert not sp.jobs and not rec.active  # no recording, no engine


def test_gamepad_and_teammates_follow_their_switches(ctx):
    c, hk, sp, rec, ov, subs, pad, team = ctx
    assert pad.on is False and team.started is None  # both off by default
    new = c.settings.clone()
    new.features.gamepad_enabled = True
    new.teammates.enabled = True
    new.teammates.sensitivity = 70
    c.apply_settings(new)
    assert pad.on is True and pad._bindings == {"RB": "ptt"}
    assert team.started == ("", 70)
    assert sp.local_mt_wanted is True  # offline translator prepared
    pad.pressed.emit("ptt")
    assert c.recording
    hk.released.emit("ptt")  # the keyboard can't end a controller recording
    assert not c._release_timer.isActive()
    pad.released.emit("ptt")
    assert c._release_timer.isActive()


def test_team_segments_are_rate_limited_and_shown_in_subtitles(ctx):
    from gametalk.translate import TranslationResult

    c, hk, sp, rec, ov, subs, pad, team = ctx
    new = c.settings.clone()
    new.teammates.enabled = True
    c.apply_settings(new)
    c._on_team_segment(AUDIO)
    c._on_team_segment(AUDIO)  # one in flight at a time
    team_jobs = [j for j in sp.jobs if j.tag == "team"]
    assert len(team_jobs) == 1 and team_jobs[0].team.translator == "local"
    sp.finished.emit("team", TranslationResult(text="العدو على السطح", source_text=""))
    assert subs.last == ("show_result", "العدو على السطح", "")
    assert ov.calls == [c for c in ov.calls if c[0] != "show_result"]  # main overlay untouched
    hk.pressed.emit("ptt")  # while you talk, teammates are ignored
    c._on_team_segment(AUDIO)
    assert len([j for j in sp.jobs if j.tag == "team"]) == 1
