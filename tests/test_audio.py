import numpy as np

from gametalk.audio import (
    MAX_SECONDS,
    Recorder,
    is_digital_silence,
    resample,
    to_mono,
)


def test_resample_lengths():
    assert resample(np.zeros(48000, np.float32), 48000).size == 16000
    assert resample(np.zeros(44100, np.float32), 44100).size == 16000
    same = np.ones(160, np.float32)
    assert resample(same, 16000) is same or np.array_equal(resample(same, 16000), same)
    assert resample(np.zeros(0, np.float32), 48000).size == 0


def test_resample_preserves_tone():
    t = np.arange(48000) / 48000
    tone = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    out = resample(tone, 48000)
    assert out.dtype == np.float32
    assert abs(float(np.max(np.abs(out))) - 1.0) < 0.01


def test_to_mono():
    stereo = np.array([[1.0, 0.0], [0.5, 0.5]], np.float32)
    assert np.allclose(to_mono(stereo), [0.5, 0.5])


def test_digital_silence():
    assert is_digital_silence(np.zeros(100, np.float32))
    assert not is_digital_silence(np.full(100, 1e-4, np.float32))
    assert not is_digital_silence(np.zeros(0, np.float32))


def test_recorder_caps_length_and_tracks_level():
    r = Recorder()
    r._rate = 16000
    r._max_frames = 16000 * MAX_SECONDS
    block = np.full((16000, 1), 0.25, np.float32)
    for _ in range(MAX_SECONDS + 5):
        r._callback(block, 16000, None, None)
    assert r.level == 0.25
    audio = r.stop()
    assert audio.size == 16000 * MAX_SECONDS
    assert r.level == 0.0


def test_stop_without_start_returns_empty():
    assert Recorder().stop().size == 0


class FakeSD:
    """Minimal sounddevice stand-in: the mic only 'appears' after PortAudio is re-initialised."""

    class PortAudioError(Exception):
        pass

    def __init__(self):
        self.inits = 0
        self.visible = False
        self.default = type("D", (), {"device": (0, -1)})()

    def _terminate(self):
        pass

    def _initialize(self):
        self.inits += 1
        self.visible = True  # e.g. the USB mic was plugged back in

    def query_hostapis(self, index=None):
        api = {"name": "Windows WASAPI", "default_input_device": 0}
        return api if index is not None else [api]

    def query_devices(self):
        if not self.visible:
            return []
        return [
            {"name": "USB Mic", "hostapi": 0, "max_input_channels": 1, "default_samplerate": 48000}
        ]

    def WasapiSettings(self, **kw):  # noqa: N802 (mirrors sounddevice)
        return object()

    def InputStream(self, **kw):  # noqa: N802
        return type(
            "S", (), {"start": lambda s: None, "stop": lambda s: None, "close": lambda s: None}
        )()


def test_replugged_mic_is_found_after_a_rescan(monkeypatch):
    import gametalk.audio as audio

    sd = FakeSD()
    monkeypatch.setattr(audio, "_sd", lambda: sd)
    r = audio.Recorder()
    r.start("USB Mic")  # stale list -> not found -> re-scan -> retry succeeds
    assert r.active and sd.inits == 1
    assert audio.refresh_devices() is False  # never re-init while a stream is open
    r.stop()
    assert audio.refresh_devices() is True


def test_missing_mic_still_fails_cleanly_after_rescan(monkeypatch):
    import pytest

    import gametalk.audio as audio

    sd = FakeSD()
    monkeypatch.setattr(audio, "_sd", lambda: sd)
    with pytest.raises(audio.MicrophoneError, match="not found"):
        audio.Recorder().start("Some Other Mic")
    assert sd.inits == 1  # one re-scan attempt, no loop


def test_trim_silence_keeps_speech_and_drops_silence():
    from gametalk.audio import trim_silence

    rng = np.random.default_rng(1)
    noise = (rng.standard_normal(16000) * 0.0008).astype(np.float32)
    tone = (0.1 * np.sin(np.arange(8000) / 16000 * 2 * np.pi * 200)).astype(np.float32)
    clip = np.concatenate([noise, tone, noise])
    out = trim_silence(clip)
    assert 8000 <= out.size <= 8000 + 2 * 4800 + 640  # speech + 300 ms padding each side
    assert trim_silence(noise).size == 0  # nothing to send
    short = np.zeros(100, np.float32)
    assert trim_silence(short) is short  # too short to judge: untouched


def test_trim_silence_keeps_audio_that_is_loud_throughout():
    from gametalk.audio import trim_silence

    loud = (0.2 * np.sin(np.arange(16000) / 5)).astype(np.float32)
    assert trim_silence(loud).size == loud.size
    rng = np.random.default_rng(3)
    room = (rng.standard_normal(16000) * 0.03).astype(np.float32)  # loud fan: never discarded
    assert trim_silence(room).size == room.size
