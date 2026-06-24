"""Join frame-plan + dialogue + story-index into a structural comic manifest."""
import csv
import json
from pathlib import Path

from tools.comic.slugs import slugify

ACT_TITLE = "The Fifth Harmonic"


def load_sources(gen_repo: Path):
    fp = json.loads((gen_repo / "output/act1-1006-frame-plan.json").read_text(encoding="utf-8"))
    dlg = json.loads((gen_repo / "src/act1-dialogue.json").read_text(encoding="utf-8"))
    text = (gen_repo / "output/act1-story-index.csv").read_text(encoding="utf-8")
    rows = list(csv.DictReader(text.splitlines()))
    return fp, dlg, rows


def _beat_descriptions(story_rows):
    """First description seen per beat (entry row wins by file order)."""
    desc = {}
    for row in story_rows:
        beat = row["beat"]
        if beat not in desc and row.get("description"):
            desc[beat] = row["description"].strip()
    return desc


def build_manifest(frame_plan, dialogue, story_rows):
    descriptions = _beat_descriptions(story_rows)
    frames = sorted(frame_plan["frames"], key=lambda f: f["global_frame"])

    beats = []
    by_beat = {}
    for f in frames:
        beat = f["beat"]
        if beat not in by_beat:
            entry = {
                "beat": beat,
                "slug": slugify(beat),
                "section": f["section"],
                "pacing_role": f["pacing_role"],
                "is_section_break": beat.startswith("section_break"),
                "narration": "pending",
                "panels": [],
                "dialogue": dialogue.get(beat, []),
            }
            by_beat[beat] = entry
            beats.append(entry)
        base = descriptions.get(beat, beat)
        by_beat[beat]["panels"].append({
            "file": f["target_filename"],
            "role": f["role"],
            "alt": f"{base} ({f['role']})",
        })

    return {"act": "I", "title": ACT_TITLE, "beats": beats}
