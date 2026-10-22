#!/usr/bin/env python3
"""Build auditioned VO + ducked music mixes on the composition timeline.

Composition t=0 is take t=T0. Each bed is auto-levelled so the voice sits
CLEAR dB over the ducked bed in the 300-3400 Hz band, then the whole mix gets a
static gain to -14 LUFS plus a true-peak limiter (no loudnorm in the graph:
it eats the tail). Usage: python3 src/build-mix.py [bed-name ...]
"""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUSIC = ROOT.parents[1] / "assets/audio/music"
CFG = json.loads((ROOT / "reel.json").read_text())
T0, DUR, PAD = 0.0, float(CFG["duration"]), 2.0
SFX_DB = -9.0   # SFX sit under the voice
CLEAR = 13.0
BEDS = {k: tuple(v) for k, v in CFG["music"].items()}  # name: (file in assets/audio/music, window start s)
SR = 48000
L = DUR + PAD


def ff(*a):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *a], capture_output=True, text=True)
    if r.returncode: sys.exit(r.stderr)
    return r


def level(path, af=""):
    chain = (af + "," if af else "") + "volumedetect"
    r = subprocess.run(["ffmpeg", "-i", str(path), "-af", chain, "-f", "null", "-"], capture_output=True, text=True)
    return float(re.search(r"mean_volume: (-?[\d.]+)", r.stderr).group(1))


def lufs(path):
    r = subprocess.run(["ffmpeg", "-i", str(path), "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    return float(re.findall(r'"input_i"\s*:\s*"(-?[\d.]+)"', r.stderr)[-1])


tmp = ROOT / "src/mix-tmp"; tmp.mkdir(exist_ok=True)
vo = tmp / "vo-key.wav"  # VO on comp timeline, padded, written to a file (in-graph apad on a key can fail)
ff("-i", str(ROOT / "media/vo-clean.wav"), "-af",
   f"atrim=start={T0},asetpts=N/SR/TB,apad=whole_dur={L}", "-ar", str(SR), "-ac", "1", str(vo))
speech = "highpass=f=300,lowpass=f=3400"
# VO speech-band level measured over the spoken span only (comp 0.4 .. 36.8)
vo_band = level(vo, f"atrim=0.05:{DUR-2.0},{speech}")


def mix(name, bed_gain):
    f, st = BEDS[name]
    out = tmp / f"{name}-g{bed_gain:+.1f}.wav"
    ff("-i", str(vo), "-i", str(MUSIC / f), "-i", str(ROOT / "media/sfx.wav"), "-filter_complex",
       f"[1:a]atrim=start={st}:duration={L},asetpts=N/SR/TB,aresample={SR},pan=stereo|c0=c0|c1=c1,volume={bed_gain}dB[bed];"
       f"[0:a]asplit=2[key][v];[v]pan=stereo|c0=c0|c1=c0[vs];"
       f"[2:a]aresample={SR},pan=stereo|c0=c0|c1=c0,volume={SFX_DB}dB,apad=whole_dur={L}[fx];"
       f"[bed][key]sidechaincompress=threshold=0.06:ratio=4:attack=25:release=420:makeup=1[duck];"
       f"[vs][duck][fx]amix=inputs=3:normalize=0:duration=first,atrim=0:{DUR},asetpts=N/SR/TB,"
       f"afade=t=in:d=0.03,afade=t=out:st={DUR-1.6}:d=1.6", "-ar", str(SR), str(out))
    return out


def bed_only(name, bed_gain):
    f, st = BEDS[name]
    out = tmp / f"{name}-duckedbed.wav"
    ff("-i", str(vo), "-i", str(MUSIC / f), "-filter_complex",
       f"[1:a]atrim=start={st}:duration={L},asetpts=N/SR/TB,aresample={SR},volume={bed_gain}dB[bed];"
       f"[bed][0:a]sidechaincompress=threshold=0.06:ratio=4:attack=25:release=420:makeup=1,atrim=0.05:{DUR-2.0}",
       "-ar", str(SR), str(out))
    return out


names = sys.argv[1:] or list(BEDS)
for name in names:
    g = -12.0
    clearance = vo_band - level(bed_only(name, g), speech)
    g += clearance - CLEAR  # raise the bed into the available clearance
    m = mix(name, g)
    gain = -14.0 - lufs(m)
    final = ROOT / f"media/mix-{name}.wav"
    ff("-i", str(m), "-af", f"volume={gain:.2f}dB,alimiter=limit=0.841:level=disabled", "-ar", str(SR), str(final))
    tails = [level(final, f"atrim={DUR-x}:{DUR-x+0.3}") for x in (3, 2, 1.7)]
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(final)], capture_output=True, text=True).stdout)
    print(f"{name}: bed {g:+.1f} dB (clearance was {clearance:.1f}), master {gain:+.2f} dB, LUFS {lufs(final):.1f}, dur {dur:.2f}, tail {['%.0f' % t for t in tails]}")
