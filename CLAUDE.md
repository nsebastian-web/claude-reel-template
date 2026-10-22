# Reel studio: instructions for Claude Code

You turn one raw talking-head take into a finished 9:16 reel with HyperFrames (HTML rendered to video).
Everything runs locally and is free: HyperFrames, Whisper, torchaudio forced alignment, FFmpeg, numpy SFX.

## Hard rules
- Free and open source only. Never add a paid API or service.
- Never render without showing the person the Studio preview first (`npx hyperframes preview`) and getting an explicit "render it".
- Caption sync is the #1 quality bar: every word pops on exactly when it is spoken. Use forced alignment, never raw Whisper times.
- Every number or claim on screen must come from the person's script or a source they gave you.
- Load the HyperFrames skills before writing any composition: `/hyperframes`, `/hyperframes-cli`, `/gsap`.

## The pipeline (one project = projects/<name>/, created with `npm run new -- <name> <take.mov>`)
1. **Transcribe**: `npx hyperframes transcribe src/take-16k.wav -m medium.en --json`. Read what was really said.
2. **Find pauses**: `ffmpeg -i src/take-16k.wav -af silencedetect=noise=-38dB:d=0.3 -f null -`.
   Whisper smears the first words over leading silence, trust silencedetect for where speech starts.
3. **Pick segments**: fill `reel.json` `segments` with the stretches to KEEP (drop long pauses, flubbed takes,
   fillers). If a line was said twice, keep the better take and cut the other.
4. **Cut**: `python3 src/edit.py` writes `media/face.mp4`, `media/vo-clean.wav`, `src/edl.json`.
5. **Align**: write the exact spoken words (including any cut takes) to `src/text-raw.txt`
   (`display|spoken` for numbers, e.g. `40|forty`), then
   `<venv>/bin/python src/align.py src/take-16k.wav src/fa-raw.json src/text-raw.txt` and `python3 src/map-words.py`.
   The venv: `python3.12 -m venv ~/.cache/fa-venv && ~/.cache/fa-venv/bin/pip install torch torchaudio soundfile numpy`.
   Check: every gap the aligner reports should match a silencedetect pause.
6. **Design**: write `SPEC.md` (look, palette, fonts, shots keyed to words). Edit `build.py` (it generates `index.html`).
   Key every animation to a word with `at("word", n)` so picture and voice stay locked.
   `examples/split-fight-reel/` is a complete worked example: split layout, takeovers with a LIVE facecam, seam captions.
7. **Sound**: `python3 build.py` also writes `src/sfx-cues.json`; `<venv>/bin/python src/sfx.py`; then
   `python3 src/build-mix.py` (ducks the music under the voice, masters to -14 LUFS, checks the tail is not silent).
   Copy the chosen `media/mix-<name>.wav` to `media/mix.wav`.
8. **Check**: `npx hyperframes check --json` (fix every error), then `npx hyperframes snapshot --at <times>` and look at the frames.
9. **Preview**: `npx hyperframes preview`, share the URL, wait for approval.
10. **Render**: `npx hyperframes render -q delivery -o ../../output/<name>.mp4`.

## Gotchas that cost hours
- One DOM node, one writer: never let two tweens write the same text node. Counters and split-flaps use a single onUpdate.
- A second `<video>` with the same src/start/duration (e.g. a facecam) triggers a duplicate-media warning. Crop a separate facecam file.
- GSAP `className` tweens silently do nothing. Animate real properties (opacity, color, transform).
- `loudnorm` and `sidechaincompress` can silently eat the end of the audio. build-mix.py pads, then asserts the tail level.
- This FFmpeg may have no `drawtext`. Put all text in HTML.
- No `Math.random()`, no `Date.now()`, no `repeat: -1`. Use the seeded `mulberry()` helper.
