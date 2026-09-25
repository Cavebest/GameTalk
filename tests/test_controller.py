import numpy as np
import pytest
from PySide6.QtCore import QObject, Signal

from gametalk.app import Controller, Phase
from gametalk.audio import MicrophoneError
from gametalk.config import ConfigStore, Profile, Settings, validate
from gametalk.translate import TranslationResult


class FakeHotkey(QObject):
    pressed = Signal(str)
    released = Signal(str)
    captured = Signal(str)
    foreground_changed = Signal(str)
    failed = Signal(str)

    def __init__(self):
        super().__init__()
        self.hotkey = None
        self.watch = None
        self.resets = 0

    def start(self, bindings, watch):
        self.set_bindings(bindings)
        self.watch = watch

    def set_bindings(self, bindings):
        self.bindings = dict(bindings)
        self.hotkey = self.bindings.get("ptt")

    def stop(self):
        pass

    def set_hotkey(self, name):
        self.hotkey = name

    def set_watch_foreground(self, watch):
        self.watch = watch

    def reset_state(self):
        self.resets += 1


class FakeSpeech(QObject):
    status = Signal(str)
    ready = Signal(str, str)
    load_failed = Signal(str)
    finished = Signal(str, object)
    failed = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.config = None
        self.loaded = False
        self.loading = False
        self.last_error = ""
        self.summary = "small on CUDA (float16)"
        self.jobs = []
        self.prewarmed = []
        self.loads = 0

    def load(self, cfg):
        self.config, self.loaded, self.loads = cfg, True, self.loads + 1

    def process(self, job):
        self.jobs.append(job)

    def prewarm(self, creds):
        self.prewarmed.append(creds)

    def prepare_local_mt(self, wanted):
        self.local_mt_wanted = wanted

    def prepare_text_mt(self, wanted):
        self.text_mt_wanted = wanted

    def shutdown(self):
        pass


class FakeRecorder:
    def __init__(self):
        self.active = False
        self.level = 0.0
        self.audio = np.full(16000, 0.1, np.float32)
        self.error = None
        self.device = None

    def start(self, device=""):
        if self.error:
            raise self.error
        self.active, self.device = True, device

    def stop(self):
        self.active = False
        return self.audio


class FakeOverlay:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def record(*args):
            self.calls.append((name, *args))

        return record

    @property
    def last(self):
        return self.calls[-1]


@pytest.fixture
def ctx(qapp, tmp_path):
    settings = validate(Settings())
    hk, sp, rec, ov = FakeHotkey(), FakeSpeech(), FakeRecorder(), FakeOverlay()
    c = Controller(
        ConfigStore(tmp_path / "c.json"),
        settings,
        speech=sp,
        recorder=rec,
        hotkey=hk,
        overlay=ov,
        key_is_down=lambda vk: KEY_DOWN[0],
        exclusive_fullscreen=lambda: FULLSCREEN[0],
    )
    KEY_DOWN[0], FULLSCREEN[0] = True, False
    c.start()
    return c, hk, sp, rec, ov


KEY_DOWN = [True]  # what the fake GetAsyncKeyState reports
FULLSCREEN = [False]


def release(c, hk):
    """Key-up plus the 40 ms debounce elapsing."""
    hk.released.emit("ptt")
    if c._release_timer.isActive():
        c._release_timer.stop()
        c._finish_recording()


def test_start_loads_model_once_and_registers_hotkey(ctx):
    c, hk, sp, *_ = ctx
    assert hk.hotkey == "F9"
    assert sp.loads == 1 and sp.config.model == "small"


def test_push_to_talk_happy_path(ctx):
    c, hk, sp, rec, ov = ctx
    hk.pressed.emit("ptt")
    assert c.phase is Phase.RECORDING and rec.active
    assert ov.last == ("show_listening",)
    release(c, hk)
    assert c.phase is Phase.PROCESSING and ov.last == ("show_processing",)
    job = sp.jobs[0]
    assert job.request.language == "ar" and job.request.speech_provider == "whisper-local"
    assert job.azure is None  # local mode sends nothing anywhere
    assert "Medic" in job.request.vocabulary
    sp.finished.emit("ptt", TranslationResult(text="Wait for me, I'm coming."))
    assert c.phase is Phase.IDLE
    assert ov.last == ("show_result", "Wait for me, I'm coming.", "")


def test_auto_detect_passes_no_language(ctx):
    c, hk, sp, *_ = ctx
    c.settings.profile.auto_detect_language = True
    hk.pressed.emit("ptt")
    release(c, hk)
    assert sp.jobs[0].request.language is None


def test_accidental_tap_gets_a_neutral_hint(ctx):
    c, hk, sp, rec, ov = ctx
    rec.audio = np.full(1000, 0.1, np.float32)
    hk.pressed.emit("ptt")
    release(c, hk)
    assert c.phase is Phase.IDLE and not sp.jobs
    assert ov.last == ("show_info", "Hold F9 while you speak.", 2)  # not a red error


def test_silent_mic_hint(ctx):
    c, hk, sp, rec, ov = ctx
    rec.audio = np.zeros(16000, np.float32)
    hk.pressed.emit("ptt")
    release(c, hk)
    assert ov.last[0] == "show_error" and "muted" in ov.last[1]


def test_microphone_failure_is_reported_not_raised(ctx):
    c, hk, sp, rec, ov = ctx
    rec.error = MicrophoneError("No microphone found.")
    hk.pressed.emit("ptt")
    assert c.phase is Phase.IDLE
    assert ov.last == ("show_error", "No microphone found.")
    release(c, hk)
    assert not sp.jobs


def test_model_loading_blocks_recording(ctx):
    c, hk, sp, rec, ov = ctx
    sp.loaded, sp.loading = False, True
    hk.pressed.emit("ptt")
    assert c.phase is Phase.IDLE and not rec.active
    assert "loading" in ov.last[1]


def test_model_load_failure_message(ctx):
    c, hk, sp, rec, ov = ctx
    sp.loaded, sp.last_error = False, "Speech model 'small' is missing"
    hk.pressed.emit("ptt")
    assert ov.last == ("show_error", "Speech model 'small' is missing")


def test_second_sentence_records_while_first_is_processing(ctx):
    c, hk, sp, rec, ov = ctx
    hk.pressed.emit("ptt")
    release(c, hk)
    hk.pressed.emit("ptt")  # user keeps talking before the first translation is back
    assert c.phase is Phase.RECORDING and c.pending == 1 and rec.active
    sp.finished.emit("ptt", TranslationResult(text="Wait for me."))
    assert ov.calls[-2] == ("show_result", "Wait for me.", "")
    assert ov.last == ("set_recording_badge", True)  # result shown, still recording
    release(c, hk)
    assert len(sp.jobs) == 2 and c.pending == 1 and c.phase is Phase.PROCESSING
    sp.finished.emit("ptt", TranslationResult(text="I'm coming."))
    assert c.phase is Phase.IDLE and ov.last == ("show_result", "I'm coming.", "")


def test_mouse_button_chatter_does_not_split_a_recording(ctx):
    c, hk, sp, rec, ov = ctx
    hk.pressed.emit("ptt")
    hk.released.emit("ptt")  # bounce: release...
    hk.pressed.emit("ptt")  # ...and press again within the debounce window
    assert c._release_timer.isActive() is False and c.recording
    release(c, hk)
    assert len(sp.jobs) == 1


def test_missed_key_up_is_caught_by_the_key_watchdog(ctx):
    c, hk, sp, rec, ov = ctx
    hk.pressed.emit("ptt")
    assert c._key_watch.isActive()
    c._check_key_still_down()  # key still physically down: keep recording
    assert c.recording
    KEY_DOWN[0] = False  # key-up never arrived (e.g. focus moved to an admin window)
    c._check_key_still_down()
    assert c.recording  # one reading isn't trusted
    c._check_key_still_down()
    assert not c.recording and len(sp.jobs) == 1 and hk.resets == 1
    assert not c._key_watch.isActive()


def test_no_key_watchdog_in_toggle_mode_or_when_idle(ctx):
    c, hk, sp, rec, ov = ctx
    assert not c._key_watch.isActive()
    c.settings.profile.hotkey_mode = "toggle"
    hk.pressed.emit("ptt")
    assert c.recording and not c._key_watch.isActive()


def test_exclusive_fullscreen_warns_once(ctx):
    c, hk, sp, rec, ov = ctx
    notes = []
    c.tray = type("T", (), {"notify": lambda self, m, error=False: notes.append(m)})()
    FULLSCREEN[0] = True
    for _ in range(3):
        hk.pressed.emit("ptt")
        release(c, hk)
    assert len(notes) == 1 and "Borderless" in notes[0]


def test_job_errors_route_by_their_own_tag(ctx):
    c, hk, sp, rec, ov = ctx
    results = []
    c.test_result.connect(results.append)
    c.test_microphone()
    c._finish_recording()  # mic-test job queued
    hk.pressed.emit("ptt")  # a push-to-talk recording starts meanwhile
    sp.failed.emit("test", "Azure Speech: invalid key or wrong region.")
    assert results == ["Azure Speech: invalid key or wrong region."]
    sp.failed.emit("ptt", "boom")
    assert results == ["Azure Speech: invalid key or wrong region."]  # ptt error not routed


def test_toggle_mode(ctx):
    c, hk, sp, *_ = ctx
    c.settings.profile.hotkey_mode = "toggle"
    hk.pressed.emit("ptt")
    release(c, hk)
    assert c.phase is Phase.RECORDING
    hk.pressed.emit("ptt")
    assert c.phase is Phase.PROCESSING and len(sp.jobs) == 1


def test_disabled_ignores_hotkey(ctx):
    c, hk, sp, rec, ov = ctx
    c.set_enabled(False)
    hk.pressed.emit("ptt")
    assert c.phase is Phase.IDLE and not rec.active


def test_translation_failure_and_empty_result(ctx):
    c, hk, sp, rec, ov = ctx
    hk.pressed.emit("ptt")
    release(c, hk)
    sp.failed.emit("ptt", "Translation failed — try again.")
    assert c.phase is Phase.IDLE and ov.last == ("show_error", "Translation failed — try again.")
    hk.pressed.emit("ptt")
    release(c, hk)
    sp.finished.emit("ptt", TranslationResult(text=""))
    assert c.phase is Phase.IDLE and "catch" in ov.last[1]


def test_mic_test_reports_result(ctx):
    c, hk, sp, rec, ov = ctx
    results = []
    c.test_result.connect(results.append)
    c.test_microphone("HyperX")
    assert rec.device == "HyperX" and c.phase is Phase.RECORDING
    hk.released.emit("ptt")  # PTT release must not end a mic test
    assert c.phase is Phase.RECORDING
    c._finish_recording()
    sp.finished.emit("test", TranslationResult(text="Hello."))
    assert results == ["Hello."]


def test_foreground_switches_profile(ctx):
    c, hk, sp, *_ = ctx
    game = Profile(name="CS2", exe_names=["cs2.exe"], hotkey="Mouse5", model="medium")
    new = c.settings.clone()
    new.profiles.append(game)
    c.apply_settings(new)
    assert hk.watch is True
    hk.foreground_changed.emit("cs2.exe")
    assert c.settings.active_profile == "CS2"
    assert hk.hotkey == "Mouse5"
    assert sp.config.model == "medium" and sp.loads == 2
    hk.foreground_changed.emit("discord.exe")  # unknown app: keep current profile
    assert c.settings.active_profile == "CS2"


def test_apply_settings_persists(ctx, tmp_path):
    c, *_ = ctx
    new = c.settings.clone()
    new.profile.font_size = 26
    c.apply_settings(new)
    assert ConfigStore(tmp_path / "c.json").load().profile.font_size == 26


def _use_azure(c, mode="azure", keys=True):
    from gametalk.credentials import protect

    new = c.settings.clone()
    new.profile.set_mode(mode)
    new.profile.azure_locale = "ar-SY"
    if keys:
        new.azure.speech_key = protect("speech-secret")
        new.azure.speech_region = "westeurope"
        new.azure.translator_key = protect("translator-secret")
        new.azure.translator_region = "global"
    c.apply_settings(new)


def test_azure_mode_without_keys_warns_before_recording(ctx):
    c, hk, sp, rec, ov = ctx
    _use_azure(c, keys=False)
    hk.pressed.emit("ptt")
    assert c.phase is Phase.IDLE and not rec.active
    assert ov.last[0] == "show_error" and "Azure Speech key" in ov.last[1]


def test_hybrid_mode_only_needs_translator_key(ctx):
    c, hk, sp, rec, ov = ctx
    _use_azure(c, mode="hybrid")
    c.settings.azure.speech_key = ""
    hk.pressed.emit("ptt")
    assert c.phase is Phase.RECORDING
    assert c.engine_config().model == "small"  # Whisper still recognises locally


def test_azure_mode_end_to_end_job(ctx):
    c, hk, sp, rec, ov = ctx
    _use_azure(c)
    assert c.engine_config().model == ""  # no local model loaded in full-Azure mode
    assert sp.config.model == ""
    hk.pressed.emit("ptt")
    assert sp.prewarmed and sp.prewarmed[0].has_speech  # connections warmed while talking
    release(c, hk)
    job = sp.jobs[0]
    assert job.request.speech_provider == job.request.translation_provider == "azure"
    assert job.request.azure_locale == "ar-SY"
    assert job.azure.speech_key == "speech-secret"
    assert job.azure.translator_key == "translator-secret"
    assert "secret" not in repr(job.azure)
    sp.finished.emit("ptt", TranslationResult(text="Wait for me, I'm coming."))
    assert ov.last == ("show_result", "Wait for me, I'm coming.", "")


def test_ipc_commands(ctx):
    c, *_ = ctx
    status = c.handle_command("status").split("|")
    assert status[:4] == ["ready", "Default", "F9", "local"]
    assert c.handle_command("settings:azure") == "ok"
    assert c.handle_command("nonsense") == "unknown"


def test_reload_config_picks_up_launcher_changes(ctx):
    c, hk, sp, *_ = ctx
    s = c.store.load()
    s.profile.set_mode("hybrid")
    s.profile.hotkey = "F8"
    c.store.save(s)
    c.reload_config()
    assert c.profile.mode == "hybrid" and hk.hotkey == "F8"
