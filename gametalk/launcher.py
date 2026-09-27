# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""GameTalk Launcher: one window to start/stop the app and choose what to do.

Run with `pythonw -m gametalk.launcher` (GameTalk.bat does this). It talks to the running app
over the local command channel (ipc.py) and edits config.json for the mode picker.
"""

from __future__ import annotations

import ctypes
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gametalk import APP_NAME, AUTHOR_URL, COPYRIGHT, __version__, ipc, theme
from gametalk.config import (
    AZURE,
    AZURE_LOCALES,
    LOCAL,
    MODELS,
    TARGET_LANGUAGES,
    ConfigStore,
    Profile,
    default_config_dir,
    validate,
)
from gametalk.credentials import unprotect
from gametalk.i18n import apply_layout_direction, is_rtl, set_language, tr
from gametalk.runtime import (
    FROZEN,
    app_command,
    autostart_command,
    autostart_enabled,
    launcher_command,
    set_autostart,
    spawn,
)

__all__ = ["app_command", "autostart_command"]

NO_LOCAL_TRANSLATION = (
    "Whisper can only translate straight from your voice, not from text. "
    "With Azure Speech, translation is done by Azure Translator."
)
FEATURE_NAMES = [
    ("replay_enabled", "Replay"),
    ("history_enabled", "History"),
    ("quick_phrases_enabled", "Quick phrases"),
    ("corrections_enabled", "Corrections"),
    ("pronunciation_enabled", "Pronunciation"),
    ("gamepad_enabled", "Controller"),
]
LAUNCHER_STYLE = """
QPushButton { padding: 9px 12px; }
QLabel#step { font-weight: 600; }
QLabel#stepnum { background: #d9480f; color: white; border-radius: 9px; font-weight: 700;
                 min-width: 18px; max-width: 18px; min-height: 18px; max-height: 18px; }
QLabel#flow { background: #111114; border: 1px solid #222227; border-radius: 8px; padding: 8px; }
QLabel#private { color: #3ddc84; }
QLabel#cloud { color: #ffb020; }
QPushButton#seg { padding: 8px 10px; text-align: left; }
QPushButton#seg:checked { background: #3a1a0e; border: 1px solid #ff5a1f; font-weight: 600; }
"""


# ---- helpers (pure where possible, so they're testable) ------------------------------------


def launch_app(*args: str) -> None:
    spawn(app_command(*args))


def parse_status(reply: str | None) -> dict | None:
    """'ready|Default|F9|local|small on CUDA' -> dict (None when the app isn't running)."""
    if reply is None:
        return None
    parts = (reply.split("|") + [""] * 5)[:5]
    return dict(zip(("state", "profile", "hotkey", "mode", "engine"), parts, strict=True))


def key_status(settings) -> tuple[bool, bool]:
    """(Azure Speech key+region saved, Azure Translator key saved)."""
    a = settings.azure
    return bool(unprotect(a.speech_key) and a.speech_region), bool(unprotect(a.translator_key))


def missing_keys(profile: Profile, settings) -> list[str]:
    speech_ok, translator_ok = key_status(settings)
    missing = []
    if profile.speech_provider == AZURE and not speech_ok:
        missing.append(tr("Azure Speech key + region"))
    if profile.translation_provider == AZURE and not translator_ok:
        missing.append(tr("Azure Translator key"))
    return missing


def dialect_name(locale: str) -> str:
    """'ar-JO' -> 'Jordan'."""
    return tr(AZURE_LOCALES.get(locale, locale)).split("— ")[-1]


def pipeline_summary(p: Profile) -> tuple[str, str, bool]:
    """(flow text, what is sent where, uses the cloud) for the active profile."""
    target = tr(TARGET_LANGUAGES.get(p.target_language, p.target_language))
    arrow = " ← " if is_rtl() else " → "
    voice = tr("🎤 Your voice")
    whisper = tr("Whisper {model} (this PC)", model=p.model)
    if p.speech_provider == LOCAL and p.translation_provider == LOCAL:
        return (
            arrow.join([voice, whisper, tr("English")]),
            tr("🔒 Nothing leaves this PC."),
            False,
        )
    if p.speech_provider == AZURE:
        listen = f"Azure Speech ({dialect_name(p.azure_locale)})"
        sent = tr("☁ Sent to Azure: your push-to-talk audio + the recognised text.")
    else:
        listen = whisper
        sent = tr("☁ Sent to Azure: only the recognised Arabic text — never your audio.")
    return arrow.join([voice, listen, "Azure Translator", target]), sent, True


def ps_quote(value: str) -> str:
    """PowerShell single-quoted literal (an apostrophe in a path, e.g. O'Brien, can't break out)."""
    return "'" + value.replace("'", "''") + "'"


def make_ico() -> str:
    """Write the runtime-drawn icon to %APPDATA%\\GameTalk\\gametalk.ico for shortcuts."""
    from gametalk.tray import make_icon

    path = default_config_dir() / "gametalk.ico"
    path.parent.mkdir(parents=True, exist_ok=True)
    make_icon(True).pixmap(256, 256).save(str(path), "ICO")
    return str(path) if path.exists() else ""


def create_desktop_shortcut() -> Path:
    """Desktop .lnk that opens this launcher (uses the WScript.Shell COM object)."""
    icon = make_ico()
    target, *args = launcher_command()
    script = (
        "$d=[Environment]::GetFolderPath('Desktop');"
        f'$s=(New-Object -ComObject WScript.Shell).CreateShortcut("$d\\{APP_NAME}.lnk");'
        f"$s.TargetPath={ps_quote(target)};"
        f"$s.Arguments={ps_quote(' '.join(args))};"
        f"$s.WorkingDirectory={ps_quote(str(Path.home()))};"
        f"$s.Description={ps_quote(APP_NAME)};"
        + (f"$s.IconLocation={ps_quote(icon + ',0')};" if icon and not FROZEN else "")
        + "$s.Save();Write-Output $d"
    )
    out = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        timeout=20,
    )
    if out.returncode != 0:
        raise OSError(out.stderr.strip() or "PowerShell failed")
    return Path(out.stdout.strip()) / f"{APP_NAME}.lnk"


# ---- window --------------------------------------------------------------------------------


def credit_label() -> QLabel:
    """'© 2026 Shkour Bashtawi · github.com/ShkourBashtawi' with a clickable link."""
    link = AUTHOR_URL.removeprefix("https://")
    label = QLabel(
        f'{COPYRIGHT} · <a href="{AUTHOR_URL}" style="color:#ff5a1f; text-decoration:none">'
        f"{link}</a>"
    )
    label.setObjectName("muted")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setOpenExternalLinks(True)
    return label


def _step_header(num: str, title: str, hint: str) -> QHBoxLayout:
    row = QHBoxLayout()
    badge = QLabel(num)
    badge.setObjectName("stepnum")
    badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
    name = QLabel(tr(title))
    name.setObjectName("step")
    sub = QLabel(f"— {tr(hint)}")
    sub.setObjectName("muted")
    row.addWidget(badge)
    row.addWidget(name)
    row.addWidget(sub)
    row.addStretch(1)
    return row


def _key_badge(label: QLabel, used: bool, saved: bool) -> None:
    label.setVisible(used)
    label.setText(tr("✅ key saved") if saved else tr("⚠ no key"))
    label.setObjectName("ok" if saved else "warn")
    label.style().unpolish(label)
    label.style().polish(label)


def _card() -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(14, 12, 14, 12)
    return frame, layout


class Launcher(QWidget):
    language_changed = Signal()

    def __init__(self):
        super().__init__()
        from gametalk.tray import make_icon

        self.store = ConfigStore()
        self.running = False
        self._help = None
        self.setWindowTitle(tr("{app} — Launcher", app=tr(APP_NAME)))
        self.setWindowIcon(make_icon(True))
        theme.apply(self, LAUNCHER_STYLE)
        self.setMinimumWidth(500)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(12)

        head = QHBoxLayout()
        title = QLabel(tr(APP_NAME))
        title.setObjectName("title")
        head.addWidget(title, 1)
        self.lang_btn = QPushButton("English" if is_rtl() else "العربية")
        self.lang_btn.setToolTip(tr("Switch the interface language"))
        self.lang_btn.clicked.connect(self._toggle_language)
        help_btn = QPushButton(tr("Help"))
        help_btn.clicked.connect(lambda: self._show_help("start"))
        head.addWidget(self.lang_btn)
        head.addWidget(help_btn)
        root.addLayout(head)
        sub = QLabel(
            tr("v{version} · hold your hotkey, speak Arabic, read the English", version=__version__)
        )
        sub.setObjectName("muted")
        root.addWidget(sub)

        # Status
        card, lay = _card()
        row = QHBoxLayout()
        self.dot = QLabel("●")
        self.status = QLabel(tr("Checking…"))
        self.status.setStyleSheet("font-weight: 600")
        row.addWidget(self.dot)
        row.addWidget(self.status, 1)
        lay.addLayout(row)
        self.engine = QLabel("")
        self.engine.setObjectName("muted")
        self.engine.setWordWrap(True)
        lay.addWidget(self.engine)
        root.addWidget(card)

        # Pipeline: step 1 (speech -> text) and step 2 (text -> translation), chosen separately
        card, lay = _card()
        lay.setSpacing(8)
        self.pipe_title = QLabel(tr("How GameTalk understands and translates you"))
        self.pipe_title.setObjectName("step")
        lay.addWidget(self.pipe_title)

        lay.addLayout(_step_header("1", "Speech → text", "who listens to your voice"))
        self.speech_buttons = self._segmented(
            lay,
            [(LOCAL, tr("💻  Whisper — on this PC")), (AZURE, "☁  Azure Speech")],
            self._set_speech,
        )
        row = QHBoxLayout()
        self.model_label = QLabel(tr("Whisper model:"))
        self.model_box = QComboBox()
        for m in MODELS:
            self.model_box.addItem(m, m)
        self.model_box.activated.connect(lambda _i: self._set("model", self.model_box))
        self.dialect_label = QLabel(tr("Your dialect:"))
        self.dialect = QComboBox()
        for code, name in AZURE_LOCALES.items():
            self.dialect.addItem(f"{tr(name)}  ({code})", code)
        self.dialect.activated.connect(lambda _i: self._set("azure_locale", self.dialect))
        self.speech_key = QLabel("")
        for w in (self.model_label, self.model_box, self.dialect_label, self.dialect):
            row.addWidget(w)
        row.addStretch(1)
        row.addWidget(self.speech_key)
        lay.addLayout(row)

        lay.addSpacing(4)
        lay.addLayout(_step_header("2", "Text → translation", "who turns it into English"))
        self.translation_buttons = self._segmented(
            lay,
            [(LOCAL, tr("💻  Whisper — on this PC")), (AZURE, "☁  Azure Translator")],
            self._set_translation,
        )
        row = QHBoxLayout()
        self.target_label = QLabel(tr("Translate to:"))
        self.target_box = QComboBox()
        for code, name in TARGET_LANGUAGES.items():
            self.target_box.addItem(tr(name), code)
        self.target_box.activated.connect(lambda _i: self._set("target_language", self.target_box))
        self.local_note = QLabel(tr("Whisper translates straight from your voice (English only)."))
        self.local_note.setObjectName("muted")
        self.translator_key = QLabel("")
        for w in (self.target_label, self.target_box, self.local_note):
            row.addWidget(w)
        row.addStretch(1)
        row.addWidget(self.translator_key)
        lay.addLayout(row)

        lay.addSpacing(4)
        self.flow = QLabel("")
        self.flow.setObjectName("flow")
        self.flow.setWordWrap(True)
        lay.addWidget(self.flow)
        self.privacy = QLabel("")
        self.privacy.setWordWrap(True)
        lay.addWidget(self.privacy)
        self.warn = QLabel("")
        self.warn.setObjectName("warn")
        self.warn.setWordWrap(True)
        lay.addWidget(self.warn)
        root.addWidget(card)

        # Features at a glance
        card, lay = _card()
        feat_head = QHBoxLayout()
        ft = QLabel(tr("Features"))
        ft.setObjectName("step")
        feat_head.addWidget(ft, 1)
        manage = QPushButton(tr("Manage…"))
        manage.clicked.connect(lambda: self._open("settings:features", "--settings"))
        feat_head.addWidget(manage)
        lay.addLayout(feat_head)
        self.features_label = QLabel("")
        self.features_label.setWordWrap(True)
        self.features_label.setObjectName("muted")
        lay.addWidget(self.features_label)
        self.team_cb = QCheckBox(tr("Teammate subtitles (translate what you hear)"))
        self.team_cb.toggled.connect(self._set_teammates)
        lay.addWidget(self.team_cb)
        root.addWidget(card)

        # Actions
        grid = QGridLayout()
        grid.setSpacing(8)
        self.start_btn = QPushButton(tr("▶  Start GameTalk"))
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(self._start_stop)
        grid.addWidget(self.start_btn, 0, 0, 1, 2)
        buttons = [
            (tr("⚙  Settings"), lambda: self._open("settings", "--settings")),
            (tr("🔑  Azure keys"), lambda: self._open("settings:azure", "--azure")),
            (tr("🎤  Test microphone"), lambda: self._open("test", "--test-mic")),
            (tr("🩺  Self-test"), lambda: self._open("selftest", "--selftest")),
            (tr("📘  My phrasebook"), lambda: self._open("phrasebook", "--phrasebook")),
            (tr("📂  Logs folder"), self._open_logs),
        ]
        for i, (text, slot) in enumerate(buttons):
            b = QPushButton(text)
            b.clicked.connect(slot)
            grid.addWidget(b, 1 + i // 2, i % 2)
        root.addLayout(grid)

        # Windows integration
        card, lay = _card()
        self.autostart = QCheckBox(tr("Start GameTalk when Windows starts"))
        self.autostart.setChecked(autostart_enabled())
        self.autostart.toggled.connect(self._toggle_autostart)
        lay.addWidget(self.autostart)
        shortcut = QPushButton(tr("Create desktop shortcut to this launcher"))
        shortcut.clicked.connect(self._shortcut)
        lay.addWidget(shortcut)
        root.addWidget(card)

        tip = QLabel(tr("Tip: you can close this window — GameTalk keeps running in the tray."))
        tip.setObjectName("muted")
        tip.setWordWrap(True)
        root.addWidget(tip)
        root.addWidget(credit_label())

        self._timer = QTimer(self, interval=1500, timeout=self.refresh)
        self._timer.start()
        self.refresh()

    # ---- state ---------------------------------------------------------------------------

    def _config_mtime(self) -> float:
        try:
            return self.store.path.stat().st_mtime
        except OSError:
            return 0.0

    def refresh(self) -> None:
        mtime = self._config_mtime()
        if mtime != getattr(self, "_seen_mtime", None):  # e.g. keys saved in Settings
            self._seen_mtime = mtime
            self._load_mode()
        info = parse_status(ipc.send_command("status", 400))
        self.running = info is not None
        if info is None:
            self.dot.setStyleSheet("color: #6b7280")
            self.status.setText(tr("Not running"))
            self.engine.setText(tr("Click Start — GameTalk then lives in the system tray."))
            self.start_btn.setText(tr("▶  Start GameTalk"))
            self.start_btn.setObjectName("primary")
        else:
            ok = info["state"] == "ready"
            self.dot.setStyleSheet(f"color: {'#3ddc84' if ok else '#ffb020'}")
            if ok:
                state = tr("Running — hold {key} to talk", key=info["hotkey"])
            else:
                state = tr("Running — disabled from the tray")
            self.status.setText(state)
            self.engine.setText(
                tr("Profile: {name}", name=info["profile"]) + f" · {tr(info['engine'])}"
            )
            self.start_btn.setText(tr("■  Stop GameTalk"))
            self.start_btn.setObjectName("danger")
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)

    def _segmented(self, layout, options, on_pick) -> dict[str, QPushButton]:
        """Row of exclusive toggle buttons; `on_pick(value)` fires on user clicks only."""
        row = QHBoxLayout()
        group = QButtonGroup(self)
        buttons = {}
        for value, text in options:
            b = QPushButton(text)
            b.setObjectName("seg")
            b.setCheckable(True)
            b.clicked.connect(lambda _c=False, v=value: on_pick(v))
            group.addButton(b)
            row.addWidget(b, 1)
            buttons[value] = b
        layout.addLayout(row)
        return buttons

    def _load_mode(self) -> None:
        s = self.store.load()
        p = s.profile
        azure_speech = p.speech_provider == AZURE
        azure_translate = p.translation_provider == AZURE
        self.pipe_title.setText(tr("How GameTalk understands and translates you") + f" · {p.name}")

        self.speech_buttons[p.speech_provider].setChecked(True)
        self.translation_buttons[p.translation_provider].setChecked(True)
        local_tr = self.translation_buttons[LOCAL]
        local_tr.setEnabled(not azure_speech)
        local_tr.setToolTip(tr(NO_LOCAL_TRANSLATION) if azure_speech else "")

        if self.model_box.findData(p.model) < 0:  # custom local model folder
            self.model_box.addItem(p.model, p.model)
        for box, value in (
            (self.model_box, p.model),
            (self.dialect, p.azure_locale),
            (self.target_box, p.target_language),
        ):
            box.setCurrentIndex(max(0, box.findData(value)))
        for w in (self.model_label, self.model_box):
            w.setVisible(not azure_speech)
        for w in (self.dialect_label, self.dialect):
            w.setVisible(azure_speech)
        for w in (self.target_label, self.target_box):
            w.setVisible(azure_translate)
        self.local_note.setVisible(not azure_translate)

        speech_ok, translator_ok = key_status(s)
        _key_badge(self.speech_key, azure_speech, speech_ok)
        _key_badge(self.translator_key, azure_translate, translator_ok)

        flow, sent, cloud = pipeline_summary(p)
        self.flow.setText(flow)
        self.privacy.setText(sent)
        self.privacy.setObjectName("cloud" if cloud else "private")
        self.privacy.style().unpolish(self.privacy)
        self.privacy.style().polish(self.privacy)
        missing = missing_keys(p, s)
        self.warn.setText(
            tr("⚠ Missing: {what}. Click “Azure keys” to add it.", what=tr(" and ").join(missing))
            if missing
            else ""
        )
        self.warn.setVisible(bool(missing))

        on = [tr(name) for key, name in FEATURE_NAMES if getattr(s.features, key)]
        off = [tr(name) for key, name in FEATURE_NAMES if not getattr(s.features, key)]
        self.features_label.setText(
            tr("On: {on}", on=", ".join(on) or "—")
            + "\n"
            + tr("Off: {off}", off=", ".join(off) or "—")
        )
        self.team_cb.blockSignals(True)
        self.team_cb.setChecked(s.teammates.enabled)
        self.team_cb.blockSignals(False)

    def _save(self, mutate, target: str = "profile") -> None:
        s = self.store.load()
        mutate(s.profile if target == "profile" else s)
        validate(s)
        self.store.save(s)
        self._seen_mtime = self._config_mtime()
        if self.running:
            ipc.send_command("reload")
        self._load_mode()

    def _set_speech(self, provider: str) -> None:
        def apply(p: Profile) -> None:
            p.speech_provider = provider
            if provider == AZURE:
                p.translation_provider = AZURE  # see NO_LOCAL_TRANSLATION

        self._save(apply)

    def _set_translation(self, provider: str) -> None:
        self._save(lambda p: setattr(p, "translation_provider", provider))

    def _set(self, field: str, box: QComboBox) -> None:
        value = box.currentData()
        self._save(lambda p: setattr(p, field, value))

    def _set_teammates(self, on: bool) -> None:
        self._save(lambda s: setattr(s.teammates, "enabled", on), target="settings")

    def _toggle_language(self) -> None:
        new = "en" if is_rtl() else "ar"
        self._save(lambda s: setattr(s.features, "ui_language", new), target="settings")
        set_language(new)
        self.language_changed.emit()

    # ---- actions -------------------------------------------------------------------------

    def _show_help(self, topic: str) -> None:
        from gametalk.help import HelpDialog

        if self._help is None:
            self._help = HelpDialog(topic)
        else:
            self._help.show_topic(topic)
        self._help.show()
        self._help.raise_()

    def _start_stop(self) -> None:
        if self.running:
            ipc.send_command("quit")
        else:
            launch_app()
        QTimer.singleShot(1200, self.refresh)

    def _open(self, command: str, flag: str) -> None:
        if not self.running or ipc.send_command(command) is None:
            launch_app(flag)
        QTimer.singleShot(1500, self.refresh)

    def _open_logs(self) -> None:
        path = default_config_dir() / "logs"
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _toggle_autostart(self, on: bool) -> None:
        try:
            set_autostart(on)
        except OSError as e:
            QMessageBox.warning(self, tr(APP_NAME), tr("Couldn't change Windows startup: {e}", e=e))
            self.autostart.blockSignals(True)
            self.autostart.setChecked(autostart_enabled())
            self.autostart.blockSignals(False)

    def _shortcut(self) -> None:
        try:
            path = create_desktop_shortcut()
            QMessageBox.information(self, tr(APP_NAME), tr("Shortcut created:") + f"\n{path}")
        except (OSError, subprocess.SubprocessError) as e:
            QMessageBox.warning(self, tr(APP_NAME), tr("Couldn't create the shortcut: {e}", e=e))


def main() -> int:
    """Open the main window: the new hub, or the classic launcher with --classic."""
    if "--classic" not in sys.argv[1:]:
        from gametalk.hub import main as hub_main

        return hub_main()
    if sys.platform == "win32":
        # Own taskbar identity so Windows shows our icon rather than Python's.
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("GameTalk.Launcher")
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    app = QApplication(sys.argv[:1])
    app.setApplicationName(f"{APP_NAME} Launcher")
    set_language(ConfigStore().load().features.ui_language)
    return run_classic(app)


def run_classic(app: QApplication) -> int:
    """The original widget launcher (also the fallback if Qt Quick can't load)."""
    apply_layout_direction(app)
    holder: dict[str, Launcher] = {}

    def build() -> None:
        old = holder.get("w")
        apply_layout_direction(app)
        w = Launcher()
        w.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        w.language_changed.connect(lambda: QTimer.singleShot(0, build))
        if old is not None:
            w.move(old.pos())
            old.close()
        holder["w"] = w
        w.show()

    build()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
