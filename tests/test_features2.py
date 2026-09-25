import json

import numpy as np
import pytest

from gametalk.config import Correction, Settings, settings_from_dict, validate
from gametalk.translate import TranslationRequest, run_pipeline, run_text_pipeline

# ---------------------------------------------------------------- usage counter


def test_usage_counts_warns_once_and_rolls_over(tmp_path):
    from gametalk.usage import SPEECH_FREE_SECONDS, TRANSLATOR_FREE_CHARS, UsageTracker

    now = [1_780_000_000.0]  # some day in 2026
    u = UsageTracker(tmp_path / "usage.json", clock=lambda: now[0])
    assert u.add(speech_seconds=SPEECH_FREE_SECONDS * 0.5) == []
    assert u.add(speech_seconds=SPEECH_FREE_SECONDS * 0.31) == ["speech:0.8"]
    assert u.add(speech_seconds=1) == []  # warned already
    assert u.add(translator_chars=TRANSLATOR_FREE_CHARS) == ["translator:0.8", "translator:1.0"]
    u.save()
    again = UsageTracker(tmp_path / "usage.json", clock=lambda: now[0])
    assert again.current.translator_chars == TRANSLATOR_FREE_CHARS
    now[0] += 40 * 86400  # next month
    assert UsageTracker(tmp_path / "usage.json", clock=lambda: now[0]).current.speech_seconds == 0


def test_usage_file_holds_no_content(tmp_path):
    from gametalk.usage import UsageTracker

    u = UsageTracker(tmp_path / "usage.json")
    u.add(speech_seconds=3.5, translator_chars=42)
    u.save()
    data = json.loads((tmp_path / "usage.json").read_text(encoding="utf-8"))
    assert set(data) == {
        "month",
        "speech_seconds",
        "translator_chars",
        "warned_speech",
        "warned_translator",
    }


# ---------------------------------------------------------------- phrasebook


def test_phrasebook_counts_and_only_persists_when_enabled(tmp_path):
    from gametalk.phrasebook import Phrasebook

    path = tmp_path / "phrasebook.json"
    book = Phrasebook(path, persistent=False)
    book.add("Cover me!", "غطيني")
    book.add("cover me")
    book.save()
    assert book.count("COVER ME.") == 2 and not path.exists()  # learning off: nothing on disk
    book.set_persistent(True)
    book.add("Fall back!")
    book.save()
    loaded = Phrasebook(path, persistent=True)
    assert loaded.count("cover me") == 2 and loaded.entries["cover me"].arabic == "غطيني"
    loaded.set_known("Fall back!", True)
    assert loaded.practice_order()[0].english == "Cover me!"  # unknown first
    loaded.clear()
    assert Phrasebook(path, persistent=True).entries == {}


# ---------------------------------------------------------------- Arabic corrections


def test_default_arabic_corrections_normalise_dialect():
    from gametalk.translate import apply_corrections

    s = validate(Settings())
    rules = tuple((c.find, c.replace) for c in s.profile.arabic_corrections)
    assert apply_corrections("خليكم وراي", rules) == "ابقوا خلفي"
    assert apply_corrections("استنوني شوي أنا جاي", rules) == "انتظروني قليلاً أنا قادم"
    assert apply_corrections("والعدو هون", rules) == "والعدو هنا"  # untouched word kept


class Cloud:
    def __init__(self):
        self.sent = []

    def recognize(self, audio, locale, phrases=()):
        return "خليكم وراي"

    def translate(self, text, source, target):
        self.sent.append(text)
        return "Stay behind me"


SPEECH = (0.2 * np.sin(np.arange(16000) / 5)).astype(np.float32)


def test_arabic_corrections_applied_before_azure_translation():
    cloud = Cloud()
    req = TranslationRequest(
        "ar",
        speech_provider="azure",
        translation_provider="azure",
        show_source=True,
        source_corrections=(("خليكم", "ابقوا"), ("وراي", "خلفي")),
    )
    r = run_pipeline(SPEECH, req, None, cloud)
    assert cloud.sent == ["ابقوا خلفي"]  # corrected text translated
    assert r.source_text == "خليكم وراي"  # user sees what they actually said
    assert r.azure_audio_seconds == pytest.approx(1.0) and r.azure_chars == len("ابقوا خلفي")


class LocalArEn:
    def __init__(self):
        self.got = []

    def translate(self, text):
        self.got.append(text)
        return "stay behind me"


def test_text_pipeline_local_and_azure():
    mt = LocalArEn()
    req = TranslationRequest("ar", source_corrections=(("خليكم", "ابقوا"),), pronounce=True)
    r = run_text_pipeline("  خليكم   وراي ", req, "local", None, mt)
    assert mt.got == ["ابقوا وراي"] and r.text == "Stay behind me." and r.pronunciation
    assert r.source_text == "خليكم وراي" and r.azure_chars == 0
    cloud = Cloud()
    r = run_text_pipeline("خليكم وراي", TranslationRequest("ar"), "azure", cloud, None)
    assert r.text == "Stay behind me." and r.azure_chars == len("خليكم وراي")
    assert run_text_pipeline("   ", req, "local", None, mt).text == ""


# ---------------------------------------------------------------- sounds


def test_sound_cues_are_short_and_quiet():
    from gametalk.sounds import CUES, RATE, _tone

    for freqs in CUES.values():
        wave = _tone(freqs, volume=1.0)
        assert wave.size / RATE < 0.15 and float(np.max(np.abs(wave))) <= 0.36


# ---------------------------------------------------------------- controller wiring


@pytest.fixture
def ctx(qapp, tmp_path):
    from PySide6.QtCore import QObject, Signal
    from test_controller import FakeHotkey, FakeOverlay, FakeRecorder, FakeSpeech

    from gametalk.app import Controller
    from gametalk.config import ConfigStore

    class Voice(QObject):
        segment = Signal(object)
        failed = Signal(str)

        def __init__(self):
            super().__init__()
            self.active = False
            self.muted = False

        def start(self, device="", sensitivity=50):
            self.active, self.started = True, (device, sensitivity)

        def stop(self):
            self.active = False

    sounds = []
    hk, sp, rec, ov, voice = FakeHotkey(), FakeSpeech(), FakeRecorder(), FakeOverlay(), Voice()
    c = Controller(
        ConfigStore(tmp_path / "c.json"),
        validate(Settings()),
        speech=sp,
        recorder=rec,
        hotkey=hk,
        overlay=ov,
        voice=voice,
        play_sound=lambda cue, vol: sounds.append(cue),
        key_is_down=lambda vk: True,
        exclusive_fullscreen=lambda: False,
    )
    c.start()
    return c, hk, sp, rec, ov, voice, sounds


def _set(c, **features):
    new = c.settings.clone()
    for k, v in features.items():
        setattr(new.features, k, v)
    c.apply_settings(new)


def test_sound_cues_follow_their_switch(ctx):
    from test_controller import release

    c, hk, sp, rec, ov, voice, sounds = ctx
    hk.pressed.emit("ptt")
    release(c, hk)
    assert sounds == []
    _set(c, sound_cues=True)
    hk.pressed.emit("ptt")
    release(c, hk)
    assert sounds == ["start", "stop"]


def test_clipboard_suggestions_and_usage(ctx, qapp):
    from PySide6.QtGui import QGuiApplication

    from gametalk.translate import TranslationResult

    c, hk, sp, rec, ov, voice, sounds = ctx
    _set(c, copy_to_clipboard=True)
    notes = []
    c._notify = lambda m, error=False: notes.append(m)
    for _ in range(3):
        sp.finished.emit("ptt", TranslationResult(text="Cover me!", azure_chars=10))
    assert QGuiApplication.clipboard().text() == "Cover me!"
    assert len([n for n in notes if "Cover me!" in n]) == 1  # suggested once
    assert c.phrase_suggestions() == ["Cover me!"]
    assert c.usage.current.translator_chars == 30
    c.add_quick_phrase("Cover me!")
    assert c.phrase_suggestions() == []


def test_open_mic_mode(ctx):
    c, hk, sp, rec, ov, voice, sounds = ctx
    assert not voice.active
    new = c.settings.clone()
    new.profile.hotkey_mode = "voice"
    new.features.voice_sensitivity = 70
    c.apply_settings(new)
    assert voice.active and voice.started == ("", 70)
    voice.segment.emit(SPEECH)
    job = sp.jobs[-1]
    assert job.tag == "voice" and job.speech_gate is True
    from gametalk.translate import TranslationResult

    sp.finished.emit("voice", TranslationResult(text=""))
    assert ov.last == ("hide_now",)  # noise: no "didn't catch that" nagging
    hk.pressed.emit("ptt")  # the talk key mutes in open-mic mode
    assert voice.muted and not rec.active
    new = c.settings.clone()
    new.profile.hotkey_mode = "push"
    c.apply_settings(new)
    assert not voice.active


def test_quick_text_flow(ctx, monkeypatch):
    from gametalk.translate import TranslationResult

    c, hk, sp, rec, ov, voice, sounds = ctx
    assert "quicktext" not in hk.bindings
    _set(c, quick_text_enabled=True)
    assert hk.bindings["quicktext"] == "F8"
    assert sp.text_mt_wanted is True  # no Azure key -> offline model prepared

    class Box:
        def __init__(self):
            self.results = []

        def show_result(self, text, extra=""):
            self.results.append(text)

        def show_error(self, m):
            self.results.append("ERR " + m)

    c._quick_text = Box()
    c.translate_text("خليكم وراي")
    job = sp.jobs[-1]
    assert job.tag == "text" and job.text == "خليكم وراي" and job.text_translator == "local"
    assert ("خليكم", "ابقوا") in job.request.source_corrections
    sp.finished.emit("text", TranslationResult(text="Stay behind me."))
    assert c._quick_text.results == ["Stay behind me."]
    assert ov.last[:2] == ("show_result", "Stay behind me.")


def test_worker_speech_gate_drops_non_speech(qapp, monkeypatch):
    import gametalk.speech as sp_mod
    import gametalk.teammates as tm

    monkeypatch.setattr(tm, "is_speech", lambda audio: False)
    called = []
    monkeypatch.setattr(sp_mod, "run_pipeline", lambda *a, **k: called.append(1))
    w = sp_mod._Worker()
    out = []
    w.finished.connect(lambda tag, r: out.append((tag, r.text)))
    w.process(sp_mod.Job(SPEECH, TranslationRequest("ar"), "voice", speech_gate=True))
    assert out == [("voice", "")] and called == []


# ---------------------------------------------------------------- profile export / import


def test_profile_export_import_round_trip(qapp, tmp_path, monkeypatch):
    from test_settings_dialog import make_controller

    from gametalk import settings_dialog
    from gametalk.config import QuickPhrase
    from gametalk.settings_dialog import SettingsDialog

    c = make_controller(tmp_path)
    dlg = SettingsDialog(c)
    dlg.cur.quick_phrases = [QuickPhrase("Numpad9", "Rotate B!")]
    dlg.cur.corrections = [Correction("Zafira", "ammo")]
    dlg._load_profile(dlg.cur)
    out = tmp_path / "cs2.gametalk.json"
    monkeypatch.setattr(
        settings_dialog.QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: (str(out), ""))
    )
    monkeypatch.setattr(
        settings_dialog.QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: (str(out), ""))
    )
    monkeypatch.setattr(settings_dialog.QMessageBox, "information", staticmethod(lambda *a: None))
    dlg._export_profile()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["profile"]["quick_phrases"] == [{"key": "Numpad9", "text": "Rotate B!"}]
    assert "azure" not in data["profile"] and "speech_key" not in json.dumps(data)  # no keys
    dlg._import_profile()
    names = [p.name for p in dlg.s.profiles]
    assert names == ["Default", "Default (2)"]  # never overwrites
    imported = dlg.s.find_profile("Default (2)")
    assert imported.corrections == [Correction("Zafira", "ammo")]
    dlg.reject()


def test_import_rejects_garbage(qapp, tmp_path, monkeypatch):
    from test_settings_dialog import make_controller

    from gametalk import settings_dialog
    from gametalk.settings_dialog import SettingsDialog

    bad = tmp_path / "bad.json"
    bad.write_text('{"hello": 1}', encoding="utf-8")
    warnings = []
    monkeypatch.setattr(
        settings_dialog.QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: (str(bad), ""))
    )
    monkeypatch.setattr(
        settings_dialog.QMessageBox, "warning", staticmethod(lambda *a: warnings.append(a))
    )
    dlg = SettingsDialog(make_controller(tmp_path))
    dlg._import_profile()
    assert warnings and len(dlg.s.profiles) == 1
    dlg.reject()


# ---------------------------------------------------------------- self-test


def test_self_test_checks(monkeypatch):
    import gametalk.speech as sp_mod
    from gametalk.azure import AzureCredentials
    from gametalk.diagnostics import report_text, run_checks

    monkeypatch.setattr(sp_mod, "cuda_device_count", lambda: 1)
    facts = {
        "loaded": True,
        "loading": False,
        "summary": "small on CPU (int8)",
        "last_error": "",
        "model": "small",
        "uses_whisper": True,
        "device_pref": "auto",
        "microphone": "",
        "recording": False,
        "voice_mode": False,
        "hotkey_running": True,
        "bindings": {"ptt": "F9"},
        "overlay_ok": True,
        "tray": True,
        "azure_needed": False,
        "creds": AzureCredentials(),
        "team_enabled": False,
        "team_device": "",
        "team_local": False,
        "text_local": False,
        "gamepad": False,
        "exclusive_fullscreen": True,
    }
    checks = run_checks(facts, open_mic=lambda dev: np.zeros(16000, np.float32))
    by_title = {c.title: c for c in checks}
    assert by_title["Graphics card"].status == "warn"  # GPU present but running on CPU
    assert by_title["Microphone"].status == "fail" and "Privacy" in by_title["Microphone"].fix
    assert by_title["Fullscreen"].status == "warn"
    assert by_title["Hotkeys"].status == "ok" and "F9" in by_title["Hotkeys"].detail
    text = report_text(checks)
    assert "self-test" in text and "❌" in text


def test_settings_load_new_feature_fields():
    s = settings_from_dict(
        {
            "features": {"sound_volume": 500, "quick_text_translator": "x"},
            "profiles": [
                {"hotkey_mode": "voice", "arabic_corrections": [{"find": "", "replace": "x"}]}
            ],
        }
    )
    assert s.features.sound_volume == 100 and s.features.quick_text_translator == "auto"
    assert s.profile.hotkey_mode == "voice" and s.profile.arabic_corrections == []
