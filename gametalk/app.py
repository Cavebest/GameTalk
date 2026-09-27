# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Controller: hotkey/gamepad -> recorder -> speech worker -> overlay. Owns the app state.

Every optional system (replay, history, quick phrases, corrections, pronunciation, gamepad,
teammate subtitles, …) is switched on/off from Settings.features and applied here.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum, auto

import numpy as np
from PySide6.QtCore import QObject, QTimer, Signal

from . import win32
from .audio import MAX_SECONDS, MIN_SECONDS, TARGET_RATE, MicrophoneError, is_digital_silence
from .azure import AzureCredentials
from .config import AZURE, GOOGLE, LOCAL, ConfigStore, Profile, Settings
from .credentials import unprotect
from .google import GoogleCredentials
from .hotkey import hotkey_vk
from .i18n import tr
from .phrasebook import Phrasebook, normalize
from .speech import EngineConfig, Job
from .translate import TeamRequest, TranslationRequest, TranslationResult
from .usage import UsageTracker

log = logging.getLogger(__name__)

TEST_SECONDS = 3
RELEASE_DEBOUNCE_MS = 40  # mouse-button chatter can produce release+press within a few ms
KEY_WATCH_MS = 150  # while recording: re-check the physical key in case a key-up was missed
KEY_WATCH_MISSES = 2  # consecutive "key is up" readings before we trust it
SUGGEST_AT = 3  # say the same sentence this often -> suggest making it a quick phrase


class Phase(Enum):
    IDLE = auto()
    RECORDING = auto()
    PROCESSING = auto()


@dataclass
class HistoryItem:
    text: str
    extra: str  # pronunciation / original text lines shown under it
    when: float
    kind: str = "you"  # "you" | "phrase" | "team"


class TrayOverlay:
    """Fallback used if the overlay window can't be created: results go to tray balloons."""

    def __init__(self, tray):
        self.tray = tray

    def apply(self, *_):
        pass

    def show_listening(self):
        pass

    def show_processing(self):
        pass

    def show_result(self, text, secondary=""):
        if self.tray:
            self.tray.notify(text)

    def show_error(self, message):
        if self.tray:
            self.tray.notify(message, error=True)

    def show_info(self, message, seconds=0):
        pass

    def hide_now(self):
        pass

    def set_move_mode(self, enabled):
        pass

    def set_recording_badge(self, on):
        pass


class Controller(QObject):
    test_result = Signal(str)  # settings dialog mic test outcome (translation or error)
    history_changed = Signal()

    def __init__(
        self,
        store: ConfigStore,
        settings: Settings,
        *,
        speech,
        recorder,
        hotkey,
        overlay,
        tray=None,
        gamepad=None,
        teammates=None,
        subtitles=None,
        voice=None,
        play_sound=None,
        key_is_down=win32.key_is_down,
        exclusive_fullscreen=win32.exclusive_fullscreen,
    ):
        super().__init__()
        self.store, self.settings = store, settings
        self.speech, self.recorder, self.hotkey = speech, recorder, hotkey
        self.overlay, self.tray = overlay, tray
        self.gamepad, self.teammates, self.subtitles = gamepad, teammates, subtitles
        self.voice = voice
        if play_sound is None:
            from .sounds import play as play_sound
        self._play_sound = play_sound
        data_dir = store.path.parent
        self.usage = UsageTracker(data_dir / "usage.json")
        self.phrasebook = Phrasebook(
            data_dir / "phrasebook.json", persistent=settings.features.learning_enabled
        )
        self._suggested: set[str] = set()
        self._quick_text = None
        self._diagnostics = None
        self._learn = None
        self._key_is_down = key_is_down
        self._exclusive_fullscreen = exclusive_fullscreen
        self.recording = False
        self.pending = 0  # push-to-talk / test jobs sent to the worker and not answered yet
        self.team_pending = 0  # teammate-subtitle jobs in flight (at most one)
        self.history: deque[HistoryItem] = deque(maxlen=settings.features.history_size)
        self._tag = "ptt"  # tag of the recording in progress
        self._ptt_source = "key"  # "key" | "pad": which device started the recording
        self._settings_dialog = None
        self._help_dialog = None
        self._creds_cache: tuple[tuple, AzureCredentials] | None = None
        self._google_cache: tuple[tuple, GoogleCredentials] | None = None
        self._pending_test = False
        self._fullscreen_warned = False
        self._key_misses = 0

        self._stop_timer = QTimer(self, singleShot=True, timeout=self._finish_recording)
        self._release_timer = QTimer(
            self, singleShot=True, interval=RELEASE_DEBOUNCE_MS, timeout=self._finish_recording
        )
        self._key_watch = QTimer(self, interval=KEY_WATCH_MS, timeout=self._check_key_still_down)

        hotkey.pressed.connect(lambda action: self._on_action(action, True, "key"))
        hotkey.released.connect(lambda action: self._on_action(action, False, "key"))
        hotkey.foreground_changed.connect(self.on_foreground_changed)
        hotkey.failed.connect(self._on_hotkey_failed)
        if gamepad is not None:
            gamepad.pressed.connect(lambda action: self._on_action(action, True, "pad"))
            gamepad.released.connect(lambda action: self._on_action(action, False, "pad"))
            gamepad.failed.connect(lambda m: self._notify(tr(m), error=True))
        if voice is not None:
            voice.segment.connect(self._on_voice_segment)
            voice.failed.connect(lambda m: self.overlay.show_error(tr(m)))
        if teammates is not None:
            teammates.segment.connect(self._on_team_segment)
            teammates.failed.connect(lambda m: self._notify(tr(m), error=True))
        speech.status.connect(self._on_speech_status)
        speech.ready.connect(self._on_speech_ready)
        speech.load_failed.connect(self._on_speech_load_failed)
        speech.finished.connect(self._on_finished)
        speech.failed.connect(self._on_failed)
        if tray is not None:
            tray.enabled_toggled.connect(self.set_enabled)
            tray.settings_requested.connect(lambda: self.open_settings())
            tray.help_requested.connect(lambda: self.open_help())
            tray.test_requested.connect(lambda: self.test_microphone())
            tray.reload_requested.connect(self.reload_model)
            tray.profile_selected.connect(self.set_active_profile)
            tray.history_selected.connect(self.show_history_item)
            tray.selftest_requested.connect(lambda: self.open_diagnostics())
            tray.phrasebook_requested.connect(lambda: self.open_phrasebook())
            tray.quit_requested.connect(self.quit)

    # ---- helpers -------------------------------------------------------------------------

    @property
    def profile(self) -> Profile:
        return self.settings.profile

    @property
    def features(self):
        return self.settings.features

    @property
    def phase(self) -> Phase:
        if self.recording:
            return Phase.RECORDING
        return Phase.PROCESSING if self.pending else Phase.IDLE

    def _notify(self, message: str, error: bool = False) -> None:
        if self.tray is not None and self.features.tray_notifications:
            self.tray.notify(message, error=error)

    def _team_uses_whisper(self) -> bool:
        tm = self.settings.teammates
        return tm.enabled and tm.recognizer == LOCAL

    def engine_config(self) -> EngineConfig:
        needs_whisper = self.profile.uses_whisper or self._team_uses_whisper()
        model = self.profile.model if needs_whisper else ""
        return EngineConfig(model=model, device=self.settings.compute_device)

    def azure_credentials(self) -> AzureCredentials:
        """Decrypted Azure keys (cached until the stored values change)."""
        a = self.settings.azure
        key = (a.speech_key, a.speech_region, a.translator_key, a.translator_region)
        if self._creds_cache is None or self._creds_cache[0] != key:
            creds = AzureCredentials(
                speech_key=unprotect(a.speech_key),
                speech_region=a.speech_region,
                translator_key=unprotect(a.translator_key),
                translator_region=a.translator_region,
            )
            self._creds_cache = (key, creds)
        return self._creds_cache[1]

    def google_credentials(self) -> GoogleCredentials:
        """Decrypted Google key (cached until the stored values change)."""
        g = self.settings.google
        key = (g.api_key, g.project_id, g.model, g.location)
        if self._google_cache is None or self._google_cache[0] != key:
            creds = GoogleCredentials(
                api_key=unprotect(g.api_key),
                project_id=g.project_id,
                model=g.model,
                location=g.location,
            )
            self._google_cache = (key, creds)
        return self._google_cache[1]

    def _google_problem(self) -> str:
        creds = self.google_credentials()
        if not creds.has_key:
            return tr("Add your Google Translate API key in Settings > Cloud keys.")
        if not creds.ready:
            return tr("Google Translation LLM needs your Google Cloud project ID.")
        return ""

    def _missing_azure_setup(self) -> str:
        """'' if the active profile's cloud services are configured, else what to fix."""
        p = self.profile
        if p.uses_google and (problem := self._google_problem()):
            return problem
        if not p.uses_azure:
            return ""
        creds = self.azure_credentials()
        if p.speech_provider == AZURE and not creds.has_speech:
            return tr("Add your Azure Speech key and region in Settings > Azure.")
        if p.translation_provider == AZURE and not creds.has_translator:
            return tr("Add your Azure Translator key in Settings > Azure.")
        return ""

    def _watch_foreground(self) -> bool:
        return self.settings.auto_switch_profiles and any(
            p.exe_names for p in self.settings.profiles
        )

    def hotkey_bindings(self) -> dict[str, str]:
        """action -> key for everything the keyboard/mouse can trigger right now."""
        f, p = self.features, self.profile
        bindings = {"ptt": p.hotkey}
        if f.replay_enabled and f.replay_hotkey:
            bindings["replay"] = f.replay_hotkey
        if f.quick_text_enabled and f.quick_text_hotkey:
            bindings["quicktext"] = f.quick_text_hotkey
        if f.quick_phrases_enabled:
            for i, phrase in enumerate(p.quick_phrases):
                if phrase.key:
                    bindings[f"phrase:{i}"] = phrase.key
        return bindings

    # ---- lifecycle -----------------------------------------------------------------------

    def start(self) -> None:
        self.overlay.apply(self.settings.overlay, self.profile)
        if self.tray is not None:
            self.tray.set_enabled(self.settings.enabled)
            self._refresh_tray_profiles()
            self._refresh_tray_history()
            self.tray.show()
        self.hotkey.start(self.hotkey_bindings(), self._watch_foreground())
        self.speech.load(self.engine_config())
        self._apply_features()

    def shutdown(self) -> bool:
        """Release mic, hotkey, worker and tray. False if the worker couldn't stop in time."""
        self._stop_recording_timers()
        if self.recorder.active:
            self.recorder.stop()
        self.hotkey.stop()
        if self.gamepad is not None:
            self.gamepad.stop()
        if self.teammates is not None:
            self.teammates.stop()
        if self.voice is not None:
            self.voice.stop()
        self.usage.save()
        self.phrasebook.save()
        clean = self.speech.shutdown()
        if self.tray is not None:
            self.tray.hide()
        self.overlay.hide_now()
        if self.subtitles is not None:
            self.subtitles.hide_now()
        return clean is not False

    def quit(self) -> None:
        from PySide6.QtWidgets import QApplication

        QApplication.quit()

    # ---- input actions -------------------------------------------------------------------

    def _on_action(self, action: str, down: bool, source: str) -> None:
        if action == "ptt":
            if down:
                self.on_pressed(source)
            else:
                self.on_released(source)
        elif not down or not self.settings.enabled:
            return
        elif action == "replay":
            self.replay_last()
        elif action == "quicktext":
            self.open_quick_text()
        elif action.startswith("phrase:"):
            self.show_phrase(int(action.split(":", 1)[1]))

    def on_pressed(self, source: str = "key") -> None:
        if not self.settings.enabled:
            return
        if self.profile.hotkey_mode == "voice":  # open mic: the talk key mutes/unmutes
            self.toggle_voice_mute()
            return
        if self.recording:
            if self._release_timer.isActive():
                self._release_timer.stop()  # bounce: release+press within a few ms, keep going
            elif self.profile.hotkey_mode == "toggle" and self._tag == "ptt":
                self._finish_recording()
            return
        # Recording never waits for the previous sentence: the worker queues jobs in order.
        self._ptt_source = source
        self._begin_recording("ptt")

    def on_released(self, source: str = "key") -> None:
        if (
            self.recording
            and self._tag == "ptt"
            and self.profile.hotkey_mode == "push"
            and source == self._ptt_source
        ):
            self._release_timer.start()

    def test_microphone(self, device: str | None = None) -> None:
        if self.recording:
            self.test_result.emit(tr("Busy — try again in a moment."))
            return
        self._begin_recording("test", device, TEST_SECONDS)

    def _begin_recording(self, tag: str, device: str | None = None, seconds: int = 0) -> bool:
        if self.speech.loading:
            self._report_error(tr("Speech model is still loading…"), tag)
            return False
        if not self.speech.loaded:
            self._report_error(tr(self.speech.last_error or "Speech model isn't loaded."), tag)
            return False
        missing = self._missing_azure_setup()
        if missing:  # tell the user before they talk, not after
            self._report_error(missing, tag)
            return False
        try:
            self.recorder.start(self.profile.microphone if device is None else device)
        except MicrophoneError as e:
            self._report_error(tr(str(e)), tag)
            return False
        except Exception:
            log.exception("Unexpected microphone failure")
            self._report_error(tr("Microphone error."), tag)
            return False
        self._tag, self.recording = tag, True
        if self.teammates is not None:
            self.teammates.paused = True  # don't subtitle while you're talking
        self._cue("start")
        self.overlay.show_listening()
        self._stop_timer.start((seconds or MAX_SECONDS) * 1000)
        watch = self.features.stuck_key_protection and self._ptt_source == "key"
        if tag == "ptt" and self.profile.hotkey_mode == "push" and watch:
            self._key_misses = 0
            self._key_watch.start()
        if self.profile.uses_azure:
            self.speech.prewarm(self.azure_credentials())
        self._warn_if_exclusive_fullscreen()
        return True

    def _check_key_still_down(self) -> None:
        """Safety net for a missed key-up (focus moved to an admin window, screen locked…)."""
        vk = hotkey_vk(self.profile.hotkey)
        if not self.recording or vk is None or self._key_is_down(vk):
            self._key_misses = 0
            return
        self._key_misses += 1
        if self._key_misses >= KEY_WATCH_MISSES:
            log.info("Hotkey release was missed; finishing the recording")
            self.hotkey.reset_state()
            self._finish_recording()

    def _warn_if_exclusive_fullscreen(self) -> None:
        if (
            not self.features.fullscreen_warning
            or self._fullscreen_warned
            or not self._exclusive_fullscreen()
        ):
            return
        self._fullscreen_warned = True
        log.info("Foreground app is in exclusive fullscreen; overlay can't draw over it")
        self._notify(
            tr(
                "Your game is in exclusive fullscreen, so the overlay can't appear on top. "
                "Switch the game to Borderless or Windowed mode."
            ),
            error=True,
        )

    def _stop_recording_timers(self) -> None:
        self._stop_timer.stop()
        self._release_timer.stop()
        self._key_watch.stop()

    def _finish_recording(self) -> None:
        if not self.recording:
            return
        self._stop_recording_timers()
        self.recording = False
        if self.teammates is not None:
            self.teammates.paused = False
        tag = self._tag
        audio = self.recorder.stop()
        self._cue("stop")
        if audio.size < MIN_SECONDS * TARGET_RATE:
            hint = tr("Hold {key} while you speak.", key=self.profile.hotkey)
            if tag == "test":
                self.test_result.emit(hint)
            self.overlay.show_info(hint, 2)
            return
        if is_digital_silence(audio):
            self._report_error(
                tr("No sound from the mic — is it muted? Pick another in Settings."), tag
            )
            return
        self._send_audio(audio, tag)

    def _request(self) -> TranslationRequest:
        p, f = self.profile, self.features
        return TranslationRequest(
            language=None if p.auto_detect_language else p.source_language,
            target_language=p.target_language,
            gaming_mode=p.gaming_mode,
            vocabulary=tuple(p.vocabulary) if p.vocabulary_enabled else (),
            show_source=self.settings.show_arabic,
            speech_provider=p.speech_provider,
            translation_provider=p.translation_provider,
            azure_locale=p.azure_locale,
            corrections=(
                tuple((c.find, c.replace) for c in p.corrections) if f.corrections_enabled else ()
            ),
            pronounce=f.pronunciation_enabled,
            trim_silence=f.trim_silence,
            phrases=(
                tuple(p.vocabulary)
                if f.azure_phrase_list and p.vocabulary_enabled and p.speech_provider == AZURE
                else ()
            ),
            source_corrections=(
                tuple((c.find, c.replace) for c in p.arabic_corrections)
                if f.arabic_corrections_enabled
                else ()
            ),
        )

    def _send_audio(self, audio, tag: str, speech_gate: bool = False) -> None:
        creds = self.azure_credentials() if self.profile.uses_azure else None
        self.pending += 1
        self.overlay.show_processing()
        job = Job(audio, self._request(), tag, creds, speech_gate=speech_gate)
        if self.profile.uses_google:
            job.google = self.google_credentials()
        self.speech.process(job)

    def _on_finished(self, tag: str, result: TranslationResult) -> None:
        self._count_usage(result)
        if tag == "team":
            self._on_team_finished(result)
            return
        if tag == "text":
            self._on_text_finished(result)
            return
        self.pending = max(0, self.pending - 1)
        if not result.text:
            if tag == "voice":  # open mic: noise that wasn't speech -> stay quiet
                self.overlay.hide_now()
                return
            self._cue("error")
            self._report_error(tr("Didn't catch that — try again."), tag)
            return
        extra = "\n".join(x for x in (result.pronunciation, result.source_text) if x)
        self.overlay.show_result(result.text, extra)
        self._remember(result.text, extra, "you")
        self._after_translation(result)
        if self.recording:  # user already started the next sentence
            self.overlay.set_recording_badge(True)
        if tag == "test":
            self.test_result.emit(result.text)

    def _on_failed(self, tag: str, message: str) -> None:
        if tag == "team":
            self.team_pending = 0
            log.info("Teammate subtitle failed")
            return
        if tag == "text":
            if self._quick_text is not None:
                self._quick_text.show_error(tr(message))
            return
        self._cue("error")
        self.pending = max(0, self.pending - 1)
        self._report_error(tr(message), tag)

    def _report_error(self, message: str, tag: str = "ptt") -> None:
        self.overlay.show_error(message)
        if self.recording:
            self.overlay.set_recording_badge(True)
        if tag == "test":
            self.test_result.emit(message)

    def cancel_recording(self) -> None:
        if self.recording:
            self._stop_recording_timers()
            self.recorder.stop()  # discarded
            self.recording = False
            if self.teammates is not None:
                self.teammates.paused = False
            self.overlay.hide_now()

    # ---- sounds, clipboard, usage, suggestions -------------------------------------------

    def _cue(self, cue: str) -> None:
        if self.features.sound_cues:
            self._play_sound(cue, self.features.sound_volume)

    def _count_usage(self, result: TranslationResult) -> None:
        if not self.features.azure_usage_tracking:
            return
        warnings = self.usage.add(
            result.azure_audio_seconds, result.azure_chars, result.google_chars
        )
        names = {"speech": "Azure Speech", "translator": "Azure Translator"}
        for w in warnings:
            service, level = w.split(":")
            name = names.get(service, "Google Translate")
            if float(level) >= 1.0:
                msg = tr("{name}: this month's free quota is used up.", name=name)
            else:
                msg = tr("{name}: 80% of this month's free quota used.", name=name)
            self._notify(msg, error=True)
            self.overlay.show_info(msg, 4)

    def _after_translation(self, result: TranslationResult) -> None:
        """Clipboard, phrasebook and quick-phrase suggestions for a finished translation."""
        f = self.features
        if f.copy_to_clipboard:
            from PySide6.QtGui import QGuiApplication

            QGuiApplication.clipboard().setText(result.text)
        entry = self.phrasebook.add(result.text, result.source_text)
        if (
            f.phrase_suggestions
            and entry is not None
            and entry.count >= SUGGEST_AT
            and normalize(result.text) not in self._suggested
            and normalize(result.text)
            not in {normalize(q.text) for q in self.profile.quick_phrases}
        ):
            self._suggested.add(normalize(result.text))
            self._notify(
                tr(
                    "You often say “{text}”. Add it as a quick phrase in Settings → Quick phrases.",
                    text=result.text,
                )
            )

    def phrase_suggestions(self) -> list[str]:
        """Sentences said at least SUGGEST_AT times that aren't quick phrases yet."""
        have = {normalize(q.text) for q in self.profile.quick_phrases}
        return [
            e.english
            for e in self.phrasebook.most_used(30)
            if e.count >= SUGGEST_AT and normalize(e.english) not in have
        ][:10]

    def add_quick_phrase(self, text: str, key: str = "") -> None:
        from .config import QuickPhrase, validate

        new = self.settings.clone()
        new.profile.quick_phrases.append(QuickPhrase(key, text))
        self.apply_settings(validate(new))

    # ---- open mic ---------------------------------------------------------------------------

    def toggle_voice_mute(self) -> None:
        if self.voice is None:
            return
        self.voice.muted = not self.voice.muted
        self._cue("stop" if self.voice.muted else "start")
        self.overlay.show_info(
            tr("Open mic: muted") if self.voice.muted else tr("Open mic: listening"), 2
        )

    def _on_voice_segment(self, audio) -> None:
        if not self.settings.enabled or self.profile.hotkey_mode != "voice" or self.recording:
            return
        if not self.speech.loaded or self._missing_azure_setup():
            return
        self._send_audio(audio, "voice", speech_gate=True)

    # ---- quick text box ---------------------------------------------------------------------

    def _text_translator(self) -> str:
        """auto: the profile's cloud translator if set up, then any cloud key, else offline."""
        choice = self.features.quick_text_translator
        if choice != "auto":
            return choice
        azure_ok = self.azure_credentials().has_translator
        google_ok = self.google_credentials().ready
        provider = self.profile.translation_provider
        if provider == GOOGLE and google_ok:
            return GOOGLE
        if provider == AZURE and azure_ok:
            return AZURE
        return AZURE if azure_ok else GOOGLE if google_ok else "local"

    def open_quick_text(self) -> None:
        if not self.features.quick_text_enabled:
            return
        if self._quick_text is None:
            from .quick_text import QuickTextBox

            self._quick_text = QuickTextBox()
            self._quick_text.submitted.connect(self.translate_text)
        self._quick_text.open_box()

    def translate_text(self, text: str) -> None:
        translator = self._text_translator()
        creds = self.azure_credentials() if translator == AZURE else None
        problem = ""
        if translator == AZURE and not creds.has_translator:
            problem = tr("Add your Azure Translator key in Settings > Azure.")
        elif translator == GOOGLE:
            problem = self._google_problem()
        if problem:
            if self._quick_text is not None:
                self._quick_text.show_error(problem)
            return
        req = self._request()
        job = Job(
            np.zeros(0, np.float32), req, "text", creds, text=text, text_translator=translator
        )
        if translator == GOOGLE:
            job.google = self.google_credentials()
        self.speech.process(job)

    def _on_text_finished(self, result: TranslationResult) -> None:
        extra = result.pronunciation
        if self._quick_text is not None:
            self._quick_text.show_result(result.text, extra)
        if result.text:
            self.overlay.show_result(result.text, extra)
            self._remember(result.text, extra, "you")
            self._after_translation(result)

    # ---- windows ----------------------------------------------------------------------------

    def open_diagnostics(self) -> None:
        from .diagnostics import DiagnosticsDialog

        if self._diagnostics is None:
            self._diagnostics = DiagnosticsDialog(self)
            self._diagnostics.finished.connect(lambda _r: setattr(self, "_diagnostics", None))
        else:
            self._diagnostics.run()
        self._diagnostics.show()
        self._diagnostics.raise_()
        self._diagnostics.activateWindow()

    def open_phrasebook(self) -> None:
        from .learn import LearnDialog

        if self._learn is None:
            self._learn = LearnDialog(self)
            self._learn.finished.connect(lambda _r: setattr(self, "_learn", None))
        self._learn.show()
        self._learn.raise_()
        self._learn.activateWindow()

    # ---- replay / history / quick phrases ------------------------------------------------

    def _remember(self, text: str, extra: str, kind: str) -> None:
        if not self.features.history_enabled:
            return
        self.history.append(HistoryItem(text, extra, time.time(), kind))
        self._refresh_tray_history()
        self.history_changed.emit()

    def replay_last(self) -> None:
        mine = [h for h in self.history if h.kind != "team"]
        if not mine:
            self.overlay.show_info(tr("Nothing to show yet."), 2)
            return
        self.overlay.show_result(mine[-1].text, mine[-1].extra)

    def show_history_item(self, index: int) -> None:
        items = list(self.history)
        if 0 <= index < len(items):
            self.overlay.show_result(items[index].text, items[index].extra)

    def show_phrase(self, index: int) -> None:
        phrases = self.profile.quick_phrases
        if not self.features.quick_phrases_enabled or not 0 <= index < len(phrases):
            return
        text = phrases[index].text
        extra = ""
        if self.features.pronunciation_enabled:
            from .pronounce import to_arabic

            extra = to_arabic(text)
        self.overlay.show_result(text, extra)
        self._remember(text, extra, "phrase")

    def _refresh_tray_history(self) -> None:
        if self.tray is not None:
            items = [h.text for h in self.history] if self.features.history_enabled else []
            self.tray.set_history(items)

    # ---- teammate subtitles --------------------------------------------------------------

    def _team_request(self) -> TeamRequest:
        tm = self.settings.teammates
        return TeamRequest(
            recognizer=tm.recognizer,
            translator=tm.translator,
            target_language=tm.target_language,
            show_original=tm.show_original,
        )

    def _on_team_segment(self, audio) -> None:
        tm = self.settings.teammates
        # Keep it light: one teammate sentence in flight, never while you're talking/processing.
        if (
            not tm.enabled
            or not self.settings.enabled
            or self.team_pending
            or self.recording
            or self.pending
            or not self.speech.loaded
        ):
            return
        creds = None
        if AZURE in (tm.recognizer, tm.translator):
            creds = self.azure_credentials()
            if (tm.recognizer == AZURE and not creds.has_speech) or (
                tm.translator == AZURE and not creds.has_translator
            ):
                return
        if tm.translator == GOOGLE and self._google_problem():
            return
        self.team_pending = 1
        job = Job(audio, TranslationRequest("en"), "team", creds, team=self._team_request())
        if tm.translator == GOOGLE:
            job.google = self.google_credentials()
        self.speech.process(job)

    def _on_team_finished(self, result: TranslationResult) -> None:
        self.team_pending = 0
        if not result.text or self.subtitles is None:
            return
        self.subtitles.show_result(result.text, result.source_text)
        self._remember(result.text, result.source_text, "team")

    def _team_profile(self) -> Profile:
        """The subtitle overlay reuses Overlay, configured through a Profile-shaped object."""
        tm = self.settings.teammates
        return Profile(
            name="teammates",
            overlay_position=tm.position,
            overlay_offset_x=tm.offset_x,
            overlay_offset_y=tm.offset_y,
            font_size=tm.font_size,
            display_seconds=tm.display_seconds,
            max_width=tm.max_width,
            background_opacity=self.profile.background_opacity,
            text_opacity=self.profile.text_opacity,
        )

    # ---- settings / profiles / features --------------------------------------------------

    def set_enabled(self, enabled: bool) -> None:
        self.settings.enabled = enabled
        if not enabled:
            self.cancel_recording()
        if self.tray is not None:
            self.tray.set_enabled(enabled)
        self.store.save(self.settings)

    def set_active_profile(self, name: str) -> None:
        if self.settings.find_profile(name) is None or name == self.settings.active_profile:
            return
        self.cancel_recording()
        self.settings.active_profile = name
        self._apply_profile()
        self.store.save(self.settings)
        log.info("Active profile switched")

    def on_foreground_changed(self, exe: str) -> None:
        if not self.settings.auto_switch_profiles or self.phase is not Phase.IDLE:
            return
        for p in self.settings.profiles:
            if exe in p.exe_names:
                if p.name != self.settings.active_profile:
                    self.set_active_profile(p.name)
                    self.overlay.show_info(tr("Profile: {name}", name=p.name), 2)
                return

    def apply_settings(self, new: Settings) -> None:
        language_changed = new.features.ui_language != self.settings.features.ui_language
        self.cancel_recording()
        self.settings = new
        self._apply_profile()
        self.hotkey.set_watch_foreground(self._watch_foreground())
        self._apply_features()
        if language_changed:
            self._apply_language()
        if self.tray is not None:
            self.tray.set_enabled(new.enabled)
        if not self.store.save(new):
            self.overlay.show_error(tr("Couldn't save settings."))

    def _apply_profile(self) -> None:
        self.hotkey.set_bindings(self.hotkey_bindings())
        self.overlay.apply(self.settings.overlay, self.profile)
        if self.subtitles is not None:
            self.subtitles.apply(self.settings.overlay, self._team_profile())
        if self.engine_config() != self.speech.config:
            self.speech.load(self.engine_config())
        self._refresh_tray_profiles()

    def _apply_features(self) -> None:
        """Start/stop optional systems to match the current settings (cheap when unchanged)."""
        f, tm = self.features, self.settings.teammates
        self.hotkey.set_bindings(self.hotkey_bindings())
        if self.history.maxlen != f.history_size:
            self.history = deque(self.history, maxlen=f.history_size)
        if not f.history_enabled:
            self.history.clear()
        self._refresh_tray_history()
        if f.pronunciation_enabled:
            from .pronounce import preload_async

            preload_async()
        if self.gamepad is not None:
            if f.gamepad_enabled:
                bindings = {"ptt": f.gamepad_button}
                if f.replay_enabled and f.gamepad_replay_button:
                    bindings["replay"] = f.gamepad_replay_button
                self.gamepad.set_bindings(bindings)
                self.gamepad.start()
            else:
                self.gamepad.stop()
        if self.subtitles is not None:
            self.subtitles.apply(self.settings.overlay, self._team_profile())
        if self.teammates is not None:
            if tm.enabled:
                self.teammates.start(tm.device, tm.sensitivity)
            else:
                self.teammates.stop()
                if self.subtitles is not None:
                    self.subtitles.hide_now()
        self.speech.prepare_local_mt(tm.enabled and tm.translator == "local")
        self.speech.prepare_text_mt(f.quick_text_enabled and self._text_translator() == "local")
        self.phrasebook.set_persistent(f.learning_enabled)
        if self.voice is not None:
            if self.profile.hotkey_mode == "voice" and self.settings.enabled:
                if not self.voice.active:
                    self.voice.start(self.profile.microphone, f.voice_sensitivity)
            else:
                self.voice.stop()
        if self.engine_config() != self.speech.config:
            self.speech.load(self.engine_config())

    def _apply_language(self) -> None:
        from PySide6.QtWidgets import QApplication

        from .i18n import apply_layout_direction, set_language

        set_language(self.features.ui_language)
        app = QApplication.instance()
        if app is not None:
            apply_layout_direction(app)
        if self.tray is not None:
            self.tray.retranslate()
            self._refresh_tray_profiles()
            self._refresh_tray_history()

    def _refresh_tray_profiles(self) -> None:
        if self.tray is not None:
            names = [p.name for p in self.settings.profiles]
            self.tray.set_profiles(names, self.settings.active_profile)

    def reload_model(self) -> None:
        self.speech.load(self.engine_config())
        self.overlay.show_info(tr("Reloading speech model…"))

    def reload_config(self) -> None:
        """Pick up changes another process (the launcher) wrote to config.json."""
        self.apply_settings(self.store.load())

    def status_text(self) -> str:
        if self.speech.loading:
            engine = "loading speech model…"
        elif self.speech.loaded:
            engine = self.speech.summary
        else:
            engine = self.speech.last_error or "speech engine not ready"
        p = self.profile
        state = "ready" if self.settings.enabled else "disabled"
        return f"{state}|{p.name}|{p.hotkey}|{p.mode}|{engine}"

    def handle_command(self, command: str) -> str:
        """IPC entry point (see ipc.py). Runs on the main thread."""
        if command == "status":
            return self.status_text()
        if command.startswith("settings"):
            _, _, tab = command.partition(":")
            QTimer.singleShot(0, lambda: self.open_settings(tab or None))
        elif command.startswith("help"):
            _, _, topic = command.partition(":")
            QTimer.singleShot(0, lambda: self.open_help(topic or None))
        elif command == "test":
            if self.speech.loading:
                self._pending_test = True  # run once the model is ready
                self.overlay.show_info(tr("Loading speech model… the mic test starts after."), 0)
            else:
                QTimer.singleShot(0, self.test_microphone)
        elif command == "reload":
            QTimer.singleShot(0, self.reload_config)
        elif command == "selftest":
            QTimer.singleShot(0, self.open_diagnostics)
        elif command == "phrasebook":
            QTimer.singleShot(0, self.open_phrasebook)
        elif command == "hello":
            self._notify(tr("GameTalk is already running (tray icon)."))
        elif command == "quit":
            QTimer.singleShot(100, self.quit)
        else:
            return "unknown"
        return "ok"

    def open_settings(self, tab: str | None = None) -> None:
        from .settings_dialog import SettingsDialog

        if self._settings_dialog is not None:
            if tab:
                self._settings_dialog.show_tab(tab)
            self._settings_dialog.showNormal()
            self._settings_dialog.raise_()
            self._settings_dialog.activateWindow()
            return
        dlg = SettingsDialog(self)
        if tab:
            dlg.show_tab(tab)
        self._settings_dialog = dlg
        dlg.finished.connect(self._on_settings_closed)
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

    def open_help(self, topic: str | None = None) -> None:
        from .help import HelpDialog

        if self._help_dialog is None:
            self._help_dialog = HelpDialog()
            self._help_dialog.finished.connect(lambda _r: setattr(self, "_help_dialog", None))
        if topic:
            self._help_dialog.show_topic(topic)
        self._help_dialog.show()
        self._help_dialog.raise_()
        self._help_dialog.activateWindow()

    def _on_settings_closed(self, _result: int) -> None:
        dlg, self._settings_dialog = self._settings_dialog, None
        self.overlay.apply(self.settings.overlay, self.profile)  # drop unsaved previews
        if dlg is not None:
            dlg.deleteLater()

    # ---- status ---------------------------------------------------------------------------

    def _on_speech_status(self, text: str) -> None:
        if self.tray is not None:
            self.tray.set_status(tr(text))
        if text.startswith("Downloading"):
            self._notify(tr("{what} This only happens once.", what=tr(text)))

    def _on_speech_ready(self, summary: str, note: str) -> None:
        hotkey = self.profile.hotkey
        if self.profile.mode == "hybrid":
            summary += " + Azure Translator"
        if self.tray is not None:
            self.tray.set_status(tr("Ready — hold {key} to talk", key=hotkey) + f"\n{summary}")
        if note:
            self._notify(tr(note), error=True)
            self.overlay.show_info(tr(note))
        if self._pending_test:
            self._pending_test = False
            QTimer.singleShot(300, self.test_microphone)

    def _on_speech_load_failed(self, message: str) -> None:
        self._pending_test = False
        log.error("Speech model unavailable")
        if self.tray is not None:
            self.tray.set_status(tr(message))
        self._notify(tr(message), error=True)
        self.overlay.show_error(tr(message))

    def _on_hotkey_failed(self, message: str) -> None:
        self._notify(tr(message), error=True)
        self.overlay.show_error(tr(message))
