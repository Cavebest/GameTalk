# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Pronunciation helper: English sentence -> how to say it, written in Arabic letters.

"Wait for me, I'm coming." -> "وايت فور مي، آيم كامينغ."
Uses the public-domain CMU Pronouncing Dictionary (offline). It's loaded lazily, and only
when the feature is on (~0.4 s, ~17 MB). Unknown words fall back to suffix rules, then to
letter rules.
"""

from __future__ import annotations

import logging
import re
import threading

log = logging.getLogger(__name__)

_dict: dict[str, str] | None = None
_lock = threading.Lock()

# ARPAbet consonants -> Arabic letters (Arabic has no p/v/g/ch sounds: closest readable letters)
_CONS = {
    "B": "ب",
    "CH": "تش",
    "D": "د",
    "DH": "ذ",
    "F": "ف",
    "G": "غ",
    "HH": "ه",
    "JH": "ج",
    "K": "ك",
    "L": "ل",
    "M": "م",
    "N": "ن",
    "NG": "نغ",
    "P": "ب",
    "R": "ر",
    "S": "س",
    "SH": "ش",
    "T": "ت",
    "TH": "ث",
    "V": "ف",
    "W": "و",
    "Y": "ي",
    "Z": "ز",
    "ZH": "ج",
}
# Vowels inside a word / at the start of a word (needs an alef carrier)
_VOWEL_MID = {
    "AA": "ا",
    "AE": "ا",
    "AH": "ا",
    "AO": "و",
    "AW": "او",
    "AY": "اي",
    "EH": "ي",
    "ER": "ير",
    "EY": "اي",
    "IH": "ي",
    "IY": "ي",
    "OW": "و",
    "OY": "وي",
    "UH": "و",
    "UW": "و",
}
_VOWEL_START = {
    "AA": "آ",
    "AE": "أ",
    "AH": "أ",
    "AO": "أو",
    "AW": "آو",
    "AY": "آي",
    "EH": "إ",
    "ER": "إر",
    "EY": "إي",
    "IH": "إ",
    "IY": "إي",
    "OW": "أو",
    "OY": "أوي",
    "UH": "أو",
    "UW": "أو",
}
_PUNCT = {",": "،", "?": "؟", ";": "؛"}
_WORD = re.compile(r"[A-Za-z']+|\d+|[^\sA-Za-z'\d]+")

# Rough letter fallback for names/slang the dictionary doesn't know.
_LETTER_RULES = [
    ("sh", "ش"),
    ("ch", "تش"),
    ("th", "ث"),
    ("ph", "ف"),
    ("ck", "ك"),
    ("ee", "ي"),
    ("oo", "و"),
    ("ou", "او"),
    ("ai", "اي"),
    ("ay", "اي"),
    ("qu", "كو"),
    ("a", "ا"),
    ("b", "ب"),
    ("c", "ك"),
    ("d", "د"),
    ("e", "ي"),
    ("f", "ف"),
    ("g", "غ"),
    ("h", "ه"),
    ("i", "ي"),
    ("j", "ج"),
    ("k", "ك"),
    ("l", "ل"),
    ("m", "م"),
    ("n", "ن"),
    ("o", "و"),
    ("p", "ب"),
    ("q", "ك"),
    ("r", "ر"),
    ("s", "س"),
    ("t", "ت"),
    ("u", "ا"),
    ("v", "ف"),
    ("w", "و"),
    ("x", "كس"),
    ("y", "ي"),
    ("z", "ز"),
]


def _load() -> dict[str, str]:
    global _dict
    with _lock:
        if _dict is None:
            import cmudict

            d: dict[str, str] = {}
            with cmudict.dict_stream() as f:
                for raw in f:
                    line = raw.decode("latin-1") if isinstance(raw, bytes) else raw
                    if not line or line.startswith(";;;"):
                        continue
                    word, _, phones = line.strip().partition(" ")
                    if "(" not in word:  # skip alternate pronunciations
                        d[word.lower()] = phones.strip()
            _dict = d
            log.info("Pronunciation dictionary loaded (%d words)", len(d))
        return _dict


def preload_async() -> None:
    """Load the dictionary in the background so the first sentence doesn't wait."""
    if _dict is None:
        threading.Thread(target=_safe_load, name="gametalk-cmudict", daemon=True).start()


def _safe_load() -> None:
    try:
        _load()
    except Exception as e:  # never break translation because of the helper
        log.warning("Pronunciation dictionary unavailable: %s", e)


def _phones(word: str, d: dict[str, str]) -> list[str] | None:
    w = word.lower()
    if w in d:
        return d[w].split()
    for suffix, extra, cut in (
        ("ing", ["IH0", "NG"], 3),
        ("in'", ["IH0", "N"], 3),
        ("ed", ["D"], 2),
        ("es", ["IH0", "Z"], 2),
        ("s", ["Z"], 1),
        ("'s", ["Z"], 2),
        ("er", ["ER0"], 2),
    ):
        if w.endswith(suffix) and len(w) > cut + 2:
            base = w[:-cut]
            for cand in (base, base + "e"):
                if cand in d:
                    return d[cand].split() + extra
    if w.startswith("re") and w[2:] in d:
        return ["R", "IY0"] + d[w[2:]].split()
    return None


def _arabic_from_phones(phones: list[str]) -> str:
    out = []
    for i, ph in enumerate(phones):
        base = ph.rstrip("012")
        stress = ph[-1] if ph[-1].isdigit() else ""
        nxt = phones[i + 1].rstrip("012") if i + 1 < len(phones) else ""
        if base == "NG" and nxt in ("K", "G"):
            out.append("ن")  # "tank" -> تانك, not تانغك
        elif base in _CONS:
            out.append(_CONS[base])
        elif base == "ER" and stress != "1" and i > 0:
            out.append("ر")  # unstressed "-er": "cover" -> كافر
        elif i == 0:
            out.append(_VOWEL_START.get(base, ""))
        elif base == "AH" and stress == "0" and i < len(phones) - 1:
            continue  # unstressed schwa mid-word is barely heard: "enemy" -> إنمي
        else:
            out.append(_VOWEL_MID.get(base, ""))
    return "".join(out)


def _arabic_from_letters(word: str) -> str:
    w, out, i = word.lower().replace("'", ""), [], 0
    while i < len(w):
        for src, dst in _LETTER_RULES:
            if w.startswith(src, i):
                out.append(dst)
                i += len(src)
                break
        else:
            i += 1
    text = "".join(out)
    if text and text[0] in "اوي" and w[0] in "aeiou":
        text = "أ" + text[1:] if text[0] == "ا" else "إ" + text
    return text


def to_arabic(sentence: str) -> str:
    """How to pronounce an English sentence, in Arabic letters ('' if unavailable)."""
    try:
        d = _load()
    except Exception as e:
        log.warning("Pronunciation dictionary unavailable: %s", e)
        return ""
    parts = []
    for token in _WORD.findall(sentence):
        if token[0].isalpha() or token[0] == "'":
            phones = _phones(token, d)
            parts.append(_arabic_from_phones(phones) if phones else _arabic_from_letters(token))
        elif token.isdigit():
            parts.append(token)
        else:
            punct = "".join(_PUNCT.get(c, c) for c in token)
            if parts:
                parts[-1] += punct
            continue
    return " ".join(p for p in parts if p)
