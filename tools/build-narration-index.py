"""CLI: transcode available S1 narration mixes to MP3 and write the narration index."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.comic.narration import build_index

DEFAULT_GEN = "../../ai-video-photo/The Void is Crimson"
SHOTS_REL = "src/act1-video-shots-S1.json"
NARR_REL = "generated/videos/_narr"
OUT_DIR = "assets/comic/narration/act1"
WEB_PREFIX = "assets/comic/narration/act1"
OUT_INDEX = "assets/comic/act1.narration.json"


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--gen-repo", default=DEFAULT_GEN)
    args = p.parse_args(argv)
    gen = Path(args.gen_repo)

    shots = json.loads((gen / SHOTS_REL).read_text(encoding="utf-8"))
    if isinstance(shots, dict):
        shots = shots.get("shots", [])

    narr_dir = gen / NARR_REL
    available = {f.stem.replace("_mixed", "")
                 for f in narr_dir.glob("*_mixed.wav")}

    out_dir = Path(OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    for sid in sorted(available):
        src = narr_dir / f"{sid}_mixed.wav"
        dst = out_dir / f"{sid}.mp3"
        subprocess.run(["ffmpeg", "-y", "-i", str(src),
                        "-codec:a", "libmp3lame", "-q:a", "4", str(dst)], check=True)

    index = build_index(shots, available, WEB_PREFIX)
    Path(OUT_INDEX).write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    ready = [s["shot"] for s in index["shots"] if s["status"] == "ready"]
    print(f"narration: {len(ready)} ready shots {ready}; index -> {OUT_INDEX}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
