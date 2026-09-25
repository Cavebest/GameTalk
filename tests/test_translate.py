import numpy as np
import pytest

from gametalk.translate import (
    GAMING_STYLE_PROMPT,
    PipelineError,
    TranslationRequest,
    build_prompt,
    clean_output,
    is_hallucination,
    run_pipeline,
)


@pytest.mark.parametrize(
    "raw, expected",
    [
        (" wait for me, I'm coming", "Wait for me, I'm coming."),
        ('"Stay behind me."', "Stay behind me."),
        ("Translation: Stay behind me.", "Stay behind me."),
        ("English - Push left!", "Push left!"),
        ("[Music] Enemy on the roof ", "Enemy on the roof."),
        ("Reload   ,  cover me", "Reload, cover me."),
        ("Fall back...", "Fall back."),
        ("“Medic!”", "Medic!"),
        ("   ", ""),
        ("iPhone is on B", "iPhone is on B."),  # no "IPhone"
        ("5v5 on B site", "5v5 on B site."),
        ("B-site, rotate", "B-site, rotate."),
    ],
)
def test_clean_output(raw, expected):
    assert clean_output(raw) == expected


def test_hallucinations():
    assert is_hallucination("")
    assert is_hallucination("Thanks for watching!")
    assert is_hallucination("Please subscribe to my channel.")
    assert is_hallucination("Subtitles by the Amara.org community")
    assert not is_hallucination("Thank you.")
    assert not is_hallucination("Okay.")
    assert not is_hallucination("Wait for me, I'm coming.")


def test_prompt_echo_is_hallucination():
    prompt = build_prompt(["Medic", "Flank"], True)
    assert is_hallucination("Voice chat with my squad.", prompt)


def test_build_prompt():
    assert build_prompt([], False) is None
    assert build_prompt([], True) == GAMING_STYLE_PROMPT
    p = build_prompt(["Medic", "Fall back"], False)
    assert p == "Medic, Fall back."


class FakeBackend:
    def __init__(self, outputs):
        self.outputs = outputs
        self.calls = []

    def decode(self, audio, task, language, prompt):
        self.calls.append((task, language, prompt))
        return self.outputs[task], "ar"


class FakeCloud:
    def __init__(self, heard="استنوني شوي، أنا جاي", translated="Wait for me, I'm coming"):
        self.heard, self.translated = heard, translated
        self.calls = []

    def recognize(self, audio, locale, phrases=()):
        self.calls.append(("recognize", locale))
        return self.heard

    def translate(self, text, source, target):
        self.calls.append(("translate", text, source, target))
        return self.translated


AUDIO = np.zeros(16000, np.float32)
# 1 s: 0.3 s silence, 0.4 s "speech" (tone), 0.3 s silence
SPEECH = np.concatenate(
    [
        np.zeros(4800, np.float32),
        0.2 * np.sin(np.linspace(0, 2 * np.pi * 180, 6400)).astype(np.float32),
        np.zeros(4800, np.float32),
    ]
)


def test_local_route_translates_and_optionally_transcribes():
    backend = FakeBackend(
        {"translate": " wait for me, I'm coming", "transcribe": "استنوني شوي، أنا جاي"}
    )
    req = TranslationRequest(language="ar", vocabulary=("Medic",), show_source=True)
    result = run_pipeline(AUDIO, req, backend, None)
    assert result.text == "Wait for me, I'm coming."
    assert result.source_text == "استنوني شوي، أنا جاي"
    assert backend.calls[0][0] == "translate" and backend.calls[0][1] == "ar"
    assert "Medic" in backend.calls[0][2]
    assert backend.calls[1] == ("transcribe", "ar", None)


def test_local_route_skips_transcript_when_nothing_recognised():
    backend = FakeBackend({"translate": "Thanks for watching!", "transcribe": "x"})
    req = TranslationRequest(language=None, show_source=True)
    result = run_pipeline(AUDIO, req, backend, None)
    assert result.text == ""
    assert len(backend.calls) == 1


def test_hybrid_route_sends_only_text_to_azure():
    backend = FakeBackend({"transcribe": " خليكم وراي "})
    cloud = FakeCloud(translated="Stay behind me")
    req = TranslationRequest(language="ar", translation_provider="azure")
    result = run_pipeline(AUDIO, req, backend, cloud)
    assert result.text == "Stay behind me."
    assert backend.calls == [("transcribe", "ar", None)]
    assert cloud.calls == [("translate", "خليكم وراي", "ar", "en")]
    assert result.source_text == ""  # show_source off


def test_azure_route_uses_dialect_locale_and_target():
    cloud = FakeCloud(translated="Attends-moi, j'arrive")
    req = TranslationRequest(
        language="ar",
        speech_provider="azure",
        translation_provider="azure",
        azure_locale="ar-SY",
        target_language="fr",
        show_source=True,
    )
    result = run_pipeline(SPEECH, req, None, cloud)
    assert cloud.calls[0] == ("recognize", "ar-SY")
    assert cloud.calls[1][2:] == ("ar", "fr")
    assert result.text == "Attends-moi, j'arrive."
    assert result.source_text == "استنوني شوي، أنا جاي"


def test_azure_route_nothing_heard_skips_translation():
    cloud = FakeCloud(heard="")
    req = TranslationRequest("ar", speech_provider="azure", translation_provider="azure")
    assert run_pipeline(SPEECH, req, None, cloud).text == ""
    assert [c[0] for c in cloud.calls] == ["recognize"]


def test_azure_route_never_uploads_pure_silence():
    cloud = FakeCloud()
    req = TranslationRequest("ar", speech_provider="azure", translation_provider="azure")
    noise = (np.random.default_rng(0).standard_normal(16000) * 0.0005).astype(np.float32)
    assert run_pipeline(noise, req, None, cloud).text == ""
    assert cloud.calls == []  # nothing sent to Azure


def test_arabic_whisper_hallucination_is_dropped_before_translation():
    backend = FakeBackend({"transcribe": "اشتركوا في القناة"})
    cloud = FakeCloud()
    req = TranslationRequest("ar", translation_provider="azure")
    assert run_pipeline(AUDIO, req, backend, cloud).text == ""
    assert cloud.calls == []


def test_missing_engines_raise_friendly_errors():
    with pytest.raises(PipelineError, match="Azure"):
        run_pipeline(AUDIO, TranslationRequest("ar", translation_provider="azure"), None, None)
    with pytest.raises(PipelineError, match="model"):
        run_pipeline(AUDIO, TranslationRequest("ar"), None, None)
