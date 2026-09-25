# Copyright (c) 2026 Shkour Bashtawi (github.com/ShkourBashtawi). MIT License.
"""Tiny sound cues when recording starts/stops (useful when the overlay can't be seen).

Tones are generated in code (no sound files), ~80 ms, played asynchronously on the default
output. Failures are silent: a missing sound never breaks translation.
"""

from __future__ import annotations

import logging

import numpy as np

log = logging.getLogger(__name__)

RATE = 44100


def _tone(freqs: list[float], note_s: float = 0.045, volume: float = 0.4) -> np.ndarray:
    parts = []
    for f in freqs:
        t = np.arange(int(RATE * note_s)) / RATE
        wave = np.sin(2 * np.pi * f * t)
        fade = np.minimum(1.0, np.minimum(t, t[::-1]) / 0.006)  # click-free edges
        parts.append(wave * fade)
    return (np.concatenate(parts) * 0.35 * volume).astype(np.float32)


CUES = {
    "start": [660.0, 990.0],  # rising: listening
    "stop": [990.0, 660.0],  # falling: processing
    "error": [330.0, 247.0],
}


def play(cue: str, volume_percent: int = 40) -> None:
    if volume_percent <= 0 or cue not in CUES:
        return
    try:
        import sounddevice as sd

        sd.play(_tone(CUES[cue], volume=volume_percent / 100), RATE, blocking=False)
    except Exception as e:
        log.debug("Sound cue failed: %s", e)
