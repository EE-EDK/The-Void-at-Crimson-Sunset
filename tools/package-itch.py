"""CLI: assemble an itch.io-ready zip (index.html at root) after validation."""
import argparse
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.comic.validate import validate

# Everything that ships. Relative to --root. frames-generated/ is intentionally excluded.
INCLUDE_GLOBS = ["*.html", "assets/css/*.css", "assets/js/*.js", "assets/vendor/*.js",
                 "assets/comic/*.json", "assets/comic/strips/act1/*.webp",
                 "assets/comic/narration/act1/*.mp3", "assets/audio/**/*",
                 "assets/video/*.mp4", "Media/*.wav"]


def _collect(root: Path):
    files = []
    for g in INCLUDE_GLOBS:
        files.extend(p for p in root.glob(g) if p.is_file())
    # de-dup, stable order
    seen, out = set(), []
    for p in files:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--out", default="dist/void-itch.zip")
    p.add_argument("--manifest", default="assets/comic/act1.comic.json")
    p.add_argument("--strips", default="assets/comic/strips/act1")
    p.add_argument("--skip-validate", action="store_true")
    args = p.parse_args(argv)

    root = Path(args.root)
    files = _collect(root)

    if not args.skip_validate:
        manifest = json.loads((root / args.manifest).read_text(encoding="utf-8"))
        errors = validate(manifest, root / args.strips, files, root)
        if errors:
            print(f"ABORT: manifest invalid ({len(errors)} errors). Run validate-comic-manifest.py.")
            return 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, arcname=str(f.relative_to(root)).replace("\\", "/"))
    print(f"wrote {len(files)} files -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
