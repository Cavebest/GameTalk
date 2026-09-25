# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Settings window: a sidebar of pages, each with a short explanation and a "?" for more.

Edits a copy of Settings; nothing is applied or saved until Save. Every optional system has an
on/off switch on the Features page, mirrored on its own page (both stay in sync).
"""

from __future__ import annotations

import copy
import pathlib
import threading

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFontComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from . import APP_NAME, AUTHOR_URL, COPYRIGHT, __version__, help, theme
from .audio import list_input_devices, refresh_devices
from .config import (
    AZURE,
    AZURE_LOCALES,
    GAMEPAD_BUTTONS,
    LOCAL,
    MAX_VOCABULARY,
    MAX_VOCABULARY_ITEM,
    MODELS,
    MONITORS,
    NEVER_HIDE,
    QUICK_TEXT_TRANSLATORS,
    SOURCE_LANGUAGES,
    SPEECH_PROVIDERS,
    TARGET_LANGUAGES,
    TEAM_RECOGNIZERS,
    TEAM_TRANSLATORS,
    TRANSLATION_PROVIDERS,
    UI_LANGUAGES,
    Correction,
    Profile,
    QuickPhrase,
    clean_vocabulary,
    validate,
)
from .credentials import protect, unprotect
from .hotkey import SUPPORTED_HOTKEYS
from .i18n import is_rtl, tr

PREVIEW_TEXT = "Wait for me, I'm coming."
DEVICE_LABELS = {"auto": "Auto (GPU if available)", "cuda": "GPU (NVIDIA CUDA)", "cpu": "CPU"}
MONITOR_LABELS = {"game": "Monitor with the game", "primary": "Primary monitor"}
POSITION_LABELS = {
    "top-left": "Top left",
    "top-center": "Top center",
    "top-right": "Top right",
    "middle-left": "Middle left",
    "center": "Center",
    "middle-right": "Middle right",
    "bottom-left": "Bottom left",
    "bottom-center": "Bottom center",
    "bottom-right": "Bottom right",
}
SAVED_PLACEHOLDER = "•••••••• saved — leave empty to keep"
# (page key, sidebar icon, help topic)
PAGES = [
    ("general", "⚙", "general"),
    ("features", "🧩", "features"),
    ("microphone", "🎤", "microphone"),
    ("speech", "🗣", "speech"),
    ("translation", "🌐", "translation"),
    ("azure", "🔑", "azure"),
    ("hotkey", "⌨", "hotkey"),
    ("overlay", "🪟", "overlay"),
    ("phrases", "💬", "phrases"),
    ("corrections", "✏", "corrections"),
    ("quicktext", "⌨️", "quicktext"),
    ("learning", "📘", "learning"),
    ("gamepad", "🎮", "gamepad"),
    ("teammates", "👥", "teammates"),
    ("games", "🎯", "profiles"),
]
# Feature switches: key in Features/TeammateSettings -> (label, help topic)
FEATURE_SWITCHES = [
    (
        "replay_enabled",
        "Replay key (show the last translation again)",
        "replay",
        "Press the replay key (F10) to show your last translation again.",
    ),
    (
        "history_enabled",
        "Translation history (tray menu)",
        "replay",
        "Keeps your recent translations in memory; pick one from the tray menu to show it again.",
    ),
    (
        "quick_phrases_enabled",
        "Quick phrases on keys",
        "phrases",
        "Ready-made sentences on keys, shown instantly without speaking.",
    ),
    (
        "corrections_enabled",
        "Correction rules",
        "corrections",
        "Fixes words that are often translated wrong (your own rules).",
    ),
    (
        "pronunciation_enabled",
        "Pronunciation helper (English in Arabic letters)",
        "pronunciation",
        "Shows how to say the English sentence, written in Arabic letters.",
    ),
    (
        "gamepad_enabled",
        "Game controller button as push-to-talk",
        "gamepad",
        "Hold a controller button (e.g. RB) to talk, like the keyboard hotkey.",
    ),
    (
        "teammates.enabled",
        "Teammate subtitles (translate what you hear)",
        "teammates",
        "Shows what your teammates say, translated, as subtitles.",
    ),
    (
        "fullscreen_warning",
        "Warn when a game is in exclusive fullscreen",
        "overlay",
        "Tells you once when a game hides the overlay, so you can switch to Borderless.",
    ),
    (
        "stuck_key_protection",
        "Stuck-key protection",
        "hotkey",
        "Stops the recording even if Windows misses the moment you let go of the key.",
    ),
    (
        "trim_silence",
        "Trim silence before sending audio to Azure",
        "privacy",
        "Sends only the part of the recording with speech: less data, faster, cheaper.",
    ),
    (
        "azure_phrase_list",
        "Send gaming vocabulary to Azure Speech (phrase list)",
        "azure",
        "Helps Azure Speech recognise game words like Medic or Flank.",
    ),
    (
        "tray_notifications",
        "Tray notifications",
        "general",
        "Small pop-up messages for warnings and tips.",
    ),
    (
        "arabic_corrections_enabled",
        "Arabic dialect corrections before translating",
        "corrections",
        "Turns dialect words into standard Arabic first (خليكم → ابقوا) for better translations.",
    ),
    (
        "sound_cues",
        "Sound cues when recording starts/stops",
        "sounds",
        "A short beep so you know GameTalk heard you, even without looking.",
    ),
    (
        "copy_to_clipboard",
        "Copy translations to the clipboard",
        "general",
        "Paste the English yourself into a game's text chat (Ctrl+V). Nothing is typed for you.",
    ),
    (
        "phrase_suggestions",
        "Suggest quick phrases for sentences you repeat",
        "phrases",
        "Say the same thing often? GameTalk suggests putting it on a key.",
    ),
    (
        "quick_text_enabled",
        "Quick text box (type Arabic, get English)",
        "quicktext",
        "A key opens a small box: type Arabic, press Enter, get English for text chat.",
    ),
    (
        "learning_enabled",
        "Learning mode (save my phrasebook)",
        "learning",
        "Keeps the sentences you use on this PC so you can practise them. Off = nothing saved.",
    ),
    (
        "azure_usage_tracking",
        "Azure usage counter and quota warnings",
        "azure",
        "Counts how much of Azure's free monthly quota you've used and warns at 80% and 100%.",
    ),
]


def _combo(items: dict[str, str] | list[str], translate: bool = True) -> QComboBox:
    box = QComboBox()
    pairs = items.items() if isinstance(items, dict) else ((i, i) for i in items)
    for data, label in pairs:
        box.addItem(tr(label) if translate else label, data)
    return box


def _select(box: QComboBox, data) -> None:
    i = box.findData(data)
    if i < 0 and box.isEditable():
        box.setEditText(str(data))
    elif i >= 0:
        box.setCurrentIndex(i)


def _slider(lo: int, hi: int) -> QSlider:
    s = QSlider(Qt.Orientation.Horizontal)
    s.setRange(lo, hi)
    return s


def _note(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setObjectName("muted")
    return lbl


def _hotkey_combo(allow_none: bool = False) -> QComboBox:
    box = QComboBox()
    if allow_none:
        box.addItem(tr("(none)"), "")
    for key in SUPPORTED_HOTKEYS:
        box.addItem(key, key)
    return box


class _Relay(QObject):
    """Carries a background-thread result back to the UI thread."""

    done = Signal(object)


class SettingsDialog(QDialog):
    def __init__(self, controller):
        super().__init__(None)
        self.c = controller
        self.s = controller.settings.clone()
        self.cur: Profile = self.s.profile
        self._switches: dict[str, list[QCheckBox]] = {}
        self.setWindowTitle(tr("{app} — Settings", app=tr(APP_NAME)))
        self.setMinimumWidth(760)
        if is_rtl():
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        theme.apply(
            self,
            "QListWidget#nav { background: #0f1218; border: none; outline: 0; }"
            " QListWidget#nav::item { padding: 6px 10px; border-radius: 6px; margin: 1px 4px; }"
            " QListWidget#nav::item:selected { background: #0c4a5e; color: white; }"
            " QListWidget#nav::item:hover:!selected { background: #1d2330; }"
            " QLabel#pagetitle { font-size: 14pt; font-weight: 600; }"
            " QFrame#summary { background: #10151d; border: 1px solid #232937;"
            " border-radius: 8px; }"
            " QPushButton#helpbtn { padding: 2px 9px; border-radius: 11px; font-weight: 700; }"
            " QTableWidget { background: #1d2330; gridline-color: #2b3345;"
            " border: 1px solid #2b3345; border-radius: 6px; }"
            " QHeaderView::section { background: #161a22; color: #8b93a3; border: none;"
            " padding: 5px; }",
        )

        root = QVBoxLayout(self)
        root.addLayout(self._profile_bar())
        body = QHBoxLayout()
        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.setFixedWidth(190)
        self.stack = QStackedWidget()
        builders = {
            "general": self._general_page,
            "features": self._features_page,
            "microphone": self._mic_page,
            "speech": self._speech_page,
            "translation": self._translation_page,
            "azure": self._azure_page,
            "hotkey": self._hotkey_page,
            "overlay": self._overlay_page,
            "phrases": self._phrases_page,
            "corrections": self._corrections_page,
            "quicktext": self._quicktext_page,
            "learning": self._learning_page,
            "gamepad": self._gamepad_page,
            "teammates": self._teammates_page,
            "games": self._games_page,
        }
        self._page_keys: list[str] = []
        for key, icon, topic in PAGES:
            content = builders[key]()
            self.stack.addWidget(self._wrap_page(topic, content))
            item = QListWidgetItem(f"{icon}  {help.title(topic)}")
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.nav.addItem(item)
            self._page_keys.append(key)
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        body.addWidget(self.nav)
        body.addWidget(self.stack, 1)
        root.addLayout(body, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(tr("Save"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("Cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        help_btn = QPushButton(tr("Help"))
        help_btn.clicked.connect(lambda: self.c.open_help(self._current_topic()))
        credit = QLabel(
            f'v{__version__} · {COPYRIGHT} · <a href="{AUTHOR_URL}" '
            f'style="color:{theme.ACCENT}; text-decoration:none">'
            f"{AUTHOR_URL.removeprefix('https://')}</a>"
        )
        credit.setOpenExternalLinks(True)
        credit.setObjectName("muted")
        footer = QHBoxLayout()
        footer.addWidget(help_btn)
        footer.addWidget(credit, 1)
        footer.addWidget(buttons)
        root.addLayout(footer)

        self._relay = _Relay(self)
        self._relay.done.connect(self._on_azure_tested)
        self._level_timer = QTimer(self, interval=50, timeout=self._update_level)
        self.c.test_result.connect(self._on_test_result)
        self.c.hotkey.captured.connect(self._on_captured)
        self._capture_target: QComboBox | None = None
        self._overlay_moved = getattr(self.c.overlay, "moved", None)
        if not hasattr(self._overlay_moved, "connect"):
            self._overlay_moved = None  # fallback overlay has no move mode
        if self._overlay_moved is not None:
            self._overlay_moved.connect(self._on_overlay_moved)

        self._load_global()
        self._load_profile(self.cur)
        self.nav.setCurrentRow(0)
        self._fit_to_screen()

    # ---- structure -----------------------------------------------------------------------

    def _fit_to_screen(self) -> None:
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is None:
            return
        avail = screen.availableGeometry()
        self.resize(min(900, avail.width() - 40), min(760, int(avail.height() * 0.9)))

    def _wrap_page(self, topic: str, content: QWidget) -> QScrollArea:
        """Page = title + '?' + short explanation + the form, scrollable on small screens."""
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(18, 12, 18, 12)
        head = QHBoxLayout()
        title = QLabel(help.title(topic))
        title.setObjectName("pagetitle")
        qbtn = QPushButton("?")
        qbtn.setObjectName("helpbtn")
        qbtn.setToolTip(tr("Explain this page"))
        qbtn.clicked.connect(lambda: self.c.open_help(topic))
        head.addWidget(title)
        head.addStretch(1)
        head.addWidget(qbtn)
        lay.addLayout(head)
        box = QFrame()
        box.setObjectName("summary")
        bl = QVBoxLayout(box)
        bl.setContentsMargins(10, 8, 10, 8)
        bl.addWidget(_note(help.summary(topic)))
        lay.addWidget(box)
        lay.addWidget(content)
        lay.addStretch(1)
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QScrollArea.Shape.NoFrame)
        area.setWidget(page)
        return area

    def _form(self) -> tuple[QWidget, QFormLayout]:
        w = QWidget()
        f = QFormLayout(w)
        f.setContentsMargins(0, 8, 0, 0)
        f.setVerticalSpacing(10)
        return w, f

    def _switch(self, key: str, text: str, tip: str = "") -> QCheckBox:
        """A feature on/off checkbox; several can exist for one key and stay in sync."""
        cb = QCheckBox(tr(text))
        if tip:
            cb.setToolTip(tr(tip))
        self._switches.setdefault(key, []).append(cb)

        def sync(on: bool, key=key, source=cb):
            for other in self._switches[key]:
                if other is not source and other.isChecked() != on:
                    other.blockSignals(True)
                    other.setChecked(on)
                    other.blockSignals(False)
            self._update_dependent_widgets()

        cb.toggled.connect(sync)
        return cb

    def _current_topic(self) -> str:
        return PAGES[max(0, self.nav.currentRow())][2]

    def show_tab(self, name: str) -> None:
        key = name.lower()
        aliases = {"profiles": "games", "keys": "azure"}
        key = aliases.get(key, key)
        if key in self._page_keys:
            self.nav.setCurrentRow(self._page_keys.index(key))

    # ---- profile bar ---------------------------------------------------------------------

    def _profile_bar(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(QLabel(tr("Profile:")))
        self.profile_box = QComboBox()
        self.profile_box.setToolTip(tr("Settings marked per game belong to this profile."))
        self._fill_profiles()
        self.profile_box.currentIndexChanged.connect(self._on_profile_changed)
        row.addWidget(self.profile_box, 1)
        for text, slot in (
            ("New", self._new_profile),
            ("Rename", self._rename_profile),
            ("Delete", self._delete_profile),
            ("Export…", self._export_profile),
            ("Import…", self._import_profile),
        ):
            b = QPushButton(tr(text))
            b.clicked.connect(slot)
            row.addWidget(b)
        return row

    # ---- pages ---------------------------------------------------------------------------

    def _general_page(self) -> QWidget:
        w, f = self._form()
        self.language_box = _combo(UI_LANGUAGES)
        self.language_box.setToolTip(tr("Takes effect when you click Save."))
        f.addRow(tr("Interface language:"), self.language_box)
        self.enabled_cb = QCheckBox(tr("GameTalk is enabled"))
        self.enabled_cb.setToolTip(tr("Off = hotkeys do nothing until you turn it back on."))
        f.addRow("", self.enabled_cb)
        f.addRow("", self._switch("tray_notifications", "Tray notifications"))
        self.autostart_cb = QCheckBox(tr("Start GameTalk when Windows starts"))
        f.addRow("", self.autostart_cb)
        f.addRow("", self._switch("sound_cues", "Sound cues when recording starts/stops"))
        self.sound_volume = _slider(0, 100)
        f.addRow(tr("Sound volume:"), self.sound_volume)
        f.addRow("", self._switch("copy_to_clipboard", "Copy translations to the clipboard"))
        tools = QHBoxLayout()
        selftest = QPushButton(tr("🩺  Run self-test"))
        selftest.clicked.connect(self.c.open_diagnostics)
        book = QPushButton(tr("📘  My phrasebook"))
        book.clicked.connect(self.c.open_phrasebook)
        tools.addWidget(selftest)
        tools.addWidget(book)
        tools.addStretch(1)
        f.addRow(tr("Tools:"), tools)
        return w

    def _features_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 8, 0, 0)
        for key, text, topic, description in FEATURE_SWITCHES:
            row = QHBoxLayout()
            cb = self._switch(key, text)
            desc = _note(tr(description))
            q = QPushButton("?")
            q.setObjectName("helpbtn")
            q.setToolTip(tr("Explain this page"))
            q.clicked.connect(lambda _c=False, t=topic: self.c.open_help(t))
            col = QVBoxLayout()
            col.setSpacing(2)
            col.addWidget(cb)
            desc.setContentsMargins(26, 0, 0, 4)
            col.addWidget(desc)
            row.addLayout(col, 1)
            row.addWidget(q, 0, Qt.AlignmentFlag.AlignTop)
            lay.addLayout(row)
        return w

    def _mic_page(self) -> QWidget:
        w, f = self._form()
        self.mic_box = QComboBox()
        self._fill_mics()
        refresh = QPushButton(tr("Refresh"))
        refresh.setToolTip(tr("Re-scan audio devices (after plugging in a microphone)"))
        refresh.clicked.connect(lambda: self._fill_mics(rescan=True))
        row = QHBoxLayout()
        row.addWidget(self.mic_box, 1)
        row.addWidget(refresh)
        f.addRow(tr("Input device:"), row)
        self.level = QProgressBar()
        self.level.setRange(0, 100)
        self.level.setTextVisible(False)
        self.level.setFixedHeight(10)
        f.addRow(tr("Input level:"), self.level)
        self.test_btn = QPushButton(tr("Test microphone (speak for 3 s)"))
        self.test_btn.clicked.connect(self._test_mic)
        f.addRow("", self.test_btn)
        self.test_label = QLabel("")
        self.test_label.setWordWrap(True)
        f.addRow(tr("Result:"), self.test_label)
        return w

    def _speech_page(self) -> QWidget:
        w, f = self._form()
        self.speech_box = _combo(SPEECH_PROVIDERS)
        self.speech_box.currentIndexChanged.connect(self._update_dependent_widgets)
        f.addRow(tr("Recognition:"), self.speech_box)
        self.locale_box = _combo(AZURE_LOCALES)
        self.locale_box.setToolTip(
            tr("The dialect you speak; Azure is more accurate with the match")
        )
        f.addRow(tr("Azure dialect:"), self.locale_box)
        self.model_box = _combo(MODELS, translate=False)
        self.model_box.setEditable(True)  # also accepts a local model folder
        self.model_box.setToolTip(tr("Model name or a local CTranslate2 model folder"))
        f.addRow(tr("Whisper model:"), self.model_box)
        self.device_box = _combo(DEVICE_LABELS)
        self.device_box.setToolTip(
            tr("Auto uses your NVIDIA GPU when available and falls back to the CPU.")
        )
        f.addRow(tr("Run on:"), self.device_box)
        self.src_box = _combo(SOURCE_LANGUAGES)
        f.addRow(tr("Source language:"), self.src_box)
        self.autodetect = QCheckBox(tr("Auto-detect spoken language"))
        self.autodetect.toggled.connect(self._update_dependent_widgets)
        f.addRow("", self.autodetect)
        self.show_arabic = QCheckBox(tr("Also show the original transcript (slower)"))
        self.show_arabic.setToolTip(tr("Adds the Arabic text under the translation."))
        f.addRow("", self.show_arabic)
        f.addRow(
            _note(
                tr(
                    "tiny/base/small are fastest. medium and large-v3 translate dialect more "
                    "naturally but need more VRAM (large-v3 ≈ 3 GB on GPU). Models download "
                    "once, then run offline."
                )
            )
        )
        return w

    def _translation_page(self) -> QWidget:
        w, f = self._form()
        self.provider_box = _combo(TRANSLATION_PROVIDERS)
        self.provider_box.currentIndexChanged.connect(self._update_dependent_widgets)
        f.addRow(tr("Provider:"), self.provider_box)
        self.target_box = _combo(TARGET_LANGUAGES)
        self.target_box.setToolTip(tr("Whisper's built-in translation always outputs English"))
        f.addRow(tr("Target language:"), self.target_box)
        self.gaming = QCheckBox(tr("Gaming translation mode (short, casual callouts)"))
        self.gaming.setToolTip(tr("Steers Whisper toward short squad-chat phrasing."))
        f.addRow("", self.gaming)
        f.addRow(
            "",
            self._switch(
                "pronunciation_enabled",
                "Pronunciation helper (English in Arabic letters)",
                "Shows how to say the English sentence, written in Arabic letters.",
            ),
        )
        self.vocab_on = QCheckBox(tr("Use gaming vocabulary as recognition hints"))
        self.vocab_on.setToolTip(
            tr("Whisper is nudged toward these words. Nothing is ever find-and-replaced.")
        )
        self.vocab_on.toggled.connect(self._update_dependent_widgets)
        f.addRow("", self.vocab_on)
        self.vocab = QPlainTextEdit()
        self.vocab.setPlaceholderText(
            tr("One word or phrase per line, e.g. Medic, Flank, Fall back")
        )
        self.vocab.setToolTip(
            tr(
                "Up to {n} entries of {m} characters; duplicates are removed. "
                "The first 24 are sent to Whisper.",
                n=MAX_VOCABULARY,
                m=MAX_VOCABULARY_ITEM,
            )
        )
        f.addRow(tr("Gaming vocabulary:"), self.vocab)
        self.translation_note = _note("")
        f.addRow(self.translation_note)
        return w

    def _azure_page(self) -> QWidget:
        w, f = self._form()
        self.speech_key = QLineEdit()
        self.speech_key.setEchoMode(QLineEdit.EchoMode.Password)
        f.addRow(tr("Speech key:"), self.speech_key)
        self.speech_region = QLineEdit()
        self.speech_region.setPlaceholderText(tr("e.g. westeurope, uaenorth, eastus"))
        f.addRow(tr("Speech region:"), self.speech_region)
        self.translator_key = QLineEdit()
        self.translator_key.setEchoMode(QLineEdit.EchoMode.Password)
        f.addRow(tr("Translator key:"), self.translator_key)
        self.translator_region = QLineEdit()
        self.translator_region.setPlaceholderText(tr("e.g. westeurope, or global"))
        f.addRow(tr("Translator region:"), self.translator_region)
        row = QHBoxLayout()
        self.azure_test_btn = QPushButton(tr("Test connection"))
        self.azure_test_btn.clicked.connect(self._test_azure)
        clear = QPushButton(tr("Forget saved keys"))
        clear.clicked.connect(self._clear_azure_keys)
        row.addWidget(self.azure_test_btn)
        row.addWidget(clear)
        row.addStretch(1)
        f.addRow("", row)
        self.azure_result = QLabel("")
        self.azure_result.setWordWrap(True)
        self.azure_result.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        f.addRow(self.azure_result)
        f.addRow(
            "",
            self._switch(
                "azure_phrase_list", "Send gaming vocabulary to Azure Speech (phrase list)"
            ),
        )
        f.addRow("", self._switch("azure_usage_tracking", "Azure usage counter and quota warnings"))
        self.usage_label = QLabel("")
        self.usage_label.setWordWrap(True)
        reset = QPushButton(tr("Reset counter"))
        reset.clicked.connect(self._reset_usage)
        urow = QHBoxLayout()
        urow.addWidget(self.usage_label, 1)
        urow.addWidget(reset)
        f.addRow(tr("This month:"), urow)
        self._show_usage()
        f.addRow(
            _note(
                tr(
                    "Privacy: nothing is sent to Azure unless a profile uses it. Azure Speech "
                    "receives your push-to-talk audio; Azure Translator receives only the "
                    "recognised text. Keys are encrypted with your Windows account (DPAPI) "
                    "before being saved."
                )
            )
        )
        return w

    def _hotkey_page(self) -> QWidget:
        w, f = self._form()
        self.hotkey_box = _hotkey_combo()
        self.capture_btn = QPushButton(tr("Press a key…"))
        self.capture_btn.clicked.connect(lambda: self._begin_capture(self.hotkey_box))
        row = QHBoxLayout()
        row.addWidget(self.hotkey_box, 1)
        row.addWidget(self.capture_btn)
        f.addRow(tr("Talk key:"), row)
        self.mode_push = QRadioButton(tr("Push-to-talk (hold to record)"))
        self.mode_toggle = QRadioButton(tr("Toggle (press to start, press again to stop)"))
        self.mode_voice = QRadioButton(tr("Open mic (no key needed — the key mutes/unmutes)"))
        self.mode_voice.setToolTip(
            tr("The microphone stays open while this mode is on. Audio stays in memory only.")
        )
        group = QButtonGroup(w)
        group.addButton(self.mode_push)
        group.addButton(self.mode_toggle)
        group.addButton(self.mode_voice)
        f.addRow(tr("Mode:"), self.mode_push)
        f.addRow("", self.mode_toggle)
        f.addRow("", self.mode_voice)
        self.voice_sensitivity = _slider(0, 100)
        self.voice_sensitivity.setToolTip(tr("Higher catches quieter voices (and more noise)."))
        f.addRow(tr("Open mic sensitivity:"), self.voice_sensitivity)
        f.addRow("", self._switch("replay_enabled", "Replay key (show the last translation again)"))
        self.replay_box = _hotkey_combo()
        replay_capture = QPushButton(tr("Press a key…"))
        replay_capture.clicked.connect(lambda: self._begin_capture(self.replay_box))
        row = QHBoxLayout()
        row.addWidget(self.replay_box, 1)
        row.addWidget(replay_capture)
        f.addRow(tr("Replay key:"), row)
        f.addRow("", self._switch("stuck_key_protection", "Stuck-key protection"))
        f.addRow(_note(tr("The key still reaches the game — pick one the game doesn't use.")))
        return w

    def _overlay_page(self) -> QWidget:
        w, f = self._form()
        self.pos_box = _combo(POSITION_LABELS)
        f.addRow(tr("Position:"), self.pos_box)
        self.off_x, self.off_y = QSpinBox(), QSpinBox()
        for sb in (self.off_x, self.off_y):
            sb.setRange(-4000, 4000)
            sb.setSuffix(" px")
            sb.setToolTip(tr("Distance from the chosen screen edge"))
        row = QHBoxLayout()
        row.addWidget(QLabel("X"))
        row.addWidget(self.off_x)
        row.addWidget(QLabel("Y"))
        row.addWidget(self.off_y)
        f.addRow(tr("Offset from edge:"), row)
        self.monitor_box = _combo({m: MONITOR_LABELS[m] for m in MONITORS})
        f.addRow(tr("Monitor:"), self.monitor_box)
        self.font_box = QFontComboBox()
        f.addRow(tr("Font:"), self.font_box)
        self.font_size = QSpinBox()
        self.font_size.setRange(10, 48)
        self.font_size.setSuffix(" pt")
        f.addRow(tr("Font size:"), self.font_size)
        self.max_width = QSpinBox()
        self.max_width.setRange(200, 2000)
        self.max_width.setSingleStep(20)
        self.max_width.setSuffix(" px")
        f.addRow(tr("Maximum width:"), self.max_width)
        self.bg_opacity = _slider(0, 100)
        f.addRow(tr("Background opacity:"), self.bg_opacity)
        self.text_opacity = _slider(10, 100)
        f.addRow(tr("Text opacity:"), self.text_opacity)
        colors = QHBoxLayout()
        self.color_buttons: dict[str, QPushButton] = {}
        for attr, label in (
            ("text_color", "Text"),
            ("background_color", "Background"),
            ("accent_color", "Accent"),
        ):
            b = QPushButton(tr(label))
            b.clicked.connect(lambda _c=False, a=attr: self._pick_color(a))
            self.color_buttons[attr] = b
            colors.addWidget(b)
        f.addRow(tr("Colours:"), colors)
        self.outline_cb = QCheckBox(tr("Dark outline around the text"))
        self.outline_cb.setToolTip(tr("Keeps text readable over bright scenes."))
        f.addRow("", self.outline_cb)
        self.radius = QSpinBox()
        self.radius.setRange(0, 40)
        self.radius.setSuffix(" px")
        f.addRow(tr("Corner radius:"), self.radius)
        self.duration = QSpinBox()
        self.duration.setRange(1, 15)
        self.duration.setSuffix(" s")
        self.duration.setToolTip(
            tr("Long translations stay up a little longer so you can read them.")
        )
        self.never_hide = QCheckBox(tr("Never auto-hide"))
        self.never_hide.toggled.connect(lambda on: self.duration.setEnabled(not on))
        row = QHBoxLayout()
        row.addWidget(self.duration)
        row.addWidget(self.never_hide)
        f.addRow(tr("Display duration:"), row)
        self.animation = QCheckBox(tr("Fade in/out"))
        f.addRow(tr("Animation:"), self.animation)
        f.addRow(
            "",
            self._switch("fullscreen_warning", "Warn when a game is in exclusive fullscreen"),
        )
        preview = QPushButton(tr("Preview"))
        preview.clicked.connect(self._preview)
        self.move_btn = QPushButton(tr("Move overlay"))
        self.move_btn.setCheckable(True)
        self.move_btn.toggled.connect(self._toggle_move)
        row = QHBoxLayout()
        row.addWidget(preview)
        row.addWidget(self.move_btn)
        f.addRow("", row)
        return w

    def _table(self, headers: list[str]) -> QTableWidget:
        t = QTableWidget(0, len(headers))
        t.setHorizontalHeaderLabels([tr(h) for h in headers])
        t.verticalHeader().setVisible(False)
        t.horizontalHeader().setSectionResizeMode(len(headers) - 1, QHeaderView.ResizeMode.Stretch)
        t.setMinimumHeight(220)
        return t

    def _phrases_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 8, 0, 0)
        lay.addWidget(self._switch("quick_phrases_enabled", "Quick phrases on keys"))
        self.phrase_table = self._table(["Key", "Phrase"])
        self.phrase_table.setColumnWidth(0, 170)
        lay.addWidget(self.phrase_table)
        row = QHBoxLayout()
        add = QPushButton(tr("Add phrase"))
        add.clicked.connect(lambda: self._add_phrase_row(QuickPhrase("", "")))
        rem = QPushButton(tr("Remove selected"))
        rem.clicked.connect(lambda: self._remove_rows(self.phrase_table))
        row.addWidget(add)
        row.addWidget(rem)
        row.addStretch(1)
        lay.addLayout(row)
        lay.addWidget(
            _note(tr("A phrase can't use the talk key or the replay key. Phrases are per game."))
        )
        lay.addWidget(
            self._switch("phrase_suggestions", "Suggest quick phrases for sentences you repeat")
        )
        self.suggest_box = QVBoxLayout()
        lay.addLayout(self.suggest_box)
        self._fill_suggestions()
        return w

    def _corrections_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 8, 0, 0)
        lay.addWidget(self._switch("corrections_enabled", "Correction rules"))
        self.correction_table = self._table(["Find (English)", "Replace with"])
        self.correction_table.setColumnWidth(0, 220)
        lay.addWidget(self.correction_table)
        row = QHBoxLayout()
        add = QPushButton(tr("Add rule"))
        add.clicked.connect(lambda: self._add_correction_row(Correction("", "")))
        rem = QPushButton(tr("Remove selected"))
        rem.clicked.connect(lambda: self._remove_rows(self.correction_table))
        row.addWidget(add)
        row.addWidget(rem)
        row.addStretch(1)
        lay.addLayout(row)
        lay.addWidget(
            _note(
                tr(
                    "Whole words only, upper/lower case ignored, applied once (no loops). "
                    "Rules are per game."
                )
            )
        )
        lay.addSpacing(10)
        lay.addWidget(
            self._switch(
                "arabic_corrections_enabled", "Arabic dialect corrections before translating"
            )
        )
        self.arabic_table = self._table(["Dialect word", "Standard Arabic"])
        self.arabic_table.setColumnWidth(0, 220)
        lay.addWidget(self.arabic_table)
        row = QHBoxLayout()
        add = QPushButton(tr("Add rule"))
        add.clicked.connect(lambda: self._add_arabic_row(Correction("", "")))
        rem = QPushButton(tr("Remove selected"))
        rem.clicked.connect(lambda: self._remove_rows(self.arabic_table))
        row.addWidget(add)
        row.addWidget(rem)
        row.addStretch(1)
        lay.addLayout(row)
        lay.addWidget(
            _note(
                tr(
                    "Used when there is Arabic text to translate (Azure/Hybrid modes and the "
                    "quick text box). Comes with common dialect words; edit freely."
                )
            )
        )
        return w

    def _quicktext_page(self) -> QWidget:
        w, f = self._form()
        f.addRow(
            "", self._switch("quick_text_enabled", "Quick text box (type Arabic, get English)")
        )
        self.quick_text_key = _hotkey_combo()
        capture = QPushButton(tr("Press a key…"))
        capture.clicked.connect(lambda: self._begin_capture(self.quick_text_key))
        row = QHBoxLayout()
        row.addWidget(self.quick_text_key, 1)
        row.addWidget(capture)
        f.addRow(tr("Open with:"), row)
        self.quick_text_translator = _combo(QUICK_TEXT_TRANSLATORS)
        f.addRow(tr("Translate with:"), self.quick_text_translator)
        f.addRow(
            _note(
                tr(
                    "The box takes keyboard focus while it's open (you type into it); Esc closes "
                    "it and returns to the game. The offline model downloads once (~160 MB)."
                )
            )
        )
        return w

    def _learning_page(self) -> QWidget:
        w, f = self._form()
        f.addRow("", self._switch("learning_enabled", "Learning mode (save my phrasebook)"))
        book = QPushButton(tr("📘  Open my phrasebook"))
        book.clicked.connect(self.c.open_phrasebook)
        f.addRow("", book)
        f.addRow(
            _note(
                tr(
                    "Privacy: this is the only feature that saves what you said — the English "
                    "sentences (and Arabic, when available) — in a file on this PC. Nothing is "
                    "uploaded. Clear it any time from the phrasebook window."
                )
            )
        )
        return w

    def _fill_suggestions(self) -> None:
        while self.suggest_box.count():
            item = self.suggest_box.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        suggestions = self.c.phrase_suggestions()
        if not suggestions:
            return
        self.suggest_box.addWidget(QLabel(tr("Suggestions (sentences you say often):")))
        for text in suggestions[:6]:
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.addWidget(QLabel(text), 1)
            add = QPushButton(tr("Add"))
            add.clicked.connect(lambda _c=False, tx=text, r=row: self._accept_suggestion(tx, r))
            rl.addWidget(add)
            self.suggest_box.addWidget(row)

    def _accept_suggestion(self, text: str, row: QWidget) -> None:
        self._add_phrase_row(QuickPhrase("", text))
        row.hide()

    def _show_usage(self) -> None:
        from .usage import SPEECH_FREE_SECONDS, TRANSLATOR_FREE_CHARS

        u = self.c.usage.current
        self.usage_label.setText(
            tr(
                "Speech: {m:.0f} of {mt:.0f} free minutes ({sp:.0%}) · Translator: {c:,} of "
                "{ct:,} free characters ({tp:.0%})",
                m=u.speech_seconds / 60,
                mt=SPEECH_FREE_SECONDS / 60,
                sp=u.speech_fraction,
                c=u.translator_chars,
                ct=TRANSLATOR_FREE_CHARS,
                tp=u.translator_fraction,
            )
        )

    def _reset_usage(self) -> None:
        self.c.usage.reset()
        self._show_usage()

    def _export_profile(self) -> None:
        import json
        from dataclasses import asdict

        self._store_profile(self.cur)
        path, _ = QFileDialog.getSaveFileName(
            self, tr("Export profile"), f"{self.cur.name}.gametalk.json", "GameTalk (*.json)"
        )
        if not path:
            return
        data = {"gametalk_profile": 1, "profile": asdict(self.cur)}
        data["profile"]["exe_names"] = self.cur.exe_names  # keeps the game association
        try:
            pathlib.Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
            QMessageBox.information(
                self, tr("Export profile"), tr("Saved. Share this file with friends.")
            )
        except OSError as e:
            QMessageBox.warning(self, tr("Export profile"), str(e))

    def _import_profile(self) -> None:
        import json

        from .config import Profile, _from_dict, clean_corrections, clean_phrases, clean_vocabulary

        path, _ = QFileDialog.getOpenFileName(self, tr("Import profile"), "", "GameTalk (*.json)")
        if not path:
            return
        try:
            data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
            if not isinstance(data, dict) or "profile" not in data:
                raise ValueError("not a GameTalk profile")
            prof = _from_dict(Profile, data["profile"])
        except (OSError, ValueError) as e:
            QMessageBox.warning(
                self, tr("Import profile"), tr("This isn't a GameTalk profile file.") + f"\n{e}"
            )
            return
        base, name, n = prof.name.strip() or "Imported", prof.name.strip() or "Imported", 2
        while self.s.find_profile(name) is not None:  # never overwrite an existing profile
            name, n = f"{base} ({n})", n + 1
        prof.name = name
        prof.vocabulary = clean_vocabulary(prof.vocabulary)
        prof.corrections = clean_corrections(prof.corrections)
        prof.arabic_corrections = clean_corrections(prof.arabic_corrections)
        prof.quick_phrases = clean_phrases(prof.quick_phrases, reserved={prof.hotkey})
        self._store_profile(self.cur)
        self.s.profiles.append(prof)
        self.cur = prof
        self._fill_profiles()
        self._load_profile(prof)
        QMessageBox.information(self, tr("Import profile"), tr("Imported as “{name}”.", name=name))

    def _add_arabic_row(self, c: Correction) -> None:
        t = self.arabic_table
        r = t.rowCount()
        t.insertRow(r)
        for col, value in enumerate((c.find, c.replace)):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            t.setItem(r, col, item)

    def _gamepad_page(self) -> QWidget:
        w, f = self._form()
        f.addRow("", self._switch("gamepad_enabled", "Game controller button as push-to-talk"))
        self.pad_button = _combo([b for b in GAMEPAD_BUTTONS if b], translate=False)
        f.addRow(tr("Talk button:"), self.pad_button)
        self.pad_replay = _combo(GAMEPAD_BUTTONS, translate=False)
        self.pad_replay.setItemText(0, tr("(none)"))
        f.addRow(tr("Replay button:"), self.pad_replay)
        f.addRow(
            _note(
                tr(
                    "Xbox controllers work directly. PlayStation controllers work through "
                    "Steam Input or DS4Windows."
                )
            )
        )
        return w

    def _teammates_page(self) -> QWidget:
        from .teammates import output_devices

        w, f = self._form()
        f.addRow(
            "", self._switch("teammates.enabled", "Teammate subtitles (translate what you hear)")
        )
        self.team_device = QComboBox()
        self.team_device.addItem(tr("Windows default output"), "")
        for name in output_devices():
            self.team_device.addItem(name, name)
        f.addRow(tr("Listen to:"), self.team_device)
        self.team_recognizer = _combo(TEAM_RECOGNIZERS)
        f.addRow(tr("Recognition:"), self.team_recognizer)
        self.team_translator = _combo(TEAM_TRANSLATORS)
        self.team_translator.currentIndexChanged.connect(self._update_dependent_widgets)
        f.addRow(tr("Translate with:"), self.team_translator)
        self.team_target = _combo(TARGET_LANGUAGES)
        f.addRow(tr("Translate to:"), self.team_target)
        self.team_original = QCheckBox(tr("Also show the original English"))
        f.addRow("", self.team_original)
        self.team_sensitivity = _slider(0, 100)
        self.team_sensitivity.setToolTip(tr("Higher catches quieter voices (and more noise)."))
        f.addRow(tr("Sensitivity:"), self.team_sensitivity)
        self.team_pos = _combo(POSITION_LABELS)
        f.addRow(tr("Subtitle position:"), self.team_pos)
        self.team_offset_y = QSpinBox()
        self.team_offset_y.setRange(-4000, 4000)
        self.team_offset_y.setSuffix(" px")
        f.addRow(tr("Distance from edge:"), self.team_offset_y)
        self.team_font = QSpinBox()
        self.team_font.setRange(10, 48)
        self.team_font.setSuffix(" pt")
        f.addRow(tr("Font size:"), self.team_font)
        self.team_seconds = QSpinBox()
        self.team_seconds.setRange(1, 15)
        self.team_seconds.setSuffix(" s")
        f.addRow(tr("Display duration:"), self.team_seconds)
        f.addRow(
            _note(
                tr(
                    "Uses some CPU/GPU while people are talking. It pauses while you talk "
                    "and handles one sentence at a time."
                )
            )
        )
        return w

    def _games_page(self) -> QWidget:
        w, f = self._form()
        self.exe_names = QLineEdit()
        self.exe_names.setPlaceholderText(tr("e.g. cs2.exe, VALORANT-Win64-Shipping.exe"))
        f.addRow(tr("Game executables:"), self.exe_names)
        self.auto_switch = QCheckBox(
            tr("Switch to this profile automatically when the game is focused")
        )
        f.addRow("", self.auto_switch)
        f.addRow(
            _note(
                tr(
                    "Each profile keeps its own hotkey, microphone, model, overlay position, "
                    "size, opacity, vocabulary, quick phrases and correction rules. Find a "
                    "game's .exe name in Task Manager > Details."
                )
            )
        )
        return w

    # ---- data binding --------------------------------------------------------------------

    def _fill_profiles(self) -> None:
        self.profile_box.blockSignals(True)
        self.profile_box.clear()
        for p in self.s.profiles:
            self.profile_box.addItem(p.name)
        self.profile_box.setCurrentText(self.cur.name)
        self.profile_box.blockSignals(False)

    def _fill_mics(self, rescan: bool = False) -> None:
        if rescan:
            refresh_devices()
        current = self.mic_box.currentData() if self.mic_box.count() else self.cur.microphone
        self.mic_box.clear()
        self.mic_box.addItem(tr("Windows default"), "")
        names = list_input_devices()
        for name in names:
            self.mic_box.addItem(name, name)
        if current and current not in names:
            self.mic_box.addItem(tr("{name} (not connected)", name=current), current)
        _select(self.mic_box, current or "")

    def _feature_value(self, key: str) -> bool:
        if key.startswith("teammates."):
            return getattr(self.s.teammates, key.split(".", 1)[1])
        return getattr(self.s.features, key)

    def _set_feature_value(self, key: str, value: bool) -> None:
        if key.startswith("teammates."):
            setattr(self.s.teammates, key.split(".", 1)[1], value)
        else:
            setattr(self.s.features, key, value)

    def _load_global(self) -> None:
        from .runtime import autostart_enabled

        s, o, fe, tm = self.s, self.s.overlay, self.s.features, self.s.teammates
        _select(self.language_box, fe.ui_language)
        self.enabled_cb.setChecked(s.enabled)
        self.autostart_cb.setChecked(autostart_enabled())
        for key, boxes in self._switches.items():
            for cb in boxes:
                cb.blockSignals(True)
                cb.setChecked(self._feature_value(key))
                cb.blockSignals(False)
        _select(self.device_box, s.compute_device)
        self.show_arabic.setChecked(s.show_arabic)
        self.auto_switch.setChecked(s.auto_switch_profiles)
        _select(self.monitor_box, o.monitor)
        self.font_box.setCurrentFont(QFont(o.font_family))
        self._colors = {
            "text_color": o.text_color,
            "background_color": o.background_color,
            "accent_color": o.accent_color,
        }
        self._paint_color_buttons()
        self.outline_cb.setChecked(o.text_outline)
        self.radius.setValue(o.corner_radius)
        self.animation.setChecked(o.animation)
        _select(self.replay_box, fe.replay_hotkey)
        _select(self.quick_text_key, fe.quick_text_hotkey)
        _select(self.quick_text_translator, fe.quick_text_translator)
        self.sound_volume.setValue(fe.sound_volume)
        self.voice_sensitivity.setValue(fe.voice_sensitivity)
        _select(self.pad_button, fe.gamepad_button)
        _select(self.pad_replay, fe.gamepad_replay_button)
        _select(self.team_device, tm.device)
        _select(self.team_recognizer, tm.recognizer)
        _select(self.team_translator, tm.translator)
        _select(self.team_target, tm.target_language)
        self.team_original.setChecked(tm.show_original)
        self.team_sensitivity.setValue(tm.sensitivity)
        _select(self.team_pos, tm.position)
        self.team_offset_y.setValue(tm.offset_y)
        self.team_font.setValue(tm.font_size)
        self.team_seconds.setValue(tm.display_seconds)
        self._load_azure()

    def _load_azure(self) -> None:
        a = self.s.azure
        for field, stored in (
            (self.speech_key, a.speech_key),
            (self.translator_key, a.translator_key),
        ):
            field.clear()
            field.setPlaceholderText(tr(SAVED_PLACEHOLDER) if stored else tr("paste key here"))
        self.speech_region.setText(a.speech_region)
        self.translator_region.setText(a.translator_region)

    def _store_azure(self) -> None:
        a = self.s.azure
        if self.speech_key.text().strip():
            a.speech_key = protect(self.speech_key.text().strip())
        if self.translator_key.text().strip():
            a.translator_key = protect(self.translator_key.text().strip())
        a.speech_region = self.speech_region.text()
        a.translator_region = self.translator_region.text()

    def _form_credentials(self):
        """Credentials as currently shown: typed keys win over saved ones."""
        from .azure import AzureCredentials

        a = self.s.azure
        return AzureCredentials(
            speech_key=self.speech_key.text().strip() or unprotect(a.speech_key),
            speech_region=self.speech_region.text().strip(),
            translator_key=self.translator_key.text().strip() or unprotect(a.translator_key),
            translator_region=self.translator_region.text().strip(),
        )

    def _store_global(self) -> None:
        s, o, fe, tm = self.s, self.s.overlay, self.s.features, self.s.teammates
        fe.ui_language = self.language_box.currentData()
        s.enabled = self.enabled_cb.isChecked()
        for key, boxes in self._switches.items():
            self._set_feature_value(key, boxes[0].isChecked())
        s.compute_device = self.device_box.currentData()
        s.show_arabic = self.show_arabic.isChecked()
        s.auto_switch_profiles = self.auto_switch.isChecked()
        o.monitor = self.monitor_box.currentData()
        o.font_family = self.font_box.currentFont().family()
        o.text_color = self._colors["text_color"]
        o.background_color = self._colors["background_color"]
        o.accent_color = self._colors["accent_color"]
        o.text_outline = self.outline_cb.isChecked()
        o.corner_radius = self.radius.value()
        o.animation = self.animation.isChecked()
        fe.replay_hotkey = self.replay_box.currentData()
        fe.quick_text_hotkey = self.quick_text_key.currentData()
        fe.quick_text_translator = self.quick_text_translator.currentData()
        fe.sound_volume = self.sound_volume.value()
        fe.voice_sensitivity = self.voice_sensitivity.value()
        fe.gamepad_button = self.pad_button.currentData()
        fe.gamepad_replay_button = self.pad_replay.currentData()
        tm.device = self.team_device.currentData()
        tm.recognizer = self.team_recognizer.currentData()
        tm.translator = self.team_translator.currentData()
        tm.target_language = self.team_target.currentData()
        tm.show_original = self.team_original.isChecked()
        tm.sensitivity = self.team_sensitivity.value()
        tm.position = self.team_pos.currentData()
        tm.offset_y = self.team_offset_y.value()
        tm.font_size = self.team_font.value()
        tm.display_seconds = self.team_seconds.value()
        self._store_azure()

    def _load_profile(self, p: Profile) -> None:
        _select(self.mic_box, p.microphone)
        _select(self.speech_box, p.speech_provider)
        _select(self.locale_box, p.azure_locale)
        _select(self.model_box, p.model)
        _select(self.src_box, p.source_language)
        self.autodetect.setChecked(p.auto_detect_language)
        _select(self.provider_box, p.translation_provider)
        _select(self.target_box, p.target_language)
        self.gaming.setChecked(p.gaming_mode)
        self.vocab_on.setChecked(p.vocabulary_enabled)
        self.vocab.setPlainText("\n".join(p.vocabulary))
        _select(self.hotkey_box, p.hotkey)
        {"toggle": self.mode_toggle, "voice": self.mode_voice}.get(
            p.hotkey_mode, self.mode_push
        ).setChecked(True)
        _select(self.pos_box, p.overlay_position)
        self.off_x.setValue(p.overlay_offset_x)
        self.off_y.setValue(p.overlay_offset_y)
        self.font_size.setValue(p.font_size)
        self.max_width.setValue(p.max_width)
        self.bg_opacity.setValue(round(p.background_opacity * 100))
        self.text_opacity.setValue(round(p.text_opacity * 100))
        never = p.display_seconds == NEVER_HIDE
        self.never_hide.setChecked(never)
        self.duration.setValue(4 if never else p.display_seconds)
        self.duration.setEnabled(not never)
        self.exe_names.setText(", ".join(p.exe_names))
        self.phrase_table.setRowCount(0)
        for ph in p.quick_phrases:
            self._add_phrase_row(ph)
        self.correction_table.setRowCount(0)
        for c in p.corrections:
            self._add_correction_row(c)
        self.arabic_table.setRowCount(0)
        for c in p.arabic_corrections:
            self._add_arabic_row(c)
        self._update_dependent_widgets()

    def _store_profile(self, p: Profile) -> None:
        p.microphone = self.mic_box.currentData() or ""
        model = self.model_box.currentText().strip()
        p.model = model or "small"
        p.source_language = self.src_box.currentData()
        p.auto_detect_language = self.autodetect.isChecked()
        p.speech_provider = self.speech_box.currentData()
        p.azure_locale = self.locale_box.currentData()
        p.translation_provider = self.provider_box.currentData()
        p.target_language = self.target_box.currentData()
        p.gaming_mode = self.gaming.isChecked()
        p.vocabulary_enabled = self.vocab_on.isChecked()
        p.vocabulary = clean_vocabulary(self.vocab.toPlainText().splitlines())
        p.hotkey = self.hotkey_box.currentData()
        p.hotkey_mode = (
            "toggle"
            if self.mode_toggle.isChecked()
            else "voice"
            if self.mode_voice.isChecked()
            else "push"
        )
        p.overlay_position = self.pos_box.currentData()
        p.overlay_offset_x = self.off_x.value()
        p.overlay_offset_y = self.off_y.value()
        p.font_size = self.font_size.value()
        p.max_width = self.max_width.value()
        p.background_opacity = self.bg_opacity.value() / 100
        p.text_opacity = self.text_opacity.value() / 100
        p.display_seconds = NEVER_HIDE if self.never_hide.isChecked() else self.duration.value()
        p.exe_names = [e.strip().lower() for e in self.exe_names.text().split(",") if e.strip()]
        p.quick_phrases = [
            QuickPhrase(
                self.phrase_table.cellWidget(r, 0).currentData(),
                (self.phrase_table.item(r, 1).text() if self.phrase_table.item(r, 1) else ""),
            )
            for r in range(self.phrase_table.rowCount())
        ]
        p.corrections = [
            Correction(
                self.correction_table.item(r, 0).text() if self.correction_table.item(r, 0) else "",
                self.correction_table.item(r, 1).text() if self.correction_table.item(r, 1) else "",
            )
            for r in range(self.correction_table.rowCount())
        ]
        p.arabic_corrections = [
            Correction(
                self.arabic_table.item(r, 0).text() if self.arabic_table.item(r, 0) else "",
                self.arabic_table.item(r, 1).text() if self.arabic_table.item(r, 1) else "",
            )
            for r in range(self.arabic_table.rowCount())
        ]

    def _update_dependent_widgets(self, *_) -> None:
        """Enable only the options that apply to the current choices."""
        if not hasattr(self, "team_target"):
            return  # still building the pages
        azure_speech = self.speech_box.currentData() == AZURE
        # Whisper can't translate text, so Azure Speech implies Azure Translator.
        whisper_item = self.provider_box.model().item(self.provider_box.findData(LOCAL))
        whisper_item.setEnabled(not azure_speech)
        if azure_speech and self.provider_box.currentData() == LOCAL:
            _select(self.provider_box, AZURE)
        azure_translate = self.provider_box.currentData() == AZURE
        self.locale_box.setEnabled(azure_speech)
        for widget in (self.model_box, self.src_box, self.autodetect):
            widget.setEnabled(not azure_speech)
        if not azure_speech:
            self.src_box.setEnabled(not self.autodetect.isChecked())
        self.target_box.setEnabled(azure_translate)
        if not azure_translate:
            _select(self.target_box, "en")
        self.vocab_on.setEnabled(True)
        self.vocab.setEnabled(self.vocab_on.isChecked())
        if azure_speech:
            note = tr("Azure Speech → Azure Translator: your audio and its text are sent to Azure.")
        elif azure_translate:
            note = tr(
                "Whisper recognises Arabic locally; only the recognised text is sent to "
                "Azure Translator."
            )
        else:
            note = tr(
                "Everything runs locally; no audio or text leaves this PC. Vocabulary is a "
                "context hint, not a find-and-replace list."
            )
        self.translation_note.setText(note)
        local_team = self.team_translator.currentData() == "local"
        self.team_target.setEnabled(not local_team and self.team_translator.currentData() != "none")
        if local_team:
            _select(self.team_target, "ar")

    # ---- tables --------------------------------------------------------------------------

    def _add_phrase_row(self, ph: QuickPhrase) -> None:
        t = self.phrase_table
        r = t.rowCount()
        t.insertRow(r)
        key_box = _hotkey_combo(allow_none=True)
        _select(key_box, ph.key)
        t.setCellWidget(r, 0, key_box)
        t.setItem(r, 1, QTableWidgetItem(ph.text))

    def _add_correction_row(self, c: Correction) -> None:
        t = self.correction_table
        r = t.rowCount()
        t.insertRow(r)
        t.setItem(r, 0, QTableWidgetItem(c.find))
        t.setItem(r, 1, QTableWidgetItem(c.replace))

    @staticmethod
    def _remove_rows(table: QTableWidget) -> None:
        rows = sorted({i.row() for i in table.selectedIndexes()}, reverse=True)
        if not rows and table.currentRow() >= 0:
            rows = [table.currentRow()]
        for r in rows:
            table.removeRow(r)

    # ---- colours -------------------------------------------------------------------------

    def _paint_color_buttons(self) -> None:
        for attr, btn in self.color_buttons.items():
            color = QColor(self._colors[attr])
            fg = "#000000" if color.lightness() > 140 else "#ffffff"
            btn.setStyleSheet(f"background: {color.name()}; color: {fg};")

    def _pick_color(self, attr: str) -> None:
        color = QColorDialog.getColor(QColor(self._colors[attr]), self, tr("Choose a colour"))
        if color.isValid():
            self._colors[attr] = color.name()
            self._paint_color_buttons()

    # ---- profiles ------------------------------------------------------------------------

    def _on_profile_changed(self, _index: int) -> None:
        new = self.s.find_profile(self.profile_box.currentText())
        if new is None or new is self.cur:
            return
        self._store_profile(self.cur)
        self.cur = new
        self._load_profile(new)

    def _ask_name(self, title: str, default: str) -> str | None:
        name, ok = QInputDialog.getText(self, title, tr("Profile name:"), text=default)
        name = name.strip()
        if not ok or not name:
            return None
        if self.s.find_profile(name) is not None:
            QMessageBox.warning(self, title, tr("A profile with that name already exists."))
            return None
        return name

    def _new_profile(self) -> None:
        name = self._ask_name(tr("New profile"), "")
        if name is None:
            return
        self._store_profile(self.cur)
        p = copy.deepcopy(self.cur)
        p.name, p.exe_names = name, []
        self.s.profiles.append(p)
        self.cur = p
        self._fill_profiles()
        self._load_profile(p)

    def _rename_profile(self) -> None:
        name = self._ask_name(tr("Rename profile"), self.cur.name)
        if name is None:
            return
        self.cur.name = name
        self._fill_profiles()

    def _delete_profile(self) -> None:
        if len(self.s.profiles) <= 1:
            QMessageBox.information(
                self, tr("Delete profile"), tr("At least one profile is required.")
            )
            return
        self.s.profiles.remove(self.cur)
        self.cur = self.s.profiles[0]
        self._fill_profiles()
        self._load_profile(self.cur)

    # ---- actions -------------------------------------------------------------------------

    def _test_mic(self) -> None:
        self.test_btn.setEnabled(False)
        self.test_label.setText(tr("Listening… speak now"))
        self._level_timer.start()
        self.c.test_microphone(self.mic_box.currentData() or "")

    def _test_azure(self) -> None:
        from .azure import check_connection

        creds = self._form_credentials()
        self.azure_test_btn.setEnabled(False)
        self.azure_result.setText(tr("Testing…"))
        relay = self._relay

        def work():
            try:
                results = check_connection(creds)
            except Exception as e:  # never let the worker thread die silently
                results = [(False, f"Test failed: {type(e).__name__}")]
            relay.done.emit(results)

        threading.Thread(target=work, name="gametalk-azure-test", daemon=True).start()

    def _on_azure_tested(self, results) -> None:
        self.azure_test_btn.setEnabled(True)
        lines = []
        for ok, msg in results:
            head, sep, rest = msg.partition(" (")  # "Azure Translator: connected (مرحبا → Hi)"
            lines.append(f"{'✅' if ok else '❌'} {tr(head)}{sep}{rest}")
        self.azure_result.setText("\n".join(lines))

    def _clear_azure_keys(self) -> None:
        a = self.s.azure
        a.speech_key = a.translator_key = ""
        self._load_azure()
        self.azure_result.setText(tr("Saved keys will be removed when you click Save."))

    def _update_level(self) -> None:
        self.level.setValue(min(100, int(self.c.recorder.level * 140)))

    def _on_test_result(self, text: str) -> None:
        self._level_timer.stop()
        self.level.setValue(0)
        self.test_btn.setEnabled(True)
        self.test_label.setText(text)

    def _begin_capture(self, target: QComboBox) -> None:
        self._capture_target = target
        self.capture_btn.setText(tr("Press a key or mouse button (Esc cancels)"))
        self.c.hotkey.begin_capture()

    def _on_captured(self, name: str) -> None:
        self.capture_btn.setText(tr("Press a key…"))
        if name and self._capture_target is not None:
            _select(self._capture_target, name)
        self._capture_target = None

    def _preview_settings(self):
        self._store_global()
        self._store_profile(self.cur)
        return self.s.overlay, self.cur

    def _preview(self) -> None:
        style, profile = self._preview_settings()
        self.c.overlay.apply(style, profile)
        extra = ""
        if self.s.features.pronunciation_enabled:
            from .pronounce import to_arabic

            extra = to_arabic(PREVIEW_TEXT)
        self.c.overlay.show_result(PREVIEW_TEXT, extra)

    def _toggle_move(self, on: bool) -> None:
        style, profile = self._preview_settings()
        self.c.overlay.apply(style, profile)
        self.move_btn.setText(tr("Done") if on else tr("Move overlay"))
        self.c.overlay.set_move_mode(on)

    def _on_overlay_moved(self, x: int, y: int) -> None:
        self.off_x.setValue(x)
        self.off_y.setValue(y)
        self.cur.overlay_offset_x, self.cur.overlay_offset_y = x, y

    # ---- close ---------------------------------------------------------------------------

    def _cleanup(self) -> None:
        self._level_timer.stop()
        if self.move_btn.isChecked():
            self.move_btn.setChecked(False)
        self.c.hotkey.cancel_capture()
        for signal, slot in (
            (self.c.test_result, self._on_test_result),
            (self.c.hotkey.captured, self._on_captured),
        ):
            try:
                signal.disconnect(slot)
            except (RuntimeError, TypeError):
                pass
        if self._overlay_moved is not None:
            try:
                self._overlay_moved.disconnect(self._on_overlay_moved)
            except (RuntimeError, TypeError):
                pass

    def accept(self) -> None:
        from .runtime import autostart_enabled, set_autostart

        self._store_global()
        self._store_profile(self.cur)
        self.s.active_profile = self.cur.name
        if self.autostart_cb.isChecked() != autostart_enabled():
            try:
                set_autostart(self.autostart_cb.isChecked())
            except OSError:
                pass
        self._cleanup()
        self.c.apply_settings(validate(self.s))
        super().accept()

    def reject(self) -> None:
        self._cleanup()
        super().reject()
