# claude-reel-template

Record one take. Claude Code edits it into a reel: cuts your pauses, syncs every caption to your voice
word by word, builds the animations around you, ducks the music under your voice, and renders it.

The whole stack is free and open source. The only paid tool is Claude.

| Job | Tool |
|---|---|
| Video, animation, render | [HyperFrames](https://github.com/heygen-com/hyperframes) (HTML to video) + GSAP |
| Transcript | Whisper (`npx hyperframes transcribe`) |
| Word-perfect captions | torchaudio MMS forced alignment |
| Cuts, voice cleanup, music ducking, loudness | FFmpeg |
| Sound effects | numpy (synthesized, no samples) |

## Setup (about 10 minutes)
1. Install Node 22+, FFmpeg, Google Chrome and Python 3.12.
2. Clone this repo and open it in [Claude Code](https://claude.com/claude-code).
3. Install the HyperFrames skills: `npm run skills`
4. Create the forced-alignment venv:
   ```bash
   python3.12 -m venv ~/.cache/fa-venv && ~/.cache/fa-venv/bin/pip install torch torchaudio soundfile numpy
   ```
5. Health check: `npm run doctor`

## Make a reel
1. Record one take. Landscape or vertical, face centred, half-second pause between lines.
2. `npm run new -- my-first-reel /path/to/take.mov`
3. Drop a free music track into `assets/audio/music/` (sources in its README).
4. In Claude Code, say: **"make a reel from projects/my-first-reel, here's my script: ..."**
5. Claude follows `CLAUDE.md`, shows you a preview link, and renders when you say "render it".

## What's inside
- `CLAUDE.md`: the pipeline Claude follows, step by step, plus the gotchas.
- `pipeline/`: cut (`edit.py`), forced alignment (`align.py`, `map-words.py`), SFX (`sfx.py`), ducked mix (`build-mix.py`).
- `examples/split-fight-reel/`: a complete generator for a split-screen reel (graphics on top, you below,
  karaoke captions on the seam, full-screen takeovers with a LIVE facecam). Start from it and restyle.

Made by [@nikcore.ai](https://www.instagram.com/nikcore.ai/). MIT licensed.
