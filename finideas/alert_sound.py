"""Synthesized bell alert with volume control (no extra audio deps)."""

from __future__ import annotations

import io
import logging
import math
import struct
import tempfile
import wave
from pathlib import Path

logger = logging.getLogger(__name__)

_RATE = 22050
_DURATION_S = 0.55
_CACHE: dict[int, Path] = {}


def _bell_samples(volume: float) -> bytes:
    """Bright metallic ding: partials + exponential decay + soft attack."""
    vol = max(0.0, min(1.0, float(volume)))
    n = int(_RATE * _DURATION_S)
    partials = (
        (988.0, 1.00, 6.5),
        (1480.0, 0.55, 9.0),
        (1976.0, 0.32, 12.0),
        (2960.0, 0.18, 16.0),
        (3952.0, 0.10, 22.0),
    )
    frames = bytearray()
    peak = 0.55 * vol
    for i in range(n):
        t = i / _RATE
        attack = min(1.0, t / 0.006)
        sample = 0.0
        for freq, amp, decay in partials:
            sample += amp * math.exp(-decay * t) * math.sin(2.0 * math.pi * freq * t)
        sample += 0.08 * math.exp(-18.0 * t) * math.sin(2.0 * math.pi * 4200.0 * t)
        sample *= attack * peak
        sample = max(-1.0, min(1.0, sample))
        frames += struct.pack("<h", int(sample * 32767.0))
    return bytes(frames)


def build_bell_wav(volume: float = 0.7) -> bytes:
    pcm = _bell_samples(volume)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(_RATE)
        wf.writeframes(pcm)
    return buf.getvalue()


def _wav_path_for_volume(volume: float) -> Path:
    """Cache one WAV file per volume step (0–100). winsound cannot SND_MEMORY+ASYNC."""
    key = max(0, min(100, int(round(float(volume) * 100))))
    cached = _CACHE.get(key)
    if cached is not None and cached.exists():
        return cached
    path = Path(tempfile.gettempdir()) / f"finviz_scanner_bell_{key}.wav"
    path.write_bytes(build_bell_wav(key / 100.0))
    _CACHE[key] = path
    return path


def play_bell(volume: float = 0.7) -> None:
    """Play a short bell ding at ``volume`` (0.0–1.0)."""
    if volume <= 0.001:
        return
    try:
        import winsound

        path = _wav_path_for_volume(volume)
        # Filename + async is required — SND_MEMORY|SND_ASYNC raises on Windows.
        winsound.PlaySound(
            str(path),
            winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
        )
    except Exception:
        logger.warning("Could not play bell alert", exc_info=True)
