# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Speech -> translated text pipeline and gaming-mode output shaping.

Speech -> text and text -> translation are picked separately per profile:
  Whisper + Whisper : translate task (speech -> English in one local pass, nothing leaves the PC)
  Whisper + cloud   : Whisper transcribe (local) -> Azure Translator or Google (only text is sent)
  Azure + cloud     : Azure Speech (audio is sent) -> Azure Translator or Google
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

import numpy as np

from .audio import trim_silence

# Short English context steers Whisper's translate task toward casual squad-chat phrasing.
# Kept brief: long prompts make Whisper echo the prompt on silence.
GAMING_STYLE_PROMPT = "Voice chat with my squad. Short, casual callouts."

# Phrases Whisper commonly hallucinates on silence/noise (trained on subtitled video).
# Legit short replies ("Thank you.", "Okay.") are deliberately NOT listed; the VAD filter and
# no-speech probability check in speech.py handle silence.
_HALLUCINATIONS = {"you", "you.", "...", "."}
_HALLUCINATION_PATTERNS = (
    re.compile(r"(thanks|thank you) for watching", re.I),
    re.compile(r"(please )?(like and )?subscribe", re.I),
    re.compile(r"amara\.org", re.I),
    re.compile(r"translated by", re.I),
    re.compile(r"subtitles? by", re.I),
    # Whisper's classic Arabic hallucinations on silence/noise
    re.compile(r"اشتركوا? في القناة"),
    re.compile(r"شكرا (لكم )?على المشاهدة"),
    re.compile(r"ترجمة نانسي"),
)
_PREFIX = re.compile(r"^\s*(translation|english|translated text)\s*[:\-]\s*", re.I)
_TAGS = re.compile(r"\[[^\]]*\]|\([^)]*(music|applause|laughs?|noise|inaudible)[^)]*\)", re.I)
_QUOTES = "\"'“”‘’«»「」"


@dataclass
class TranslationRequest:
    language: str | None  # source language code; None = auto-detect
    target_language: str = "en"
    gaming_mode: bool = True
    vocabulary: tuple[str, ...] = ()
    show_source: bool = False  # also return the source-language transcript
    speech_provider: str = "whisper-local"
    translation_provider: str = "whisper-local"
    azure_locale: str = "ar-SA"
    corrections: tuple[tuple[str, str], ...] = ()  # (find, replace) on the final text
    source_corrections: tuple[tuple[str, str], ...] = ()  # dialect -> standard Arabic, pre-MT
    pronounce: bool = False  # add Arabic-letter pronunciation of the English result
    trim_silence: bool = True  # before uploading audio to Azure
    phrases: tuple[str, ...] = ()  # Azure Speech phrase-list hints


@dataclass
class TeamRequest:
    """Teammate subtitles: English speech from the PC's output -> target language."""

    recognizer: str = "whisper-local"  # or "azure"
    translator: str = "local"  # "local" | "azure" | "none"
    target_language: str = "ar"
    show_original: bool = False


@dataclass
class TranslationResult:
    text: str  # final English text ("" = nothing recognised)
    source_text: str = ""
    detected_language: str = ""
    seconds: float = 0.0
    pronunciation: str = ""  # English written in Arabic letters (pronunciation helper)
    azure_audio_seconds: float = 0.0  # usage counters (amounts only, never content)
    azure_chars: int = 0
    google_chars: int = 0


class SpeechBackend(Protocol):
    def decode(
        self, audio: np.ndarray, task: str, language: str | None, prompt: str | None
    ) -> tuple[str, str]:
        """Return (text, detected_language)."""


class CloudBackend(Protocol):
    def recognize(self, audio: np.ndarray, locale: str, phrases: tuple[str, ...] = ()) -> str: ...

    def translate(self, text: str, source: str | None, target: str) -> str: ...


class TextTranslator(Protocol):
    def translate(self, text: str, source: str | None, target: str) -> str: ...


class PipelineError(Exception):
    """User-presentable configuration problem (e.g. a needed engine isn't available)."""


def build_prompt(vocabulary: tuple[str, ...] | list[str], gaming_mode: bool) -> str | None:
    """Context hint for the decoder. Vocabulary biases spelling/word choice; it never replaces."""
    parts = []
    if gaming_mode:
        parts.append(GAMING_STYLE_PROMPT)
    vocab = [v for v in vocabulary if v][:24]
    if vocab:
        parts.append(", ".join(vocab) + ".")
    return " ".join(parts) or None


def is_hallucination(text: str, prompt: str | None = None) -> bool:
    t = text.strip().lower()
    if not t or t in _HALLUCINATIONS:
        return True
    if any(p.search(t) for p in _HALLUCINATION_PATTERNS):
        return True
    if prompt and len(t) > 8 and t.rstrip(".") in prompt.lower():
        return True  # Whisper echoed its own prompt
    return False


def clean_output(text: str, gaming_mode: bool = True) -> str:
    """Leave only the sentence: no labels, quotes, sound tags or stray whitespace."""
    t = _TAGS.sub(" ", text)
    t = _PREFIX.sub("", t)
    t = " ".join(t.split())
    t = t.strip().strip(_QUOTES).strip()
    t = re.sub(r"\s+([,.!?])", r"\1", t)
    if not t:
        return ""
    if gaming_mode:
        t = re.sub(r"\.{2,}$", ".", t)
    first = t.split(" ", 1)[0]
    if first.islower():  # "wait…" -> "Wait…", but leave "iPhone", "B-site", "5v5" alone
        t = t[0].upper() + t[1:]
    if t[-1].isascii() and t[-1].isalnum():
        t += "."
    return t


def apply_corrections(text: str, rules: tuple[tuple[str, str], ...]) -> str:
    """User fixes like "Zafira" -> "ammo": whole words/phrases, case-insensitive, one pass.

    A single combined regex means a replacement is never re-scanned, so rules can't loop or
    chain ("a"->"b", "b"->"a" just swaps). Word boundaries keep "ammo" from touching "ammonia".
    """
    rules = tuple((f, r) for f, r in rules if f.strip())
    if not rules or not text:
        return text
    table = {f.casefold(): r for f, r in rules}
    alternatives = sorted((re.escape(f) for f, _ in rules), key=len, reverse=True)
    pattern = re.compile(r"(?<![\w'])(" + "|".join(alternatives) + r")(?![\w'])", re.IGNORECASE)
    return pattern.sub(lambda m: table.get(m.group(0).casefold(), m.group(0)), text)


def _finish(text: str, req: TranslationRequest) -> tuple[str, str]:
    """Corrections + pronunciation for a final English text."""
    if text and req.corrections:
        text = clean_output(apply_corrections(text, req.corrections), req.gaming_mode)
    pron = ""
    if text and req.pronounce and (req.target_language or "en") == "en":
        from .pronounce import to_arabic

        pron = to_arabic(text)
    return text, pron


def _whisper_translate(
    whisper: SpeechBackend, audio: np.ndarray, req: TranslationRequest
) -> TranslationResult:
    """Local route: Whisper translate task, Arabic speech -> English in one pass."""
    prompt = build_prompt(req.vocabulary, req.gaming_mode)
    raw, detected = whisper.decode(audio, "translate", req.language, prompt)
    text = clean_output(raw, req.gaming_mode)
    if is_hallucination(text, prompt):
        text = ""
    source = ""
    if req.show_source and text:
        source, _ = whisper.decode(audio, "transcribe", req.language or detected or None, None)
        source = " ".join(source.split())
    text, pron = _finish(text, req)
    return TranslationResult(
        text=text, source_text=source, detected_language=detected, pronunciation=pron
    )


GOOGLE_KEY_MISSING = "Add your Google Translate API key on the Cloud keys page."


def _usage(translator: str, source: str, text: str, google) -> dict:
    """Billing amounts for one translation (characters only, never content)."""
    if translator == "azure":
        return {"azure_chars": len(source)}
    if translator == "google":
        from .google import billed_chars

        creds = getattr(google, "creds", None)
        return {"google_chars": billed_chars(creds, source, text) if creds else len(source)}
    return {}


def run_pipeline(
    audio: np.ndarray,
    req: TranslationRequest,
    whisper: SpeechBackend | None,
    cloud: CloudBackend | None,
    google: TextTranslator | None = None,
) -> TranslationResult:
    uses_azure = "azure" in (req.speech_provider, req.translation_provider)
    if uses_azure and cloud is None:
        raise PipelineError("Add your Azure keys on the Cloud keys page.")
    if req.translation_provider == "google" and google is None:
        raise PipelineError(GOOGLE_KEY_MISSING)
    if req.speech_provider != "azure" and whisper is None:
        raise PipelineError("Speech model isn't loaded.")

    if req.speech_provider == "whisper-local" and req.translation_provider == "whisper-local":
        return _whisper_translate(whisper, audio, req)

    # Two-stage routes: speech -> source text -> Azure Translator / Google.
    if req.speech_provider == "azure":
        if req.trim_silence:
            audio = trim_silence(audio)  # upload only the part with speech in it
            if audio.size == 0:
                return TranslationResult(text="")  # only silence: don't call Azure at all
        source = cloud.recognize(audio, req.azure_locale, req.phrases)
        azure_seconds = audio.size / 16000
        detected = req.azure_locale.split("-")[0]
    else:
        azure_seconds = 0.0
        source, detected = whisper.decode(audio, "transcribe", req.language, None)
    source = " ".join(source.split())
    if not source or is_hallucination(source):
        return TranslationResult(
            text="", detected_language=detected, azure_audio_seconds=azure_seconds
        )
    shown_source = source
    source = apply_corrections(source, req.source_corrections)
    target = req.target_language or "en"
    src_lang = detected or req.language
    usage = {}
    if src_lang == target.split("-")[0]:
        text = source  # already in the target language
    else:
        translator = google if req.translation_provider == "google" else cloud
        text = translator.translate(source, src_lang, target)
        usage = _usage(req.translation_provider, source, text, google)
    text = clean_output(text, req.gaming_mode)
    if is_hallucination(text):
        text = ""
    text, pron = _finish(text, req)
    return TranslationResult(
        text=text,
        source_text=shown_source if req.show_source else "",
        detected_language=detected,
        pronunciation=pron,
        azure_audio_seconds=azure_seconds,
        **usage,
    )


def run_text_pipeline(
    text: str,
    req: TranslationRequest,
    translator: str,
    cloud: CloudBackend | None,
    local_mt: LocalMT | None,
    google: TextTranslator | None = None,
) -> TranslationResult:
    """Quick text window: typed Arabic -> English. translator: 'azure' | 'google' | 'local'."""
    source = " ".join(text.split())
    if not source:
        return TranslationResult(text="")
    fixed = apply_corrections(source, req.source_corrections)
    usage = {}
    if translator == "azure":
        if cloud is None:
            raise PipelineError("Add your Azure Translator key on the Cloud keys page.")
        english = cloud.translate(fixed, None, req.target_language or "en")
        usage = _usage("azure", fixed, english, google)
    elif translator == "google":
        if google is None:
            raise PipelineError(GOOGLE_KEY_MISSING)
        english = google.translate(fixed, "ar", req.target_language or "en")
        usage = _usage("google", fixed, english, google)
    else:
        if local_mt is None:
            raise PipelineError("Offline translator isn't available.")
        english = local_mt.translate(fixed)
    english = clean_output(english, req.gaming_mode)
    english, pron = _finish(english, req)
    return TranslationResult(text=english, source_text=source, pronunciation=pron, **usage)


class LocalMT(Protocol):
    def translate(self, text: str) -> str: ...


def run_team_pipeline(
    audio: np.ndarray,
    req: TeamRequest,
    whisper: SpeechBackend | None,
    cloud: CloudBackend | None,
    local_mt: LocalMT | None,
    speech_check=None,
    google: TextTranslator | None = None,
) -> TranslationResult:
    """Teammate subtitles: English speech -> (optionally) translated text."""
    if req.recognizer == "azure":
        if cloud is None:
            raise PipelineError("Add your Azure Speech key on the Cloud keys page.")
        if speech_check is not None and not speech_check(audio):
            return TranslationResult(text="")  # gunfire/music: never sent to Azure
        clip = trim_silence(audio)
        english = cloud.recognize(clip, "en-US")
        team_seconds = clip.size / 16000
    else:
        if whisper is None:
            raise PipelineError("Speech model isn't loaded.")
        team_seconds = 0.0
        english, _ = whisper.decode(audio, "transcribe", "en", None)
    english = " ".join(english.split())
    if not english or is_hallucination(english):
        return TranslationResult(text="")
    usage = {}
    if req.translator == "azure":
        if cloud is None:
            raise PipelineError("Add your Azure Translator key on the Cloud keys page.")
        text = cloud.translate(english, "en", req.target_language)
        usage = _usage("azure", english, text, google)
    elif req.translator == "google":
        if google is None:
            raise PipelineError(GOOGLE_KEY_MISSING)
        text = google.translate(english, "en", req.target_language)
        usage = _usage("google", english, text, google)
    elif req.translator == "local":
        if local_mt is None:
            raise PipelineError("Offline translator isn't available.")
        text = local_mt.translate(english)
    else:
        text = english
    shown_original = english if req.show_original and req.translator != "none" else ""
    return TranslationResult(
        text=text.strip(),
        source_text=shown_original,
        detected_language="en",
        azure_audio_seconds=team_seconds,
        **usage,
    )
