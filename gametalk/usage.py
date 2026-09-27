# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Cloud usage counter: how much of the monthly free tiers you've used.

Counts only amounts (seconds of audio sent to Azure Speech, characters sent to Azure
Translator and Google Translate) — never what was said. Stored in
%APPDATA%\\GameTalk\\usage.json, written at most once every 30 s (and on exit) to avoid
needless disk writes.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path

log = logging.getLogger(__name__)

SPEECH_FREE_SECONDS = 5 * 3600  # Azure Speech F0: 5 audio hours / month
TRANSLATOR_FREE_CHARS = 2_000_000  # Azure Translator F0: 2 million characters / month
GOOGLE_FREE_CHARS = 500_000  # Google Cloud Translation: $10 monthly credit (NMT characters)
WARN_AT = (0.8, 1.0)
SAVE_EVERY_S = 30.0


def month_key(ts: float | None = None) -> str:
    return time.strftime("%Y-%m", time.localtime(ts))


@dataclass
class MonthUsage:
    month: str
    speech_seconds: float = 0.0
    translator_chars: int = 0
    google_chars: int = 0
    google_speech_seconds: float = 0.0  # Chirp 3 has no free tier: shown as minutes and cost
    warned_speech: float = 0.0  # highest warning level already shown (0, 0.8, 1.0)
    warned_translator: float = 0.0
    warned_google: float = 0.0

    @property
    def speech_fraction(self) -> float:
        return self.speech_seconds / SPEECH_FREE_SECONDS

    @property
    def translator_fraction(self) -> float:
        return self.translator_chars / TRANSLATOR_FREE_CHARS

    @property
    def google_fraction(self) -> float:
        return self.google_chars / GOOGLE_FREE_CHARS


class UsageTracker:
    def __init__(self, path: Path, clock=time.time):
        self.path = path
        self._clock = clock
        self._dirty = False
        self._last_save = 0.0
        self.current = self._load()

    def _load(self) -> MonthUsage:
        month = month_key(self._clock())
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if data.get("month") == month:
                return MonthUsage(
                    month=month,
                    speech_seconds=float(data.get("speech_seconds", 0)),
                    translator_chars=int(data.get("translator_chars", 0)),
                    google_chars=int(data.get("google_chars", 0)),
                    google_speech_seconds=float(data.get("google_speech_seconds", 0)),
                    warned_speech=float(data.get("warned_speech", 0)),
                    warned_translator=float(data.get("warned_translator", 0)),
                    warned_google=float(data.get("warned_google", 0)),
                )
        except (OSError, ValueError, TypeError):
            pass
        return MonthUsage(month=month)

    def _roll_month(self) -> None:
        month = month_key(self._clock())
        if self.current.month != month:
            self.current = MonthUsage(month=month)
            self._dirty = True

    def add(
        self,
        speech_seconds: float = 0.0,
        translator_chars: int = 0,
        google_chars: int = 0,
        google_speech_seconds: float = 0.0,
    ) -> list[str]:
        """Record usage; returns warning keys that just crossed a threshold."""
        if not (speech_seconds or translator_chars or google_chars or google_speech_seconds):
            return []
        self._roll_month()
        u = self.current
        u.speech_seconds += max(0.0, speech_seconds)
        u.translator_chars += max(0, translator_chars)
        u.google_chars += max(0, google_chars)
        u.google_speech_seconds += max(0.0, google_speech_seconds)
        self._dirty = True
        warnings = []
        for level in WARN_AT:
            if u.speech_fraction >= level > u.warned_speech:
                u.warned_speech = level
                warnings.append(f"speech:{level}")
            if u.translator_fraction >= level > u.warned_translator:
                u.warned_translator = level
                warnings.append(f"translator:{level}")
            if u.google_fraction >= level > u.warned_google:
                u.warned_google = level
                warnings.append(f"google:{level}")
        if self._clock() - self._last_save >= SAVE_EVERY_S:
            self.save()
        return warnings

    def reset(self) -> None:
        self.current = MonthUsage(month=month_key(self._clock()))
        self._dirty = True
        self.save()

    def save(self) -> None:
        if not self._dirty:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(asdict(self.current), indent=2), "utf-8")
            os.replace(tmp, self.path)
            self._dirty = False
            self._last_save = self._clock()
        except OSError as e:
            log.warning("Could not save usage: %s", e)
