from gametalk.config import Profile, Settings, validate
from gametalk.launcher import app_command, autostart_command


def test_modes_map_to_providers():
    p = Profile()
    assert p.mode == "local" and p.uses_whisper and not p.uses_azure
    p.set_mode("hybrid")
    assert (p.speech_provider, p.translation_provider) == ("whisper-local", "azure")
    assert p.uses_whisper and p.uses_azure
    p.set_mode("azure")
    assert (p.speech_provider, p.translation_provider) == ("azure", "azure")
    assert not p.uses_whisper and p.mode == "azure"


def test_validate_forces_azure_translation_with_azure_speech():
    s = Settings()
    s.profile.speech_provider = "azure"
    s.profile.translation_provider = "whisper-local"
    s.profile.target_language = "fr"
    validate(s)
    assert s.profile.translation_provider == "azure"
    assert s.profile.target_language == "fr"  # Azure Translator can do French
    s.profile.set_mode("local")
    validate(s)
    assert s.profile.target_language == "en"  # Whisper only outputs English


def test_commands_use_windowless_python():
    cmd = app_command("--settings")
    assert cmd[1:] == ["-m", "gametalk", "--settings"]
    assert cmd[0].lower().endswith(("pythonw.exe", "python.exe"))
    assert "-m gametalk" in autostart_command()


def test_powershell_quoting_survives_apostrophes():
    from gametalk.launcher import ps_quote

    assert ps_quote("C:/Users/O'Brien/py.exe") == "'C:/Users/O''Brien/py.exe'"
    assert ps_quote("plain") == "'plain'"
