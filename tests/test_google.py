import json

import httpx
import numpy as np
import pytest
from test_translate import AUDIO, SPEECH, FakeBackend, FakeCloud

from gametalk.config import GOOGLE, Settings, settings_from_dict, validate
from gametalk.google import (
    GoogleClient,
    GoogleCredentials,
    GoogleError,
    billed_chars,
    check_connection,
)
from gametalk.translate import (
    PipelineError,
    TeamRequest,
    TranslationRequest,
    run_pipeline,
    run_team_pipeline,
    run_text_pipeline,
)

NMT = GoogleCredentials("gk")
LLM = GoogleCredentials("gk", project_id="my-proj", model="llm")


def reply(text="Stay behind me"):
    return httpx.Response(200, json={"data": {"translations": [{"translatedText": text}]}})


def client_with(handler, creds=NMT):
    return GoogleClient(creds, transport=httpx.MockTransport(handler))


def test_translate_request_shape_and_key_stays_out_of_the_url():
    seen = {}

    def handler(request: httpx.Request):
        seen["url"] = str(request.url)
        seen["headers"] = request.headers
        seen["body"] = json.loads(request.content)
        return reply("Stay behind me &amp; cover")

    out = client_with(handler).translate("خليكم وراي", "ar", "zh-Hans")
    assert out == "Stay behind me & cover"  # HTML entities decoded
    assert "gk" not in seen["url"] and "key=" not in seen["url"]
    assert seen["headers"]["X-goog-api-key"] == "gk"
    assert seen["body"] == {
        "q": ["خليكم وراي"],
        "target": "zh-CN",  # our code -> Google's
        "source": "ar",
        "format": "text",
        "model": "nmt",
    }


def test_llm_model_uses_project_resource_name():
    seen = {}

    def handler(request):
        seen["body"] = json.loads(request.content)
        return reply()

    client_with(handler, LLM).translate("خليكم وراي", None, "en")
    assert seen["body"]["model"] == (
        "projects/my-proj/locations/us-central1/models/general/translation-llm"
    )
    assert "source" not in seen["body"]  # auto-detect


def test_llm_without_project_id_is_a_friendly_error():
    creds = GoogleCredentials("gk", model="llm")
    assert not creds.ready
    with pytest.raises(GoogleError, match="project ID"):
        client_with(lambda r: reply(), creds).translate("x", "ar", "en")


@pytest.mark.parametrize(
    ("status", "body", "expected"),
    [
        (400, {"error": {"message": "API key not valid. Please pass a valid API key."}}, "valid"),
        (403, {"error": {"message": "This API method requires billing to be enabled."}}, "billing"),
        (
            403,
            {"error": {"message": "Cloud Translation API has not been used in project 1"}},
            "enable",
        ),
        (429, {"error": {"message": "Quota exceeded"}}, "quota"),
        (500, {}, "HTTP 500"),
    ],
)
def test_errors_are_explained(status, body, expected):
    c = client_with(lambda r: httpx.Response(status, json=body))
    with pytest.raises(GoogleError, match=expected):
        c.translate("x", "ar", "en")


def test_repr_never_shows_the_key():
    assert "gk" not in repr(NMT) and "gk" not in repr(LLM)


def test_billing_counts_output_only_for_llm():
    assert billed_chars(NMT, "abcd", "xy") == 4
    assert billed_chars(LLM, "abcd", "xy") == 6


def test_check_connection():
    assert check_connection(GoogleCredentials())[0][0] is False
    ok = check_connection(NMT, transport=httpx.MockTransport(lambda r: reply("Hello")))
    assert ok == [(True, "Google Translate: connected (مرحبا → Hello)")]


class FakeGoogle(FakeCloud):
    def __init__(self, translated="Stay behind me", creds=NMT):
        super().__init__(translated=translated)
        self.creds = creds


def test_whisper_then_google_sends_only_text():
    backend = FakeBackend({"transcribe": " خليكم وراي "})
    google, azure = FakeGoogle(), FakeCloud()
    req = TranslationRequest(language="ar", translation_provider=GOOGLE)
    result = run_pipeline(AUDIO, req, backend, azure, google=google)
    assert result.text == "Stay behind me."
    assert google.calls == [("translate", "خليكم وراي", "ar", "en")]
    assert azure.calls == []
    assert result.google_chars == len("خليكم وراي") and result.azure_chars == 0


def test_azure_speech_then_google():
    google, azure = FakeGoogle(translated="Wait for me"), FakeCloud()
    req = TranslationRequest(
        language="ar", speech_provider="azure", translation_provider=GOOGLE, azure_locale="ar-JO"
    )
    result = run_pipeline(SPEECH, req, None, azure, google=google)
    assert result.text == "Wait for me."
    assert azure.calls == [("recognize", "ar-JO")]
    assert google.calls[0][0] == "translate"


def test_google_route_without_key_is_a_friendly_error():
    req = TranslationRequest(language="ar", translation_provider=GOOGLE)
    with pytest.raises(PipelineError, match="Google"):
        run_pipeline(AUDIO, req, FakeBackend({"transcribe": "x"}), None)


def test_text_and_team_pipelines_use_google():
    google = FakeGoogle(translated="Stay behind me", creds=LLM)
    req = TranslationRequest(language="ar")
    r = run_text_pipeline("خليكم وراي", req, "google", None, None, google=google)
    assert r.text == "Stay behind me."
    assert r.google_chars == len("خليكم وراي") + len("Stay behind me")  # LLM: in + out
    team = run_team_pipeline(
        AUDIO,
        TeamRequest(translator=GOOGLE, target_language="ar"),
        FakeBackend({"transcribe": "Push B now"}),
        None,
        None,
        google=FakeGoogle(translated="ادفعوا على B"),
    )
    assert team.text == "ادفعوا على B" and team.google_chars == len("Push B now")


def test_config_keeps_azure_speech_with_google_translation():
    s = Settings()
    s.profile.speech_provider = "azure"
    s.profile.translation_provider = GOOGLE
    s.profile.target_language = "fr"
    s.google.model = "bogus"
    s.google.project_id = " my proj "
    validate(s)
    assert s.profile.translation_provider == GOOGLE
    assert s.profile.target_language == "fr"  # Google can translate to any listed language
    assert s.google.model == "nmt" and s.google.project_id == "myproj"
    assert s.profile.uses_google and s.profile.uses_azure


def test_old_config_without_google_section_loads():
    s = settings_from_dict({"profiles": [{"name": "Default"}]})
    assert s.google.api_key == "" and s.google.model == "nmt"


def test_usage_counts_google_separately(tmp_path):
    from gametalk.usage import GOOGLE_FREE_CHARS, UsageTracker

    u = UsageTracker(tmp_path / "usage.json")
    assert u.add(google_chars=int(GOOGLE_FREE_CHARS * 0.85)) == ["google:0.8"]
    assert u.current.translator_chars == 0


def test_quick_text_auto_prefers_the_profiles_google(qapp, tmp_path):
    from factory import make_controller

    from gametalk.credentials import protect

    c = make_controller(tmp_path)
    assert c._text_translator() == "local"  # no keys at all
    c.settings.google.api_key = protect("gk")
    assert c._text_translator() == GOOGLE  # the only cloud key
    c.settings.azure.translator_key = protect("tk")
    c._creds_cache = None
    assert c._text_translator() == "azure"  # both: Azure unless the profile uses Google
    c.profile.translation_provider = GOOGLE
    assert c._text_translator() == GOOGLE


def test_send_audio_attaches_google_credentials(qapp, tmp_path):
    from factory import make_controller

    from gametalk.credentials import protect

    c = make_controller(tmp_path)
    c.settings.google.api_key = protect("gk")
    c.profile.translation_provider = GOOGLE
    c._send_audio(np.zeros(16000, np.float32), "ptt")
    job = c.speech.jobs[-1]
    assert job.google is not None and job.google.api_key == "gk"
    assert job.azure is None
