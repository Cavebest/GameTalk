# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Microphone capture. The stream is open only while push-to-talk is held; audio stays in RAM."""

from __future__ import annotations

import logging
import threading

import numpy as np

log = logging.getLogger(__name__)

TARGET_RATE = 16000
MAX_SECONDS = 30
MIN_SECONDS = 0.3


class MicrophoneError(Exception):
    """User-presentable microphone failure."""


def resample(audio: np.ndarray, src_rate: int, dst_rate: int = TARGET_RATE) -> np.ndarray:
    """Linear-interpolation resample of mono float32 audio (plenty for speech recognition)."""
    if src_rate == dst_rate or audio.size == 0:
        return audio.astype(np.float32, copy=False)
    n_out = int(round(audio.size * dst_rate / src_rate))
    if n_out <= 0:
        return np.zeros(0, np.float32)
    x_old = np.arange(audio.size, dtype=np.float64)
    x_new = np.linspace(0, audio.size - 1, n_out)
    return np.interp(x_new, x_old, audio).astype(np.float32)


def to_mono(block: np.ndarray) -> np.ndarray:
    return block if block.ndim == 1 else block.mean(axis=1)


def _sd():
    import sounddevice  # imported lazily so a broken PortAudio can't stop app startup

    return sounddevice


_open_streams = 0  # PortAudio must not be re-initialised while a stream is open


def refresh_devices() -> bool:
    """Re-scan audio devices (PortAudio caches the list at start-up, so a replugged USB mic or a
    new Windows default device is invisible until this runs). ~60 ms; skipped while recording."""
    if _open_streams:
        return False
    try:
        sd = _sd()
        sd._terminate()
        sd._initialize()
        log.info("Audio devices re-scanned")
        return True
    except Exception as e:
        log.warning("Audio device re-scan failed: %s", e)
        return False


def trim_silence(
    audio: np.ndarray, rate: int = TARGET_RATE, pad_ms: int = 300, frame_ms: int = 20
) -> np.ndarray:
    """Cut leading/trailing silence (used before uploading to Azure: less audio sent, lower
    cost and latency). Returns an empty array when nothing rises above the noise floor."""
    frame = max(1, rate * frame_ms // 1000)
    n = audio.size // frame
    if n < 3:
        return audio
    rms = np.sqrt(np.mean(audio[: n * frame].reshape(n, frame) ** 2, axis=1))
    noise = float(np.percentile(rms, 10))
    # 2x the noise floor, but never above -34 dBFS: clearly audible audio is always kept, even
    # when it's loud from the first to the last moment (no quiet part to learn the noise from).
    threshold = max(min(noise * 2.0, 0.02), 0.0025)
    loud = np.flatnonzero(rms > threshold)
    if loud.size == 0:
        return np.zeros(0, np.float32)
    pad = rate * pad_ms // 1000
    start = max(0, int(loud[0]) * frame - pad)
    end = min(audio.size, (int(loud[-1]) + 1) * frame + pad)
    return audio[start:end]


def _preferred_hostapi(sd) -> int | None:
    for i, api in enumerate(sd.query_hostapis()):
        if api["name"] == "Windows WASAPI":
            return i
    return None


def _wasapi_autoconvert(sd):
    """WASAPI settings letting Windows resample/downmix (kwarg name differs across versions)."""
    for kwargs in ({"auto_convert": True}, {"autoconvert": True}):
        try:
            return sd.WasapiSettings(**kwargs)
        except TypeError:
            continue
    return None


def list_input_devices() -> list[str]:
    """Input device names (WASAPI names on Windows: full length, no duplicates)."""
    try:
        sd = _sd()
        api = _preferred_hostapi(sd)
        names = []
        for dev in sd.query_devices():
            if dev["max_input_channels"] < 1:
                continue
            if api is not None and dev["hostapi"] != api:
                continue
            if dev["name"] not in names:
                names.append(dev["name"])
        return names
    except Exception as e:
        log.warning("Could not enumerate microphones: %s", e)
        return []


def resolve_device(name: str) -> tuple[int, dict]:
    """Map a configured device name ('' = default) to (index, info)."""
    try:
        sd = _sd()
        devices = sd.query_devices()
    except Exception as e:
        raise MicrophoneError("Audio system unavailable.") from e
    api = _preferred_hostapi(sd)
    if name:
        for i, dev in enumerate(devices):
            if dev["name"] == name and dev["max_input_channels"] > 0:
                if api is None or dev["hostapi"] == api:
                    return i, dev
        raise MicrophoneError("Selected microphone not found.")
    idx = -1
    if api is not None:
        idx = sd.query_hostapis(api)["default_input_device"]
    if idx is None or idx < 0:
        idx = sd.default.device[0]
    if idx is None or idx < 0:
        raise MicrophoneError("No microphone found.")
    return idx, devices[idx]


class Recorder:
    """Push-to-talk recorder: start() opens the device, stop() closes it and returns 16 kHz."""

    def __init__(self):
        self._stream = None
        self._chunks: list[np.ndarray] = []
        self._frames = 0
        self._max_frames = 0
        self._rate = TARGET_RATE
        self._lock = threading.Lock()
        self.level = 0.0  # 0..1 peak of the last block, for the level meter

    @property
    def active(self) -> bool:
        return self._stream is not None

    def start(self, device_name: str = "") -> None:
        if self._stream is not None:
            return
        try:
            self._open(device_name)
        except MicrophoneError:
            # Device list may be stale (mic replugged, default changed, resumed from sleep).
            if not refresh_devices():
                raise
            self._open(device_name)

    def _open(self, device_name: str) -> None:
        global _open_streams
        sd = _sd()
        index, info = resolve_device(device_name)
        self._chunks, self._frames, self.level = [], 0, 0.0
        stream = None
        # 1st choice: let the Windows audio engine convert to 16 kHz mono for us.
        attempts = []
        if info.get("hostapi") == _preferred_hostapi(sd):
            wasapi = _wasapi_autoconvert(sd)
            if wasapi is not None:
                attempts.append((TARGET_RATE, 1, wasapi))
        attempts.append((int(info["default_samplerate"]), 1, None))
        attempts.append(
            (int(info["default_samplerate"]), max(1, int(info["max_input_channels"])), None)
        )
        last_error: Exception | None = None
        for rate, channels, extra in attempts:
            try:
                stream = sd.InputStream(
                    device=index,
                    samplerate=rate,
                    channels=channels,
                    dtype="float32",
                    callback=self._callback,
                    extra_settings=extra,
                )
                self._rate = rate
                break
            except Exception as e:
                last_error = e
        if stream is None:
            log.error("Opening microphone failed: %s", last_error)
            raise MicrophoneError(
                "Can't open the microphone. It may be in use or blocked in "
                "Windows Privacy > Microphone."
            )
        self._max_frames = self._rate * MAX_SECONDS
        try:
            stream.start()
        except Exception as e:
            stream.close()
            log.error("Starting microphone failed: %s", e)
            raise MicrophoneError("Microphone access failed.") from e
        self._stream = stream
        _open_streams += 1

    def _callback(self, indata, frames, _time, _status) -> None:
        mono = to_mono(indata)
        self.level = float(np.max(np.abs(mono))) if mono.size else 0.0
        with self._lock:
            if self._frames >= self._max_frames:
                return
            self._chunks.append(mono.copy())
            self._frames += frames

    def stop(self) -> np.ndarray:
        global _open_streams
        stream, self._stream = self._stream, None
        if stream is not None:
            _open_streams = max(0, _open_streams - 1)
            try:
                stream.stop()
                stream.close()
            except Exception as e:
                log.warning("Closing microphone failed: %s", e)
        with self._lock:
            chunks, self._chunks, self._frames = self._chunks, [], 0
        self.level = 0.0
        if not chunks:
            return np.zeros(0, np.float32)
        audio = np.concatenate(chunks)[: self._rate * MAX_SECONDS]
        return resample(audio, self._rate)


def is_digital_silence(audio: np.ndarray) -> bool:
    """All-zero input usually means Windows privacy settings are blocking the mic."""
    return audio.size > 0 and float(np.max(np.abs(audio))) == 0.0
