"""
Quick Techno Loop Player – no extra audio libs
==============================================
Generates a **10‑second (132 BPM) acid‑techno loop**, saves it as `quick_loop.wav`,
then opens the file in your OS’s default audio player — so you don’t need
`simpleaudio` or any C‑compiler‑requiring wheels. Perfect for a quick test
in VS Code.

🔧 **Requirements**  (built‑ins only: `wave`, `os`, `sys` are std‑lib)
    pip install numpy

Usage: `python quick_techno_loop.py`
"""
import numpy as np
import wave
import os
import sys

# --- Config ----------------------------------------------------------
BPM = 132
BARS = 4            # 4 bars ≈ 7.3 s
SAMPLE_RATE = 44100
BEATS_PER_BAR = 4

secs_per_beat = 60 / BPM
TOTAL_SAMPLES = int(BARS * BEATS_PER_BAR * secs_per_beat * SAMPLE_RATE)

audio = np.zeros(TOTAL_SAMPLES, dtype=np.float32)

# --- Basic drum synthesizers ----------------------------------------

def kick():
    length = int(0.3 * SAMPLE_RATE)
    t = np.linspace(0, 0.3, length, False)
    freq = np.linspace(100, 45, length)
    sig = np.sin(2 * np.pi * freq * t)
    env = np.exp(-12 * t)
    return (sig * env * 1.2).astype(np.float32)


def snare():
    length = int(0.2 * SAMPLE_RATE)
    noise = np.random.uniform(-1, 1, length)
    env = np.exp(-20 * np.linspace(0, 1, length))
    tone = np.sin(2 * np.pi * 200 * np.linspace(0, 0.2, length)) * 0.4
    return ((noise * 0.6 + tone) * env).astype(np.float32)


def hat(closed=True):
    length = int((0.06 if closed else 0.25) * SAMPLE_RATE)
    noise = np.random.uniform(-1, 1, length)
    env = np.exp(-40 * np.linspace(0, 1, length))
    return (noise * env * (0.3 if closed else 0.25)).astype(np.float32)

# --- Acid bass synthesizer ------------------------------------------

def acid(freq, length_secs):
    length = int(length_secs * SAMPLE_RATE)
    t = np.linspace(0, length_secs, length, False)
    saw = 2 * (t * freq - np.floor(0.5 + t * freq))
    env = np.exp(-5 * t)
    return (np.tanh(saw * 2) * env * 0.6).astype(np.float32)

# --- Sequencing helpers ---------------------------------------------

def add(sound, beat):
    start = int(beat * secs_per_beat * SAMPLE_RATE)
    end = start + len(sound)
    if end > len(audio):
        sound = sound[: len(audio) - start]
        end = len(audio)
    audio[start:end] += sound

# --- Program the pattern -------------------------------------------
for bar in range(BARS):
    for beat in range(BEATS_PER_BAR):
        beat_pos = bar * BEATS_PER_BAR + beat
        add(kick(), beat_pos)                    # kick every beat
        if beat in [1, 3]:                       # snare on 2 & 4
            add(snare(), beat_pos)
        # closed hat every 8th note
        for sub in [0, 0.5]:
            add(hat(True), beat_pos + sub)
        # open hat on the "a" (last 16th)
        add(hat(False), beat_pos + 0.75)

# Acid 16‑note pattern (F‑A‑G‑C)
pattern = [65.41, 87.31, 77.78, 130.81]  # Hz
step_len = secs_per_beat / 4
for step in range(BARS * BEATS_PER_BAR * 4):
    freq = pattern[step % len(pattern)]
    add(acid(freq, step_len), step * 0.25)

# --- Normalize & convert -------------------------------------------
max_amp = np.max(np.abs(audio))
wave_int16 = (audio / max_amp * 0.9 * 32767).astype(np.int16)

# --- Save to WAV ----------------------------------------------------
filename = "quick_loop.wav"
with wave.open(filename, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)  # 16‑bit
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(wave_int16.tobytes())
print(f"Saved {filename}")

# --- Open with the system default player ---------------------------
if sys.platform.startswith("win32"):
    os.startfile(filename)
elif sys.platform == "darwin":
    os.system(f"open '{filename}'")
else:
    os.system(f"xdg-open '{filename}'")
