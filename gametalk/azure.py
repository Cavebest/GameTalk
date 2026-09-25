# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Azure Speech-to-Text (REST, short audio) and Azure Translator v3 clients.

Used only when the user selects an Azure provider. Azure Speech receives the recorded audio;
Azure Translator receives only the recognised text. Keys travel in request headers only and are
never logged. One HTTP client is kept per credential set so TLS connections are reused.
"""

from __future__ import annotations

import logging
import struct
import time
from dataclasses import dataclass

import httpx
import numpy as np

from . import __version__
from .audio import TARGET_RATE as SAMPLE_RATE

log = logging.getLogger(__name__)

TRANSLATOR_URL = "https://api.cognitive.microsofttranslator.com"
PREWARM_AFTER_IDLE = 60.0  # seconds; reopen connections only if they've likely gone cold
_STALE_CONNECTION_ERRORS = (httpx.ConnectError, httpx.RemoteProtocolError, httpx.ReadError)


class AzureError(Exception):
    """User-presentable Azure failure."""


@dataclass(frozen=True)
class AzureCredentials:
    speech_key: str = ""
    speech_region: str = ""
    translator_key: str = ""
    translator_region: str = ""

    @property
    def has_speech(self) -> bool:
        return bool(self.speech_key and self.speech_region)

    @property
    def has_translator(self) -> bool:
        return bool(self.translator_key)

    def __repr__(self) -> str:  # never leak keys into logs/tracebacks
        return (
            f"AzureCredentials(speech={'set' if self.has_speech else 'unset'}, "
            f"translator={'set' if self.has_translator else 'unset'})"
        )


def normalize_region(region: str) -> str:
    """'West Europe ' -> 'westeurope' (the form Azure endpoints and headers expect)."""
    return "".join(region.split()).lower()


def wav_bytes(audio: np.ndarray, rate: int = SAMPLE_RATE) -> bytes:
    """Mono float32 [-1, 1] -> 16-bit PCM WAV."""
    pcm = (np.clip(audio, -1.0, 1.0) * 32767.0).astype("<i2").tobytes()
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + len(pcm),
        b"WAVE",
        b"fmt ",
        16,
        1,  # PCM
        1,  # mono
        rate,
        rate * 2,
        2,
        16,
        b"data",
        len(pcm),
    )
    return header + pcm


class AzureClient:
    def __init__(self, creds: AzureCredentials, transport=None, timeout: float = 8.0):
        self.creds = creds
        self._http = httpx.Client(
            timeout=httpx.Timeout(timeout, connect=4.0),
            transport=transport,
            headers={"User-Agent": f"GameTalk/{__version__}"},
        )
        self._last_use = 0.0

    def close(self) -> None:
        self._http.close()

    @property
    def _speech_url(self) -> str:
        region = normalize_region(self.creds.speech_region)
        return (
            f"https://{region}.stt.speech.microsoft.com"
            "/speech/recognition/conversation/cognitiveservices/v1"
        )

    def recognize(self, audio: np.ndarray, locale: str, phrases: tuple[str, ...] = ()) -> str:
        """Speech -> text in `locale`. Returns '' when Azure heard no speech.

        With `phrases` (gaming vocabulary) the Speech SDK is used, because only it supports
        phrase lists; without them (or if the SDK is missing) the lighter REST API is used.
        """
        if not self.creds.has_speech:
            raise AzureError("Add your Azure Speech key and region in Settings > Azure.")
        if phrases:
            try:
                return recognize_with_phrases(self.creds, audio, locale, phrases)
            except ImportError:
                log.info("Azure Speech SDK not installed; using REST without phrase list")
        r = self._post(
            self._speech_url,
            "Speech",
            params={"language": locale, "format": "simple", "profanity": "raw"},
            content=wav_bytes(audio),
            headers={
                "Ocp-Apim-Subscription-Key": self.creds.speech_key,
                "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
                "Accept": "application/json",
            },
        )
        try:
            data = r.json()
        except ValueError as e:
            raise AzureError("Azure Speech sent an unexpected reply.") from e
        status = data.get("RecognitionStatus")
        if status == "Success":
            return str(data.get("DisplayText", "")).strip()
        if status in ("NoMatch", "InitialSilenceTimeout", "BabbleTimeout"):
            return ""
        log.warning("Azure Speech status: %s", status)
        raise AzureError("Azure Speech couldn't process the audio.")

    def translate(self, text: str, source: str | None, target: str) -> str:
        if not self.creds.has_translator:
            raise AzureError("Add your Azure Translator key in Settings > Azure.")
        params = {"api-version": "3.0", "to": target}
        if source:
            params["from"] = source
        headers = {
            "Ocp-Apim-Subscription-Key": self.creds.translator_key,
            "Content-Type": "application/json; charset=UTF-8",
        }
        region = normalize_region(self.creds.translator_region)
        if region and region != "global":
            headers["Ocp-Apim-Subscription-Region"] = region
        r = self._post(
            f"{TRANSLATOR_URL}/translate",
            "Translator",
            params=params,
            json=[{"Text": text}],
            headers=headers,
        )
        try:
            return str(r.json()[0]["translations"][0]["text"]).strip()
        except (ValueError, LookupError, TypeError) as e:
            raise AzureError("Azure Translator sent an unexpected reply.") from e

    def prewarm(self, speech: bool, translator: bool) -> None:
        """Open TLS connections while the user is still talking (only if they've gone cold)."""
        if time.monotonic() - self._last_use < PREWARM_AFTER_IDLE:
            return
        urls = []
        if speech and self.creds.has_speech:
            urls.append(self._speech_url)
        if translator and self.creds.has_translator:
            urls.append(f"{TRANSLATOR_URL}/languages?api-version=3.0&scope=dictionary")
        for url in urls:
            try:
                self._http.head(url, timeout=2.0)
            except httpx.HTTPError:
                pass
        self._last_use = time.monotonic()

    def _post(self, url: str, service: str, **kwargs) -> httpx.Response:
        t0 = time.perf_counter()
        for attempt in (1, 2):
            try:
                r = self._http.post(url, **kwargs)
                break
            except httpx.TimeoutException as e:  # don't retry: the user is already waiting
                raise AzureError(f"Azure {service} timed out — check your connection.") from e
            except _STALE_CONNECTION_ERRORS as e:
                # A kept-alive connection often dies across sleep/resume or a network switch;
                # one retry on a fresh connection fixes that without bothering the user.
                if attempt == 1:
                    log.info(
                        "Azure %s: connection dropped (%s), retrying", service, type(e).__name__
                    )
                    continue
                log.warning("Azure %s request failed: %s", service, type(e).__name__)
                raise AzureError(f"Can't reach Azure {service} — check internet and region.") from e
            except httpx.HTTPError as e:
                log.warning("Azure %s request failed: %s", service, type(e).__name__)
                raise AzureError(f"Can't reach Azure {service} — check internet and region.") from e
        log.info("Azure %s: HTTP %s in %.2fs", service, r.status_code, time.perf_counter() - t0)
        if r.status_code in (401, 403):
            raise AzureError(f"Azure {service}: invalid key or wrong region.")
        if r.status_code == 429:
            raise AzureError(f"Azure {service}: rate limit or free quota reached.")
        if r.status_code >= 400:
            raise AzureError(f"Azure {service} error (HTTP {r.status_code}).")
        self._last_use = time.monotonic()
        return r


def recognize_with_phrases(
    creds: AzureCredentials,
    audio: np.ndarray,
    locale: str,
    phrases: tuple[str, ...],
    timeout: float = 15.0,
) -> str:
    """Azure Speech SDK recognition with a phrase list (boosts gaming terms like "Medic").

    Continuous recognition over the whole push-to-talk clip, so multi-sentence recordings
    aren't cut after the first pause. Raises ImportError if the SDK isn't installed.
    """
    import threading

    import azure.cognitiveservices.speech as speechsdk

    config = speechsdk.SpeechConfig(
        subscription=creds.speech_key, region=normalize_region(creds.speech_region)
    )
    config.speech_recognition_language = locale
    fmt = speechsdk.audio.AudioStreamFormat(samples_per_second=SAMPLE_RATE, bits_per_sample=16)
    stream = speechsdk.audio.PushAudioInputStream(stream_format=fmt)
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=config, audio_config=speechsdk.audio.AudioConfig(stream=stream)
    )
    grammar = speechsdk.PhraseListGrammar.from_recognizer(recognizer)
    for phrase in phrases[:100]:
        grammar.addPhrase(phrase)

    texts: list[str] = []
    errors: list[str] = []
    done = threading.Event()

    def on_recognized(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech and evt.result.text:
            texts.append(evt.result.text.strip())

    def on_canceled(evt):
        try:
            details = evt.cancellation_details
            if details.reason == speechsdk.CancellationReason.Error:
                errors.append(f"{getattr(details, 'code', '')} {details.error_details or ''}")
        except Exception as e:  # an exception here would be swallowed by the SDK
            errors.append(f"canceled ({type(e).__name__})")
        done.set()

    recognizer.recognized.connect(on_recognized)
    recognizer.canceled.connect(on_canceled)
    recognizer.session_stopped.connect(lambda _evt: done.set())

    t0 = time.perf_counter()
    recognizer.start_continuous_recognition_async().get()
    pcm = (np.clip(audio, -1.0, 1.0) * 32767.0).astype("<i2").tobytes()
    stream.write(pcm)
    stream.close()  # end of audio -> session stops after the last phrase
    finished = done.wait(timeout)
    recognizer.stop_continuous_recognition_async().get()
    log.info("Azure Speech (phrase list): %.2fs", time.perf_counter() - t0)
    if errors:
        code = errors[0]
        if any(w in code for w in ("Authentication", "Forbidden", "401", "403")):
            raise AzureError("Azure Speech: invalid key or wrong region.")
        if "TooManyRequests" in code:
            raise AzureError("Azure Speech: rate limit or free quota reached.")
        if "Connection" in code or "Timeout" in code:
            raise AzureError("Can't reach Azure Speech — check internet and region.")
        raise AzureError("Azure Speech couldn't process the audio.")
    if not finished:
        raise AzureError("Azure Speech timed out — check your connection.")
    return " ".join(texts)


def check_connection(creds: AzureCredentials, transport=None) -> list[tuple[bool, str]]:
    """Check each configured service. Sends 0.5 s of silence and one Arabic word, nothing else."""
    results: list[tuple[bool, str]] = []
    client = AzureClient(creds, transport=transport)
    try:
        if creds.has_speech:
            try:
                client.recognize(np.zeros(SAMPLE_RATE // 2, np.float32), "ar-SA")
                results.append((True, "Azure Speech: connected"))
            except AzureError as e:
                results.append((False, str(e)))
        else:
            results.append((False, "Azure Speech: no key/region entered"))
        if creds.has_translator:
            try:
                out = client.translate("مرحبا", "ar", "en")
                results.append((True, f"Azure Translator: connected (مرحبا → {out})"))
            except AzureError as e:
                results.append((False, str(e)))
        else:
            results.append((False, "Azure Translator: no key entered"))
    finally:
        client.close()
    return results
