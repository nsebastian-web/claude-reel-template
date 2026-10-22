# Example: split-screen fight reel

The generator behind a 33 s reel explaining a Claude Code skill: fighting-game broadcast look, graphics on top,
the speaker below, pop-on karaoke captions on the seam, four full-screen takeovers with a LIVE facecam.

`build.py` reads `src/edl.json` and `src/fa-words.json` (made by the pipeline), keys every beat to a spoken word
with `at("word", n)`, and writes `index.html` plus `src/sfx-cues.json`. The scene text is specific to that reel,
so treat it as a pattern: keep the helpers (captions, takeovers, facecam, shake, slam, seeded randomness) and
replace the scenes with your own. `SPEC.md` is the design brief it was built from.
