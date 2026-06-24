import json
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("build_cli", ROOT / "tools/build-comic-manifest.py")
build_cli = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_cli)


def test_writes_manifest(tmp_path):
    fix = Path(__file__).parent / "fixtures"
    gen = tmp_path / "gen"
    (gen / "output").mkdir(parents=True)
    (gen / "src").mkdir(parents=True)
    (gen / "output/act1-1006-frame-plan.json").write_text((fix / "frame-plan.json").read_text())
    (gen / "src/act1-dialogue.json").write_text((fix / "dialogue.json").read_text())
    (gen / "output/act1-story-index.csv").write_text((fix / "story-index.csv").read_text())
    out = tmp_path / "act1.comic.json"

    rc = build_cli.main(["--gen-repo", str(gen), "--out", str(out)])

    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["beats"][0]["beat"] == "headache_studio"
