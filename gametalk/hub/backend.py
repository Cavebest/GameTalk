# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""The main window's Python side: settings, live numbers and actions for the QML interface.

It lives inside the GameTalk app (the tray process) and talks to the Controller directly.
Every change is applied and saved immediately. API keys never reach QML: the interface only
learns whether one is saved.
"""

from __future__ import annotations

import copy
import json
import logging
import pathlib
import subprocess
import threading
from dataclasses import asdict, fields, is_dataclass
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from .. import AUTHOR_URL, COPYRIGHT, __version__
from ..config import (
    AZURE_LOCALES,
    GAMEPAD_BUTTONS,
    MODELS,
    QUICK_TEXT_TRANSLATORS,
    SOURCE_LANGUAGES,
    SPEECH_PROVIDERS,
    TARGET_LANGUAGES,
    TEAM_RECOGNIZERS,
    TEAM_TRANSLATORS,
    TRANSLATION_PROVIDERS,
    UI_LANGUAGES,
    Correction,
    QuickPhrase,
    Settings,
    default_config_dir,
    validate,
)
from ..credentials import protect
from ..i18n import is_rtl, language, set_language, tr
from ..options import DEVICE_LABELS, FEATURE_SWITCHES, MONITOR_LABELS, POSITION_LABELS
from ..runtime import autostart_enabled, set_autostart

log = logging.getLogger(__name__)

SECRETS = {
    "azure.speech_key",
    "azure.translator_key",
    "google.api_key",
    "google.service_account",
}
SECTIONS = ("profile", "overlay", "features", "teammates", "azure", "google")
MODEL_NOTES = {
    "tiny": "75 MB · fastest",
    "base": "145 MB · very fast",
    "small": "480 MB · balanced",
    "medium": "1.5 GB · natural dialect",
    "large-v3": "3 GB · most accurate",
}
HOTKEY_MODE_LABELS = {
    "push": "Hold to talk",
    "toggle": "Press to start / stop",
    "voice": "Open mic (no key)",
}
QML_DIR = Path(__file__).resolve().parent / "qml"


def _plain(obj):
    return asdict(obj) if is_dataclass(obj) else obj


def config_view(s: Settings) -> dict:
    """Everything the interface shows. Secrets become booleans ("is a key saved?")."""
    view = {
        "enabled": s.enabled,
        "compute_device": s.compute_device,
        "show_arabic": s.show_arabic,
        "auto_switch_profiles": s.auto_switch_profiles,
        "active_profile": s.profile.name,
        "profiles": [p.name for p in s.profiles],
    }
    for name in SECTIONS:
        view[name] = _plain(s.profile if name == "profile" else getattr(s, name))
    for path in SECRETS:
        section, key = path.split(".")
        view[section][key] = bool(view[section][key])
    return view


def _coerce(current, value):
    if isinstance(current, bool):
        return bool(value)
    if isinstance(current, int):
        return int(round(float(value)))
    if isinstance(current, float):
        return float(value)
    if isinstance(current, str):
        return str(value)
    return value


def apply_value(s: Settings, path: str, value) -> None:
    """'features.replay_enabled' / 'profile.model' / 'enabled' -> set on the settings."""
    head, _, tail = path.partition(".")
    if not tail:
        obj, field = s, head
    elif head == "profile":
        obj, field = s.profile, tail
    elif head in SECTIONS:
        obj, field = getattr(s, head), tail
    else:
        raise KeyError(path)
    if field not in {f.name for f in fields(obj)}:
        raise KeyError(path)
    current = getattr(obj, field)
    if isinstance(current, list):
        raise KeyError(path)  # lists have their own setters
    setattr(obj, field, _coerce(current, value))


def unique_name(s: Settings, wanted: str) -> str:
    base = " ".join(wanted.split())[:40] or "Profile"
    name, n = base, 2
    while s.find_profile(name) is not None:
        name, n = f"{base} ({n})", n + 1
    return name


class Hub(QObject):
    configChanged = Signal()
    statsChanged = Signal()
    languageChanged = Signal()
    toast = Signal(str, str)  # message, kind: ok | warn | error
    testDone = Signal(str, "QVariantList")  # which ("azure" | "google"), [{ok, text}]
    micTested = Signal(str)  # mic test outcome (the translation, or what went wrong)
    keyCaptured = Signal(str, str)  # target, key name ("" = cancelled)
    overlayMoved = Signal()
    _tested = Signal(str, list)  # from worker threads

    def __init__(self, controller, poll: bool = True):
        super().__init__()
        self.c = controller
        self._config = config_view(controller.settings)
        self._stats: dict = {}
        self._capture_target = ""
        self._moving = False
        self._tested.connect(self._emit_tested)
        controller.test_result.connect(self.micTested)
        controller.hotkey.captured.connect(self._on_captured)
        self._moved_signal = getattr(controller.overlay, "moved", None)
        if not hasattr(self._moved_signal, "connect"):  # e.g. the tray fallback overlay
            self._moved_signal = None
        if self._moved_signal is not None:
            self._moved_signal.connect(self._on_overlay_moved)
        self._timer = QTimer(self, interval=500, timeout=self.poll)
        if poll:
            self._timer.start()
        self.poll()

    def close(self) -> None:
        """The window is closing: stop polling, end any capture/move, detach from the app."""
        self._timer.stop()
        if self._capture_target:
            self.c.hotkey.cancel_capture()
            self._capture_target = ""
        if self._moving:
            self.moveOverlay(False)
        for signal, slot in (
            (self.c.test_result, self.micTested),
            (self.c.hotkey.captured, self._on_captured),
            (self._moved_signal, self._on_overlay_moved),
        ):
            if signal is None:
                continue
            try:
                signal.disconnect(slot)
            except (RuntimeError, TypeError):
                pass

    # ---- properties --------------------------------------------------------------------

    @Property("QVariantMap", notify=configChanged)
    def config(self) -> dict:
        return self._config

    @Property("QVariantMap", notify=statsChanged)
    def stats(self) -> dict:
        return self._stats

    @Property(bool, notify=languageChanged)
    def rtl(self) -> bool:
        return is_rtl()

    @Property(str, notify=languageChanged)
    def lang(self) -> str:
        return language()

    @Property(str, constant=True)
    def version(self) -> str:
        return __version__

    @Property(str, constant=True)
    def copyright(self) -> str:
        return COPYRIGHT

    @Property(str, constant=True)
    def authorUrl(self) -> str:
        return AUTHOR_URL

    @Property(bool, notify=configChanged)
    def autostart(self) -> bool:
        try:
            return autostart_enabled()
        except OSError:
            return False

    @Property(bool, notify=statsChanged)
    def micLevelActive(self) -> bool:
        return bool(self.c.recording)

    @Property(float, notify=statsChanged)
    def micLevel(self) -> float:
        return float(min(1.0, getattr(self.c.recorder, "level", 0.0) * 1.4))

    # ---- text --------------------------------------------------------------------------

    @Slot(str, result=str)
    def t(self, text: str) -> str:
        return tr(text)

    @Slot(str, "QVariantMap", result=str)
    def tf(self, text: str, values: dict) -> str:
        return tr(text, **values)

    @Slot(str, result=str)
    def helpTitle(self, topic: str) -> str:
        from .. import help

        return help.title(topic)

    @Slot(str, result=str)
    def helpSummary(self, topic: str) -> str:
        from .. import help

        return help.summary(topic)

    @Slot(str, result="QVariantList")
    def options(self, name: str) -> list:
        """[{value, label, note}] for the interface's pickers (labels already translated)."""
        from ..google import MODELS as GOOGLE_MODELS
        from ..hotkey import SUPPORTED_HOTKEYS

        tables = {
            "speech": SPEECH_PROVIDERS,
            "translation": TRANSLATION_PROVIDERS,
            "targets": TARGET_LANGUAGES,
            "sources": SOURCE_LANGUAGES,
            "locales": AZURE_LOCALES,
            "devices": DEVICE_LABELS,
            "positions": POSITION_LABELS,
            "monitors": MONITOR_LABELS,
            "teamRecognizers": TEAM_RECOGNIZERS,
            "teamTranslators": TEAM_TRANSLATORS,
            "quickText": QUICK_TEXT_TRANSLATORS,
            "googleModels": GOOGLE_MODELS,
            "hotkeyModes": HOTKEY_MODE_LABELS,
            "uiLanguages": UI_LANGUAGES,
        }
        if name == "models":
            return [{"value": m, "label": m, "note": tr(MODEL_NOTES[m])} for m in MODELS]
        if name == "hotkeys":
            return [{"value": k, "label": k, "note": ""} for k in SUPPORTED_HOTKEYS]
        if name == "gamepad":
            return [{"value": b, "label": b, "note": ""} for b in GAMEPAD_BUTTONS if b]
        if name == "gamepadReplay":
            return [{"value": "", "label": tr("None"), "note": ""}] + [
                {"value": b, "label": b, "note": ""} for b in GAMEPAD_BUTTONS if b
            ]
        if name == "microphones":
            from ..audio import list_input_devices

            return [{"value": "", "label": tr("Windows default"), "note": ""}] + [
                {"value": n, "label": n, "note": ""} for n in list_input_devices()
            ]
        if name == "speakers":
            from ..teammates import output_devices

            return [{"value": "", "label": tr("Windows default output"), "note": ""}] + [
                {"value": n, "label": n, "note": ""} for n in output_devices()
            ]
        if name == "fonts":
            from PySide6.QtGui import QFontDatabase

            fams = [f for f in QFontDatabase.families() if not f.startswith("@")]
            return [{"value": f, "label": f, "note": ""} for f in fams]
        table = tables[name]
        return [{"value": k, "label": tr(v), "note": ""} for k, v in table.items()]

    @Slot(result="QVariantList")
    def featureList(self) -> list:
        return [
            {"key": key, "label": tr(label), "topic": topic, "desc": tr(desc)}
            for key, label, topic, desc in FEATURE_SWITCHES
        ]

    @Slot(result="QVariantList")
    def suggestions(self) -> list:
        return list(self.c.phrase_suggestions()[:6])

    # ---- settings ----------------------------------------------------------------------

    def _edit(self, change, message: str = "") -> bool:
        """Change a copy of the live settings, validate, then apply + save in one go."""
        s = self.c.settings.clone()
        try:
            change(s)
        except (KeyError, ValueError, TypeError) as e:
            log.warning("Hub: bad setting change (%s)", type(e).__name__)
            return False
        validate(s)
        self.c.apply_settings(s)
        self._refresh_config()
        if message:
            self.toast.emit(message, "ok")
        return True

    def _refresh_config(self) -> None:
        self._config = config_view(self.c.settings)
        self.configChanged.emit()

    @Slot(str, "QVariant")
    def set(self, path: str, value) -> None:
        if path in SECRETS:
            return
        self._edit(lambda s: apply_value(s, path, value))

    @Slot(str, str)
    def setSecret(self, path: str, value: str) -> None:
        value = value.strip()
        if path not in SECRETS or not value:
            return
        section, key = path.split(".")
        self._edit(lambda s: setattr(getattr(s, section), key, protect(value)), tr("Key saved"))

    @Slot(str)
    def clearSecret(self, path: str) -> None:
        if path in SECRETS:
            section, key = path.split(".")
            self._edit(lambda s: setattr(getattr(s, section), key, ""), tr("Key removed"))

    @Slot(str)
    def setLanguage(self, code: str) -> None:
        self._edit(lambda s: setattr(s.features, "ui_language", code))
        set_language(code)
        self.languageChanged.emit()

    @Slot(bool)
    def setAutostart(self, on: bool) -> None:
        try:
            set_autostart(on)
        except OSError:
            self.toast.emit(tr("Couldn't change Windows startup."), "error")
        self.configChanged.emit()

    # ---- lists (phrases, corrections, vocabulary, games) --------------------------------

    @Slot("QVariantList")
    def setPhrases(self, rows: list) -> None:
        items = [QuickPhrase(str(r.get("key", "")), str(r.get("text", ""))) for r in rows]
        self._edit(lambda s: setattr(s.profile, "quick_phrases", items))

    @Slot(str, "QVariantList")
    def setCorrections(self, which: str, rows: list) -> None:
        field = "arabic_corrections" if which == "arabic" else "corrections"
        items = [Correction(str(r.get("find", "")), str(r.get("replace", ""))) for r in rows]
        self._edit(lambda s: setattr(s.profile, field, items))

    @Slot(str, str)
    def setLines(self, which: str, text: str) -> None:
        """Vocabulary or game .exe names, one per line."""
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        field = {"vocabulary": "vocabulary", "games": "exe_names"}[which]
        self._edit(lambda s: setattr(s.profile, field, lines))

    # ---- profiles ----------------------------------------------------------------------

    @Slot(str)
    def setProfile(self, name: str) -> None:
        self._edit(lambda s: setattr(s, "active_profile", name))

    @Slot(str)
    def newProfile(self, name: str) -> None:
        def change(s):
            p = copy.deepcopy(s.profile)
            p.name, p.exe_names = unique_name(s, name or tr("New profile")), []
            s.profiles.append(p)
            s.active_profile = p.name

        self._edit(change, tr("Profile created"))

    @Slot(str)
    def renameProfile(self, name: str) -> None:
        def change(s):
            new = " ".join(name.split())[:40]
            if not new or new == s.profile.name:
                raise ValueError("same name")
            new = unique_name(s, new)
            s.profile.name = new
            s.active_profile = new

        self._edit(change)

    @Slot()
    def deleteProfile(self) -> None:
        if len(self.c.settings.profiles) <= 1:
            self.toast.emit(tr("At least one profile is required."), "warn")
            return

        def change(s):
            s.profiles.remove(s.profile)
            s.active_profile = s.profiles[0].name

        self._edit(change, tr("Profile deleted"))

    @Slot()
    def loadServiceAccount(self) -> None:
        """Pick the service-account .json from Google Cloud; it's stored encrypted (DPAPI)."""
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(
            None, tr("Google service account file"), "", "JSON (*.json)"
        )
        if path:
            self.loadServiceAccountFrom(path)

    def loadServiceAccountFrom(self, path: str) -> bool:
        from ..google import parse_service_account

        try:
            text = pathlib.Path(path).read_text(encoding="utf-8")
            account = parse_service_account(text)
        except (OSError, ValueError):
            self.toast.emit(tr("That isn't a Google service account key file."), "error")
            return False

        def change(s):
            s.google.service_account = protect(text)
            if not s.google.project_id:
                s.google.project_id = account["project_id"]

        return self._edit(change, tr("Service account saved (encrypted)"))

    @Slot()
    def exportProfile(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        p = self.c.settings.profile
        path, _ = QFileDialog.getSaveFileName(
            None, tr("Export profile"), f"{p.name}.gametalk.json", "GameTalk (*.json)"
        )
        if not path:
            return
        data = {"gametalk_profile": 1, "profile": asdict(p)}
        try:
            pathlib.Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
            self.toast.emit(tr("Saved. Share this file with friends."), "ok")
        except OSError:
            self.toast.emit(tr("Couldn't save the file."), "error")

    @Slot()
    def importProfile(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(None, tr("Import profile"), "", "GameTalk (*.json)")
        if path:
            self.importProfileFrom(path)

    def importProfileFrom(self, path: str) -> bool:
        from ..config import Profile, _from_dict

        try:
            data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("profile"), dict):
                raise ValueError("not a GameTalk profile")
            prof = _from_dict(Profile, data["profile"])
        except (OSError, ValueError):
            self.toast.emit(tr("This isn't a GameTalk profile file."), "error")
            return False

        def change(s):
            prof.name = unique_name(s, prof.name or "Imported")  # never overwrite one
            s.profiles.append(prof)
            s.active_profile = prof.name

        ok = self._edit(change)
        if ok:
            self.toast.emit(tr("Imported as “{name}”.", name=prof.name), "ok")
        return ok

    # ---- live state --------------------------------------------------------------------

    @Slot()
    def poll(self) -> None:
        stats = self.c.stats()
        if stats != self._stats or self.c.recording:
            self._stats = stats
            self.statsChanged.emit()

    @Slot()
    def resetUsage(self) -> None:
        self.c.usage.reset()
        self.poll()
        self.toast.emit(tr("Counter reset"), "ok")

    # ---- actions -----------------------------------------------------------------------

    @Slot()
    def toggleEnabled(self) -> None:
        on = not self.c.settings.enabled
        self.c.set_enabled(on)
        self._refresh_config()
        self.poll()
        if on:
            self.toast.emit(tr("GameTalk is on"), "ok")
        else:
            self.toast.emit(tr("GameTalk is paused"), "warn")

    @Slot()
    def quitApp(self) -> None:
        self.c.quit()

    @Slot(str)
    def testMic(self, device: str) -> None:
        self.c.test_microphone(device or None)

    @Slot()
    def refreshMics(self) -> None:
        from ..audio import refresh_devices

        refresh_devices()
        self.configChanged.emit()  # pickers re-read their options

    @Slot()
    def selfTest(self) -> None:
        self.c.open_diagnostics()

    @Slot()
    def phrasebook(self) -> None:
        self.c.open_phrasebook()

    @Slot()
    def previewOverlay(self) -> None:
        self.c.preview_overlay()

    @Slot(bool)
    def moveOverlay(self, on: bool) -> None:
        """Let the user drag the real overlay; its new offsets are saved when they're done."""
        if on == self._moving or not hasattr(self.c.overlay, "set_move_mode"):
            return
        self._moving = on
        self.c.overlay.apply(self.c.settings.overlay, self.c.profile)
        self.c.overlay.set_move_mode(on)

    def _on_overlay_moved(self, x: int, y: int) -> None:
        def change(s):
            s.profile.overlay_offset_x, s.profile.overlay_offset_y = x, y

        self._edit(change)
        self.overlayMoved.emit()

    @Slot(str)
    def beginCapture(self, target: str) -> None:
        """Next key/mouse button the user presses (seen by GameTalk's own hotkey system)."""
        self._capture_target = target
        self.c.hotkey.begin_capture()

    @Slot()
    def cancelCapture(self) -> None:
        if self._capture_target:
            self._capture_target = ""
            self.c.hotkey.cancel_capture()

    def _on_captured(self, name: str) -> None:
        target, self._capture_target = self._capture_target, ""
        if not target:
            return
        self.c.hotkey.cancel_capture()
        self.keyCaptured.emit(target, name)

    @Slot(str)
    def openHelp(self, topic: str) -> None:
        self.c.open_help(topic or "start")

    @Slot()
    def openLogs(self) -> None:
        path = default_config_dir() / "logs"
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    @Slot(str)
    def openUrl(self, url: str) -> None:
        if url.startswith("https://"):
            QDesktopServices.openUrl(QUrl(url))

    @Slot()
    def createShortcut(self) -> None:
        from ..launcher import create_desktop_shortcut

        try:
            create_desktop_shortcut()
            self.toast.emit(tr("Desktop shortcut created"), "ok")
        except (OSError, subprocess.SubprocessError):
            self.toast.emit(tr("Couldn't create the shortcut."), "error")

    # ---- connection tests (background threads) -----------------------------------------

    def _run_test(self, which: str, work) -> None:
        def run():
            try:
                results = work()
            except Exception as e:  # never let a worker thread die silently
                results = [(False, f"Test failed: {type(e).__name__}")]
            self._tested.emit(which, results)

        threading.Thread(target=run, name=f"gametalk-hub-{which}", daemon=True).start()

    def _emit_tested(self, which: str, results: list) -> None:
        lines = []
        for ok, msg in results:
            head, sep, rest = msg.partition(" (")
            lines.append({"ok": ok, "text": tr(head) + sep + rest})
        self.testDone.emit(which, lines)

    @Slot()
    def testAzure(self) -> None:
        from ..azure import check_connection

        creds = self.c.azure_credentials()
        self._run_test("azure", lambda: check_connection(creds))

    @Slot()
    def testGoogle(self) -> None:
        from ..google import check_connection

        creds = self.c.google_credentials()
        speech = self.c.profile.speech_provider == "google"
        self._run_test("google", lambda: check_connection(creds, speech=speech))
