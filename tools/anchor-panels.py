"""CLI: anchor one panel per paragraph.

Reads the curated paragraph->panel map (assets/comic/act1.panelmap.json, keyed by
paragraph index) and tags each mapped <p> with data-pidx="<index>" so the comic
engine can drop the matching frame after it. Replaces the older beat-level
anchoring (data-beat); both are stripped first so re-runs stay clean.
"""
import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_HTML = "act1-fifth-harmonic.html"
DEFAULT_PANELMAP = "assets/comic/act1.panelmap.json"

_P = re.compile(r"<p\b([^>]*)>(.*?)</p>", re.IGNORECASE | re.DOTALL)


def strip_anchors(html):
    html = re.sub(r'\s+data-beat="[^"]*"', "", html)
    html = re.sub(r'\s+data-pidx="[^"]*"', "", html)
    return html


def apply_panelmap(html, mapping):
    """Tag the Nth paragraph with data-pidx=N for every index in `mapping`."""
    html = strip_anchors(html)
    paragraphs = list(_P.finditer(html))
    P = len(paragraphs)
    wanted = {int(k) for k in mapping}
    placed = 0
    for i in sorted(wanted, reverse=True):
        if not (0 <= i < P):
            continue
        m = paragraphs[i]
        html = (html[:m.start()]
                + f'<p data-pidx="{i}"{m.group(1)}>{m.group(2)}</p>'
                + html[m.end():])
        placed += 1
    return html, placed, P


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--html", default=DEFAULT_HTML)
    p.add_argument("--panelmap", default=DEFAULT_PANELMAP)
    args = p.parse_args(argv)

    mapping = json.loads(Path(args.panelmap).read_text(encoding="utf-8"))
    html = Path(args.html).read_text(encoding="utf-8")
    new_html, placed, paras = apply_panelmap(html, mapping)
    Path(args.html).write_text(new_html, encoding="utf-8")
    print(f"anchored {placed}/{len(mapping)} panels across {paras} paragraphs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
