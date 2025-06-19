"""
Quick Techno Loop Player – PUNCHIER MIX (no extra libs)
=======================================================
Still just one Python file, still no external audio libraries – but now the
loop **hits harder** thanks to fatter kick, brighter hats, saw‑lead drive, and
***soft‑clip saturation*** on the master bus.

🔧 **Requirements**: only `numpy` (math) and std‑lib `wave/os/sys`
    pip install numpy

Usage: `python quick_techno_loop.py`
Produces `quick_loop.wav` (≈7 s @ 132 BPM) and auto‑opens it with your OS’s
default player.
"""
import numpy as np
import wave
import os
import sys

# ----------------------------------------------------- Config ------
BPM = 132
BARS = 4                  # 4 bars ≈ 7.3 s
SAMPLE_RATE = 44_100
BEATS_PER_BAR = 4
MASTER_DRIVE = 3.0        # <‑‑ raise for more saturation (2‑5)

secs_per_beat = 60 / BPM
TOTAL_SAMPLES = int(BARS * BEATS_PER_BAR * secs_per_beat * SAMPLE_RATE)

audio = np.zeros(TOTAL_SAMPLES, dtype=np.float32)

# ------------------------------------------------ Drum generators --

def kick():
    length = int(0.32 * SAMPLE_RATE)
    t = np.linspace(0, 0.32, length, False)
    freq = np.linspace(110, 40, length)
    body = np.sin(2 * np.pi * freq * t)
    click = np.sin(2 * np.pi * 2400 * t) * np.exp(-80 * t)
    env = np.exp(-10 * t)
    return ((body + click * 0.3) * env * 1.8).astype(np.float32)


def snare():
    length = int(0.23 * SAMPLE_RATE)
    noise = np.random.uniform(-1, 1, length)
    tone  = np.sin(2 * np.pi * 180 * np.linspace(0, 0.23, length))
    env   = np.exp(-25 * np.linspace(0, 1, length))
    return ((noise * 0.7 + tone * 0.5) * env).astype(np.float32)


def hat(closed=True):
    length = int((0.05 if closed else 0.3) * SAMPLE_RATE)
    noise = np.random.uniform(-1, 1, length)
    hp = np.convolve(noise, [-1, 1], mode="same")  # pseudo high‑pass
    env = np.exp(-60 * np.linspace(0, 1, length))
    amp = 0.45 if closed else 0.35
    return (hp * env * amp).astype(np.float32)

# --------------------------------------------- Acid bass generator --

def acid(freq, length_secs):
    length = int(length_secs * SAMPLE_RATE)
    t = np.linspace(0, length_secs, length, False)
    saw = 2 * (t * freq - np.floor(0.5 + t * freq))
    env = np.exp(-6 * t)
    return (np.tanh(saw * 2.5) * env * 0.8).astype(np.float32)

# ------------------------------------------------ Sequencing utils --

def add(sound, beat):
    start = int(beat * secs_per_beat * SAMPLE_RATE)
    end   = start + len(sound)
    if end > len(audio):
        sound = sound[: len(audio) - start]
    audio[start:start + len(sound)] += sound

# ------------------------------------------------ Pattern program ---
for bar in range(BARS):
    for beat in range(BEATS_PER_BAR):
        pos = bar * BEATS_PER_BAR + beat
        add(kick(), pos)                    # kick every beat
        if beat in (1, 3):                  # snare on 2 & 4
            add(snare(), pos)
        # closed hat (8th notes)
        for sub in (0, 0.5):
            add(hat(True), pos + sub)
        # open hat on last 16th
        add(hat(False), pos + 0.75)

# 16th‑note acid sequence – F A G C (down an octave)
scale = [65.41, 87.31, 77.78, 130.81]
step_len = secs_per_beat / 4
for idx in range(BARS * BEATS_PER_BAR * 4):
    add(acid(scale[idx % len(scale)], step_len), idx * 0.25)

# ------------------------------------------------ Mastering stage ---
# Soft‑clip saturation for louder, thicker sound
sat = np.tanh(audio * MASTER_DRIVE) / np.tanh(MASTER_DRIVE)

# Normalise to ‑1 dBFS headroom
sat /= np.max(np.abs(sat)) * 1.1
wave_int16 = (sat * 32767).astype(np.int16)

# ------------------------------------------------ Export / Play  ----
filename = "quick_loop.wav"
with wave.open(filename, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(wave_int16.tobytes())
print(f"Saved {filename}")

# auto‑open in default player
if sys.platform.startswith("win32"):
    os.startfile(filename)
elif sys.platform == "darwin":
    os.system(f"open '{filename}'")
else:
    os.system(f"xdg-open '{filename}'")
