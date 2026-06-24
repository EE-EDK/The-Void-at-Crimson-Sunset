"""Pack a beat's frames into one vertical WebP sprite strip."""
import sys
from pathlib import Path
from PIL import Image

PANEL_W, PANEL_H = 1280, 720
WEBP_QUALITY = 80


def pack_beat(panel_files, out_path, panel_w=PANEL_W, panel_h=PANEL_H):
    imgs = [Image.open(p).convert("RGB").resize((panel_w, panel_h)) for p in panel_files]
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
        present_panels, present_files = [], []
        for p in beat["panels"]:
            fp = Path(frames_dir) / p["file"]
            if fp.exists():
                present_panels.append(p); present_files.append(fp)
            else:
                print(f"WARNING: missing frame, dropping panel: {p['file']}", file=sys.stderr)
        out_path = Path(strips_dir) / f"{beat['slug']}.webp"
        rects = pack_beat(present_files, out_path)
        beat["panels"] = present_panels
        beat["strip"] = f"{web_prefix}/{beat['slug']}.webp"
        beat["strip_w"] = PANEL_W
        beat["strip_h"] = PANEL_H * len(rects)
        for panel, rect in zip(present_panels, rects):
            panel["rect"] = rect
    return manifest
