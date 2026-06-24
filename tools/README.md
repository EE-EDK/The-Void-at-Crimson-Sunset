# Comic Build Pipeline

Run from the web repo root with the venv python (`.venv/Scripts/python`):

1. `build-comic-manifest.py` — joins generation-repo metadata (`--gen-repo`,
   default `../../ai-video-photo/The Void is Crimson`) into `assets/comic/act1.comic.json`.
2. `pack-comic-strips.py` — packs each beat's frames from `frames-generated/` into one
   WebP strip under `assets/comic/strips/act1/` and writes per-panel `rect`s into the manifest.
3. `validate-comic-manifest.py` — checks manifest integrity + itch.io limits (≤1000 files etc).
4. `package-itch.py` — assembles `dist/void-itch.zip` (index.html at root) after validation.

Tests: `.venv/Scripts/python -m pytest tools/tests -v`

Narration (`narration` field) stays `"pending"` here; Plan 2 fills section S1.
