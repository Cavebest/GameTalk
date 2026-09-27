import json

import pytest
from factory import make_controller

from gametalk.config import ConfigStore, Correction, QuickPhrase, Settings
from gametalk.credentials import unprotect
from gametalk.hub.backend import Hub, apply_value, config_view


@pytest.fixture
def c(qapp, tmp_path):
    return make_controller(tmp_path)


@pytest.fixture
def hub(c):
    h = Hub(c, poll=False)
    yield h
    h.close()


def saved(c):
    return ConfigStore(c.store.path).load()


def test_config_view_never_contains_keys():
    from gametalk.credentials import protect

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
    for bad in ("profile.nope", "nothing.here", "profile", "profile.vocabulary"):
        with pytest.raises(KeyError):
            apply_value(s, bad, 1)


def test_set_applies_to_the_running_app_and_saves(c, hub):
    hub.set("profile.hotkey", "Mouse4")
    hub.set("profile.model", "medium")
    assert c.hotkey.hotkey == "Mouse4"  # live, no restart
    assert c.speech.config.model == "medium"
    assert saved(c).profile.hotkey == "Mouse4"
    hub.set("profile.speech_provider", "azure")  # Whisper can't translate Azure's text…
    assert saved(c).profile.translation_provider == "azure"  # …so validate() switched it
    assert hub.config["profile"]["translation_provider"] == "azure"
    assert c.speech.config.model == ""  # Whisper isn't loaded in full-Azure mode
    hub.set("profile.font_size", 999)
    assert saved(c).profile.font_size == 48  # clamped


def test_bad_paths_and_secret_paths_are_ignored(c, hub):
    hub.set("profile.bogus", 1)
    hub.set("azure.speech_key", "plain")  # secrets only through setSecret
    assert saved(c).azure.speech_key == ""


def test_secrets_are_encrypted_and_can_be_removed(c, hub):
    toasts = []
    hub.toast.connect(lambda m, k: toasts.append(k))
    hub.setSecret("azure.speech_key", "  speech-secret ")
    hub.set("azure.speech_region", "West Europe")
    raw = c.store.path.read_text(encoding="utf-8")
    assert "speech-secret" not in raw  # only DPAPI ciphertext on disk
    s = saved(c)
    assert unprotect(s.azure.speech_key) == "speech-secret"
    assert s.azure.speech_region == "westeurope"
    assert hub.config["azure"]["speech_key"] is True
    hub.clearSecret("azure.speech_key")
    assert saved(c).azure.speech_key == "" and toasts == ["ok", "ok"]
    hub.setSecret("profile.hotkey", "F1")  # not a secret path
    assert saved(c).profile.hotkey == "F9"


def test_power_button_pauses_and_resumes(c, hub):
    hub.toggleEnabled()
    assert c.settings.enabled is False and hub.stats["state"] == "disabled"
    hub.toggleEnabled()
    assert c.settings.enabled is True and saved(c).enabled is True


def test_lists_phrases_corrections_vocabulary_games(c, hub):
    hub.setPhrases([{"key": "Numpad9", "text": "Rotate B!"}, {"key": "", "text": ""}])
    hub.setCorrections("english", [{"find": "Zafira", "replace": "ammo"}])
    hub.setCorrections("arabic", [{"find": "هلق", "replace": "الآن"}])
    hub.setLines("vocabulary", "Medic\n\n medic \nFlank\n")
    hub.setLines("games", "CS2.exe\n")
    p = saved(c).profile
    assert p.quick_phrases == [QuickPhrase("Numpad9", "Rotate B!")]  # empty rows dropped
    assert p.corrections == [Correction("Zafira", "ammo")]
    assert p.arabic_corrections == [Correction("هلق", "الآن")]
    assert p.vocabulary == ["Medic", "Flank"]  # duplicates removed
    assert p.exe_names == ["cs2.exe"]
    assert c.hotkey.watch is True  # a game .exe turns on foreground watching


def test_profiles_new_rename_switch_delete(c, hub):
    hub.set("profile.font_size", 30)
    hub.newProfile("CS2")
    s = saved(c)
    assert [p.name for p in s.profiles] == ["Default", "CS2"] and s.active_profile == "CS2"
    assert s.find_profile("CS2").font_size == 30  # a copy of the current profile
    hub.set("profile.font_size", 22)
    hub.setProfile("Default")
    assert saved(c).profile.font_size == 30 and saved(c).find_profile("CS2").font_size == 22
    hub.renameProfile("Default")  # taken: gets a unique name
    hub.newProfile("CS2")
    assert "CS2 (2)" in hub.config["profiles"]
    hub.deleteProfile()
    hub.deleteProfile()
    hub.deleteProfile()  # the last one always stays
    assert len(saved(c).profiles) == 1


def test_profile_export_import_round_trip(c, hub, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QFileDialog

    hub.setPhrases([{"key": "Numpad9", "text": "Rotate B!"}])
    hub.setCorrections("english", [{"find": "Zafira", "replace": "ammo"}])
    out = tmp_path / "cs2.gametalk.json"
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: (str(out), ""))
    )
    monkeypatch.setattr(
        QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: (str(out), ""))
    )
    hub.exportProfile()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["profile"]["quick_phrases"] == [{"key": "Numpad9", "text": "Rotate B!"}]
    assert "speech_key" not in json.dumps(data)  # keys are never exported
    hub.importProfile()
    s = saved(c)
    assert [p.name for p in s.profiles] == ["Default", "Default (2)"]  # never overwrites
    assert s.find_profile("Default (2)").corrections == [Correction("Zafira", "ammo")]


def test_import_rejects_garbage(c, hub, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"hello": 1}', encoding="utf-8")
    toasts = []
    hub.toast.connect(lambda m, k: toasts.append(k))
    assert hub.importProfileFrom(str(bad)) is False
    assert toasts == ["error"] and len(saved(c).profiles) == 1


def test_key_capture_uses_the_apps_hotkey_system(c, hub):
    got = []
    hub.keyCaptured.connect(lambda target, name: got.append((target, name)))
    hub.beginCapture("replay")
    c.hotkey.captured.emit("F7")
    assert got == [("replay", "F7")]
    assert c.hotkey.captures == ["begin", "cancel"]
    c.hotkey.captured.emit("F6")  # not capturing any more: ignored
    assert got == [("replay", "F7")]


def test_mic_test_result_reaches_the_window(c, hub):
    got = []
    hub.micTested.connect(got.append)
    c.test_result.emit("Wait for me.")
    assert got == ["Wait for me."]


def test_stats_are_live(c, hub):
    hub.poll()
    assert hub.stats["hotkey"] == "F9" and hub.stats["state"] == "ready"


def test_options_are_translated_lists(hub):
    models = hub.options("models")
    assert models[0]["value"] == "tiny" and models[0]["note"]
    assert {o["value"] for o in hub.options("translation")} >= {"whisper-local", "azure", "google"}
    assert "Mouse4" in [o["value"] for o in hub.options("hotkeys")]
    assert hub.options("gamepadReplay")[0]["value"] == ""
    assert all(f["label"] and f["topic"] for f in hub.featureList())


def test_window_opens_closes_to_tray_and_reopens(c, monkeypatch):
    """The real Main.qml, off-screen: every page loads without a QML warning, closing frees it
    (GameTalk keeps running), and it opens again on the requested page."""
    from PySide6.QtTest import QTest

    from gametalk import hub as hub_mod

    warnings = []
    monkeypatch.setattr(
        hub_mod.log, "warning", lambda msg, *a: warnings.append(msg % a if a else msg)
    )
    c.open_window()
    w = c._window
    win = w.window
    assert win is not None
    for page in range(11):
        win.setProperty("page", page)
        QTest.qWait(60)
    w.hub.setLanguage("ar")  # rebuilds right-to-left on the same page
    QTest.qWait(60)
    assert w.window.property("page") == 10
    w.hub.setLanguage("en")
    QTest.qWait(30)
    w.window.close()  # the X button
    QTest.qWait(30)
    assert w.window is None and w.hub is None  # freed; the controller lives on
    c.open_window("overlay")
    assert w.window.property("page") == 4
    w.close()
    assert warnings == []
