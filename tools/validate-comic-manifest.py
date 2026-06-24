"""CLI: validate manifest + the set of files that would ship to itch.io."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.comic.validate import validate

DEFAULT_MANIFEST = "assets/comic/act1.comic.json"
DEFAULT_STRIPS = "assets/comic/strips/act1"
# Files that ship to itch.io (relative to web root). Excludes frames-generated/ (gitignored source).
DEPLOY_GLOBS = ["*.html", "assets/css/*.css", "assets/js/*.js", "assets/vendor/*.js",
                "assets/comic/*.json", "assets/comic/strips/act1/*.webp",
                "assets/comic/narration/act1/*.mp3", "assets/audio/**/*.ogg",
                "assets/audio/**/*.mp3", "assets/video/*.mp4"]


def collect_deploy_files(root: Path):
    files = []
    for g in DEPLOY_GLOBS:
        files.extend(sorted(root.glob(g)))
    return files


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", default=DEFAULT_MANIFEST)
    p.add_argument("--strips", default=DEFAULT_STRIPS)
    p.add_argument("--root", default=".")
    args = p.parse_args(argv)

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    files = collect_deploy_files(Path(args.root))
    errors = validate(manifest, Path(args.strips), files)
    if errors:
        print(f"INVALID ({len(errors)} errors):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK: {len(manifest['beats'])} beats, {len(files)} deploy files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
