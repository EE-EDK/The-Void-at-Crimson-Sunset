"""Validate a packed comic manifest + itch.io deploy constraints."""
import os
import re
from pathlib import Path

SLUG_RE = re.compile(r"^[a-z0-9_-]+$")
MAX_FILES = 1000
MAX_PATH = 240
MAX_FILE_BYTES = 200 * 1024 * 1024
MAX_TOTAL_BYTES = 500 * 1024 * 1024


def validate(manifest, strips_dir, deploy_files, root):
    errors = []
    beats = manifest.get("beats", [])
    if not beats:
        errors.append("manifest has no beats")

    for b in beats:
        slug = b.get("slug", "")
        if not SLUG_RE.match(slug):
            errors.append(f"beat '{b.get('beat')}' has non-slug-safe slug '{slug}'")
        if not b.get("panels"):
            errors.append(f"beat '{b.get('beat')}' has no panels")
        for panel in b.get("panels", []):
            if "rect" not in panel:
                errors.append(f"panel {panel.get('file')} in '{b.get('beat')}' missing rect")
        strip = b.get("strip")
        if not strip or not (Path(strips_dir) / f"{slug}.webp").exists():
            errors.append(f"beat '{b.get('beat')}' strip file missing: {strip}")

    if len(deploy_files) > MAX_FILES:
        errors.append(f"deploy has {len(deploy_files)} files; itch.io max is {MAX_FILES}")
    total = 0
    for f in deploy_files:
        rel = os.path.relpath(f, root).replace(os.sep, "/")
        if len(rel) > MAX_PATH:
            errors.append(f"path exceeds {MAX_PATH} chars: {rel}")
        if f.exists():
            size = f.stat().st_size
            total += size
            if size > MAX_FILE_BYTES:
                errors.append(f"file exceeds 200MB: {rel}")
    if total > MAX_TOTAL_BYTES:
        errors.append(f"total deploy size {total} exceeds 500MB")
    return errors
