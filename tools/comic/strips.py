"""Pack a beat's frames into one vertical WebP sprite strip."""
import sys
from pathlib import Path
from PIL import Image

PANEL_W, PANEL_H = 1280, 720
WEBP_QUALITY = 80


def pack_beat(panel_files, out_path, panel_w=PANEL_W, panel_h=PANEL_H):
    pairs = []
    for p in panel_files:
        p = Path(p)
        if not p.exists():
            print(f"WARNING: missing frame, skipping: {p}", file=sys.stderr)
            continue
        pairs.append(p)
    imgs = [Image.open(p).convert("RGB").resize((panel_w, panel_h)) for p in pairs]
    strip = Image.new("RGB", (panel_w, panel_h * len(imgs)))
    rects = []
    for i, im in enumerate(imgs):
        y = i * panel_h
        strip.paste(im, (0, y))
        rects.append({"x": 0, "y": y, "w": panel_w, "h": panel_h})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    strip.save(out_path, "WEBP", quality=WEBP_QUALITY, method=6)
    return rects


def augment_manifest(manifest, frames_dir, strips_dir, web_prefix):
    for beat in manifest["beats"]:
        files = [Path(frames_dir) / p["file"] for p in beat["panels"]]
        out_path = Path(strips_dir) / f"{beat['slug']}.webp"
        rects = pack_beat(files, out_path)
        beat["strip"] = f"{web_prefix}/{beat['slug']}.webp"
        beat["strip_w"] = PANEL_W
        beat["strip_h"] = PANEL_H * len(rects)
        # zip stops at shorter list — panels with missing frames get no rect
        for panel, rect in zip(beat["panels"], rects):
            panel["rect"] = rect
    return manifest
