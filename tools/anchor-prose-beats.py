"""CLI: insert data-beat anchors into the prose page; report coverage."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.comic.anchor import annotate_html

DEFAULT_HTML = "act1-fifth-harmonic.html"
DEFAULT_MANIFEST = "assets/comic/act1.comic.json"


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--html", default=DEFAULT_HTML)
    p.add_argument("--manifest", default=DEFAULT_MANIFEST)
    args = p.parse_args(argv)

    beats = json.loads(Path(args.manifest).read_text(encoding="utf-8"))["beats"]
    html = Path(args.html).read_text(encoding="utf-8")
    new_html, matched, unmatched = annotate_html(html, beats)
    Path(args.html).write_text(new_html, encoding="utf-8")
    print(f"anchored {len(matched)}/{len(beats)} beats; {len(unmatched)} unmatched")
    if unmatched:
        print("UNMATCHED (need manual data-beat placement):")
        for b in unmatched:
            print(f"  - {b}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
