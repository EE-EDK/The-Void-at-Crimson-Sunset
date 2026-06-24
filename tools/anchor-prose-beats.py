"""CLI: anchor every beat to a paragraph, evenly spread across the prose."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.comic.anchor import distribute_anchors

DEFAULT_HTML = "act1-fifth-harmonic.html"
DEFAULT_MANIFEST = "assets/comic/act1.comic.json"

# Beats whose narrated line is paraphrased in the prose (so text-matching misses
# them) but which we want pinned to a specific paragraph for alignment.
MANUAL_PINS = [
    ("therapist", "stopped telling his therapist"),
    ("coordinates_write", "43°41'23"),
]


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--html", default=DEFAULT_HTML)
    p.add_argument("--manifest", default=DEFAULT_MANIFEST)
    args = p.parse_args(argv)

    beats = json.loads(Path(args.manifest).read_text(encoding="utf-8"))["beats"]
    html = Path(args.html).read_text(encoding="utf-8")
    new_html, anchored, paras = distribute_anchors(html, beats, MANUAL_PINS)
    Path(args.html).write_text(new_html, encoding="utf-8")
    print(f"anchored {anchored}/{len(beats)} beats across {paras} paragraphs "
          f"(~1 image every {paras / max(anchored, 1):.1f} paragraphs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
