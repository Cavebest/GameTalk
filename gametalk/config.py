# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Settings model and JSON persistence (%APPDATA%\\GameTalk\\config.json)."""

from __future__ import annotations

import copy
import json
import logging
import os
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

MODELS = ["tiny", "base", "small", "medium", "large-v3"]
COMPUTE_DEVICES = ["auto", "cuda", "cpu"]
HOTKEY_MODES = ["push", "toggle", "voice"]  # voice = open mic (no key needed)
LOCAL = "whisper-local"
AZURE = "azure"
SPEECH_PROVIDERS = {
    LOCAL: "Whisper (local, offline)",
    AZURE: "Azure Speech (cloud, most accurate)",
}
TRANSLATION_PROVIDERS = {
    LOCAL: "Whisper (local, speech → English)",
    AZURE: "Azure Translator (cloud)",
}
TARGET_LANGUAGES = {  # Whisper can only produce English; the rest need Azure Translator
    "en": "English",
    "ar": "Arabic",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "pt": "Portuguese",
    "it": "Italian",
    "tr": "Turkish",
    "ru": "Russian",
    "fa": "Persian",
    "ur": "Urdu",
    "hi": "Hindi",
    "zh-Hans": "Chinese (Simplified)",
    "ja": "Japanese",
    "ko": "Korean",
}
# Azure Speech locales for spoken Arabic (pick the closest dialect).
AZURE_LOCALES = {
    "ar-SA": "Arabic — Saudi Arabia",
    "ar-AE": "Arabic — UAE",
    "ar-KW": "Arabic — Kuwait",
    "ar-QA": "Arabic — Qatar",
    "ar-BH": "Arabic — Bahrain",
    "ar-OM": "Arabic — Oman",
    "ar-YE": "Arabic — Yemen",
    "ar-IQ": "Arabic — Iraq",
    "ar-JO": "Arabic — Jordan",
    "ar-LB": "Arabic — Lebanon",
    "ar-SY": "Arabic — Syria",
    "ar-PS": "Arabic — Palestine",
    "ar-EG": "Arabic — Egypt",
    "ar-LY": "Arabic — Libya",
    "ar-TN": "Arabic — Tunisia",
    "ar-DZ": "Arabic — Algeria",
    "ar-MA": "Arabic — Morocco",
}
UI_LANGUAGES = {"auto": "Automatic (Windows language)", "en": "English", "ar": "العربية"}
TEAM_RECOGNIZERS = {LOCAL: "Whisper (local)", AZURE: "Azure Speech (cloud)"}
TEAM_TRANSLATORS = {
    "local": "Offline model (on this PC)",
    AZURE: "Azure Translator (cloud)",
    "none": "Don't translate (show English text)",
}
GAMEPAD_BUTTONS = [
    "",
    "A",
    "B",
    "X",
    "Y",
    "LB",
    "RB",
    "LT",
    "RT",
    "LS",
    "RS",
    "Back",
    "Start",
    "DPadUp",
    "DPadDown",
    "DPadLeft",
    "DPadRight",
]
QUICK_TEXT_TRANSLATORS = {
    "auto": "Automatic (Azure if keys are saved, otherwise offline)",
    "local": "Offline model (on this PC)",
    "azure": "Azure Translator (cloud)",
}
# Common spoken-dialect words -> standard Arabic, applied before text translation. Offline
# models and Azure translate standard Arabic far better ("خليكم وراي" -> "ابقوا خلفي").
DEFAULT_ARABIC_CORRECTIONS = [
    ("استنوني", "انتظروني"),
    ("استناني", "انتظرني"),
    ("استنى", "انتظر"),
    ("استنوا", "انتظروا"),
    ("شوي", "قليلاً"),
    ("شوية", "قليلاً"),
    ("جاي", "قادم"),
    ("جاية", "قادمة"),
    ("جايين", "قادمون"),
    ("خليكم", "ابقوا"),
    ("خليك", "ابقَ"),
    ("وراي", "خلفي"),
    ("ورايا", "خلفي"),
    ("لورا", "إلى الخلف"),
    ("ورا", "خلف"),
    ("في عدو", "يوجد عدو"),
    ("هون", "هنا"),
    ("هنيك", "هناك"),
    ("يلا", "هيا"),
    ("يالله", "هيا"),
    ("بدي", "أريد"),
    ("ابغى", "أريد"),
    ("أبغى", "أريد"),
    ("عايز", "أريد"),
    ("ليش", "لماذا"),
    ("ليه", "لماذا"),
    ("وين", "أين"),
    ("فين", "أين"),
    ("شو", "ماذا"),
    ("ايش", "ماذا"),
    ("إيش", "ماذا"),
    ("مو", "ليس"),
    ("مش", "ليس"),
    ("كتير", "كثيراً"),
    ("هلق", "الآن"),
    ("هلأ", "الآن"),
    ("الحين", "الآن"),
    ("دلوقتي", "الآن"),
    ("زلمة", "رجل"),
    ("منيح", "جيد"),
    ("تمام", "حسناً"),
    ("خلص", "انتهى"),
    ("انتو", "أنتم"),
    ("احنا", "نحن"),
    ("إحنا", "نحن"),
    ("هاد", "هذا"),
    ("هادا", "هذا"),
    ("هذي", "هذه"),
]
HEX_COLOR = "0123456789abcdefABCDEF"
# Launcher presets: (speech provider, translation provider)
MODES = {
    "local": (LOCAL, LOCAL),
    "hybrid": (LOCAL, AZURE),
    "azure": (AZURE, AZURE),
}
SOURCE_LANGUAGES = {
    "ar": "Arabic",
    "en": "English",
    "fr": "French",
    "tr": "Turkish",
    "fa": "Persian",
    "ur": "Urdu",
    "es": "Spanish",
    "de": "German",
    "ru": "Russian",
}
POSITIONS = [
    "top-left",
    "top-center",
    "top-right",
    "middle-left",
    "center",
    "middle-right",
    "bottom-left",
    "bottom-center",
    "bottom-right",
]
MONITORS = ["game", "primary"]
DEFAULT_VOCABULARY = [
    "Medic",
    "Revive",
    "Squad",
    "Ammo",
    "Objective",
    "Tank",
    "Helicopter",
    "Sniper",
    "Enemy",
    "Flank",
    "Push",
    "Fall back",
]
NEVER_HIDE = 0  # display_seconds value meaning "never auto-hide"
MAX_VOCABULARY = 50  # entries kept per profile (the Whisper prompt uses the first 24)
MAX_VOCABULARY_ITEM = 40  # characters per entry
# Per-game overlay look; these lived in OverlayStyle before v0.2 (see _migrate_overlay).
PROFILE_OVERLAY_FIELDS = ("max_width", "background_opacity", "text_opacity")


@dataclass
class QuickPhrase:
    key: str = ""  # hotkey name, e.g. "Numpad1"
    text: str = ""  # shown instantly when the key is pressed


@dataclass
class Correction:
    find: str = ""  # whole word/phrase in the English output (case-insensitive)
    replace: str = ""


@dataclass
class Profile:
    name: str = "Default"
    exe_names: list[str] = field(default_factory=list)  # e.g. ["cs2.exe"] for auto-switching
    hotkey: str = "F9"
    hotkey_mode: str = "push"
    microphone: str = ""  # device name; "" = Windows default input
    model: str = "small"
    speech_provider: str = LOCAL
    translation_provider: str = LOCAL
    azure_locale: str = "ar-SA"
    source_language: str = "ar"
    auto_detect_language: bool = False
    target_language: str = "en"
    gaming_mode: bool = True
    vocabulary_enabled: bool = True
    vocabulary: list[str] = field(default_factory=lambda: list(DEFAULT_VOCABULARY))
    overlay_position: str = "top-center"
    overlay_offset_x: int = 0
    overlay_offset_y: int = 48
    font_size: int = 18
    display_seconds: int = 4  # 1-15, or NEVER_HIDE
    max_width: int = 640
    background_opacity: float = 0.72
    text_opacity: float = 1.0
    quick_phrases: list[QuickPhrase] = field(
        default_factory=lambda: [
            QuickPhrase("Numpad1", "Enemy spotted!"),
            QuickPhrase("Numpad2", "I need a medic!"),
            QuickPhrase("Numpad3", "Fall back!"),
            QuickPhrase("Numpad4", "Cover me, I'm reloading."),
            QuickPhrase("Numpad5", "Wait for me, I'm coming."),
        ]
    )
    corrections: list[Correction] = field(default_factory=list)
    arabic_corrections: list[Correction] = field(
        default_factory=lambda: [Correction(f, r) for f, r in DEFAULT_ARABIC_CORRECTIONS if f != r]
    )

    @property
    def uses_whisper(self) -> bool:
        return self.speech_provider == LOCAL

    @property
    def uses_azure(self) -> bool:
        return AZURE in (self.speech_provider, self.translation_provider)

    @property
    def mode(self) -> str:
        pair = (self.speech_provider, self.translation_provider)
        return next((m for m, v in MODES.items() if v == pair), "local")

    def set_mode(self, mode: str) -> None:
        self.speech_provider, self.translation_provider = MODES.get(mode, MODES["local"])


@dataclass
class AzureSettings:
    """Keys are stored DPAPI-encrypted (see credentials.py), never in plain text."""

    speech_key: str = ""
    speech_region: str = ""
    translator_key: str = ""
    translator_region: str = ""


@dataclass
class Features:
    """Every optional system can be switched on/off here."""

    ui_language: str = "auto"
    tray_notifications: bool = True
    replay_enabled: bool = True
    replay_hotkey: str = "F10"
    history_enabled: bool = True
    history_size: int = 10
    quick_phrases_enabled: bool = False
    corrections_enabled: bool = True
    pronunciation_enabled: bool = False
    gamepad_enabled: bool = False
    gamepad_button: str = "RB"
    gamepad_replay_button: str = ""
    fullscreen_warning: bool = True
    stuck_key_protection: bool = True
    trim_silence: bool = True
    azure_phrase_list: bool = True
    arabic_corrections_enabled: bool = True
    azure_usage_tracking: bool = True
    sound_cues: bool = False
    sound_volume: int = 40  # 0-100
    copy_to_clipboard: bool = False
    phrase_suggestions: bool = True
    quick_text_enabled: bool = False
    quick_text_hotkey: str = "F8"
    quick_text_translator: str = "auto"
    learning_enabled: bool = False  # saves the sentences you use (opt-in)
    voice_sensitivity: int = 50  # open-mic mode: 0-100


@dataclass
class TeammateSettings:
    """Teammate subtitles: listen to what the PC plays and show it translated."""

    enabled: bool = False
    device: str = ""  # speaker/output to listen to; "" = Windows default output
    recognizer: str = LOCAL
    translator: str = "local"
    target_language: str = "ar"
    show_original: bool = False
    position: str = "bottom-center"
    offset_x: int = 0
    offset_y: int = 140
    font_size: int = 16
    max_width: int = 900
    display_seconds: int = 5
    sensitivity: int = 50  # 0-100: higher picks up quieter voices


@dataclass
class OverlayStyle:
    """Overlay look shared by all profiles (size/opacity are per profile)."""

    font_family: str = "Segoe UI"
    text_color: str = "#f5f7fa"
    background_color: str = "#0c0e14"
    accent_color: str = "#38bdf8"
    text_outline: bool = False
    corner_radius: int = 12
    animation: bool = True
    monitor: str = "game"


@dataclass
class Settings:
    enabled: bool = True
    compute_device: str = "auto"
    show_arabic: bool = False
    auto_switch_profiles: bool = True
    active_profile: str = "Default"
    overlay: OverlayStyle = field(default_factory=OverlayStyle)
    azure: AzureSettings = field(default_factory=AzureSettings)
    features: Features = field(default_factory=Features)
    teammates: TeammateSettings = field(default_factory=TeammateSettings)
    profiles: list[Profile] = field(default_factory=lambda: [Profile()])

    @property
    def profile(self) -> Profile:
        """The active profile (always exists after validate())."""
        for p in self.profiles:
            if p.name == self.active_profile:
                return p
        return self.profiles[0]

    def find_profile(self, name: str) -> Profile | None:
        return next((p for p in self.profiles if p.name == name), None)

    def clone(self) -> Settings:
        return copy.deepcopy(self)


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def validate(settings: Settings) -> Settings:
    """Clamp ranges and repair invalid enum values in place."""
    if settings.compute_device not in COMPUTE_DEVICES:
        settings.compute_device = "auto"
    o = settings.overlay
    o.corner_radius = _clamp(o.corner_radius, 0, 40)
    if o.monitor not in MONITORS:
        o.monitor = "game"
    for attr, default in (
        ("text_color", "#f5f7fa"),
        ("background_color", "#0c0e14"),
        ("accent_color", "#38bdf8"),
    ):
        if not _is_hex_color(getattr(o, attr)):
            setattr(o, attr, default)
    o.font_family = o.font_family.strip()[:64] or "Segoe UI"
    f = settings.features
    if f.ui_language not in UI_LANGUAGES:
        f.ui_language = "auto"
    f.history_size = _clamp(f.history_size, 1, 50)
    f.sound_volume = _clamp(f.sound_volume, 0, 100)
    f.voice_sensitivity = _clamp(f.voice_sensitivity, 0, 100)
    if f.quick_text_translator not in QUICK_TEXT_TRANSLATORS:
        f.quick_text_translator = "auto"
    if f.gamepad_button not in GAMEPAD_BUTTONS or not f.gamepad_button:
        f.gamepad_button = "RB"
    if (
        f.gamepad_replay_button not in GAMEPAD_BUTTONS
        or f.gamepad_replay_button == f.gamepad_button
    ):
        f.gamepad_replay_button = ""
    tm = settings.teammates
    if tm.recognizer not in TEAM_RECOGNIZERS:
        tm.recognizer = LOCAL
    if tm.translator not in TEAM_TRANSLATORS:
        tm.translator = "local"
    if tm.target_language not in TARGET_LANGUAGES:
        tm.target_language = "ar"
    if tm.translator == "local":
        tm.target_language = "ar"  # the offline model is English -> Arabic only
    if tm.position not in POSITIONS:
        tm.position = "bottom-center"
    tm.font_size = _clamp(tm.font_size, 10, 48)
    tm.max_width = _clamp(tm.max_width, 200, 2400)
    tm.display_seconds = _clamp(tm.display_seconds, 1, 15)
    tm.sensitivity = _clamp(tm.sensitivity, 0, 100)
    az = settings.azure
    az.speech_region = "".join(az.speech_region.split()).lower()
    az.translator_region = "".join(az.translator_region.split()).lower()

    seen: set[str] = set()
    profiles = []
    for p in settings.profiles:
        p.name = p.name.strip() or "Profile"
        if p.name in seen:
            continue
        seen.add(p.name)
        if p.hotkey_mode not in HOTKEY_MODES:
            p.hotkey_mode = "push"
        if not p.model:
            p.model = "small"
        if p.speech_provider not in SPEECH_PROVIDERS:
            p.speech_provider = LOCAL
        if p.translation_provider not in TRANSLATION_PROVIDERS:
            p.translation_provider = LOCAL
        if p.speech_provider == AZURE:
            p.translation_provider = AZURE  # Whisper can't translate text
        if p.azure_locale not in AZURE_LOCALES:
            p.azure_locale = "ar-SA"
        if p.target_language not in TARGET_LANGUAGES or p.translation_provider == LOCAL:
            p.target_language = "en"
        if p.overlay_position not in POSITIONS:
            p.overlay_position = "top-center"
        p.font_size = _clamp(p.font_size, 10, 48)
        if p.display_seconds != NEVER_HIDE:
            p.display_seconds = _clamp(p.display_seconds, 1, 15)
        p.max_width = _clamp(p.max_width, 200, 2000)
        p.background_opacity = _clamp(float(p.background_opacity), 0.0, 1.0)
        p.text_opacity = _clamp(float(p.text_opacity), 0.1, 1.0)
        p.exe_names = list(dict.fromkeys(e.strip().lower() for e in p.exe_names if e.strip()))
        p.vocabulary = clean_vocabulary(p.vocabulary)
        p.corrections = clean_corrections(p.corrections)
        p.arabic_corrections = clean_corrections(p.arabic_corrections)
        p.quick_phrases = clean_phrases(
            p.quick_phrases, reserved={p.hotkey, f.replay_hotkey, f.quick_text_hotkey}
        )
        profiles.append(p)
    settings.profiles = profiles or [Profile()]
    if settings.find_profile(settings.active_profile) is None:
        settings.active_profile = settings.profiles[0].name
    return settings


def _is_hex_color(value: str) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 7
        and value[0] == "#"
        and all(c in HEX_COLOR for c in value[1:])
    )


def clean_phrases(items: list[QuickPhrase], reserved: set[str]) -> list[QuickPhrase]:
    """Keep phrases with text; one phrase per key; never steal the talk/replay hotkeys."""
    out: list[QuickPhrase] = []
    used = set(reserved)
    for ph in items[:20]:
        text = " ".join(ph.text.split())[:200]
        key = ph.key.strip()
        if not text:
            continue
        if key and key in used:
            key = ""  # conflicting key: keep the phrase, drop the binding
        if key:
            used.add(key)
        out.append(QuickPhrase(key, text))
    return out


def clean_corrections(items: list[Correction]) -> list[Correction]:
    out: list[Correction] = []
    seen: set[str] = set()
    for c in items[:100]:
        find = " ".join(c.find.split())[:60]
        if not find or find.casefold() in seen:
            continue
        seen.add(find.casefold())
        out.append(Correction(find, " ".join(c.replace.split())[:120]))
    return out


def clean_vocabulary(items: list[str]) -> list[str]:
    """Trim, collapse spaces, drop empties/overlong entries and case-insensitive duplicates."""
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        v = " ".join(str(item).split())
        if not v or len(v) > MAX_VOCABULARY_ITEM or v.casefold() in seen:
            continue
        seen.add(v.casefold())
        out.append(v)
    return out[:MAX_VOCABULARY]


def _migrate_overlay(data: Any) -> Any:
    """Old configs kept max_width/opacities globally; give each profile those values."""
    if not isinstance(data, dict):
        return data
    overlay = data.get("overlay")
    if not isinstance(overlay, dict) or not isinstance(data.get("profiles"), list):
        return data
    legacy = {k: overlay[k] for k in PROFILE_OVERLAY_FIELDS if k in overlay}
    if legacy:
        for prof in data["profiles"]:
            if isinstance(prof, dict):
                for k, v in legacy.items():
                    prof.setdefault(k, v)
    return data


def _from_dict(cls, data: Any):
    """Build a dataclass from JSON, keeping defaults for missing or wrongly typed keys."""
    obj = cls()
    if not isinstance(data, dict):
        return obj
    for f in fields(cls):
        if f.name not in data:
            continue
        current = getattr(obj, f.name)
        value = data[f.name]
        if is_dataclass(current):
            setattr(obj, f.name, _from_dict(type(current), value))
        elif f.name in _LIST_OF_DATACLASS:
            if isinstance(value, list):
                item_cls = _LIST_OF_DATACLASS[f.name]
                setattr(
                    obj, f.name, [_from_dict(item_cls, v) for v in value if isinstance(v, dict)]
                )
        elif isinstance(current, list):
            if isinstance(value, list) and all(isinstance(v, str) for v in value):
                setattr(obj, f.name, list(value))
        elif isinstance(current, bool):
            if isinstance(value, bool):
                setattr(obj, f.name, value)
        elif isinstance(current, float):
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                setattr(obj, f.name, float(value))
        elif isinstance(current, int):
            if isinstance(value, int) and not isinstance(value, bool):
                setattr(obj, f.name, value)
        elif isinstance(value, type(current)):
            setattr(obj, f.name, value)
    return obj


_LIST_OF_DATACLASS = {
    "profiles": Profile,
    "quick_phrases": QuickPhrase,
    "corrections": Correction,
    "arabic_corrections": Correction,
}


def settings_from_dict(data: Any) -> Settings:
    return validate(_from_dict(Settings, _migrate_overlay(data)))


def default_config_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / "GameTalk"


class ConfigStore:
    """Loads and atomically saves Settings. Only touches disk on load/save."""

    def __init__(self, path: Path | None = None):
        self.path = path or default_config_dir() / "config.json"

    def load(self) -> Settings:
        if not self.path.exists():
            return validate(Settings())
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            log.warning("Config unreadable (%s); backing it up and using defaults", e)
            try:
                os.replace(self.path, self.path.with_suffix(".json.bak"))
            except OSError:
                pass
            return validate(Settings())
        return settings_from_dict(data)

    def save(self, settings: Settings) -> bool:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(asdict(settings), indent=2, ensure_ascii=False), "utf-8")
            os.replace(tmp, self.path)
            return True
        except OSError as e:
            log.error("Could not save settings: %s", e)
            return False
