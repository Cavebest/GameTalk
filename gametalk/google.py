# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Google Cloud clients: Translation (Basic v2 endpoint) and Speech-to-Text v2 (Chirp 3).

Translation has two models: the standard NMT model, and Google's Translation LLM (better with
dialect and context, needs the Google Cloud project ID); it only ever receives text.
Chirp 3 receives the push-to-talk audio (silence trimmed) and needs the project ID too.
The key travels in the X-goog-api-key header (never in the URL, so it can't end up in logs).
"""

from __future__ import annotations

import base64
import html
import json
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
SPEECH_LOCATION = "us"  # Chirp 3 is generally available in the "us" and "eu" multi-regions
SPEECH_PRICE_PER_MINUTE = 0.016  # USD, Speech-to-Text v2 standard models (incl. Chirp 3)
# Arabic locales Chirp 3 knows (others fall back to its generic Arabic, ar-XA)
CHIRP_ARABIC = {
    "ar-DZ",
    "ar-BH",
    "ar-EG",
    "ar-IL",
    "ar-JO",
    "ar-KW",
    "ar-LB",
    "ar-MR",
    "ar-MA",
    "ar-OM",
    "ar-QA",
    "ar-SA",
    "ar-PS",
    "ar-SY",
    "ar-TN",
    "ar-AE",
    "ar-YE",
    "ar-XA",
}
# Our language codes -> Google's where they differ
_CODES = {"zh-Hans": "zh-CN"}
_STALE_CONNECTION_ERRORS = (httpx.ConnectError, httpx.RemoteProtocolError, httpx.ReadError)
TOKEN_SCOPE = "https://www.googleapis.com/auth/cloud-platform"
TOKEN_URI = "https://oauth2.googleapis.com/token"


class GoogleError(Exception):
    """User-presentable Google Translate failure."""


@dataclass(frozen=True)
class GoogleCredentials:
    api_key: str = ""
    project_id: str = ""
    model: str = "nmt"  # "nmt" | "llm"
    location: str = DEFAULT_LOCATION
    denoise: bool = True  # Chirp 3's built-in noise reduction (game sound in the mic)
    service_account: str = ""  # service-account JSON (Chirp 3 doesn't take API keys)

    @property
    def has_key(self) -> bool:
        return bool(self.api_key)

    @property
    def speech_ready(self) -> bool:
        return bool(self.service_account or self.api_key) and bool(self.project_id)

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
        return (
            f"GoogleCredentials(key={'set' if self.has_key else 'unset'}, model={self.model}, "
            f"service_account={'set' if self.service_account else 'unset'})"
        )


def parse_service_account(text: str) -> dict:
    """The fields GameTalk needs from a service-account key file; ValueError if it isn't one."""
    try:
        data = json.loads(text)
    except ValueError as e:
        raise ValueError("not JSON") from e
    if not isinstance(data, dict) or data.get("type") != "service_account":
        raise ValueError("not a service account key")
    for field in ("client_email", "private_key", "project_id"):
        if not isinstance(data.get(field), str) or not data[field]:
            raise ValueError(f"missing {field}")
    return data


def signed_jwt(account: dict, now: float | None = None) -> str:
    """RS256 JWT asking Google for a one-hour access token (OAuth 2.0 JWT bearer grant)."""
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    def b64(raw: bytes) -> str:
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")

    iat = int(now if now is not None else time.time())
    header = {"alg": "RS256", "typ": "JWT"}
    if account.get("private_key_id"):
        header["kid"] = account["private_key_id"]
    claims = {
        "iss": account["client_email"],
        "scope": TOKEN_SCOPE,
        "aud": account.get("token_uri") or TOKEN_URI,
        "iat": iat,
        "exp": iat + 3600,
    }
    signing_input = f"{b64(json.dumps(header).encode())}.{b64(json.dumps(claims).encode())}"
    key = serialization.load_pem_private_key(account["private_key"].encode(), password=None)
    signature = key.sign(signing_input.encode("ascii"), padding.PKCS1v15(), hashes.SHA256())
    return f"{signing_input}.{b64(signature)}"


def google_code(lang: str | None) -> str | None:
    return _CODES.get(lang, lang) if lang else lang


def chirp_locale(locale: str) -> str:
    return locale if locale in CHIRP_ARABIC or not locale.startswith("ar") else "ar-XA"


def billed_chars(creds: GoogleCredentials, source: str, output: str) -> int:
    """NMT bills input characters; the Translation LLM bills input + output."""
    return len(source) + (len(output) if creds.model == "llm" else 0)


class GoogleClient:
    def __init__(self, creds: GoogleCredentials, transport=None, timeout: float = 8.0):
        self.creds = creds
        self._token = ("", 0.0)  # (access token, expires at) for the service account
        self._http = httpx.Client(
            timeout=httpx.Timeout(timeout, connect=4.0),
            transport=transport,
            headers={"User-Agent": f"GameTalk/{__version__}"},
        )

    def close(self) -> None:
        self._http.close()

    def translate(self, text: str, source: str | None, target: str) -> str:
        if not self.creds.has_key:
            raise GoogleError("Add your Google Translate API key on the Cloud keys page.")
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
        r = self._post(URL, body, "translate")
        try:
            out = r.json()["data"]["translations"][0]["translatedText"]
        except (ValueError, LookupError, TypeError) as e:
            raise GoogleError("Google Translate sent an unexpected reply.") from e
        return html.unescape(str(out)).strip()

    def _speech_headers(self) -> dict:
        """Bearer token from the service account (cached ~1 h), or the API key."""
        if not self.creds.service_account:
            return {"X-goog-api-key": self.creds.api_key}
        token, expires = self._token
        if not token or time.time() > expires - 60:
            try:
                account = parse_service_account(self.creds.service_account)
                assertion = signed_jwt(account)
            except (ValueError, TypeError) as e:
                raise GoogleError("Google Chirp 3: the service account file isn't valid.") from e
            try:
                r = self._http.post(
                    account.get("token_uri") or TOKEN_URI,
                    data={
                        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                        "assertion": assertion,
                    },
                )
            except httpx.HTTPError as e:
                raise GoogleError("Can't reach Google Chirp 3 — check your internet.") from e
            if r.status_code != 200:
                log.warning("Google token request refused: HTTP %s", r.status_code)
                raise GoogleError("Google Chirp 3: the service account was refused.")
            try:
                body = r.json()
                token = str(body["access_token"])
                expires = time.time() + float(body.get("expires_in", 3600))
            except (ValueError, KeyError, TypeError) as e:
                raise GoogleError("Google Chirp 3 sent an unexpected reply.") from e
            self._token = (token, expires)
        return {"Authorization": f"Bearer {token}"}

    def recognize(self, audio, locale: str, phrases: tuple[str, ...] = ()) -> str:
        """Chirp 3: speech -> text in `locale`. Returns '' when nothing was said."""
        if not (self.creds.service_account or self.creds.has_key):
            raise GoogleError("Load your Google service account file on the Cloud keys page.")
        if not self.creds.project_id:
            raise GoogleError("Google Chirp 3 needs your Google Cloud project ID.")
        from .azure import wav_bytes

        config = {
            "autoDecodingConfig": {},
            "languageCodes": [chirp_locale(locale)],
            "model": "chirp_3",
        }
        if self.creds.denoise:
            config["denoiserConfig"] = {"denoiseAudio": True, "snrThreshold": 0.0}
        if phrases:  # gaming vocabulary as recognition hints
            config["adaptation"] = {
                "phraseSets": [
                    {"inlinePhraseSet": {"phrases": [{"value": p} for p in phrases[:50]]}}
                ]
            }
        body = {"config": config, "content": base64.b64encode(wav_bytes(audio)).decode("ascii")}
        url = (
            f"https://{SPEECH_LOCATION}-speech.googleapis.com/v2/projects/{self.creds.project_id}"
            f"/locations/{SPEECH_LOCATION}/recognizers/_:recognize"
        )
        r = self._post(url, body, "speech", self._speech_headers())
        try:
            results = r.json().get("results", [])
            parts = [
                res["alternatives"][0].get("transcript", "")
                for res in results
                if res.get("alternatives")
            ]
        except (ValueError, LookupError, TypeError, AttributeError) as e:
            raise GoogleError("Google Chirp 3 sent an unexpected reply.") from e
        return " ".join(p.strip() for p in parts if p.strip())

    def _post(self, url: str, body: dict, service: str, headers=None) -> httpx.Response:
        name = "Google Chirp 3" if service == "speech" else "Google Translate"
        t0 = time.perf_counter()
        headers = headers or {"X-goog-api-key": self.creds.api_key}
        for attempt in (1, 2):
            try:
                r = self._http.post(url, json=body, headers=headers)
                break
            except httpx.TimeoutException as e:
                raise GoogleError(f"{name} timed out — check your connection.") from e
            except _STALE_CONNECTION_ERRORS as e:
                if attempt == 1:  # dead keep-alive connection after sleep/network change
                    continue
                raise GoogleError(f"Can't reach {name} — check your internet.") from e
            except httpx.HTTPError as e:
                raise GoogleError(f"Can't reach {name} — check your internet.") from e
        log.info("%s: HTTP %s in %.2fs", name, r.status_code, time.perf_counter() - t0)
        if r.status_code >= 400:
            raise GoogleError(_error_message(r, service))
        return r


def _speech_error(r: httpx.Response, low: str) -> str:
    if "api key" in low and ("not supported" in low or "expected oauth" in low):
        return "Google Chirp 3 needs a service account file, not an API key (Cloud keys page)."
    if "permission" in low and r.status_code == 403:
        return "Google Chirp 3: give the service account the “Cloud Speech Client” role."
    if "api key not valid" in low or "api_key_invalid" in low:
        return "Google Chirp 3: the API key isn't valid."
    if "billing" in low:
        return "Google Chirp 3: turn on billing for your Google Cloud project."
    if "has not been used" in low or "disabled" in low or "service_disabled" in low:
        return "Google Chirp 3: enable the Cloud Speech-to-Text API for your project."
    if r.status_code == 429 or "quota" in low:
        return "Google Chirp 3: rate limit or quota reached."
    if r.status_code in (401, 403):
        return "Google Chirp 3: this key isn't allowed to use Speech-to-Text."
    if r.status_code == 404 or "project" in low:
        return "Google Chirp 3: check the project ID."
    if "language" in low or "locale" in low:
        return "Google Chirp 3: this dialect isn't available — pick another."
    return f"Google Chirp 3 error (HTTP {r.status_code})."


def _error_message(r: httpx.Response, service: str = "translate") -> str:
    reason, message = "", ""
    try:
        err = r.json().get("error", {})
        message = str(err.get("message", ""))
        details = err.get("details") or err.get("errors") or []
        reason = str(next((d.get("reason", "") for d in details if d.get("reason")), ""))
    except (ValueError, AttributeError, TypeError):
        pass
    log.warning("Google %s error: HTTP %s %s", service, r.status_code, reason or "-")
    low = (message + " " + reason).lower()
    if service == "speech":
        return _speech_error(r, low)
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


def check_connection(
    creds: GoogleCredentials, transport=None, speech: bool = False
) -> list[tuple[bool, str]]:
    """Translate one Arabic word (and, with speech=True, send half a second of silence to
    Chirp 3) to prove the key, project and models work."""
    if not creds.has_key and not (speech and creds.service_account):
        return [(False, "Google Translate: no API key entered")]
    client = GoogleClient(creds, transport=transport)
    results: list[tuple[bool, str]] = []
    try:
        if creds.has_key:
            try:
                out = client.translate("مرحبا", "ar", "en")
                name = "Google Translation LLM" if creds.model == "llm" else "Google Translate"
                results.append((True, f"{name}: connected (مرحبا → {out})"))
            except GoogleError as e:
                results.append((False, str(e)))
        if speech:
            import numpy as np

            try:
                t0 = time.perf_counter()
                client.recognize(np.zeros(8000, np.float32), "ar-JO")
                ms = round((time.perf_counter() - t0) * 1000)
                results.append((True, f"Google Chirp 3: connected ({ms} ms)"))
            except GoogleError as e:
                results.append((False, str(e)))
    finally:
        client.close()
    return results
