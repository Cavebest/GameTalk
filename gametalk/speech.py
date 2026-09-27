# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""faster-whisper engine. The model is loaded once on a worker thread and reused.

Nothing runs while idle: the worker thread sleeps in its Qt event loop until a job arrives.
"""

from __future__ import annotations

import gc
import glob
import logging
import os
import sys
import threading
import time
from dataclasses import dataclass, field

import numpy as np
from PySide6.QtCore import QObject, QThread, Signal, Slot

from .audio import TARGET_RATE as SAMPLE_RATE
from .azure import AzureClient, AzureCredentials, AzureError
from .google import GoogleClient, GoogleCredentials, GoogleError
from .i18n import tr
from .local_mt import AR_EN, LocalTranslator, LocalTranslatorError
from .translate import (
    PipelineError,
    TeamRequest,
    TranslationRequest,
    TranslationResult,
    run_pipeline,
    run_team_pipeline,
    run_text_pipeline,
)

log = logging.getLogger(__name__)


class ModelError(Exception):
    """User-presentable model loading failure."""


@dataclass(frozen=True)
class EngineConfig:
    model: str = "small"  # "" = no local model needed (Azure Speech handles recognition)
    device: str = "auto"  # auto | cuda | cpu


@dataclass
class Job:
    audio: np.ndarray
    request: TranslationRequest
    tag: str = "ptt"
    azure: AzureCredentials | None = None
    team: TeamRequest | None = None  # set for teammate-subtitle jobs
    text: str | None = None  # set for quick-text jobs (typed Arabic)
    text_translator: str = "local"  # quick text: "local" | "azure" | "google"
    google: GoogleCredentials | None = None  # set when a Google translation is needed
    speech_gate: bool = False  # open mic: drop the clip unless it really contains speech
    started: float = field(default_factory=time.perf_counter)


_dll_dirs_added = False


def add_cuda_dll_dirs() -> None:
    """Expose cuBLAS/cuDNN DLLs from the optional nvidia-* pip wheels to ctranslate2."""
    global _dll_dirs_added
    if _dll_dirs_added or sys.platform != "win32":
        return
    _dll_dirs_added = True
    roots = {p for p in sys.path if p and os.path.isdir(os.path.join(p, "nvidia"))}
    if getattr(sys, "frozen", False):
        roots.add(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)))
    for root in roots:
        for d in glob.glob(os.path.join(root, "nvidia", "*", "bin")):
            try:
                os.add_dll_directory(d)
                os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
            except OSError:
                pass


def cuda_device_count() -> int:
    try:
        import ctranslate2

        return ctranslate2.get_cuda_device_count()
    except Exception as e:
        log.info("CUDA probe failed: %s", e)
        return 0


def _cpu_threads() -> int:
    # Leave most cores to the game.
    return max(1, min(4, (os.cpu_count() or 2) // 2))


def _resolve_model_path(name: str, on_status) -> str:
    if os.path.isdir(name):
        return name
    from faster_whisper.utils import download_model

    try:
        return download_model(name, local_files_only=True)
    except Exception:
        pass
    on_status("Downloading speech model…")
    log.info("Model %s not cached; downloading", name)
    try:
        return download_model(name)
    except Exception as e:
        log.error("Model download failed: %s", type(e).__name__)
        raise ModelError(
            tr(
                "Speech model '{name}' is missing and couldn't be downloaded. "
                "Connect to the internet once, or pick another model.",
                name=name,
            )
        ) from e


class WhisperBackend:
    """Owns one loaded WhisperModel. Not thread-safe; used only from the worker thread."""

    def __init__(self):
        self.model = None
        self.summary = ""

    def unload(self) -> None:
        self.model = None
        gc.collect()

    def load(self, cfg: EngineConfig, on_status=lambda s: None) -> str:
        """Load (and warm up) the model; returns a user-facing note ('' if all good)."""
        from faster_whisper import WhisperModel

        self.unload()
        path = _resolve_model_path(cfg.model, on_status)
        note = ""
        candidates: list[tuple[str, str]] = []
        if cfg.device in ("auto", "cuda"):
            add_cuda_dll_dirs()
            if cuda_device_count() > 0:
                candidates.append(("cuda", "float16"))
            elif cfg.device == "cuda":
                note = "No NVIDIA GPU/CUDA found — using CPU."
        candidates.append(("cpu", "int8"))

        on_status("Loading speech model…")
        for device, compute_type in candidates:
            t0 = time.perf_counter()
            try:
                model = WhisperModel(
                    path, device=device, compute_type=compute_type, cpu_threads=_cpu_threads()
                )
                self.model = model
                self._warmup()
            except Exception as e:
                self.model = None
                log.warning("Loading on %s/%s failed: %s", device, compute_type, e)
                if device == "cuda":
                    note = "GPU acceleration unavailable — using CPU."
                    continue
                raise ModelError("Couldn't load the speech model.") from e
            self.summary = f"{cfg.model} on {device.upper()} ({compute_type})"
            log.info("Loaded %s in %.1fs", self.summary, time.perf_counter() - t0)
            return note
        raise ModelError("Couldn't load the speech model.")

    def _warmup(self) -> None:
        # Run the encoder/decoder once (and load the VAD) so the first real utterance is fast.
        silence = np.zeros(SAMPLE_RATE // 2, np.float32)
        list(self.model.transcribe(silence, language="en", vad_filter=False, beam_size=1)[0])
        list(self.model.transcribe(silence, language="en", vad_filter=True, beam_size=1)[0])

    def decode(
        self, audio: np.ndarray, task: str, language: str | None, prompt: str | None
    ) -> tuple[str, str]:
        if self.model is None:
            raise ModelError("Speech model isn't loaded.")
        segments, info = self.model.transcribe(
            audio,
            task=task,
            language=language,
            initial_prompt=prompt,
            beam_size=1,
            best_of=1,
            temperature=(0.0, 0.2, 0.4),
            condition_on_previous_text=False,
            without_timestamps=True,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 400, "speech_pad_ms": 200},
        )
        texts = [
            s.text.strip()
            for s in segments
            if not (s.no_speech_prob > 0.6 and s.avg_logprob < -0.8)
        ]
        return " ".join(t for t in texts if t), info.language or ""


class _Worker(QObject):
    status = Signal(str)
    ready = Signal(object, str, str)  # config, summary, note
    load_failed = Signal(object, str)  # config, message
    finished = Signal(str, object)  # tag, TranslationResult
    failed = Signal(str, str)  # tag, message

    def __init__(self):
        super().__init__()
        self.backend = WhisperBackend()
        self.azure: AzureClient | None = None
        self.google: GoogleClient | None = None
        self.local_mt = LocalTranslator()  # EN->AR, loaded only if teammate subtitles use it
        self.local_ar_en = LocalTranslator(AR_EN)  # AR->EN, loaded only for the quick text box
        self.cancelled = threading.Event()  # set on app shutdown: skip whatever is queued

    def _azure_client(self, creds: AzureCredentials | None) -> AzureClient | None:
        """One client per credential set, so TLS connections are reused between sentences."""
        if creds is None:
            return None
        if self.azure is None or self.azure.creds != creds:
            if self.azure is not None:
                self.azure.close()
            self.azure = AzureClient(creds)
        return self.azure

    def _google_client(self, creds: GoogleCredentials | None) -> GoogleClient | None:
        if creds is None or not creds.has_key:
            return None
        if self.google is None or self.google.creds != creds:
            if self.google is not None:
                self.google.close()
            self.google = GoogleClient(creds)
        return self.google

    @Slot(object)
    def load(self, cfg: EngineConfig) -> None:
        if self.cancelled.is_set():
            return
        try:
            if not cfg.model:  # Azure Speech mode: free the GPU/RAM Whisper would hold
                self.backend.unload()
                self.backend.summary = "Azure Speech (cloud)"
                self.ready.emit(cfg, self.backend.summary, "")
                return
            note = self.backend.load(cfg, self.status.emit)
            self.ready.emit(cfg, self.backend.summary, note)
        except ModelError as e:
            self.load_failed.emit(cfg, str(e))
        except Exception:
            log.exception("Unexpected model load failure")
            self.load_failed.emit(cfg, "Couldn't load the speech model.")

    @Slot(object)
    def prewarm(self, creds: AzureCredentials) -> None:
        if self.cancelled.is_set():
            return
        client = self._azure_client(creds)
        if client is not None:
            client.prewarm(speech=creds.has_speech, translator=creds.has_translator)

    @Slot(bool)
    def prepare_local_mt(self, wanted: bool) -> None:
        """Load (download once) or free the offline EN->AR translator."""
        if self.cancelled.is_set():
            return
        if not wanted:
            self.local_mt.unload()
            return
        try:
            self.local_mt.load(self.status.emit)
        except LocalTranslatorError as e:
            self.failed.emit("team", str(e))

    @Slot(bool)
    def prepare_text_mt(self, wanted: bool) -> None:
        if self.cancelled.is_set():
            return
        if not wanted:
            self.local_ar_en.unload()
            return
        try:
            self.local_ar_en.load(self.status.emit)
        except LocalTranslatorError as e:
            self.failed.emit("text", str(e))

    def close(self) -> None:
        if self.azure is not None:
            self.azure.close()
            self.azure = None
        if self.google is not None:
            self.google.close()
            self.google = None

    @Slot(object)
    def process(self, job: Job) -> None:
        if self.cancelled.is_set():
            return
        try:
            req = job.request
            whisper = self.backend if self.backend.model is not None else None
            if job.text is not None:
                result = run_text_pipeline(
                    job.text,
                    req,
                    job.text_translator,
                    self._azure_client(job.azure),
                    self.local_ar_en,
                    google=self._google_client(job.google),
                )
                result.seconds = time.perf_counter() - job.started
                log.info("Quick text translated in %.2fs", result.seconds)
                self.finished.emit(job.tag, result)
                return
            if job.team is not None:
                from .teammates import is_speech

                result: TranslationResult = run_team_pipeline(
                    job.audio,
                    job.team,
                    whisper,
                    self._azure_client(job.azure),
                    self.local_mt,
                    speech_check=is_speech,
                    google=self._google_client(job.google),
                )
                result.seconds = time.perf_counter() - job.started
                log.info(
                    "Teammate audio %.1fs processed in %.2fs (empty=%s)",
                    job.audio.size / SAMPLE_RATE,
                    result.seconds,
                    not result.text,
                )
                self.finished.emit(job.tag, result)
                return
            if job.speech_gate:
                from .teammates import is_speech

                if not is_speech(job.audio):  # a cough, a keyboard, game sound: ignore quietly
                    self.finished.emit(job.tag, TranslationResult(text=""))
                    return
            result = run_pipeline(
                job.audio,
                req,
                whisper,
                self._azure_client(job.azure),
                google=self._google_client(job.google),
            )
            result.seconds = time.perf_counter() - job.started
            # Only timings are logged — never the speech content.
            log.info(
                "Processed %.1fs of audio in %.2fs (%s -> %s, lang=%s, empty=%s)",
                job.audio.size / SAMPLE_RATE,
                result.seconds,
                req.speech_provider,
                req.translation_provider,
                result.detected_language or "?",
                not result.text,
            )
            self.finished.emit(job.tag, result)
        except (ModelError, AzureError, GoogleError, PipelineError, LocalTranslatorError) as e:
            self.failed.emit(job.tag, str(e))
        except Exception as e:
            msg = str(e).lower()
            log.error("Translation failed: %s", type(e).__name__)
            if "out of memory" in msg:
                self.failed.emit(job.tag, "GPU out of memory — try a smaller model or CPU.")
            else:
                self.failed.emit(job.tag, "Translation failed — try again.")


class SpeechService(QObject):
    """Main-thread facade over the worker thread. All signals arrive on the main thread."""

    status = Signal(str)
    ready = Signal(str, str)
    load_failed = Signal(str)
    finished = Signal(str, object)
    failed = Signal(str, str)

    _load_requested = Signal(object)
    _process_requested = Signal(object)
    _prewarm_requested = Signal(object)
    _local_mt_requested = Signal(bool)
    _text_mt_requested = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config: EngineConfig | None = None
        self.loaded = False
        self.loading = False
        self.summary = ""
        self.last_error = ""
        self._thread = QThread()
        self._thread.setObjectName("gametalk-speech")
        self._worker = _Worker()
        self._worker.moveToThread(self._thread)
        self._load_requested.connect(self._worker.load)
        self._process_requested.connect(self._worker.process)
        self._prewarm_requested.connect(self._worker.prewarm)
        self._local_mt_requested.connect(self._worker.prepare_local_mt)
        self._text_mt_requested.connect(self._worker.prepare_text_mt)
        self._worker.status.connect(self.status)
        self._worker.ready.connect(self._on_ready)
        self._worker.load_failed.connect(self._on_load_failed)
        self._worker.finished.connect(self.finished)
        self._worker.failed.connect(self.failed)
        self._thread.start()

    def load(self, cfg: EngineConfig) -> None:
        self.config = cfg
        self.loaded = False
        self.loading = True
        self.last_error = ""
        self._load_requested.emit(cfg)

    def process(self, job: Job) -> None:
        self._process_requested.emit(job)

    def prepare_local_mt(self, wanted: bool) -> None:
        """Load (or free) the offline EN->AR model on the worker thread."""
        self._local_mt_requested.emit(wanted)

    def prepare_text_mt(self, wanted: bool) -> None:
        """Load (or free) the offline AR->EN model used by the quick text box."""
        self._text_mt_requested.emit(wanted)

    def prewarm(self, creds: AzureCredentials) -> None:
        """Called on hotkey press so Azure connections are open by the time the user lets go."""
        self._prewarm_requested.emit(creds)

    def shutdown(self, timeout_ms: int = 2000) -> bool:
        """Stop the worker. Returns False if a decode/request is still running after timeout_ms
        (the caller must then end the process instead of letting Qt destroy a live thread)."""
        self._worker.cancelled.set()
        self._thread.quit()
        if not self._thread.wait(timeout_ms):
            log.warning("Speech worker still busy at shutdown")
            return False
        self._worker.close()
        return True

    def _on_ready(self, cfg: EngineConfig, summary: str, note: str) -> None:
        if cfg != self.config:
            return  # a newer load was requested meanwhile; its own reply will follow
        self.loaded, self.loading, self.summary = True, False, summary
        self.ready.emit(summary, note)

    def _on_load_failed(self, cfg: EngineConfig, message: str) -> None:
        if cfg != self.config:
            return
        self.loaded, self.loading, self.last_error = False, False, message
        self.load_failed.emit(message)
