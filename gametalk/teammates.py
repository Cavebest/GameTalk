# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Teammate subtitles: listen to what the PC plays (game / Discord voice) and cut it into
speech segments for translation.

Uses Windows' loopback capture of an output device, so nothing is injected into the game and no
virtual cable is needed. Runs only while the feature is enabled. A loud-enough stretch of audio
becomes a segment (0.4-10 s); the speech engine then decides whether it's really speech.
"""

from __future__ import annotations

import logging
import threading
import warnings

import numpy as np
from PySide6.QtCore import QObject, Signal

from .audio import TARGET_RATE

log = logging.getLogger(__name__)

BLOCK = TARGET_RATE // 10  # 100 ms
PRE_ROLL_BLOCKS = 3  # keep 300 ms before speech starts
END_SILENCE_BLOCKS = 6  # 600 ms quiet = end of the sentence
MIN_SPEECH_S = 0.3  # at least this much loud audio in a segment
MAX_SEGMENT_S = 10.0
POLL_S = 0.05  # we sleep between reads; soundcard's own wait loop would spin ~1000x/s
BUFFER_BLOCKS = 4  # 400 ms WASAPI buffer, so nothing is lost between our 50 ms wake-ups


def threshold_for(sensitivity: int) -> float:
    """0 (only loud voices) .. 100 (very quiet voices) -> RMS threshold (-25 .. -55 dBFS)."""
    db = -25.0 - 0.3 * max(0, min(100, sensitivity))
    return float(10 ** (db / 20))


class Segmenter:
    """Pure endpointing logic (testable without audio devices)."""

    def __init__(self, sensitivity: int = 50):
        self.threshold = threshold_for(sensitivity)
        self._pre: list[np.ndarray] = []
        self._cur: list[np.ndarray] = []
        self._quiet = 0
        self._loud = 0

    def feed(self, block: np.ndarray) -> np.ndarray | None:
        """Add one 100 ms block; returns a finished segment or None."""
        loud = float(np.sqrt(np.mean(block * block))) > self.threshold if block.size else False
        if not self._cur:
            if loud:
                self._cur = [*self._pre, block]
                self._quiet, self._loud = 0, 1
            else:
                self._pre = [*self._pre, block][-PRE_ROLL_BLOCKS:]
            return None
        self._cur.append(block)
        self._quiet = 0 if loud else self._quiet + 1
        self._loud += loud
        length = sum(b.size for b in self._cur) / TARGET_RATE
        if self._quiet >= END_SILENCE_BLOCKS or length >= MAX_SEGMENT_S:
            segment = np.concatenate(self._cur)
            enough = self._loud * BLOCK / TARGET_RATE >= MIN_SPEECH_S
            self._cur, self._pre, self._quiet, self._loud = [], [], 0, 0
            if enough:  # a click or a single gunshot isn't worth transcribing
                return segment
        return None


def output_devices() -> list[str]:
    try:
        import soundcard as sc

        return [s.name for s in sc.all_speakers()]
    except Exception as e:
        log.warning("Could not list output devices: %s", e)
        return []


class TeammateListener(QObject):
    segment = Signal(object)  # np.ndarray, 16 kHz mono float32
    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.device = ""
        self.sensitivity = 50
        self.paused = False  # e.g. while the user is talking with push-to-talk

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, device: str = "", sensitivity: int = 50) -> None:
        if self.running and device == self.device and sensitivity == self.sensitivity:
            return
        self.stop()
        self.device, self.sensitivity = device, sensitivity
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="gametalk-teammates", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(2.0)
        self._thread = None

    def _open(self):
        import soundcard as sc

        speaker = None
        if self.device:
            speaker = next((s for s in sc.all_speakers() if s.name == self.device), None)
        if speaker is None:
            speaker = sc.default_speaker()
        mic = sc.get_microphone(id=str(speaker.name), include_loopback=True)
        log.info("Listening to teammates on an output device")
        return mic.recorder(samplerate=TARGET_RATE, channels=1, blocksize=BLOCK * BUFFER_BLOCKS)

    def _read_available(self, rec) -> np.ndarray | None:
        """Sleep ~50 ms, then take whatever audio Windows has buffered (None if nothing).

        soundcard's blocking record() polls in ~1 ms steps; with the system timer at 1 ms
        (CUDA/Qt raise it) that alone costs ~5% of a core. Checking the packet size ourselves
        after a real sleep keeps the thread idle almost all the time.
        """
        probe = getattr(rec, "_capture_available_frames", None)
        if probe is None:  # different soundcard version: fall back to its blocking read
            return _mono(rec.record(numframes=BLOCK))
        self._stop.wait(POLL_S)
        parts = []
        while probe() > 0:
            parts.append(_mono(rec.record(numframes=None)))
        return np.concatenate(parts) if parts else None

    def _run(self) -> None:
        reported = False
        while not self._stop.is_set():
            try:
                seg = Segmenter(self.sensitivity)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")  # "data discontinuity" on silent outputs
                    with self._open() as rec:
                        reported = False
                        pending = np.zeros(0, np.float32)
                        while not self._stop.is_set():
                            chunk = self._read_available(rec)
                            if chunk is None:
                                continue
                            pending = np.concatenate([pending, chunk])
                            while pending.size >= BLOCK:
                                block, pending = pending[:BLOCK], pending[BLOCK:]
                                if self.paused:
                                    continue
                                out = seg.feed(block)
                                if out is not None:
                                    self.segment.emit(out)
            except Exception as e:
                log.warning("Teammate audio capture failed: %s", type(e).__name__)
                if not reported:
                    self.failed.emit("Can't listen to the selected output device.")
                    reported = True
                self._stop.wait(3.0)  # device unplugged / changed: retry quietly
        log.info("Teammate listener stopped")


def _mono(data: np.ndarray) -> np.ndarray:
    return (data[:, 0] if data.ndim == 2 else data).astype(np.float32, copy=False)


def is_speech(audio: np.ndarray) -> bool:
    """Silero VAD (bundled with faster-whisper, CPU): is there any real speech in the segment?
    Filters gunfire/music before anything is sent to Whisper or Azure."""
    try:
        from faster_whisper.vad import VadOptions, get_speech_timestamps

        stamps = get_speech_timestamps(audio, VadOptions(min_speech_duration_ms=250))
        return bool(stamps)
    except Exception as e:
        log.debug("VAD unavailable (%s); assuming speech", e)
        return True
