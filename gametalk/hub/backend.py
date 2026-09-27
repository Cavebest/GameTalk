# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""The hub window's Python side: settings, live numbers and actions for the QML interface.

The hub is a separate, short-lived process (like the old launcher). It edits config.json and
asks the running app to reload; live numbers come from the app over the local command channel
(ipc.py, "stats"). API keys never reach QML: the interface only learns whether one is saved.
"""

from __future__ import annotations

import json
import logging
import subprocess
import threading
from dataclasses import asdict, fields, is_dataclass
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from .. import AUTHOR_URL, COPYRIGHT, __version__, ipc
from ..config import (
    AZURE_LOCALES,
    GAMEPAD_BUTTONS,
    MODELS,
    QUICK_TEXT_TRANSLATORS,
    SPEECH_PROVIDERS,
    TARGET_LANGUAGES,
    TEAM_RECOGNIZERS,
    TEAM_TRANSLATORS,
    TRANSLATION_PROVIDERS,
    UI_LANGUAGES,
    ConfigStore,
    Settings,
    default_config_dir,
    validate,
)
from ..credentials import protect, unprotect
from ..i18n import is_rtl, language, set_language, tr
from ..runtime import app_command, autostart_enabled, set_autostart, spawn

log = logging.getLogger(__name__)

SECRETS = {
    "azure.speech_key",
    "azure.translator_key",
    "google.api_key",
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
    setattr(obj, field, _coerce(getattr(obj, field), value))


class Hub(QObject):
    configChanged = Signal()
    statsChanged = Signal()
    runningChanged = Signal()
    languageChanged = Signal()
    toast = Signal(str, str)  # message, kind: ok | warn | error
    testDone = Signal(str, "QVariantList")  # which ("azure" | "google"), [{ok, text}]
    _tested = Signal(str, list)  # from worker threads

    def __init__(self, store: ConfigStore | None = None, poll: bool = True):
        super().__init__()
        self.store = store or ConfigStore()
        self._settings = self.store.load()
        self._config = config_view(self._settings)
        self._stats: dict = {}
        self._running = False
        self._starting = 0  # polls left to wait for a freshly started app
        self._mtime = self._config_mtime()
        self._tested.connect(self._emit_tested)
        self._help = None
        self._timer = QTimer(self, interval=1000, timeout=self.poll)
        if poll:
            self._timer.start()
            QTimer.singleShot(0, self.poll)

    # ---- properties --------------------------------------------------------------------

    @Property("QVariantMap", notify=configChanged)
    def config(self) -> dict:
        return self._config

    @Property("QVariantMap", notify=statsChanged)
    def stats(self) -> dict:
        return self._stats

    @Property(bool, notify=runningChanged)
    def running(self) -> bool:
        return self._running

    @Property(bool, notify=runningChanged)
    def starting(self) -> bool:
        return self._starting > 0

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
        from ..settings_dialog import DEVICE_LABELS, POSITION_LABELS

        tables = {
            "speech": SPEECH_PROVIDERS,
            "translation": TRANSLATION_PROVIDERS,
            "targets": TARGET_LANGUAGES,
            "locales": AZURE_LOCALES,
            "devices": DEVICE_LABELS,
            "positions": POSITION_LABELS,
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
            return [
                {"value": b, "label": b or tr("None"), "note": ""} for b in GAMEPAD_BUTTONS if b
            ]
        table = tables[name]
        return [{"value": k, "label": tr(v), "note": ""} for k, v in table.items()]

    @Slot(result="QVariantList")
    def featureList(self) -> list:
        from ..settings_dialog import FEATURE_SWITCHES

        return [
            {"key": key, "label": tr(label), "topic": topic, "desc": tr(desc)}
            for key, label, topic, desc in FEATURE_SWITCHES
        ]

    # ---- settings ----------------------------------------------------------------------

    def _config_mtime(self) -> float:
        try:
            return self.store.path.stat().st_mtime
        except OSError:
            return 0.0

    def _edit(self, change, message: str = "") -> bool:
        """Load the newest config, change it, save, tell the running app. Never loses edits
        made meanwhile by the app's own Settings window."""
        s = self.store.load()
        try:
            change(s)
        except (KeyError, ValueError, TypeError) as e:
            log.warning("Hub: bad setting change (%s)", type(e).__name__)
            return False
        validate(s)
        self.store.save(s)
        self._mtime = self._config_mtime()
        self._settings = s
        self._config = config_view(s)
        self.configChanged.emit()
        if self._running:
            ipc.send_command("reload", 800)
        if message:
            self.toast.emit(message, "ok")
        return True

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
    def setProfile(self, name: str) -> None:
        self._edit(lambda s: setattr(s, "active_profile", name))

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

    # ---- live state --------------------------------------------------------------------

    @Slot()
    def poll(self) -> None:
        if self._config_mtime() != self._mtime:  # e.g. saved from the app's Settings window
            self._mtime = self._config_mtime()
            self._settings = self.store.load()
            self._config = config_view(self._settings)
            self.configChanged.emit()
        reply = ipc.send_command("stats", 400)
        running = reply is not None
        stats = {}
        if reply and reply.startswith("{"):
            try:
                stats = json.loads(reply)
            except ValueError:
                stats = {}
        if not running:
            stats = {"usage": self._disk_usage()}  # quota gauges still work while it's off
        was_starting = self._starting > 0
        if running:
            self._starting = 0
        elif self._starting:
            self._starting -= 1
        if running != self._running or was_starting != (self._starting > 0):
            self._running = running
            self.runningChanged.emit()
        if stats != self._stats:
            self._stats = stats
            self.statsChanged.emit()

    def _disk_usage(self) -> dict:
        from ..usage import UsageTracker

        u = UsageTracker(self.store.path.parent / "usage.json").current
        return {
            "speech": round(u.speech_fraction, 4),
            "translator": round(u.translator_fraction, 4),
            "google": round(u.google_fraction, 4),
        }

    # ---- actions -----------------------------------------------------------------------

    @Slot()
    def toggleRunning(self) -> None:
        if self._running:
            ipc.send_command("quit")
            self.toast.emit(tr("GameTalk stopped"), "warn")
        else:
            self.start()
        QTimer.singleShot(700, self.poll)

    @Slot()
    def start(self) -> None:
        if self._running or self._starting:
            return
        try:
            spawn(app_command())
        except OSError:
            self.toast.emit(tr("Couldn't start GameTalk."), "error")
            return
        self._starting = 25
        self.runningChanged.emit()

    def _command(self, command: str, flag: str) -> None:
        if not self._running or ipc.send_command(command) is None:
            try:
                spawn(app_command(flag))
            except OSError:
                self.toast.emit(tr("Couldn't start GameTalk."), "error")

    @Slot(str)
    def openSettings(self, tab: str) -> None:
        self._command(f"settings:{tab}" if tab else "settings", "--settings")

    @Slot()
    def testMic(self) -> None:
        self._command("test", "--test-mic")

    @Slot()
    def selfTest(self) -> None:
        self._command("selftest", "--selftest")

    @Slot()
    def phrasebook(self) -> None:
        self._command("phrasebook", "--phrasebook")

    @Slot()
    def previewOverlay(self) -> None:
        if not self._running:
            self.toast.emit(tr("Start GameTalk to see the overlay on screen."), "warn")
            return
        ipc.send_command("preview")

    @Slot(str)
    def openHelp(self, topic: str) -> None:
        from ..help import HelpDialog

        if self._help is None:
            self._help = HelpDialog(topic or "start")
        else:
            self._help.show_topic(topic or "start")
        self._help.show()
        self._help.raise_()
        self._help.activateWindow()

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
        from ..azure import AzureCredentials, check_connection

        a = self.store.load().azure
        creds = AzureCredentials(
            unprotect(a.speech_key),
            a.speech_region,
            unprotect(a.translator_key),
            a.translator_region,
        )
        self._run_test("azure", lambda: check_connection(creds))

    @Slot()
    def testGoogle(self) -> None:
        from ..google import GoogleCredentials, check_connection

        g = self.store.load().google
        creds = GoogleCredentials(unprotect(g.api_key), g.project_id, g.model, g.location)
        self._run_test("google", lambda: check_connection(creds))

    def close(self) -> None:
        self._timer.stop()


QML_DIR = Path(__file__).resolve().parent / "qml"
