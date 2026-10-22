#!/usr/bin/env bash
# Scaffold a reel project: projects/<name>/ with the pipeline in src/ and a reel.json to fill in.
# Usage: npm run new -- <name> /absolute/path/to/take.mov
set -euo pipefail
NAME="${1:?usage: npm run new -- <name> <take.mov>}"; TAKE="${2:?path to your take}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; P="$ROOT/projects/$NAME"
[ -e "$P" ] && { echo "projects/$NAME already exists"; exit 1; }
mkdir -p "$P/src" "$P/media"
cp "$ROOT"/pipeline/*.py "$P/src/"
cp "$ROOT/examples/split-fight-reel/build.py" "$P/build.py"
printf '{\n  "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",\n  "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}\n}\n' > "$P/hyperframes.json"
sed "s#/absolute/path/to/your-take.mov#$TAKE#" "$ROOT/reel.example.json" > "$P/reel.json"
ffmpeg -v error -y -i "$TAKE" -ac 1 -ar 16000 "$P/src/take-16k.wav"
echo "Created projects/$NAME. Open Claude Code in this repo and say: make a reel from projects/$NAME"
