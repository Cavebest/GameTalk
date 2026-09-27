import json
import os

import pytest

from gametalk import ipc
from gametalk.config import ConfigStore, Settings
from gametalk.credentials import protect, unprotect
from gametalk.hub.backend import Hub, apply_value, config_view


@pytest.fixture
def store(tmp_path):
    return ConfigStore(tmp_path / "config.json")


@pytest.fixture
def sent(monkeypatch):
    calls = []
    replies = {"stats": None}

    def fake(command, timeout_ms=1500):
        calls.append(command)
        return replies.get(command)

    monkeypatch.setattr(ipc, "send_command", fake)
    return calls, replies


def test_config_view_never_contains_keys():
    s = Settings()
    s.azure.speech_key = protect("secret-a")
    s.google.api_key = protect("secret-g")
    view = config_view(s)
    assert view["azure"]["speech_key"] is True
    assert view["azure"]["translator_key"] is False
    assert view["google"]["api_key"] is True
    assert "secret" not in json.dumps(view)
    assert view["profile"]["hotkey"] == "F9" and view["profiles"] == ["Default"]


def test_apply_value_paths_and_types():
    s = Settings()
    apply_value(s, "profile.font_size", 22.6)
    apply_value(s, "features.replay_enabled", 0)
    apply_value(s, "compute_device", "cpu")
    apply_value(s, "profile.background_opacity", 1)
    assert s.profile.font_size == 23 and isinstance(s.profile.font_size, int)
    assert s.features.replay_enabled is False
    assert s.compute_device == "cpu"
    assert isinstance(s.profile.background_opacity, float)
    for bad in ("profile.nope", "nothing.here", "profile"):
        with pytest.raises(KeyError):
            apply_value(s, bad, 1)


def test_set_saves_validates_and_tells_the_app(qapp, store, sent):
    calls, _ = sent
    hub = Hub(store, poll=False)
    hub._running = True
    hub.set("profile.speech_provider", "azure")  # Whisper can't translate Azure's text…
    saved = store.load()
    assert saved.profile.speech_provider == "azure"
    assert saved.profile.translation_provider == "azure"  # …so validate() switched it
    assert hub.config["profile"]["translation_provider"] == "azure"
    assert "reload" in calls
    hub.set("profile.font_size", 999)
    assert store.load().profile.font_size == 48  # clamped


def test_bad_paths_and_secret_paths_are_ignored(qapp, store, sent):
    hub = Hub(store, poll=False)
    hub.set("profile.bogus", 1)
    hub.set("azure.speech_key", "plain")  # secrets only through setSecret
    assert store.load().azure.speech_key == ""


def test_secrets_are_encrypted_and_can_be_removed(qapp, store, sent):
    hub = Hub(store, poll=False)
    toasts = []
    hub.toast.connect(lambda m, k: toasts.append(k))
    hub.setSecret("google.api_key", "  gk-123 ")
    raw = store.path.read_text(encoding="utf-8")
    assert "gk-123" not in raw
    assert unprotect(store.load().google.api_key) == "gk-123"
    assert hub.config["google"]["api_key"] is True
    hub.clearSecret("google.api_key")
    assert store.load().google.api_key == "" and toasts == ["ok", "ok"]
    hub.setSecret("profile.hotkey", "F1")  # not a secret path
    assert store.load().profile.hotkey == "F9"


def test_edits_start_from_the_newest_file(qapp, store, sent):
    hub = Hub(store, poll=False)
    other = store.load()
    other.profile.hotkey = "F7"  # e.g. saved meanwhile by the app's Settings window
    store.save(other)
    hub.set("features.sound_cues", True)
    s = store.load()
    assert s.profile.hotkey == "F7" and s.features.sound_cues is True


def test_poll_reads_live_stats_or_falls_back_to_disk_usage(qapp, store, sent):
    _, replies = sent
    hub = Hub(store, poll=False)
    hub.poll()
    assert hub.running is False and set(hub.stats) == {"usage"}
    replies["stats"] = json.dumps({"state": "ready", "phase": "idle", "today": 3})
    hub.poll()
    assert hub.running is True and hub.stats["today"] == 3


def test_poll_notices_config_saved_elsewhere(qapp, store, sent):
    hub = Hub(store, poll=False)
    s = store.load()
    s.profile.model = "medium"
    store.save(s)
    hub._mtime = -1  # force: mtime granularity can hide a fast re-save
    hub.poll()
    assert hub.config["profile"]["model"] == "medium"


def test_start_counts_down_until_the_app_answers(qapp, store, sent, monkeypatch):
    spawned = []
    monkeypatch.setattr("gametalk.hub.backend.spawn", lambda cmd: spawned.append(cmd))
    hub = Hub(store, poll=False)
    hub.start()
    assert spawned and hub.starting
    hub.start()  # a double click doesn't start a second copy
    assert len(spawned) == 1


def test_options_are_translated_lists(qapp, store):
    hub = Hub(store, poll=False)
    models = hub.options("models")
    assert models[0]["value"] == "tiny" and models[0]["note"]
    assert {o["value"] for o in hub.options("translation")} >= {"whisper-local", "azure", "google"}
    assert "Mouse4" in [o["value"] for o in hub.options("hotkeys")]
    assert all(f["label"] and f["topic"] for f in hub.featureList())


def test_whole_interface_loads_without_qml_errors(qapp, store, sent, monkeypatch):
    """Load the real Main.qml off-screen and visit every page; any QML warning fails."""
    os.environ.setdefault("QT_QUICK_BACKEND", "software")
    from PySide6.QtQuickControls2 import QQuickStyle
    from PySide6.QtTest import QTest

    from gametalk.hub import HubApp

    QQuickStyle.setStyle("Basic")
    warnings = []
    monkeypatch.setattr(
        "gametalk.hub.log.warning", lambda msg, *a: warnings.append(msg % a if a else msg)
    )
    hub = Hub(store, poll=False)
    ui = HubApp(qapp, hub)
    assert ui.build()
    win = ui.engine.rootObjects()[0]
    for page in range(8):
        win.setProperty("page", page)
        QTest.qWait(60)
    hub.setLanguage("ar")  # rebuilds right-to-left
    QTest.qWait(60)
    assert ui.engine.rootObjects()[0].property("page") == 7
    hub.setLanguage("en")
    ui.engine = None
    assert warnings == []
