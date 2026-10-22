#!/usr/bin/env python3
"""Generates index.html for "Arena" (nikcore.ai, 9:16, Nikhil on camera). See SPEC.md.

Edit here, never index.html. Run: python3 build.py
Clock = the jump-cut edit (src/edit.py). Words are raw-take forced alignments mapped
through the EDL (src/map-words.py), so picture, captions and voice share one clock.
Every label comes from the arena-skill README / strategies.json / rubric.md.
"""
import json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EDL = json.loads((ROOT / "src/edl.json").read_text())
DUR = 33.0
W, H = 1080, 1920
MIX = "media/mix.wav"
REPO = "github.com/Jakeschincariol/arena-skill"
CUTS = [s["out"] for s in EDL["segments"]]

# ------------------------------------------------------------------ words
WORDS = json.loads((ROOT / "src/fa-words.json").read_text())
for w in WORDS:
    w["s"], w["e"] = w["start"], w["end"]


def at(word, n=1):
    k = 0
    for w in WORDS:
        if w["text"].strip(".,!?:").lower() == word.lower():
            k += 1
            if k == n:
                return w["s"]
    raise KeyError(f"{word} #{n}")


B = {
    "bad": at("bad"), "answers1": at("answers"), "from": at("from"), "claude1": at("claude"),
    "try1": at("try"), "this": at("this"), "free": at("free"), "skill": at("skill"), "called": at("called"), "arena": at("arena"),
    "you": at("you", 2), "give": at("give"), "one1": at("one"), "task": at("task"), "and1": at("and"), "hundred1": at("hundred"),
    "claude2": at("claude", 2), "agents1": at("agents"), "all": at("all"), "try2": at("try", 2), "each1": at("each"),
    "one2": at("one", 2), "different": at("different"), "way": at("way"),
    "then1": at("then"), "pair": at("pair"), "up": at("up"), "fight": at("fight"),
    "they2": at("they", 2), "tear": at("tear"), "apart": at("apart"), "each2": at("each", 2), "others": at("other's"),
    "answers2": at("answers", 2), "and3": at("and", 3), "judge": at("judge"), "picks": at("picks"), "winner": at("winner"),
    "losers": at("losers"), "are": at("are", 2), "out": at("out"),
    "then2": at("then", 2), "loops": at("loops"), "again1": at("again"), "and4": at("and", 4), "again2": at("again", 2),
    "until": at("until"), "one3": at("one", 3), "answer": at("answer"), "left": at("left"),
    "tip": at("tip"), "use": at("use"), "quick": at("quick"), "mode": at("mode"), "hundred2": at("hundred", 2),
    "agents2": at("agents", 2), "eats": at("eats"), "lot": at("lot"), "tokens": at("tokens"),
    "link": at("link"), "pinned": at("pinned"), "comments": at("comments"), "no": at("no"), "need": at("need"),
    "comment": at("comment"),
}
LAST = WORDS[-1]["e"]

# full-frame takeovers: (in, out). Face moves into the LIVE facecam during these.
TK = {"arena": (B["arena"] - 0.04, CUTS[1] + 2.89), "grid": (B["hundred1"] - 0.04, CUTS[2]),
      "vs": (B["fight"] - 0.07, B["they2"]), "champ": (B["left"] - 0.07, B["tip"] - 0.02)}
TK["arena"] = (B["arena"] - 0.04, B["you"] - 0.02)
HEADLINE = [TK["arena"], TK["vs"], TK["champ"]]   # the takeover type IS the caption here

# scene windows in the stage (split layout)
SC = {
    "hook": (0, CUTS[1]), "term": (CUTS[1], TK["arena"][0] + 0.05), "task": (TK["arena"][1] - 0.02, TK["grid"][0] + 0.05),
    "pair": (CUTS[2], TK["vs"][0] + 0.05), "fight": (TK["vs"][1] - 0.02, B["then2"] - 0.06),
    "loop": (B["then2"] - 0.08, TK["champ"][0] + 0.05), "tip": (TK["champ"][1] - 0.02, CUTS[3]),
    "pin": (CUTS[3], B["comment"] + 0.62), "end": (B["comment"] + 0.58, DUR),
}


# ------------------------------------------------------------------ caption groups
def groups(maxc=20):
    phrases, cur = [], []
    for w in WORDS:
        if any(a - 0.02 <= w["s"] < b for a, b in HEADLINE):
            if cur: phrases.append(cur); cur = []
            continue
        if cur and any(cur[-1]["s"] < c <= w["s"] for c in CUTS[1:]):
            phrases.append(cur); cur = []
        cur.append(w)
        if w["text"][-1] in ".,!?:": phrases.append(cur); cur = []
    if cur: phrases.append(cur)
    out = []
    for ph in phrases:
        ln = sum(len(w["text"]) + 1 for w in ph) - 1
        target = ln / max(1, -(-ln // maxc))
        chunk, acc = [], 0
        for i, w in enumerate(ph):
            chunk.append(w); acc += len(w["text"]) + 1
            if acc >= target - 2 and len(ph) - i - 1 >= 2:
                out.append(chunk); chunk, acc = [], 0
        if chunk: out.append(chunk)
    return out


GROUPS = groups()
EMPH = {"bad", "answers", "claude?", "free", "hundred", "agents", "different", "way.", "tear", "apart", "judge", "winner.",
        "losers", "out.", "loops", "again", "one", "quick", "mode.", "tokens.", "pinned", "comments.", "no"}


def cap_html():
    h = []
    for gi, g in enumerate(GROUPS):
        ws = "".join(f'<span class="cw{" em" if w["text"].lower() in EMPH else ""}" id="w{gi}_{i}">{w["text"]}</span> ' for i, w in enumerate(g))
        h.append(f'<div class="cg" id="g{gi}">{ws.strip()}</div>')
    return "".join(h)


# ------------------------------------------------------------------ seeded randomness (no Math.random)
def mulberry(seed):
    a = [seed & 0xFFFFFFFF]
    def r():
        a[0] = (a[0] + 0x6D2B79F5) & 0xFFFFFFFF
        t = a[0]
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        t ^= (t + (((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296
    return r


# ------------------------------------------------------------------ shapes
def star(n, ro, ri, cx=50, cy=50, rot=-90):
    pts = []
    for k in range(n * 2):
        r = ro if k % 2 == 0 else ri
        a = math.radians(rot + k * 180 / n)
        pts.append(f"{cx + r * math.cos(a):.1f},{cy + r * math.sin(a):.1f}")
    return " ".join(pts)


SPARK = f'<svg viewBox="0 0 100 100" width="100%" height="100%"><polygon points="{star(8, 48, 12)}" fill="#D97757"/></svg>'
BURST = f'<svg viewBox="0 0 100 100" width="100%" height="100%"><polygon points="{star(16, 50, 40)}" fill="#FFD400" stroke="#000" stroke-width="3" stroke-linejoin="round"/></svg>'
SPARKHIT = f'<svg viewBox="0 0 100 100" width="100%" height="100%"><polygon points="{star(10, 50, 18)}" fill="#fff" stroke="#000" stroke-width="3"/></svg>'
CROWN = '<svg viewBox="0 0 120 80" width="100%" height="100%"><path d="M8 72 L14 18 L40 44 L60 6 L80 44 L106 18 L112 72 Z" fill="#FFD400" stroke="#000" stroke-width="6" stroke-linejoin="round"/><circle cx="60" cy="6" r="7" fill="#FF2D3D" stroke="#000" stroke-width="4"/></svg>'
PIN = '<svg viewBox="0 0 100 100" width="100%" height="100%"><g transform="rotate(35 50 50)"><path d="M34 8h32l-5 30 14 14H25l14-14z" fill="#FF2D3D" stroke="#000" stroke-width="5" stroke-linejoin="round"/><path d="M50 52v42" stroke="#000" stroke-width="6" stroke-linecap="round"/></g></svg>'
PINSM = '<svg viewBox="0 0 100 100" width="26" height="26"><g transform="rotate(35 50 50)"><path d="M34 8h32l-5 30 14 14H25l14-14z" fill="#8E8E8E"/><path d="M50 52v42" stroke="#8E8E8E" stroke-width="8" stroke-linecap="round"/></g></svg>'
CHECK = '<svg viewBox="0 0 24 24" width="100%" height="100%"><circle cx="12" cy="12" r="11" fill="#16A34A" stroke="#000" stroke-width="2"/><path d="M6.5 12.5l3.5 3.5 7.5-8" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>'

# 15 reasoning modes -> 15 token colours
PAL = ["#FF2D3D", "#2F6BFF", "#FFD400", "#22C55E", "#FF7A1A", "#B45CFF", "#00C2D1", "#FF5CA8", "#F4F1EA",
       "#7CDB3A", "#FFB020", "#5B7CFF", "#E23B3B", "#18B98C", "#D97757"]
REASONING = ["First principles", "Inversion", "Analogy", "Adversarial", "Constraint first", "Worked example", "Socratic",
             "Contrarian", "Systems thinking", "Decomposition", "Working backwards", "Probabilistic", "Dialectical",
             "Evidence first", "Expert panel"]


def token(cls="", color="#FF2D3D", idd="", extra=""):
    i = f' id="{idd}"' if idd else ""
    return f'<div class="tok {cls}"{i} style="--c:{color}"><i class="ey l"></i><i class="ey r"></i><i class="fl"></i>{extra}</div>'


# 10x10 grid, spawn order = distance from centre
GRID = []
TS, GAP = 68, 8
GX0, GY0 = (W - (10 * TS + 9 * GAP)) // 2, 486
for k in range(100):
    r, c = divmod(k, 10)
    d = math.hypot(r - 4.5, c - 4.5) / math.hypot(4.5, 4.5)
    GRID.append({"x": GX0 + c * (TS + GAP), "y": GY0 + r * (TS + GAP), "c": PAL[(k * 7 + r) % 15], "d": round(d * 0.7, 3)})
TAGS = [(23, "FIRST PRINCIPLES"), (67, "CONTRARIAN"), (41, "INVERSION"), (86, "EDGE CASES FIRST"), (17, "SOCRATIC"), (58, "WORKING BACKWARDS")]

rnd = mulberry(11)
SHARDS = [{"x": (i % 4) * 50, "y": (i // 4) * 50, "vx": round((rnd() - 0.5) * 520 + ((i % 4) - 1.5) * 60, 1),
           "vy": round(260 + rnd() * 380, 1), "r": round((rnd() - 0.5) * 540, 1)} for i in range(16)]
rnd = mulberry(5)
CONF = []
for i in range(44):
    a = rnd() * math.tau; sp = 380 + rnd() * 520
    CONF.append({"vx": round(math.cos(a) * sp, 1), "vy": round(math.sin(a) * sp - 260, 1), "r": round((rnd() - 0.5) * 900, 1),
                 "c": ["#FF2D3D", "#2F6BFF", "#000", "#fff", "#22C55E"][i % 5], "w": 14 + int(rnd() * 16), "h": 22 + int(rnd() * 22)})

ATTACKS = [(B["tear"], "L", "MAJOR"), (B["apart"], "R", "MINOR"), (B["each2"], "L", "FATAL"), (B["others"], "R", "MAJOR"), (B["answers2"], "L", "MAJOR")]
RUBRIC = [("Correctness", 30), ("Completeness", 25), ("Robustness", 20), ("Specificity", 15), ("Clarity", 10)]
LOOP = [(B["then2"], 100, 1), (B["loops"], 50, 2), (B["again1"], 25, 3), (B["and4"], 13, 4), (B["again2"], 7, 5), (B["until"], 4, 6), (B["one3"], 2, 7)]


def chars(text, cls):
    return "".join(f'<span class="{cls}">{c if c != " " else "&nbsp;"}</span>' for c in text)


def clip(idd, a, b, track, cls="", inner="", tag="section"):
    return f'<{tag} id="{idd}" class="clip {cls}" data-start="{a:.3f}" data-duration="{b - a:.3f}" data-track-index="{track}">{inner}</{tag}>'


# ------------------------------------------------------------------ scenes
def s_hook():
    return f"""
<div class="lbl">// CLAUDE'S BAD ANSWERS</div>
<div class="chat" id="chat">
  <div class="ubub">Write a headline for my pricing page</div>
  <div class="arow"><span class="spk">{SPARK}</span><div class="stk rep"><span id="rep1">Pricing that works for you.</span><span id="rep2">Simple pricing for everyone.</span></div></div>
  <div class="ubub sm" id="retry">try again</div>
</div>
<div class="stamp" id="st1">BAD ANSWER</div>
<div class="stamp s2" id="st2">AGAIN?!</div>"""


def s_term():
    return f"""
<div class="lbl">// TRY THIS</div>
<div class="term" id="term1">
  <div class="tbar"><i></i><i></i><i></i><span>claude</span></div>
  <div class="tline"><span class="pr">&gt;</span> <span id="tcmd">{chars("/arena", "tc")}</span><i class="caret" id="caret1"></i></div>
  <div class="tauto" id="tauto"><b>/arena</b>&nbsp;&nbsp;make 100 agents compete on your task</div>
</div>
<div class="burst" id="free"><div class="bsh">{BURST}</div><div class="btx"><b>FREE</b></div></div>
<div class="chip" id="chip">CLAUDE CODE SKILL</div>"""


def s_task():
    return f"""
<div class="lbl">// ONE TASK</div>
<div class="ticket" id="ticket"><div class="tk-l">TASK</div><div class="tk-r">Write the headline for our pricing page</div></div>
<div class="badge1" id="one1">1</div>
<div class="x100" id="x100">&times;100</div>"""


def s_pair():
    return f"""
<div class="lbl">// ROUND 1 &middot; MATCH 1</div>
<div class="fighter" id="pL">{token("big", "#FF2D3D")}<div class="np"><b>A017</b><span>CONTRARIAN</span></div></div>
<div class="fighter" id="pR">{token("big", "#2F6BFF")}<div class="np"><b>A042</b><span>FIRST PRINCIPLES</span></div></div>"""


def s_fight():
    atk = "".join(f'<div class="atk {k.lower()}" id="atk{i}">{k}</div><div class="hspark" id="hs{i}">{SPARKHIT}</div>' for i, (_, _, k) in enumerate(ATTACKS))
    rows = "".join(f'<div class="rrow" id="rr{i}"><span class="rn">{n}</span><span class="rw">&times;{w}</span><span class="rc">{CHECK}</span></div>' for i, (n, w) in enumerate(RUBRIC))
    shards = "".join(f'<i class="shard" id="sh{i}" style="left:{s["x"]}px;top:{s["y"]}px"></i>' for i, s in enumerate(SHARDS))
    return f"""
<div class="hud">
  <div class="hb L"><div class="hn">A017 &middot; CONTRARIAN</div><div class="bar"><i class="fill" id="hpL"></i></div></div>
  <div class="hr">R1</div>
  <div class="hb R"><div class="hn">FIRST PRINCIPLES &middot; A042</div><div class="bar"><i class="fill" id="hpR"></i></div></div>
</div>
<div class="fz" id="fL">{token("big", "#FF2D3D", "tkL")}<div class="crown" id="crown">{CROWN}</div><div class="ribbon" id="ribbon">WINNER</div></div>
<div class="fz" id="fR">{token("big", "#2F6BFF", "tkR")}<div class="shards" id="shards">{shards}</div></div>
{atk}
<div class="judge" id="judge"><div class="jh">THE JUDGE <small>scores on a written rubric</small></div>{rows}</div>
<div class="ko" id="ko">K.O.</div>"""


def s_loop():
    nums = "".join(f'<span class="ln" id="ln{i}">{n}</span>' for i, (_, n, _) in enumerate(LOOP))
    rounds = "".join(f'<span class="lr" id="lr{i}">ROUND {r}</span>' for i, (_, _, r) in enumerate(LOOP))
    return f"""
<div class="lbl">// THE LOOP</div>
<div class="ring" id="ring"><svg viewBox="0 0 500 500" width="100%" height="100%">
  <circle cx="250" cy="250" r="214" fill="none" stroke="#FFD400" stroke-width="26" stroke-dasharray="1180 165" stroke-linecap="round" transform="rotate(-80 250 250)"/>
  <polygon points="250,10 296,38 250,66" fill="#FFD400" transform="rotate(-6 250 250)"/></svg></div>
<div class="lcore"><div class="stk lnums">{nums}</div><div class="stk lrounds">{rounds}</div><div class="lsub">alive</div></div>
<div class="lchip" id="lcA">ATTACK</div><div class="lchip" id="lcD">DEFEND</div><div class="lchip" id="lcJ">JUDGE</div>"""


def s_tip():
    return f"""
<div class="tipst" id="tipst">PRO TIP</div>
<div class="term t2" id="term2">
  <div class="tbar"><i></i><i></i><i></i><span>claude</span></div>
  <div class="tline"><span class="pr">&gt;</span> <span>{chars("/arena ", "tq")}</span><span class="yl">{chars("--quick", "tq")}</span><i class="caret" id="caret2"></i></div>
</div>
<div class="b16" id="b16"><b>16</b> AGENTS</div>
<div class="gauge" id="gauge"><div class="gl">TOKENS</div><div class="gbar"><i class="gfill" id="gfill"></i></div></div>
<div class="grow" id="gr1"><span>/arena</span><b>100 agents</b><em>595 calls</em></div>
<div class="grow q" id="gr2"><span>--quick</span><b>16 agents</b><em>91 calls</em></div>"""


def s_pin():
    skel = "".join(f'<div class="srow" id="sk{i}"><i class="sav"></i><div><i class="sb a"></i><i class="sb b"></i></div></div>' for i in range(1))
    return f"""
<div class="sheet" id="sheet">
  <i class="handle"></i><div class="shh">Comments</div>
  <div class="crow" id="crow"><span class="av">N</span><div class="cbody"><div class="cn"><b>nikcore.ai</b>{PINSM}<span>Pinned</span></div>
    <div class="ct">Repo: <a>{REPO}</a></div></div></div>
  {skel}
  <div class="cin" id="cin"><span class="ph" id="cph">Add a comment&hellip;</span><span id="ctyped">{chars("ARENA", "ca")}</span><i class="strike" id="strike"></i></div>
</div>
<div class="bigpin" id="bigpin">{PIN}</div>
<div class="nn" id="nn">NOT NEEDED</div>"""


def s_end():
    return """
<div class="e1" id="e1">LINK'S PINNED</div>
<div class="e2" id="e2">in the comments. No keyword, no DM.</div>
<div class="e3" id="e3">@nikcore.ai &middot; free AI tools that actually work</div>"""


def t_arena():
    letters = "".join(f'<span class="al" id="al{i}">{c}</span>' for i, c in enumerate("ARENA"))
    rays = "".join(f'<polygon points="540,960 {540 + 1500 * math.cos(math.radians(a - 3)):.0f},{960 + 1500 * math.sin(math.radians(a - 3)):.0f} {540 + 1500 * math.cos(math.radians(a + 3)):.0f},{960 + 1500 * math.sin(math.radians(a + 3)):.0f}"/>' for a in range(0, 360, 15))
    return f"""<div class="tkbg yel"><svg class="rays" id="rays" viewBox="0 0 1080 1920" width="1080" height="1920"><g fill="#000" opacity=".12">{rays}</g></svg></div>
<div class="alogo">{letters}</div>
<div class="asub" id="asub">100 CLAUDES. ONE ANSWER.</div>
<div class="acmd" id="acmd">/arena</div>"""


def t_grid():
    toks = "".join(f'<div class="gt" id="a{k}" style="left:{g["x"]}px;top:{g["y"]}px">{token("", g["c"])}</div>' for k, g in enumerate(GRID))
    tags = "".join(f'<div class="gtag" id="tag{i}" style="left:{GRID[k]["x"] + TS // 2}px;top:{GRID[k]["y"] - 14}px">{n}</div>' for i, (k, n) in enumerate(TAGS))
    return f"""<div class="tkbg dark"></div>
<div class="gcount"><span id="gnum">1</span><em>AGENTS</em></div>
<div class="gline" id="gline">SAME TASK &middot; 2,160 STRATEGY CARDS &middot; NO REPEATS</div>
<div class="gwrap">{toks}{tags}</div>"""


def t_vs():
    return f"""<div class="vsL" id="vsL"><div class="vf" id="vfL">{token("huge", "#FF2D3D")}<b>CONTRARIAN</b></div></div>
<div class="vsR" id="vsR"><div class="vf" id="vfR">{token("huge", "#2F6BFF")}<b>FIRST PRINCIPLES</b></div></div>
<div class="vs" id="vs">VS</div>"""


def t_champ():
    conf = "".join(f'<i class="cf" id="cf{i}" style="background:{c["c"]};width:{c["w"]}px;height:{c["h"]}px"></i>' for i, c in enumerate(CONF))
    return f"""<div class="tkbg yel"></div>
<div class="cwrap">{conf}</div>
<div class="champ" id="champ">{token("huge", "#FF2D3D")}<div class="ccrown">{CROWN}</div></div>
<div class="c1" id="c1">1 ANSWER LEFT</div>
<div class="c2" id="c2">+ every attack it survived</div>"""


# ------------------------------------------------------------------ html
def html():
    sc = lambda k, fn: clip("s_" + k, SC[k][0], SC[k][1], 2, "scene", fn())
    tk = lambda k, fn: clip("t_" + k, TK[k][0], TK[k][1], 3, "take", fn())
    return f"""<!doctype html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width={W}, height={H}">
<title>Arena</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-width="{W}" data-height="{H}" data-duration="{DUR}">
 <div id="world">
  <div id="faceframe"><video id="face" class="clip" src="media/face.mp4" muted playsinline data-start="0" data-duration="{DUR}" data-media-start="0" data-track-index="0"></video></div>
  <div id="stage"><div class="dots"></div>
   {sc("hook", s_hook)}{sc("term", s_term)}{sc("task", s_task)}{sc("pair", s_pair)}{sc("fight", s_fight)}
   {sc("loop", s_loop)}{sc("tip", s_tip)}{sc("pin", s_pin)}{sc("end", s_end)}
  </div>
  <div id="seam"></div>
  {tk("arena", t_arena)}{tk("grid", t_grid)}{tk("vs", t_vs)}{tk("champ", t_champ)}
  <div id="fcam"><video id="face2" class="clip" src="media/facecam.mp4" muted playsinline data-start="0" data-duration="{DUR}" data-media-start="0" data-track-index="1"></video><span class="live">&#9679; LIVE</span></div>
  <div id="flash"></div>
 </div>
 {clip("arrow", SC["end"][0], DUR, 4, "", '<svg viewBox="0 0 1080 1920" width="1080" height="1920"><path id="apath" d="M760 700 C 980 820, 1040 1080, 985 1395" fill="none" stroke="#FFD400" stroke-width="16" stroke-linecap="round"/><polygon id="ahead" points="985,1440 950,1380 1022,1386" fill="#FFD400" stroke="#000" stroke-width="5" stroke-linejoin="round"/></svg>', "div")}
 <div id="caps">{cap_html()}</div>
 <audio id="mix" src="{MIX}" data-start="0" data-duration="{DUR}" data-track-index="9" data-volume="1"></audio>
</div>
<script>{JS.replace("__P__", json.dumps(P))}</script>
</body></html>"""


# ------------------------------------------------------------------ css
CSS = r"""
:root { --bg:#0D0B10; --ink:#F4F1EA; --y:#FFD400; --red:#FF2D3D; --blue:#2F6BFF; --cream:#FAF9F5; --clay:#D97757; }
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#000; font-family:"Archivo Black", "Inter", sans-serif; -webkit-font-smoothing:antialiased; }
#root { position:relative; width:1080px; height:1920px; overflow:hidden; background:var(--bg); }
#world { position:absolute; inset:0; }
.stk { display:inline-grid; } .stk > * { grid-area:1/1; }
.dots, .tkbg { position:absolute; inset:0; }
.dots { background:var(--bg) radial-gradient(rgba(255,255,255,.07) 1.6px, transparent 1.8px) 0 0/12px 12px; }

/* face */
#faceframe { position:absolute; left:0; top:0; width:1080px; height:1920px; overflow:hidden; background:#16110e; }
#face { position:absolute; left:0; top:0; width:1920px; height:1080px; transform-origin:0 0; max-width:none; }
#stage { position:absolute; left:0; top:0; width:1080px; height:860px; overflow:hidden; z-index:2; }
#seam { position:absolute; left:0; top:856px; width:1080px; height:8px; background:#000; z-index:2; }
.scene { position:absolute; left:0; top:0; width:1080px; height:860px; }
.lbl { position:absolute; left:64px; top:196px; font-family:"JetBrains Mono", monospace; font-weight:700; font-size:30px; color:var(--y); letter-spacing:.04em; }

/* comic card */
.card { border:5px solid #000; box-shadow:12px 12px 0 #000; }

/* hook */
.chat { position:absolute; left:84px; top:262px; width:912px; padding:34px 36px 30px; background:var(--cream); border:5px solid #000; border-radius:30px; box-shadow:14px 14px 0 #000; }
.ubub { margin-left:auto; width:fit-content; max-width:640px; padding:20px 28px; border-radius:26px; background:#EFE6DE; font-family:"Inter", sans-serif; font-weight:600; font-size:38px; color:#1F1E1D; }
.ubub.sm { margin-top:24px; font-size:34px; padding:14px 24px; }
.arow { display:flex; gap:22px; align-items:center; margin-top:30px; }
.spk { width:64px; height:64px; flex:none; }
.rep { font-family:"Inter", sans-serif; font-weight:500; font-size:44px; color:#1F1E1D; }
.stamp { position:absolute; left:470px; top:520px; padding:6px 26px 2px; border:9px solid var(--red); border-radius:16px; color:var(--red); background:rgba(250,249,245,.85);
  font-family:"League Gothic", sans-serif; font-size:132px; line-height:1; letter-spacing:.02em; transform:rotate(-9deg); }
.stamp.s2 { left:120px; top:600px; font-size:110px; transform:rotate(7deg); }

/* terminal */
.term { position:absolute; left:84px; top:262px; width:912px; height:300px; background:#09090B; border:5px solid var(--ink); border-radius:26px; box-shadow:14px 14px 0 var(--y); overflow:hidden; }
.tbar { height:58px; display:flex; align-items:center; gap:12px; padding:0 24px; border-bottom:3px solid #222; font-family:"JetBrains Mono", monospace; font-size:28px; color:#8A8A8A; }
.tbar i { width:16px; height:16px; border-radius:50%; background:#3A3A3A; }
.tbar span { margin-left:10px; }
.tline { padding:42px 36px 0; font-family:"JetBrains Mono", monospace; font-weight:700; font-size:72px; color:#fff; display:flex; align-items:center; }
.pr { color:var(--clay); }
.caret { width:34px; height:72px; background:var(--y); margin-left:6px; }
.tauto { margin:26px 36px 0; padding:14px 20px; border-radius:12px; background:#1C1C22; font-family:"JetBrains Mono", monospace; font-size:28px; color:#B9B9B9; }
.tauto b { color:var(--y); }
.burst { position:absolute; left:770px; top:150px; width:270px; height:270px; transform:rotate(12deg); }
.bsh { position:absolute; inset:0; }
.btx { position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; color:#000; }
.btx b { font-family:"League Gothic", sans-serif; font-size:118px; line-height:.9; font-weight:400; }
.btx small { font-family:"JetBrains Mono", monospace; font-weight:700; font-size:28px; white-space:nowrap; }
.chip { position:absolute; left:50%; top:640px; transform:translateX(-50%); padding:14px 34px; background:var(--ink); color:#000; border:5px solid #000; border-radius:999px; box-shadow:8px 8px 0 var(--red); font-size:40px; letter-spacing:.02em; white-space:nowrap; }

/* task */
.ticket { position:absolute; left:84px; top:300px; width:912px; height:300px; display:flex; background:var(--cream); border:5px solid #000; border-radius:24px; box-shadow:14px 14px 0 #000; overflow:hidden; }
.tk-l { width:150px; background:var(--y); border-right:5px dashed #000; display:flex; align-items:center; justify-content:center; font-family:"League Gothic", sans-serif; font-size:80px; writing-mode:vertical-rl; transform:rotate(180deg); }
.tk-r { flex:1; padding:40px 46px; font-family:"Inter", sans-serif; font-weight:800; font-size:58px; line-height:1.12; color:#111; display:flex; align-items:center; }
.badge1 { position:absolute; left:40px; top:250px; width:110px; height:110px; border-radius:50%; background:var(--red); border:5px solid #000; color:#fff; font-family:"League Gothic", sans-serif; font-size:84px; display:flex; align-items:center; justify-content:center; box-shadow:6px 6px 0 #000; }
.x100 { position:absolute; left:640px; top:560px; padding:0 30px; background:var(--red); color:#fff; border:6px solid #000; border-radius:18px; font-family:"League Gothic", sans-serif; font-size:170px; line-height:1.05; box-shadow:10px 10px 0 #000; transform:rotate(-6deg); }

/* tokens */
.tok { position:relative; width:100%; height:100%; background:var(--c); border:4px solid #000; border-radius:22%; box-shadow:5px 5px 0 #000; overflow:hidden; }
.tok .ey { position:absolute; top:32%; width:17%; height:26%; background:#fff; border:3px solid #000; border-radius:30%; }
.tok .ey.l { left:24%; } .tok .ey.r { right:24%; }
.tok .fl { position:absolute; inset:0; background:#fff; opacity:0; }
.tok.big { border-width:7px; box-shadow:12px 12px 0 #000; } .tok.big .ey { border-width:5px; }
.tok.huge { border-width:9px; box-shadow:16px 16px 0 #000; } .tok.huge .ey { border-width:7px; }

/* pair */
.fighter { position:absolute; top:300px; width:250px; }
.fighter .tok { height:250px; }
#pL { left:110px; } #pR { left:720px; }
.np { margin-top:30px; text-align:center; color:var(--ink); }
.np b { display:block; font-family:"League Gothic", sans-serif; font-weight:400; font-size:70px; line-height:1; }
.np span { font-family:"JetBrains Mono", monospace; font-weight:700; font-size:28px; color:var(--y); white-space:nowrap; }

/* fight */
.hud { position:absolute; left:50px; right:50px; top:200px; display:flex; align-items:flex-end; gap:22px; }
.hb { flex:1; } .hb.R { text-align:right; }
.hn { font-family:"JetBrains Mono", monospace; font-weight:700; font-size:28px; color:var(--ink); margin-bottom:10px; white-space:nowrap; }
.bar { height:46px; border:5px solid #000; background:var(--red); box-shadow:6px 6px 0 #000; overflow:hidden; }
.hb.L .bar { transform:skewX(-14deg); } .hb.R .bar { transform:skewX(14deg); }
.fill { display:block; width:100%; height:100%; background:var(--y); transform-origin:left center; }
.hb.R .fill { transform-origin:right center; }
.hr { width:96px; height:96px; border:5px solid #000; background:var(--ink); color:#000; font-family:"League Gothic", sans-serif; font-size:64px; display:flex; align-items:center; justify-content:center; box-shadow:6px 6px 0 #000; }
.fz { position:absolute; top:400px; width:230px; height:230px; }
#fL { left:140px; } #fR { left:710px; }
.crown { position:absolute; left:35px; top:-120px; width:160px; height:106px; }
.ribbon { position:absolute; left:-40px; top:268px; width:310px; text-align:center; padding:4px 0 0; background:var(--y); border:5px solid #000; box-shadow:8px 8px 0 #000; font-family:"League Gothic", sans-serif; font-size:84px; line-height:1; transform:rotate(-4deg); }
.shards { position:absolute; left:15px; top:15px; width:200px; height:200px; }
.shard { position:absolute; width:50px; height:50px; background:var(--blue); border:3px solid #000; opacity:0; }
.atk { position:absolute; left:0; top:0; padding:8px 22px 4px; border:5px solid #000; border-radius:12px; font-family:"League Gothic", sans-serif; font-size:66px; line-height:1; box-shadow:6px 6px 0 #000; }
.atk.fatal { background:var(--red); color:#fff; } .atk.major { background:var(--y); color:#000; } .atk.minor { background:var(--ink); color:#000; }
.hspark { position:absolute; left:0; top:0; width:170px; height:170px; }
.judge { position:absolute; left:150px; top:205px; width:780px; padding:26px 34px; background:var(--cream); border:5px solid #000; border-radius:26px; box-shadow:14px 14px 0 #000; }
.jh { font-family:"League Gothic", sans-serif; font-size:76px; line-height:1; color:#000; margin-bottom:12px; }
.jh small { font-family:"JetBrains Mono", monospace; font-weight:700; font-size:28px; color:#666; margin-left:10px; letter-spacing:0; }
.rrow { display:flex; align-items:center; padding:12px 4px; border-top:3px solid #E2DACF; font-family:"Inter", sans-serif; font-weight:800; font-size:40px; color:#111; }
.rn { flex:1; } .rw { font-family:"JetBrains Mono", monospace; font-weight:700; font-size:32px; color:#777; margin-right:22px; }
.rc { width:48px; height:48px; }
.ko { position:absolute; z-index:6; left:-20px; right:-20px; top:300px; padding:10px 0 0; background:#0D0B10; border-top:8px solid var(--y); border-bottom:8px solid var(--y); text-align:center; font-family:"League Gothic", sans-serif; font-size:330px; line-height:1; color:var(--red); -webkit-text-stroke:12px #000; paint-order:stroke fill; text-shadow:16px 16px 0 #000; }

/* loop */
.ring { position:absolute; left:300px; top:250px; width:480px; height:480px; }
.lcore { position:absolute; left:300px; top:250px; width:480px; height:480px; display:flex; flex-direction:column; align-items:center; justify-content:center; }
.lnums { font-family:"League Gothic", sans-serif; font-size:230px; line-height:.9; color:var(--ink); text-align:center; }
.lnums > * { justify-self:center; }
.lrounds { font-family:"JetBrains Mono", monospace; font-weight:700; font-size:30px; color:var(--y); }
.lrounds > * { justify-self:center; }
.lsub { display:none; }
.lchip { position:absolute; padding:10px 22px; border:4px solid #000; border-radius:999px; background:#2A2730; color:var(--ink); font-size:30px; box-shadow:6px 6px 0 #000; }
#lcA { left:52px; top:420px; } #lcD { left:818px; top:420px; } #lcJ { left:466px; top:186px; }

/* tip */
.tipst { position:absolute; left:64px; top:192px; padding:6px 26px 0; background:var(--y); color:#000; border:5px solid #000; box-shadow:8px 8px 0 #000; font-family:"League Gothic", sans-serif; font-size:84px; line-height:1; transform:rotate(-5deg); }
.term.t2 { top:330px; height:200px; }
.term.t2 .tline { padding-top:26px; font-size:62px; }
.term.t2 .caret { height:62px; }
.yl { color:var(--y); }
.b16 { position:absolute; left:760px; top:200px; padding:8px 24px 4px; background:var(--red); color:#fff; border:5px solid #000; border-radius:14px; box-shadow:8px 8px 0 #000; font-family:"League Gothic", sans-serif; font-size:64px; line-height:1; transform:rotate(6deg); }
.b16 b { font-size:84px; font-weight:400; }
.gauge { position:absolute; left:84px; top:584px; width:912px; display:flex; align-items:center; gap:22px; }
.gl { font-family:"JetBrains Mono", monospace; font-weight:700; font-size:30px; color:var(--ink); }
.gbar { flex:1; height:60px; border:5px solid var(--ink); border-radius:14px; padding:6px; }
.gfill { display:block; width:100%; height:100%; border-radius:6px; background:var(--y); transform-origin:left center; }
.grow { position:absolute; left:84px; top:680px; width:912px; display:flex; gap:24px; align-items:baseline; font-family:"JetBrains Mono", monospace; font-weight:700; font-size:34px; color:var(--ink); }
.grow.q { top:740px; }
.grow span { width:190px; color:#9A97A3; } .grow b { width:290px; font-weight:700; } .grow em { font-style:normal; color:var(--red); }
.grow.q em { color:#22C55E; }

/* pin */
.sheet { position:absolute; left:40px; top:196px; width:1000px; height:700px; background:#fff; border:5px solid #000; border-radius:40px 40px 0 0; box-shadow:12px 12px 0 #000; font-family:"Inter", sans-serif; color:#111; }
.handle { position:absolute; left:460px; top:18px; width:80px; height:8px; border-radius:4px; background:#D0D0D0; }
.shh { text-align:center; margin-top:40px; font-weight:800; font-size:34px; }
.crow { display:flex; gap:24px; margin:26px 26px 0; padding:22px; border-radius:22px; }
.av { width:84px; height:84px; flex:none; border-radius:50%; background:var(--clay); color:#fff; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:40px; border:3px solid #000; }
.cn { display:flex; align-items:center; gap:10px; font-size:30px; } .cn span { color:#8E8E8E; font-weight:600; font-size:28px; }
.ct { margin-top:8px; font-size:32px; font-weight:500; line-height:1.3; } .ct a { color:#2563EB; font-weight:700; }
.srow { display:flex; gap:24px; margin:20px 48px 0; }
.sav { width:70px; height:70px; border-radius:50%; background:#ECECEC; flex:none; }
.sb { display:block; height:22px; border-radius:11px; background:#ECECEC; margin-top:8px; } .sb.a { width:260px; } .sb.b { width:560px; }
.cin { position:absolute; left:30px; right:30px; top:440px; height:84px; border:3px solid #DBDBDB; border-radius:42px; display:flex; align-items:center; padding:0 34px; font-size:34px; font-weight:700; }
.cin .ph { position:absolute; left:34px; color:#9A9A9A; font-weight:500; }
.strike { position:absolute; left:24px; top:38px; width:170px; height:9px; background:var(--red); transform-origin:left center; border-radius:4px; }
.bigpin { position:absolute; left:860px; top:250px; width:150px; height:150px; }
.nn { position:absolute; left:430px; top:560px; padding:4px 24px 0; border:8px solid var(--red); color:var(--red); background:#fff; border-radius:14px; font-family:"League Gothic", sans-serif; font-size:96px; line-height:1; transform:rotate(-7deg); }

/* end */
.e1 { position:absolute; left:0; right:0; top:270px; text-align:center; font-family:"League Gothic", sans-serif; font-size:190px; line-height:1; color:var(--y); -webkit-text-stroke:8px #000; paint-order:stroke fill; text-shadow:12px 12px 0 #000; }
.e2 { position:absolute; left:0; right:0; top:500px; text-align:center; font-size:46px; color:var(--ink); }
.e3 { position:absolute; left:0; right:0; top:600px; text-align:center; font-family:"JetBrains Mono", monospace; font-weight:700; font-size:32px; color:#9A97A3; }
#arrow { position:absolute; left:0; top:0; width:1080px; height:1920px; z-index:5; pointer-events:none; }

/* takeovers */
.take { position:absolute; left:0; top:0; width:1080px; height:1920px; z-index:3; overflow:hidden; }
.tkbg.yel { background:var(--y) radial-gradient(rgba(0,0,0,.13) 2.2px, transparent 2.5px) 0 0/18px 18px; }
.tkbg.dark { background:var(--bg) radial-gradient(rgba(255,255,255,.07) 1.6px, transparent 1.8px) 0 0/12px 12px; }
.rays { position:absolute; left:0; top:0; transform-origin:540px 960px; }
.alogo { position:absolute; left:0; right:0; top:560px; text-align:center; font-family:"League Gothic", sans-serif; font-size:560px; line-height:1; color:#000; white-space:nowrap; }
.al { display:inline-block; text-shadow:18px 18px 0 var(--red); }
.asub { position:absolute; left:0; right:0; top:1150px; text-align:center; font-family:"League Gothic", sans-serif; font-size:104px; color:#000; }
.acmd { position:absolute; left:50%; top:1290px; transform:translateX(-50%); padding:10px 30px; background:#000; color:var(--y); border-radius:14px; font-family:"JetBrains Mono", monospace; font-weight:700; font-size:44px; }
.gcount { position:absolute; left:0; right:0; top:200px; display:flex; justify-content:center; align-items:baseline; gap:24px; font-family:"League Gothic", sans-serif; color:var(--y); }
.gcount span { font-size:230px; line-height:.95; -webkit-text-stroke:8px #000; paint-order:stroke fill; text-shadow:10px 10px 0 #000; min-width:250px; text-align:right; }
.gcount em { font-style:normal; font-size:120px; color:var(--ink); }
.gline { position:absolute; left:0; right:0; top:420px; text-align:center; font-family:"JetBrains Mono", monospace; font-weight:700; font-size:28px; color:var(--ink); }
.gwrap { position:absolute; inset:0; }
.gt { position:absolute; width:68px; height:68px; }
.gtag { position:absolute; transform:translate(-50%, -100%); padding:8px 18px; background:#000; color:var(--y); border:4px solid var(--ink); border-radius:12px; font-family:"JetBrains Mono", monospace; font-weight:700; font-size:28px; white-space:nowrap; z-index:3; box-shadow:6px 6px 0 #000; }
.vsL, .vsR { position:absolute; inset:0; }
.vsL { background:var(--red); clip-path:polygon(0 0, 100% 0, 100% 34%, 0 64%); }
.vsR { background:var(--blue); clip-path:polygon(0 66%, 100% 36%, 100% 100%, 0 100%); }
.vf { position:absolute; width:380px; text-align:center; }
#vfL { left:80px; top:230px; } #vfR { left:620px; top:1160px; }
.vf .tok { height:380px; }
.vf b { display:block; margin-top:26px; font-family:"League Gothic", sans-serif; font-weight:400; font-size:96px; line-height:1; color:#fff; -webkit-text-stroke:6px #000; paint-order:stroke fill; white-space:nowrap; }
#vfR b { margin-left:-120px; margin-right:-40px; }
.vs { position:absolute; left:0; right:0; top:720px; text-align:center; font-family:"League Gothic", sans-serif; font-size:460px; line-height:1; color:var(--y); -webkit-text-stroke:16px #000; paint-order:stroke fill; text-shadow:20px 20px 0 #000; }
.cwrap { position:absolute; left:540px; top:640px; z-index:1; }
.cf { position:absolute; left:0; top:0; border:3px solid #000; }
.champ { position:absolute; z-index:2; left:390px; top:480px; width:300px; height:300px; }
.champ .tok { height:300px; }
.ccrown { position:absolute; left:60px; top:-150px; width:180px; height:120px; }
.c1 { position:absolute; z-index:2; left:0; right:0; top:900px; text-align:center; font-family:"League Gothic", sans-serif; font-size:210px; line-height:1; color:#000; text-shadow:12px 12px 0 var(--red); }
.c2 { position:absolute; z-index:2; left:0; right:0; top:1130px; text-align:center; font-size:52px; color:#000; }

/* facecam */
#fcam { position:absolute; left:60px; top:1400px; width:300px; height:300px; border:7px solid var(--ink); border-radius:34px; box-shadow:12px 12px 0 #000; overflow:hidden; z-index:4; opacity:0; background:#16110e; }
#face2 { position:absolute; left:0; top:0; width:100%; height:100%; object-fit:cover; }
.live { position:absolute; left:14px; top:14px; padding:4px 12px; border-radius:8px; background:var(--red); color:#fff; font-family:"JetBrains Mono", monospace; font-weight:700; font-size:28px; }
#flash { position:absolute; inset:0; background:#fff; opacity:0; z-index:6; pointer-events:none; }

/* captions */
#caps { position:absolute; left:0; top:0; width:1080px; height:1920px; z-index:7; pointer-events:none; }
.cg { position:absolute; left:40px; right:40px; top:812px; text-align:center; font-size:66px; line-height:1.1; color:#fff; opacity:0;
  -webkit-text-stroke:11px #000; paint-order:stroke fill; text-shadow:6px 6px 0 #000; letter-spacing:-.01em; }
.cw { display:inline-block; }
"""

# ------------------------------------------------------------------ js
P = {"DUR": DUR, "B": B, "CUTS": CUTS, "TK": TK, "SC": SC, "groups": [[{"s": w["s"], "e": w["e"]} for w in g] for g in GROUPS],
     "GRID": [{"d": g["d"]} for g in GRID], "TAGS": [k for k, _ in TAGS], "SHARDS": SHARDS, "CONF": CONF,
     "ATTACKS": ATTACKS, "LOOP": LOOP, "LAST": LAST}

JS = r"""
const tl = gsap.timeline({ paused: true });
const P = __P__;
const B = P.B, CUT = P.CUTS, TK = P.TK, SC = P.SC;
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

function hid(sel) { gsap.set(Array.isArray(sel) ? sel.join(",") : sel, { opacity: 0 }); }
function pop(sel, t, o) { o = o || {}; tl.fromTo(sel, { opacity: 0, scale: o.s0 || 0.4, rotation: o.r0 || 0 }, { opacity: 1, scale: 1, rotation: o.r || 0, duration: o.d || 0.26, ease: o.ease || "back.out(2.4)", immediateRender: false }, t); }
function slam(sel, t, o) { o = o || {}; tl.fromTo(sel, { opacity: 0, scale: o.s0 || 2.6, rotation: o.r0 || 0 }, { opacity: 1, scale: 1, rotation: o.r || 0, duration: o.d || 0.13, ease: "power4.in", immediateRender: false }, t - (o.d || 0.13)); }
function out(sel, t, d) { tl.to(sel, { opacity: 0, duration: d || 0.12, ease: "none" }, t); }
function shake(t, amp, n) { n = n || 6; for (let i = 0; i < n; i++) { const k = (n - i) / n; tl.to("#world", { x: (i % 2 ? -1 : 1) * amp * k, y: ((i % 3) - 1) * amp * 0.6 * k, duration: 0.033, ease: "none" }, t + i * 0.033); } tl.to("#world", { x: 0, y: 0, duration: 0.033 }, t + n * 0.033); }
function flash(t, a) { tl.fromTo("#flash", { opacity: a || 0.75 }, { opacity: 0, duration: 0.16, ease: "power2.out", immediateRender: false }, t); }
function typeChars(sel, t0, t1) { const cs = $$(sel); const step = (t1 - t0) / cs.length; cs.forEach(function (c, i) { gsap.set(c, { opacity: 0 }); tl.set(c, { opacity: 1 }, t0 + i * step); }); }
function counter(el, from, to, t, d) { const o = { v: from }; tl.fromTo(o, { v: from }, { v: to, duration: d, ease: "power2.out", immediateRender: false, onUpdate: function () { el.textContent = Math.round(o.v); } }, t); }

// ---------- face framing: bottom split by default, punch-ins on every cut
const FX = 845, FY = 670;
function framing(s) { return { x: 540 - FX * s, y: 1920 - 1080 * s, scale: s }; }
const ZOOM = [1.30, 1.42, 1.30, 1.40];
ZOOM.forEach(function (z, i) { const f = framing(z); if (i === 0) gsap.set("#face", f); tl.set("#face", f, CUT[i]); });
tl.set("#face", framing(1.44), B.losers); tl.set("#face", framing(1.30), B.then2);
tl.set("#face", framing(1.38), B.tip); tl.set("#face", framing(1.40), CUT[3]);
// facecam crop
hid("#fcam");
Object.keys(TK).forEach(function (k) {
  const a = TK[k][0], b = TK[k][1];
  tl.fromTo("#fcam", { opacity: 0, scale: 0.6, rotation: -6 }, { opacity: 1, scale: 1, rotation: -3, duration: 0.2, ease: "back.out(2)", immediateRender: false }, a + 0.04);
  tl.set("#fcam", { opacity: 0 }, b);
});

// ---------- HOOK
hid(["#st1", "#st2", "#rep2", "#retry"]);
slam("#st1", B.bad + 0.02, { r: -9, r0: -20 }); shake(B.bad + 0.02, 14);
tl.set("#retry", { opacity: 1 }, B.from - 0.08); tl.fromTo("#retry", { y: 20 }, { y: 0, duration: 0.12, immediateRender: false }, B.from - 0.08);
tl.set("#rep1", { opacity: 0 }, B.from + 0.1); tl.set("#rep2", { opacity: 1 }, B.from + 0.1);
tl.to("#st1", { opacity: 0.0, duration: 0.08 }, B.from + 0.06);
slam("#st2", B.claude1 + 0.06, { r: 7, r0: 18 }); shake(B.claude1 + 0.06, 12);

// ---------- TERMINAL
hid(["#tauto", "#free", "#chip"]);
typeChars("#tcmd .tc", B.try1 + 0.04, B.this + 0.3);
tl.fromTo("#term1", { y: 40, opacity: 0 }, { y: 0, opacity: 1, duration: 0.14, ease: "power3.out", immediateRender: false }, CUT[1]);
pop("#free", B.free, { r: 12, r0: -30, s0: 0.2 });
pop("#chip", B.skill, { s0: 0.6 });
pop("#tauto", B.called, { s0: 0.9 });

// ---------- ARENA takeover
const al = $$(".al");
al.forEach(function (l, i) { hid(l); slam(l, B.arena + 0.02 + i * 0.05, { s0: 3.2 }); });
tl.fromTo("#rays", { scale: 0.5, rotation: 0 }, { scale: 1.15, rotation: 14, duration: TK.arena[1] - TK.arena[0], ease: "power1.out", immediateRender: false }, TK.arena[0]);
hid(["#asub", "#acmd"]);
pop("#asub", B.arena + 0.34, { s0: 0.7 }); pop("#acmd", B.arena + 0.46, { s0: 0.7 });
flash(B.arena + 0.03); shake(B.arena + 0.03, 22, 8);

// ---------- TASK
hid(["#ticket", "#one1", "#x100"]);
tl.fromTo("#ticket", { y: -620, opacity: 1, rotation: -4 }, { y: 0, rotation: 0, duration: 0.28, ease: "bounce.out", immediateRender: false }, B.give - 0.05);
tl.set("#ticket", { opacity: 1 }, B.give - 0.05);
pop("#one1", B.one1, { s0: 0.2 });
shake(B.and1, 8, 5);
slam("#x100", B.hundred1 + 0.02, { r: -6, r0: -18 });

// ---------- GRID takeover
const toks = $$(".gt");
toks.forEach(function (el, k) { gsap.set(el, { opacity: 0, scale: 0 }); tl.fromTo(el, { opacity: 0, scale: 0 }, { opacity: 1, scale: 1, duration: 0.22, ease: "back.out(3)", immediateRender: false }, TK.grid[0] + 0.06 + P.GRID[k].d); });
counter($("#gnum"), 1, 100, TK.grid[0] + 0.06, 0.78);
tl.to(".gt", { y: -9, duration: 0.12, yoyo: true, repeat: 3, ease: "sine.inOut", stagger: { each: 0.004, grid: [10, 10], from: "center" } }, B.all);
hid("#gline"); pop("#gline", B.each1 - 0.1, { s0: 0.85 });
const tagT = [B.each1 - 0.06, B.one2 - 0.06, B.one2 + 0.22, B.different - 0.1, B.different + 0.14, B.way - 0.1];
P.TAGS.forEach(function (k, i) {
  const t = tagT[i], tag = "#tag" + i, tk = "#a" + k;
  hid(tag); pop(tag, t, { s0: 0.5 });
  tl.to(tk, { scale: 1.45, zIndex: 2, duration: 0.14, ease: "back.out(3)" }, t);
  if (i < P.TAGS.length - 1) tl.to(tk, { scale: 1.15, duration: 0.12 }, tagT[i + 1]);
});

// ---------- PAIR
tl.fromTo("#pL", { x: -500 }, { x: 0, duration: 0.24, ease: "power3.out", immediateRender: false }, B.then1);
tl.fromTo("#pR", { x: 500 }, { x: 0, duration: 0.24, ease: "power3.out", immediateRender: false }, B.pair - 0.05);
gsap.set("#pL", { x: -500 }); gsap.set("#pR", { x: 500 });
tl.to("#pL", { x: 70, duration: 0.09, ease: "power2.in", yoyo: true, repeat: 1 }, B.up);
tl.to("#pR", { x: -70, duration: 0.09, ease: "power2.in", yoyo: true, repeat: 1 }, B.up);

// ---------- VS takeover
tl.fromTo("#vsL", { x: -1100 }, { x: 0, duration: 0.12, ease: "power3.out", immediateRender: false }, TK.vs[0]);
tl.fromTo("#vsR", { x: 1100 }, { x: 0, duration: 0.12, ease: "power3.out", immediateRender: false }, TK.vs[0]);
hid("#vs"); slam("#vs", B.fight + 0.05, { s0: 3.4, r0: -20 }); flash(B.fight + 0.05, 0.6); shake(B.fight + 0.05, 24, 8);
tl.fromTo("#vfL", { x: 0 }, { x: 30, duration: TK.vs[1] - TK.vs[0], ease: "none", immediateRender: false }, TK.vs[0]);
tl.fromTo("#vfR", { x: 0 }, { x: -30, duration: TK.vs[1] - TK.vs[0], ease: "none", immediateRender: false }, TK.vs[0]);

// ---------- FIGHT
const XL = 255, XR = 825, YA = 470;
let hpL = 1, hpR = 1;
gsap.set("#hpL", { scaleX: 1 }); gsap.set("#hpR", { scaleX: 1 });
P.ATTACKS.forEach(function (a, i) {
  const t = a[0], fromL = a[1] === "L", el = "#atk" + i, hs = "#hs" + i;
  const x0 = (fromL ? XL : XR) - 90, x1 = (fromL ? XR : XL) - 90;
  hid(el); hid(hs);
  tl.fromTo(el, { x: x0, y: YA, opacity: 1, scale: 0.6, rotation: fromL ? -10 : 10 }, { x: x1, y: YA - 30, scale: 1, rotation: 0, duration: 0.16, ease: "power2.in", immediateRender: false }, t - 0.04);
  tl.to(el, { opacity: 0, scale: 1.5, duration: 0.1 }, t + 0.12);
  tl.fromTo(hs, { x: x1 + 10, y: YA - 60, opacity: 1, scale: 0.2 }, { scale: 1.2, opacity: 0, duration: 0.2, ease: "power2.out", immediateRender: false }, t + 0.12);
  const def = fromL ? "#tkR" : "#tkL", box = fromL ? "#fR" : "#fL";
  tl.fromTo(def + " .fl", { opacity: 0.9 }, { opacity: 0, duration: 0.14, immediateRender: false }, t + 0.12);
  tl.to(box, { x: fromL ? 44 : -44, duration: 0.05 }, t + 0.12); tl.to(box, { x: 0, duration: 0.16, ease: "power2.out" }, t + 0.17);
  const dmg = a[2] === "FATAL" ? 0.4 : a[2] === "MAJOR" ? 0.2 : 0.12;
  if (fromL) { hpR = Math.max(0.06, hpR - dmg); tl.to("#hpR", { scaleX: hpR, duration: 0.2, ease: "power2.out" }, t + 0.12); }
  else { hpL = Math.max(0.06, hpL - dmg); tl.to("#hpL", { scaleX: hpL, duration: 0.2, ease: "power2.out" }, t + 0.12); }
  shake(t + 0.12, a[2] === "FATAL" ? 16 : 8, 4);
});
hid(["#judge", "#crown", "#ribbon", "#ko"]);
tl.fromTo("#judge", { y: -760, opacity: 1 }, { y: 0, duration: 0.26, ease: "power3.out", immediateRender: false }, B.and3 - 0.08);
tl.set("#judge", { opacity: 1 }, B.and3 - 0.08);
const rT = [B.judge, B.judge + 0.14, B.picks, B.picks + 0.12, B.picks + 0.24];
$$(".rc").forEach(function (c, i) { hid(c); pop(c, rT[i], { s0: 0.2 }); });
tl.to("#judge", { y: -760, duration: 0.2, ease: "power3.in" }, B.winner - 0.12);
tl.fromTo("#crown", { y: -300, opacity: 1 }, { y: 0, duration: 0.26, ease: "bounce.out", immediateRender: false }, B.winner + 0.02);
tl.set("#crown", { opacity: 1 }, B.winner + 0.02);
pop("#ribbon", B.winner + 0.1, { r: -4, r0: -16 });
slam("#ko", B.out + 0.03, { s0: 3 }); flash(B.out + 0.03, 0.5); shake(B.out + 0.03, 22, 8);
tl.set("#tkR", { opacity: 0 }, B.out + 0.03);
P.SHARDS.forEach(function (s, i) {
  const el = "#sh" + i;
  tl.set(el, { opacity: 1 }, B.out + 0.03);
  tl.fromTo(el, { x: 0, y: 0, rotation: 0 }, { x: s.vx, y: s.vy, rotation: s.r, duration: 0.6, ease: "power1.in", immediateRender: false }, B.out + 0.03);
  tl.to(el, { opacity: 0, duration: 0.15 }, B.out + 0.5);
});
tl.to("#ko", { opacity: 0, duration: 0.1 }, B.then2 - 0.2);

// ---------- LOOP
const L = P.LOOP;
$$(".ln").forEach(function (el, i) { hid(el); }); $$(".lr").forEach(function (el, i) { hid(el); });
tl.fromTo("#ring", { scale: 0.4, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.24, ease: "back.out(2)", immediateRender: false }, L[0][0] - 0.06);
gsap.set("#ring", { opacity: 0 });
const chips = ["#lcA", "#lcD", "#lcJ"];
L.forEach(function (st, i) {
  const t = st[0];
  if (i > 0) {
    tl.to("#ring", { rotation: 360 * i, duration: Math.min(0.32, t - L[i - 1][0] - 0.02), ease: "power2.inOut" }, t - Math.min(0.32, t - L[i - 1][0] - 0.02));
    tl.set("#ln" + (i - 1), { opacity: 0 }, t); tl.set("#lr" + (i - 1), { opacity: 0 }, t);
    const pd = Math.min(0.3, t - L[i - 1][0]) / 3;
    chips.forEach(function (c, j) { tl.to(c, { backgroundColor: "#FFD400", color: "#000", duration: 0.02 }, t - pd * (3 - j)); tl.to(c, { backgroundColor: "#2A2730", color: "#F4F1EA", duration: 0.04 }, t - pd * (2 - j)); });
  }
  tl.fromTo("#ln" + i, { opacity: 0, scale: 1.5 }, { opacity: 1, scale: 1, duration: 0.12, ease: "power3.out", immediateRender: false }, t);
  tl.set("#lr" + i, { opacity: 1 }, t);
});
chips.forEach(function (c) { hid(c); pop(c, L[0][0] + 0.12, { s0: 0.5 }); });

// ---------- CHAMPION takeover
hid(["#c1", "#c2", "#champ"]);
slam("#champ", B.left + 0.03, { s0: 2.4 }); flash(B.left + 0.03, 0.7); shake(B.left + 0.03, 20, 8);
pop("#c1", B.left + 0.16, { s0: 0.6 }); pop("#c2", B.left + 0.36, { s0: 0.8 });
P.CONF.forEach(function (c, i) {
  const el = "#cf" + i; hid(el);
  tl.set(el, { opacity: 1 }, B.left + 0.03);
  tl.fromTo(el, { x: 0, y: 0, rotation: 0 }, { x: c.vx, y: c.vy, rotation: c.r, duration: 0.85, ease: "power2.out", immediateRender: false }, B.left + 0.03);
  tl.to(el, { y: "+=420", duration: 0.5, ease: "power1.in" }, B.left + 0.88 - 0.4);
});

// ---------- TIP
hid(["#tipst", "#b16", "#gauge", "#gr1", "#gr2"]);
slam("#tipst", B.tip + 0.03, { r: -5, r0: -16 }); shake(B.tip + 0.03, 10, 5);
tl.fromTo("#term2", { y: 40, opacity: 0 }, { y: 0, opacity: 1, duration: 0.14, ease: "power3.out", immediateRender: false }, B.tip + 0.2);
gsap.set("#term2", { opacity: 0 });
typeChars("#term2 .tq", B.use, B.mode + 0.05);
pop("#b16", B.mode + 0.05, { r: 6, r0: 24, s0: 0.3 });
pop("#gauge", B.hundred2 - 0.1, { s0: 0.9 });
pop("#gr1", B.hundred2 + 0.05, { s0: 0.9 }); pop("#gr2", B.agents2 + 0.1, { s0: 0.9 });
gsap.set("#gfill", { scaleX: 1 });
tl.to("#gfill", { scaleX: 0.05, backgroundColor: "#FF2D3D", duration: B.tokens - B.eats + 0.05, ease: "power2.in" }, B.eats);
tl.to("#gauge", { x: 10, duration: 0.04, yoyo: true, repeat: 5 }, B.tokens + 0.05);

// ---------- PIN
hid(["#bigpin", "#nn", "#ctyped", "#sk0"]);
tl.fromTo("#sheet", { y: 720 }, { y: 0, duration: 0.3, ease: "power3.out", immediateRender: false }, CUT[3] + 0.02);
gsap.set("#sheet", { y: 720 });
slam("#bigpin", B.pinned + 0.04, { s0: 3, r0: -30 }); shake(B.pinned + 0.04, 12, 5);
tl.to("#crow", { backgroundColor: "#FFF3B0", duration: 0.06 }, B.pinned + 0.04);
pop("#sk0", B.comments, { s0: 0.9 });
tl.set("#cph", { opacity: 0 }, B.no - 0.05); tl.set("#ctyped", { opacity: 1 }, B.no - 0.05);
typeChars("#ctyped .ca", B.no - 0.05, B.comment - 0.05);
gsap.set("#strike", { scaleX: 0 });
tl.to("#strike", { scaleX: 1, duration: 0.1, ease: "power2.out" }, B.comment);
slam("#nn", B.comment + 0.05, { r: -7, r0: -20 }); shake(B.comment + 0.05, 12, 5);

// ---------- END
hid(["#e1", "#e2", "#e3"]);
slam("#e1", SC.end[0] + 0.12, { s0: 2.2 }); shake(SC.end[0] + 0.12, 12, 5);
pop("#e2", SC.end[0] + 0.4, { s0: 0.8 }); pop("#e3", SC.end[0] + 0.7, { s0: 0.8 });
const ap = $("#apath"), alen = 900;
gsap.set(ap, { strokeDasharray: alen, strokeDashoffset: alen }); hid("#ahead");
tl.to(ap, { strokeDashoffset: 0, duration: 0.45, ease: "power2.inOut" }, SC.end[0] + 0.55);
pop("#ahead", SC.end[0] + 0.98, { s0: 0.2 });

// ---------- captions: pop-on karaoke, never early
function capTop(t) { return (t >= TK.grid[0] && t < TK.grid[1]) ? 1262 : 812; }
P.groups.forEach(function (g, gi) {
  const el = document.getElementById("g" + gi);
  const start = g[0].s - 0.03;
  const next = gi + 1 < P.groups.length ? P.groups[gi + 1][0].s - 0.03 : P.DUR;
  let end = Math.min(next, g[g.length - 1].e + 0.55);
  [TK.arena[0], TK.vs[0], TK.champ[0]].forEach(function (c) { if (start < c && end > c) end = c; });
  tl.set(el, { opacity: 1, top: capTop(g[0].s) }, start);
  tl.set(el, { opacity: 0 }, end);
  g.forEach(function (w, i) {
    const s = document.getElementById("w" + gi + "_" + i);
    gsap.set(s, { opacity: 0 });
    tl.fromTo(s, { opacity: 0, scale: 0.5, y: 16 }, { opacity: 1, scale: 1, y: 0, duration: 0.12, ease: "back.out(2.6)", immediateRender: false }, w.s);
    if (s.classList.contains("em")) tl.set(s, { color: "#FFD400" }, w.s);
  });
});

window.__timelines = window.__timelines || {};
window.__timelines["main"] = tl;
"""


# ------------------------------------------------------------------ sfx cues (picture-locked)
def cues():
    c = [("hit", B["bad"] + 0.02), ("hit", B["claude1"] + 0.06)]
    c += [("key", B["try1"] + 0.04 + i * (B["this"] + 0.26 - B["try1"]) / 6) for i in range(6)]
    c += [("pop", B["free"] + 0.03), ("pop", B["skill"] + 0.03), ("click", B["called"])]
    c += [("whoosh", TK["arena"][0]), ("boom", B["arena"] + 0.03)]
    c += [("thud", B["give"] + 0.2), ("pop", B["one1"]), ("hit", B["hundred1"] + 0.02)]
    c += [("whoosh", TK["grid"][0]), ("pop", TK["grid"][0] + 0.1), ("pop", TK["grid"][0] + 0.35), ("pop", TK["grid"][0] + 0.6)]
    c += [("pop", t) for t in (B["each1"], B["one2"], B["one2"] + 0.3, B["different"], B["different"] + 0.24, B["way"])]
    c += [("whoosh", B["then1"] + 0.15), ("thud", B["up"] + 0.09)]
    c += [("whoosh", TK["vs"][0]), ("boom", B["fight"] + 0.05)]
    c += [("hit", t + 0.12) for t, _, _ in ATTACKS]
    c += [("whoosh", B["and3"] + 0.1), ("tick", B["judge"]), ("tick", B["judge"] + 0.14), ("tick", B["picks"]), ("tick", B["picks"] + 0.12), ("tick", B["picks"] + 0.24)]
    c += [("thud", B["winner"] + 0.2), ("boom", B["out"] + 0.03)]
    c += [("click", t) for t, _, _ in LOOP[1:]]
    c += [("riser", B["left"] + 0.03), ("boom", B["left"] + 0.03)]
    c += [("hit", B["tip"] + 0.03)]
    q = B["mode"] + 0.05 - B["use"]
    c += [("key", B["use"] + i * q / 14) for i in range(0, 14, 2)]
    c += [("pop", B["mode"] + 0.05), ("glitch", B["tokens"] + 0.05)]
    c += [("whoosh", CUTS[3] + 0.3), ("hit", B["pinned"] + 0.04)]
    c += [("key", B["no"] - 0.05 + i * (B["comment"] - B["no"]) / 5) for i in range(5)]
    c += [("hit", B["comment"] + 0.05), ("boom", SC["end"][0] + 0.12), ("whoosh", SC["end"][0] + 0.95)]
    return sorted([[n, round(t, 3)] for n, t in c], key=lambda x: x[1])


(ROOT / "index.html").write_text(html())
(ROOT / "src/sfx-cues.json").write_text(json.dumps(cues()))
print("index.html written;", len(GROUPS), "caption groups; scenes", {k: (round(a, 2), round(b, 2)) for k, (a, b) in SC.items()})
print("takeovers", {k: (round(a, 2), round(b, 2)) for k, (a, b) in TK.items()})
