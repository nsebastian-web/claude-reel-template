# Forced-align your take (MMS_FA) against the verbatim transcript.
# Run with ~/.cache/fa-venv/bin/python src/align.py from the project dir.
import json, re, torch, torchaudio, soundfile as sf
from torchaudio.pipelines import MMS_FA as bundle
torch.set_num_threads(4)

# (display word, spoken form for the aligner). Display keeps digits and brand casing.
import sys
WAV = sys.argv[1] if len(sys.argv) > 1 else 'src/edit-16k.wav'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'src/fa-words.json'
# what is said in the EDIT (fillers cut). display|spoken-form; display keeps brand casing.
TEXT = open(sys.argv[3] if len(sys.argv) > 3 else 'src/text-raw.txt').read()

pairs = []
for tok in TEXT.split():
    disp, _, spoken = tok.partition('|')
    if spoken:  # keep trailing punctuation of the display token on display
        punct = re.sub(r"^[^.,!?]*", "", spoken)
        spoken = spoken.rstrip('.,!?')
    else:
        spoken = disp
    norm = re.sub(r"[^a-z']", "", spoken.lower()) or "uh"
    pairs.append((disp if not tok.count('|') else disp + re.sub(r"^[^.,!?]*", "", tok.split('|')[1]), norm))

data, sr = sf.read(WAV)
wav = torch.tensor(data, dtype=torch.float32)
if wav.ndim == 2: wav = wav.mean(1)
wav = wav.unsqueeze(0)
if sr != bundle.sample_rate:
    wav = torchaudio.functional.resample(wav, sr, bundle.sample_rate); sr = bundle.sample_rate

model, tokenizer, aligner = bundle.get_model(), bundle.get_tokenizer(), bundle.get_aligner()
with torch.inference_mode():
    emission, _ = model(wav)
spans = aligner(emission[0], tokenizer([n for _, n in pairs]))
ratio = wav.size(1) / emission.size(1) / sr

words = []
for (disp, _), sp in zip(pairs, spans):
    words.append({"text": disp, "start": round(sp[0].start * ratio, 3), "end": round(sp[-1].end * ratio, 3)})
json.dump(words, open(OUT, 'w'), indent=1)
for a, b in zip(words, words[1:]):
    gap = b["start"] - a["end"]
    if gap > 0.25: print(f"gap {gap:.2f}s after '{a['text']}' at {a['end']:.2f}")
print(len(words), "words", words[0], words[-1])
