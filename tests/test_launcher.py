from gametalk.config import Profile, Settings, validate
from gametalk.credentials import protect
from gametalk.launcher import (
    app_command,
    autostart_command,
    missing_keys,
    parse_status,
    pipeline_summary,
)


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


def test_parse_status():
    assert parse_status(None) is None
    info = parse_status("ready|CS2|Mouse5|azure|Azure Speech (cloud)")
    assert info == {
        "state": "ready",
        "profile": "CS2",
        "hotkey": "Mouse5",
        "mode": "azure",
        "engine": "Azure Speech (cloud)",
    }
    assert parse_status("ready")["engine"] == ""


def test_missing_keys_per_service():
    s = validate(Settings())
    p = s.profile
    assert missing_keys(p, s) == []  # local: no keys needed
    p.translation_provider = "azure"
    assert missing_keys(p, s) == ["Azure Translator key"]
    p.speech_provider = "azure"
    assert missing_keys(p, s) == ["Azure Speech key + region", "Azure Translator key"]
    s.azure.translator_key = protect("t")
    s.azure.speech_key = protect("s")
    assert missing_keys(p, s) == ["Azure Speech key + region"]  # region still missing
    s.azure.speech_region = "westeurope"
    assert missing_keys(p, s) == []


def test_pipeline_summary_says_exactly_what_leaves_the_pc():
    p = Profile(model="medium")
    flow, sent, cloud = pipeline_summary(p)
    assert "Whisper medium" in flow and not cloud and "Nothing leaves" in sent

    p.translation_provider = "azure"
    p.target_language = "fr"
    flow, sent, cloud = pipeline_summary(p)
    assert flow.endswith("Azure Translator → French") and "Whisper medium" in flow
    assert cloud and "only the recognised" in sent and "never your audio" in sent

    p.speech_provider = "azure"
    p.azure_locale = "ar-JO"
    flow, sent, cloud = pipeline_summary(p)
    assert "Azure Speech (Jordan)" in flow and "audio" in sent and cloud


def test_commands_use_windowless_python():
    cmd = app_command("--settings")
    assert cmd[1:] == ["-m", "gametalk", "--settings"]
    assert cmd[0].lower().endswith(("pythonw.exe", "python.exe"))
    assert "-m gametalk" in autostart_command()


def test_powershell_quoting_survives_apostrophes():
    from gametalk.launcher import ps_quote

    assert ps_quote("C:/Users/O'Brien/py.exe") == "'C:/Users/O''Brien/py.exe'"
    assert ps_quote("plain") == "'plain'"
