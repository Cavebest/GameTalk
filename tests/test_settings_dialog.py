from test_controller import FakeHotkey, FakeOverlay, FakeRecorder, FakeSpeech

from gametalk.app import Controller
from gametalk.config import NEVER_HIDE, ConfigStore, Settings, validate


def make_controller(tmp_path):
    c = Controller(
        ConfigStore(tmp_path / "c.json"),
        validate(Settings()),
        speech=FakeSpeech(),
        recorder=FakeRecorder(),
        hotkey=FakeHotkey(),
        overlay=FakeOverlay(),
    )
    c.hotkey.begin_capture = lambda: None
    c.hotkey.cancel_capture = lambda: None
    c.start()
    return c


def test_save_applies_and_persists(qapp, tmp_path):
    from gametalk.settings_dialog import SettingsDialog

    c = make_controller(tmp_path)
    dlg = SettingsDialog(c)
    dlg.font_size.setValue(24)
    dlg.never_hide.setChecked(True)
    dlg.mode_toggle.setChecked(True)
    dlg.hotkey_box.setCurrentText("Mouse4")
    dlg.model_box.setCurrentText("medium")
    dlg.vocab.setPlainText("Medic\nRotate B\n")
    dlg.accept()

    saved = ConfigStore(tmp_path / "c.json").load().profile
    assert saved.font_size == 24
    assert saved.display_seconds == NEVER_HIDE
    assert saved.hotkey_mode == "toggle"
    assert saved.hotkey == "Mouse4" and c.hotkey.hotkey == "Mouse4"
    assert saved.model == "medium" and c.speech.config.model == "medium"
    assert saved.vocabulary == ["Medic", "Rotate B"]


def test_cancel_changes_nothing(qapp, tmp_path):
    from gametalk.settings_dialog import SettingsDialog

    c = make_controller(tmp_path)
    dlg = SettingsDialog(c)
    dlg.font_size.setValue(30)
    dlg.reject()
    assert c.settings.profile.font_size == 18
    assert not (tmp_path / "c.json").exists()


def test_profiles_are_independent(qapp, tmp_path, monkeypatch):
    from gametalk import settings_dialog
    from gametalk.settings_dialog import SettingsDialog

    c = make_controller(tmp_path)
    dlg = SettingsDialog(c)
    monkeypatch.setattr(
        settings_dialog.QInputDialog, "getText", staticmethod(lambda *a, **k: ("CS2", True))
    )
    dlg._new_profile()
    dlg.exe_names.setText("CS2.exe")
    dlg.font_size.setValue(30)
    dlg.profile_box.setCurrentText("Default")
    assert dlg.font_size.value() == 18
    dlg.profile_box.setCurrentText("CS2")
    dlg.accept()

    s = ConfigStore(tmp_path / "c.json").load()
    assert [p.name for p in s.profiles] == ["Default", "CS2"]
    assert s.active_profile == "CS2"
    assert s.find_profile("CS2").font_size == 30
    assert s.find_profile("CS2").exe_names == ["cs2.exe"]
    assert s.find_profile("Default").font_size == 18
    assert c.hotkey.watch is True


def test_azure_tab_saves_encrypted_keys_and_forces_translator(qapp, tmp_path):
    from gametalk.credentials import unprotect
    from gametalk.settings_dialog import SettingsDialog

    c = make_controller(tmp_path)
    dlg = SettingsDialog(c)
    dlg.show_tab("azure")
    assert dlg._page_keys[dlg.nav.currentRow()] == "azure"
    dlg.speech_box.setCurrentIndex(dlg.speech_box.findData("azure"))
    assert dlg.provider_box.currentData() == "azure"  # Whisper can't translate text
    assert not dlg.model_box.isEnabled() and dlg.locale_box.isEnabled()
    dlg.locale_box.setCurrentIndex(dlg.locale_box.findData("ar-SY"))
    dlg.speech_key.setText("  speech-secret ")
    dlg.speech_region.setText("West Europe")
    dlg.translator_key.setText("translator-secret")
    dlg.translator_region.setText("global")
    dlg.accept()

    raw = (tmp_path / "c.json").read_text(encoding="utf-8")
    assert "secret" not in raw  # only DPAPI ciphertext on disk
    s = ConfigStore(tmp_path / "c.json").load()
    assert unprotect(s.azure.speech_key) == "speech-secret"
    assert s.azure.speech_region == "westeurope"
    assert s.profile.mode == "azure" and s.profile.azure_locale == "ar-SY"
    assert c.speech.config.model == ""  # Whisper not loaded in full-Azure mode

    # Re-opening shows "saved" placeholders; leaving the fields empty keeps the keys.
    dlg2 = SettingsDialog(c)
    assert dlg2.speech_key.text() == "" and "saved" in dlg2.speech_key.placeholderText()
    dlg2.accept()
    assert unprotect(ConfigStore(tmp_path / "c.json").load().azure.speech_key) == "speech-secret"
