#!/usr/bin/env python3
"""Map raw-take forced-aligned words through the EDL onto the edit clock.
Raw-take alignment agrees with silencedetect; aligning the jump-cut audio runs late,
so edit times are derived arithmetically: out = seg.out + (src - seg.src_in)."""
import json
from pathlib import Path
R = Path(__file__).resolve().parents[1]
W = json.load(open(R / "src/fa-raw.json")); E = json.load(open(R / "src/edl.json"))["segments"]
out = []
for w in W:
    mid = (w["start"] + w["end"]) / 2
    seg = next((s for s in E if s["src_in"] <= mid <= s["src_out"]), None)
    if not seg: print("cut:", w["text"]); continue
    m = lambda t: round(min(max(seg["out"] + t - seg["src_in"], seg["out"]), seg["out"] + seg["dur"]), 3)
    out.append({"text": w["text"], "start": m(w["start"]), "end": m(w["end"])})
json.dump(out, open(R / "src/fa-words.json", "w"), indent=1)
print(len(out), "words on the edit clock; last", out[-1])
