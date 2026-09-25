# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Open-mic mode: no key needed — GameTalk hears when you start and stop talking.

The microphone stays open while this mode is on (that's the trade-off; it's off by default).
Audio is cut into sentences by volume (same Segmenter as teammate subtitles); each sentence is
then checked for real speech before it is translated. Audio stays in memory only. The talk key
becomes a mute/unmute switch.
"""

from __future__ import annotations

import logging

import numpy as np
from PySide6.QtCore import QObject, Signal

from .audio import (
    TARGET_RATE,
    MicrophoneError,
    _preferred_hostapi,
    _sd,
    _wasapi_autoconvert,
    resolve_device,
)
from .teammates import BLOCK, Segmenter

log = logging.getLogger(__name__)


class VoiceListener(QObject):
    segment = Signal(object)  # np.ndarray, 16 kHz mono float32
    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stream = None
        self._seg: Segmenter | None = None
        self._pending = np.zeros(0, np.float32)
        self.muted = False
        self.paused = False  # e.g. while a mic test runs
        self.level = 0.0

    @property
    def active(self) -> bool:
        return self._stream is not None

    def start(self, device: str = "", sensitivity: int = 50) -> None:
        self.stop()
        self._seg = Segmenter(sensitivity)
        self._pending = np.zeros(0, np.float32)
        try:
            sd = _sd()
            index, info = resolve_device(device)
            extra = None
            rate = TARGET_RATE
            if info.get("hostapi") == _preferred_hostapi(sd):
                extra = _wasapi_autoconvert(sd)
            if extra is None:
                rate = int(info["default_samplerate"])
            self._rate = rate
            self._stream = sd.InputStream(
                device=index,
                samplerate=rate,
                channels=1,
                dtype="float32",
                blocksize=rate // 10,
                callback=self._callback,
                extra_settings=extra,
            )
            self._stream.start()
            log.info("Open mic started")
        except (MicrophoneError, Exception) as e:
            self._stream = None
            log.warning("Open mic failed: %s", type(e).__name__)
            self.failed.emit(str(e) if isinstance(e, MicrophoneError) else "Microphone error.")

    def stop(self) -> None:
        stream, self._stream = self._stream, None
        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass
            log.info("Open mic stopped")

    def _callback(self, indata, frames, _time, _status) -> None:
        mono = indata[:, 0] if indata.ndim == 2 else indata
        if self._rate != TARGET_RATE:
            from .audio import resample

            mono = resample(mono, self._rate)
        self.level = float(np.max(np.abs(mono))) if mono.size else 0.0
        if self.muted or self.paused or self._seg is None:
            self._pending = np.zeros(0, np.float32)
            return
        self._pending = np.concatenate([self._pending, mono.astype(np.float32)])
        while self._pending.size >= BLOCK:
            block, self._pending = self._pending[:BLOCK], self._pending[BLOCK:]
            out = self._seg.feed(block)
            if out is not None:
                self.segment.emit(out)
