"""CLI: pack frames into per-beat WebP strips and augment the manifest in place."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.comic.strips import augment_manifest

DEFAULT_MANIFEST = "assets/comic/act1.comic.json"
DEFAULT_FRAMES = "frames-generated"
DEFAULT_STRIPS = "assets/comic/strips/act1"
WEB_PREFIX = "assets/comic/strips/act1"


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", default=DEFAULT_MANIFEST)
    p.add_argument("--frames", default=DEFAULT_FRAMES)
    p.add_argument("--strips", default=DEFAULT_STRIPS)
    p.add_argument("--web-prefix", default=WEB_PREFIX)
    args = p.parse_args(argv)

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    augment_manifest(manifest, Path(args.frames), Path(args.strips), args.web_prefix)
    Path(args.manifest).write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"packed {len(manifest['beats'])} strips -> {args.strips}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
