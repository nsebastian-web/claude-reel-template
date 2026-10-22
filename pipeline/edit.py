#!/usr/bin/env python3
"""Jump-cut your take into the tight edit.

Segments to KEEP come from reel.json ("segments": [[take_in, take_out, "what is said"], ...]),
chosen from forced alignment of the raw take, checked against silencedetect. Writes:
  media/face.mp4      graded H.264 picture, muted
  media/vo-clean.wav  cleaned voice, same clock
  src/edl.json        segments with their output start times (cuts drive punch-ins)
Run from the project dir: python3 src/edit.py
"""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import json as _json
CFG = _json.loads((Path(__file__).resolve().parents[1] / "reel.json").read_text())
SRC = CFG["source"]

SEG = [tuple(s) for s in CFG["segments"]]
FADE = 0.012  # de-click each audio splice

VOICE = ("highpass=f=80,afftdn=nr=18:nf=-30:tn=1,"
         "equalizer=f=240:t=q:w=1.1:g=-3,equalizer=f=520:t=q:w=1.4:g=-1.5,"
         "equalizer=f=3200:t=q:w=1.8:g=2.5,equalizer=f=7500:t=h:g=2.5,deesser=i=0.45,"
         "acompressor=threshold=-21dB:ratio=3:attack=12:release=180:makeup=3,"
         "acompressor=threshold=-14dB:ratio=2:attack=5:release=120,alimiter=limit=0.96,"
         "aresample=48000,loudnorm=I=-16:TP=-1.5:LRA=10,"
         "atrim=start=0.030,asetpts=PTS-STARTPTS,apad=pad_dur=0.030")  # chain latency is 30 ms
GRADE = "eq=contrast=1.07:saturation=1.06:gamma=0.98,unsharp=5:5:0.35"


def run(*a):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *a], capture_output=True, text=True)
    if r.returncode: sys.exit(r.stderr)


parts, edl, t = [], [], 0.0
for i, (a, b, said) in enumerate(SEG):
    d = round(b - a, 3)
    parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];"
                 f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d={FADE},afade=t=out:st={d-FADE}:d={FADE}[a{i}];")
    edl.append({"i": i, "src_in": a, "src_out": b, "out": round(t, 3), "dur": d, "said": said})
    t += d
n = len(SEG)
graph = "".join(parts) + "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a];[v]{GRADE},fps=30,format=yuv420p[vo]"
tmpa = ROOT / "src/edit-raw.wav"
run("-i", SRC, "-filter_complex", graph, "-map", "[vo]", "-an", "-c:v", "libx264", "-crf", "15", "-preset", "slow",
    "-g", "15", "-movflags", "+faststart", str(ROOT / "media/face.mp4"),
    "-map", "[a]", "-ac", "1", "-ar", "48000", str(tmpa))
run("-i", str(tmpa), "-af", VOICE, "-ar", "48000", "-ac", "1", str(ROOT / "media/vo-clean.wav"))
run("-i", str(ROOT / "media/vo-clean.wav"), "-ac", "1", "-ar", "16000", str(ROOT / "src/edit-16k.wav"))
json.dump({"total": round(t, 3), "segments": edl}, open(ROOT / "src/edl.json", "w"), indent=1)
print(f"edit: {n} segments, {t:.2f}s")
