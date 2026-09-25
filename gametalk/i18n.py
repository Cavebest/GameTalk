# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Tiny UI translation layer: English strings are the keys, Arabic lives in i18n_ar.py.

tr("Hold {key} while you speak.", key="F9") returns the Arabic text when the UI language is
Arabic, otherwise the English text. Missing translations fall back to English (never crash).
"""

from __future__ import annotations

import ctypes
import sys

from .i18n_ar import AR

_lang = "en"


def windows_language() -> str:
    """'ar' if Windows' display language is Arabic, else 'en'."""
    if sys.platform != "win32":
        return "en"
    try:
        langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
    except (AttributeError, OSError):
        return "en"
    return "ar" if (langid & 0x3FF) == 0x01 else "en"  # LANG_ARABIC primary id


def set_language(code: str) -> str:
    """'auto' | 'en' | 'ar'. Returns the language actually used."""
    global _lang
    _lang = windows_language() if code == "auto" else ("ar" if code == "ar" else "en")
    return _lang


def language() -> str:
    return _lang


def is_rtl() -> bool:
    return _lang == "ar"


RLM = "‏"  # invisible right-to-left mark


def tr(text: str, /, **kwargs) -> str:  # positional-only: "{text}" can be a placeholder
    s = text
    if _lang == "ar" and text in AR:
        # The RLM makes Arabic lines that start with an English word ("Whisper …", "Azure …")
        # still read right-to-left instead of being reordered.
        s = RLM + AR[text]
    return s.format(**kwargs) if kwargs else s


def apply_layout_direction(app) -> None:
    """Right-to-left widgets for Arabic (menus, forms and dialogs mirror correctly)."""
    from PySide6.QtCore import Qt

    app.setLayoutDirection(
        Qt.LayoutDirection.RightToLeft if is_rtl() else Qt.LayoutDirection.LeftToRight
    )
