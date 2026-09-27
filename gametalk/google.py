# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Google Cloud Translation client (Basic v2 endpoint, API key).

Two models: the standard NMT model, and Google's Translation LLM (better with dialect and
context, needs the Google Cloud project ID). Only the recognised text is sent — never audio.
The key travels in the X-goog-api-key header (never in the URL, so it can't end up in logs).
"""

from __future__ import annotations

import html
import logging
import time
from dataclasses import dataclass

import httpx

from . import __version__

log = logging.getLogger(__name__)

URL = "https://translation.googleapis.com/language/translate/v2"
MODELS = {"nmt": "Standard (NMT)", "llm": "Translation LLM (smarter, needs project ID)"}
DEFAULT_LOCATION = "us-central1"
GOOGLE_FREE_CHARS = 500_000  # $10 monthly credit = 500k NMT characters
# Our language codes -> Google's where they differ
_CODES = {"zh-Hans": "zh-CN"}
_STALE_CONNECTION_ERRORS = (httpx.ConnectError, httpx.RemoteProtocolError, httpx.ReadError)


class GoogleError(Exception):
    """User-presentable Google Translate failure."""


@dataclass(frozen=True)
class GoogleCredentials:
    api_key: str = ""
    project_id: str = ""
    model: str = "nmt"  # "nmt" | "llm"
    location: str = DEFAULT_LOCATION

    @property
    def has_key(self) -> bool:
        return bool(self.api_key)

    @property
    def ready(self) -> bool:
        return self.has_key and (self.model != "llm" or bool(self.project_id))

    @property
    def model_param(self) -> str:
        if self.model == "llm":
            return (
                f"projects/{self.project_id}/locations/{self.location or DEFAULT_LOCATION}"
                "/models/general/translation-llm"
            )
        return "nmt"

    def __repr__(self) -> str:  # never leak the key into logs/tracebacks
        return f"GoogleCredentials(key={'set' if self.has_key else 'unset'}, model={self.model})"


def google_code(lang: str | None) -> str | None:
    return _CODES.get(lang, lang) if lang else lang


def billed_chars(creds: GoogleCredentials, source: str, output: str) -> int:
    """NMT bills input characters; the Translation LLM bills input + output."""
    return len(source) + (len(output) if creds.model == "llm" else 0)


class GoogleClient:
    def __init__(self, creds: GoogleCredentials, transport=None, timeout: float = 8.0):
        self.creds = creds
        self._http = httpx.Client(
            timeout=httpx.Timeout(timeout, connect=4.0),
            transport=transport,
            headers={"User-Agent": f"GameTalk/{__version__}"},
        )

    def close(self) -> None:
        self._http.close()

    def translate(self, text: str, source: str | None, target: str) -> str:
        if not self.creds.has_key:
            raise GoogleError("Add your Google Translate API key in Settings > Cloud keys.")
        if not self.creds.ready:
            raise GoogleError("Google Translation LLM needs your Google Cloud project ID.")
        body = {
            "q": [text],
            "target": google_code(target),
            "format": "text",
            "model": self.creds.model_param,
        }
        if source:
            body["source"] = google_code(source)
        r = self._post(body)
        try:
            out = r.json()["data"]["translations"][0]["translatedText"]
        except (ValueError, LookupError, TypeError) as e:
            raise GoogleError("Google Translate sent an unexpected reply.") from e
        return html.unescape(str(out)).strip()

    def _post(self, body: dict) -> httpx.Response:
        t0 = time.perf_counter()
        headers = {"X-goog-api-key": self.creds.api_key}
        for attempt in (1, 2):
            try:
                r = self._http.post(URL, json=body, headers=headers)
                break
            except httpx.TimeoutException as e:
                raise GoogleError("Google Translate timed out — check your connection.") from e
            except _STALE_CONNECTION_ERRORS as e:
                if attempt == 1:  # dead keep-alive connection after sleep/network change
                    continue
                raise GoogleError("Can't reach Google Translate — check your internet.") from e
            except httpx.HTTPError as e:
                raise GoogleError("Can't reach Google Translate — check your internet.") from e
        log.info("Google Translate: HTTP %s in %.2fs", r.status_code, time.perf_counter() - t0)
        if r.status_code >= 400:
            raise GoogleError(_error_message(r))
        return r


def _error_message(r: httpx.Response) -> str:
    reason, message = "", ""
    try:
        err = r.json().get("error", {})
        message = str(err.get("message", ""))
        details = err.get("details") or err.get("errors") or []
        reason = str(next((d.get("reason", "") for d in details if d.get("reason")), ""))
    except (ValueError, AttributeError, TypeError):
        pass
    log.warning("Google Translate error: HTTP %s %s", r.status_code, reason or "-")
    low = (message + " " + reason).lower()
    if "api key not valid" in low or "api_key_invalid" in low:
        return "Google Translate: the API key isn't valid."
    if "billing" in low:
        return "Google Translate: turn on billing for your Google Cloud project."
    if "has not been used" in low or "disabled" in low or "service_disabled" in low:
        return "Google Translate: enable the Cloud Translation API for your project."
    if r.status_code == 429 or "quota" in low:
        return "Google Translate: rate limit or quota reached."
    if r.status_code in (401, 403):
        return "Google Translate: this key isn't allowed to use Cloud Translation."
    if r.status_code == 404 or "model" in low:
        return "Google Translate: check the project ID for the Translation LLM."
    return f"Google Translate error (HTTP {r.status_code})."


def check_connection(creds: GoogleCredentials, transport=None) -> list[tuple[bool, str]]:
    """Translate one Arabic word to prove the key (and model) work."""
    if not creds.has_key:
        return [(False, "Google Translate: no API key entered")]
    client = GoogleClient(creds, transport=transport)
    try:
        out = client.translate("مرحبا", "ar", "en")
        name = "Google Translation LLM" if creds.model == "llm" else "Google Translate"
        return [(True, f"{name}: connected (مرحبا → {out})")]
    except GoogleError as e:
        return [(False, str(e))]
    finally:
        client.close()
