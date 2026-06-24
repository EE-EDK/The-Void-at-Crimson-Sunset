"""Slug helpers for itch.io-safe, case-stable asset names."""
import re

_KEEP = re.compile(r"[^a-z0-9\-]+")


def slugify(text: str) -> str:
    """Lowercase; non [a-z0-9-] runs -> '_'; collapse/trim underscores."""
    lowered = text.lower()
    underscored = _KEEP.sub("_", lowered)
    collapsed = re.sub(r"_+", "_", underscored)
    return collapsed.strip("_")


def beat_slug(beat: str) -> str:
    return slugify(beat)
