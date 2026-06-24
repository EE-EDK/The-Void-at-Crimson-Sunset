import json
from pathlib import Path
from tools.comic.manifest import build_manifest

FIX = Path(__file__).parent / "fixtures"


def _load():
    fp = json.loads((FIX / "frame-plan.json").read_text(encoding="utf-8"))
    dlg = json.loads((FIX / "dialogue.json").read_text(encoding="utf-8"))
    import csv
    rows = list(csv.DictReader((FIX / "story-index.csv").read_text(encoding="utf-8").splitlines()))
    return fp, dlg, rows


def test_beats_ordered_and_grouped():
    m = build_manifest(*_load())
    assert [b["beat"] for b in m["beats"]] == ["headache_studio", "section_break_I"]
    assert len(m["beats"][0]["panels"]) == 2


def test_pacing_role_from_first_frame():
    m = build_manifest(*_load())
    assert m["beats"][0]["pacing_role"] == "cut-busy"


def test_alt_is_beat_description_plus_role():
    m = build_manifest(*_load())
    assert m["beats"][0]["panels"][0]["alt"] == \
        "Extreme close-up, Alex's fingers pressed hard against his left temple. (establish)"


def test_dialogue_attached_per_beat():
    m = build_manifest(*_load())
    assert m["beats"][0]["dialogue"][1]["speaker"] == "jen"
    assert m["beats"][1]["dialogue"] == []


def test_section_break_flagged_and_narration_pending():
    m = build_manifest(*_load())
    assert m["beats"][1]["is_section_break"] is True
    assert all(b["narration"] == "pending" for b in m["beats"])
