"""Canonical list of files that ship to itch.io (also the set size/count-validated)."""
from pathlib import Path

# Single source of truth for the deployable set (paths relative to the web root).
# Use explicit extensions, never a bare **/* (an unexpected large file must not slip in unvalidated).
DEPLOY_GLOBS = [
    "*.html",
    "assets/css/*.css",
    "assets/js/*.js",
    "assets/vendor/*.js",
    "assets/comic/*.json",
    "assets/comic/strips/act1/*.webp",
    "assets/comic/narration/act1/*.mp3",
    "assets/audio/**/*.ogg",
    "assets/audio/**/*.mp3",
    "assets/video/*.mp4",
    "Media/*.wav",
]


def collect_deploy_files(root):
    files = []
    for g in DEPLOY_GLOBS:
        files.extend(p for p in Path(root).glob(g) if p.is_file())
    return list(dict.fromkeys(files))
