"""CLI: build assets/comic/act1.comic.json from generation-repo metadata."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.comic.manifest import build_manifest, load_sources

DEFAULT_GEN = "../../ai-video-photo/The Void is Crimson"
DEFAULT_OUT = "assets/comic/act1.comic.json"


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--gen-repo", default=DEFAULT_GEN)
    p.add_argument("--out", default=DEFAULT_OUT)
    args = p.parse_args(argv)

    manifest = build_manifest(*load_sources(Path(args.gen_repo)))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(manifest['beats'])} beats -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
