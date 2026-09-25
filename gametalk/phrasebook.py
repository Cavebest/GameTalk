# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Learning mode: your own phrasebook of sentences you've used, for practice.

Opt-in only (Features → Learning mode): this is the one place GameTalk stores what you said,
in %APPDATA%\\GameTalk\\phrasebook.json on this PC. Clear it any time from the phrasebook window.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

MAX_ENTRIES = 1000
SAVE_EVERY_S = 30.0


def normalize(text: str) -> str:
    """Key for counting: case/space/punctuation-insensitive."""
    return " ".join("".join(c for c in text.casefold() if c.isalnum() or c.isspace()).split())


@dataclass
class Entry:
    english: str
    arabic: str = ""
    count: int = 1
    last_used: float = field(default_factory=time.time)
    known: bool = False  # practice: marked "I knew it"


class Phrasebook:
    def __init__(self, path: Path, persistent: bool, clock=time.time):
        self.path = path
        self.persistent = persistent
        self._clock = clock
        self._dirty = False
        self._last_save = 0.0
        self.entries: dict[str, Entry] = self._load() if persistent else {}

    def _load(self) -> dict[str, Entry]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            out = {}
            for item in data.get("entries", []):
                e = Entry(
                    english=str(item.get("english", "")),
                    arabic=str(item.get("arabic", "")),
                    count=int(item.get("count", 1)),
                    last_used=float(item.get("last_used", 0)),
                    known=bool(item.get("known", False)),
                )
                if e.english:
                    out[normalize(e.english)] = e
            return out
        except (OSError, ValueError, TypeError, AttributeError):
            return {}

    def set_persistent(self, on: bool) -> None:
        if on and not self.persistent:
            saved = self._load()
            for k, e in self.entries.items():  # keep this session's counts
                if k in saved:
                    saved[k].count += e.count
                else:
                    saved[k] = e
            self.entries = saved
            self._dirty = True
        self.persistent = on

    def add(self, english: str, arabic: str = "") -> Entry | None:
        key = normalize(english)
        if not key:
            return None
        e = self.entries.get(key)
        if e is None:
            e = Entry(english=english, arabic=arabic, count=0)
            self.entries[key] = e
        e.count += 1
        e.last_used = self._clock()
        if arabic and not e.arabic:
            e.arabic = arabic
        if len(self.entries) > MAX_ENTRIES:  # forget the least useful ones
            victims = sorted(
                self.entries, key=lambda k: (self.entries[k].count, self.entries[k].last_used)
            )
            for k in victims[: len(self.entries) - MAX_ENTRIES]:
                del self.entries[k]
        self._dirty = True
        if self.persistent and self._clock() - self._last_save >= SAVE_EVERY_S:
            self.save()
        return e

    def remove(self, english: str) -> None:
        if self.entries.pop(normalize(english), None) is not None:
            self._dirty = True

    def clear(self) -> None:
        self.entries.clear()
        self._dirty = True
        self.save()

    def set_known(self, english: str, known: bool) -> None:
        e = self.entries.get(normalize(english))
        if e is not None:
            e.known = known
            self._dirty = True

    def most_used(self, limit: int = 50) -> list[Entry]:
        return sorted(self.entries.values(), key=lambda e: (-e.count, -e.last_used))[:limit]

    def practice_order(self) -> list[Entry]:
        """Unknown first, most used first — the phrases most worth learning."""
        return sorted(self.entries.values(), key=lambda e: (e.known, -e.count, -e.last_used))

    def count(self, english: str) -> int:
        e = self.entries.get(normalize(english))
        return e.count if e else 0

    def save(self) -> None:
        if not self.persistent:
            return
        if not self._dirty and self.path.exists():
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            data = {"entries": [asdict(e) for e in self.most_used(MAX_ENTRIES)]}
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), "utf-8")
            os.replace(tmp, self.path)
            self._dirty = False
            self._last_save = self._clock()
        except OSError as e:
            log.warning("Could not save phrasebook: %s", e)
