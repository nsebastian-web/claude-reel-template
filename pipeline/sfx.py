#!/usr/bin/env python3
"""Synthesize the SFX track from src/sfx-cues.json (written by build.py). Deterministic, no samples.
Run: ~/.cache/fa-venv/bin/python src/sfx.py  ->  media/sfx.wav (48 kHz mono, comp clock)"""
import json
import numpy as np, soundfile as sf
from pathlib import Path

R = Path(__file__).resolve().parents[1]
SR = 48000
DUR = float(json.load(open(R / "reel.json"))["duration"])
rng = np.random.default_rng(7)
t = lambda d: np.arange(int(d * SR)) / SR
env = lambda n, a, d: np.minimum(np.arange(n) / max(1, a * SR), 1) * np.exp(-np.arange(n) / (d * SR))


def lp(x, k):  # one-pole low-pass, k in (0,1]
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x): acc += k * (v - acc); y[i] = acc
    return y


def boom():
    x = t(0.9); f = 150 * np.exp(-x * 9) + 42
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(x), 0.002, 0.28)
    click = rng.standard_normal(len(x)) * env(len(x), 0.0005, 0.012) * 0.6
    return (body + click) * 0.9

def hit():
    x = t(0.35); f = 220 * np.exp(-x * 14) + 70
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(x), 0.001, 0.09) + lp(rng.standard_normal(len(x)), 0.35) * env(len(x), 0.0005, 0.03) * 0.5) * 0.6

def thud():
    x = t(0.5); f = 95 * np.exp(-x * 6) + 45
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(x), 0.001, 0.16) + lp(rng.standard_normal(len(x)), 0.2) * env(len(x), 0.0008, 0.05) * 0.8) * 0.85

def whoosh():
    d = 0.7; x = t(d); n = rng.standard_normal(len(x))
    k = 0.02 + 0.35 * np.sin(np.pi * x / d) ** 2           # filter sweeps open then shut
    y = np.empty_like(n); acc = 0.0
    for i, v in enumerate(n): acc += k[i] * (v - acc); y[i] = acc
    return y * np.sin(np.pi * x / d) ** 1.5 * 0.55

def pop():
    x = t(0.12); f = 900 * np.exp(-x * 40) + 380
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(x), 0.0008, 0.03) * 0.45

def key():
    x = t(0.05); return lp(rng.standard_normal(len(x)), 0.5) * env(len(x), 0.0003, 0.006) * 0.28

def click():
    x = t(0.08); return (lp(rng.standard_normal(len(x)), 0.6) * env(len(x), 0.0002, 0.008) + np.sin(2 * np.pi * 1600 * x) * env(len(x), 0.0005, 0.015) * 0.3) * 0.5

def tone(fs, d, dec, gain):
    x = t(d); return sum(np.sin(2 * np.pi * f * x) * (0.6 ** i) for i, f in enumerate(fs)) * env(len(x), 0.004, dec) * gain

def chime():
    a = tone([880, 1760], 0.5, 0.18, 0.22); b = tone([1318.5, 2637], 0.6, 0.22, 0.22)
    out = np.zeros(int(0.75 * SR)); out[:len(a)] += a; out[int(0.11 * SR):int(0.11 * SR) + len(b)] += b; return out

def ding():
    return sum(tone([f, f * 2.01], 1.1, 0.42, 0.13) for f in (1046.5, 1318.5, 1568))

def tick():
    return tone([2093], 0.12, 0.035, 0.22)

def glitch():
    out = np.zeros(int(0.5 * SR))
    for k, (s0, d) in enumerate([(0, .06), (.08, .04), (.14, .07), (.25, .05), (.33, .08)]):
        n = rng.standard_normal(int(d * SR)); n = np.round(n * 3) / 3            # crushed
        n *= np.sign(np.sin(2 * np.pi * (180 + 90 * k) * t(d)))                  # buzzy gate
        out[int(s0 * SR):int(s0 * SR) + len(n)] += n * 0.32
    return out

def rewind():
    d = 0.55; x = t(d); f = 300 + 2600 * (x / d) ** 2 + 120 * np.sin(2 * np.pi * 17 * x)
    w = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.18 + lp(rng.standard_normal(len(x)), 0.3) * 0.12
    return w * np.sin(np.pi * x / d)


def riser():  # noise + rising tone, peaks at its end (cue = the impact)
    d = 1.1; x = t(d); f = 180 + 1400 * (x / d) ** 2.2
    tone_ = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.16
    n = rng.standard_normal(len(x)); k = 0.03 + 0.5 * (x / d) ** 2
    y = np.empty_like(n); acc = 0.0
    for i, v in enumerate(n): acc += k[i] * (v - acc); y[i] = acc
    return (tone_ + y * 0.35) * (x / d) ** 2.5


GEN = {k: v for k, v in globals().items() if k in ("boom", "hit", "thud", "whoosh", "pop", "key", "click", "chime", "ding", "tick", "glitch", "rewind", "riser")}
OFF = {"whoosh": -0.38, "riser": -1.1}   # whoosh peaks on the wipe
track = np.zeros(int(DUR * SR))
for name, at in json.load(open(R / "src/sfx-cues.json")):
    s = GEN[name](); i = int((at + OFF.get(name, 0)) * SR)
    if i < 0: s = s[-i:]; i = 0
    track[i:i + len(s)] += s[:len(track) - i]
track /= max(1.0, np.abs(track).max() / 0.89)
sf.write(R / "media/sfx.wav", track.astype(np.float32), SR)
print("sfx.wav", round(len(track) / SR, 2), "s, peak", round(float(np.abs(track).max()), 3))
