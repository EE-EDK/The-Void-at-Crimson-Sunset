# Act I Comic Build Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the offline data pipeline that turns the generation repo's frame/dialogue metadata + the local frame images into one runtime manifest (`assets/comic/act1.comic.json`), per-beat WebP sprite strips, and an itch.io-ready zip.

**Architecture:** Three Python CLI tools run in sequence — `build-comic-manifest.py` (join metadata → structural manifest), `pack-comic-strips.py` (pack each beat's frames into one WebP strip and write per-panel offsets back into the manifest), `validate-comic-manifest.py` (enforce integrity + itch.io limits). A fourth tool `package-itch.py` assembles the deployable zip and runs the validator. This plan covers the pipeline only; the web runtime that consumes the manifest is Plan 2.

**Tech Stack:** Python 3.10, Pillow (image packing), pytest (tests), stdlib `json`/`csv`/`zipfile`.

## Global Constraints

- Frames are 1280×720 JPG, named `#### - <role> - <beat>.jpg`, in `frames-generated/` (web repo, gitignored).
- Generation-repo metadata path defaults to `../../ai-video-photo/The Void is Crimson` relative to web repo root; override via `--gen-repo`.
- Source metadata files (in gen repo): `output/act1-1006-frame-plan.json`, `src/act1-dialogue.json`, `output/act1-story-index.csv`.
- Output paths (web repo): manifest `assets/comic/act1.comic.json`; strips `assets/comic/strips/act1/<beat-slug>.webp`; committed to git.
- itch.io limits enforced by validator: ≤ 1000 files, ≤ 500 MB extracted, ≤ 200 MB/file, ≤ 240-char paths, all-relative + slug-safe (lowercase, `[a-z0-9_-]` + `/` + `.` only), no leading `/`.
- Slug rule: lowercase; spaces/`+`/parentheses/apostrophes → `_`; collapse repeats; strip leading/trailing `_`.
- Manifest beats ordered by `global_frame` (narrative order); each beat's `pacing_role` = its first frame's `pacing_role`.
- `narration` field on every beat defaults to `"pending"` (Plan 2 flips S1 beats to `"ready"`).
- Use an isolated venv at `.venv`; never install into anaconda base.
- Commit after each task with the shown message.

---

### Task 1: Project scaffold + `slugify` utility

**Files:**
- Create: `tools/comic/__init__.py` (empty)
- Create: `tools/comic/slugs.py`
- Create: `tools/requirements.txt`
- Create: `tools/tests/__init__.py` (empty)
- Create: `tools/tests/test_slugs.py`
- Create: `tools/pytest.ini`

**Interfaces:**
- Produces: `tools/comic/slugs.py` → `slugify(text: str) -> str`; `beat_slug(beat: str) -> str` (alias of `slugify`).

- [ ] **Step 1: Create the venv and install deps**

Run:
```bash
cd "C:/Users/edk7c/ENGINEERING-PROJECTS/ACTIVE-PROJECTS/web/the-void-is-crimson"
python -m venv .venv
.venv/Scripts/python -m pip install --upgrade pip
.venv/Scripts/python -m pip install Pillow==12.2.0 pytest==8.3.4
```
Expected: installs succeed; `.venv/Scripts/python -c "import PIL, pytest"` prints nothing (no error).

- [ ] **Step 2: Write `tools/requirements.txt`**

```
Pillow==12.2.0
pytest==8.3.4
```

- [ ] **Step 3: Write `tools/pytest.ini`**

```ini
[pytest]
testpaths = tools/tests
python_files = test_*.py
```

- [ ] **Step 4: Write the failing test** — `tools/tests/test_slugs.py`

```python
from tools.comic.slugs import slugify


def test_lowercases_and_replaces_spaces():
    assert slugify("Section Break I") == "section_break_i"


def test_strips_punctuation_to_underscore():
    assert slugify("key-object ANCHOR (bow + lowest string)") == "key-object_anchor_bow_lowest_string"


def test_collapses_and_trims_underscores():
    assert slugify("  Iris  Kohler's   viola  ") == "iris_kohler_s_viola"


def test_keeps_existing_beat_ids_stable():
    assert slugify("headache_studio") == "headache_studio"
```

- [ ] **Step 5: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tools/tests/test_slugs.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tools.comic.slugs'`

- [ ] **Step 6: Create the empty package files**

Create `tools/comic/__init__.py` and `tools/tests/__init__.py` as empty files. Add a root `tools/__init__.py` (empty) so `tools.comic` imports resolve under pytest's rootdir.

- [ ] **Step 7: Implement `tools/comic/slugs.py`**

```python
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
```

- [ ] **Step 8: Run tests to verify pass**

Run: `.venv/Scripts/python -m pytest tools/tests/test_slugs.py -v`
Expected: 4 passed

- [ ] **Step 9: Commit**

```bash
git add tools/ pytest.ini
git commit -m "feat(comic): scaffold build tools + slugify utility"
```

---

### Task 2: Load + join metadata into a structural manifest

**Files:**
- Create: `tools/comic/manifest.py`
- Create: `tools/tests/fixtures/frame-plan.json`
- Create: `tools/tests/fixtures/dialogue.json`
- Create: `tools/tests/fixtures/story-index.csv`
- Create: `tools/tests/test_manifest.py`

**Interfaces:**
- Consumes: `slugify` from Task 1.
- Produces: `tools/comic/manifest.py` →
  `build_manifest(frame_plan: dict, dialogue: dict, story_rows: list[dict]) -> dict`.
  Manifest shape:
  ```json
  {"act":"I","title":"The Fifth Harmonic","beats":[
    {"beat":"headache_studio","slug":"headache_studio","section":"I","pacing_role":"cut-busy",
     "is_section_break":false,"narration":"pending",
     "panels":[{"file":"0001 - establish - headache_studio.jpg","role":"establish",
                "alt":"Extreme close-up... (establish)"}],
     "dialogue":[{"speaker":"narrator","line":"...","direction":"...","timing":"0:00-0:04"}]}
  ]}
  ```
- Produces: `load_sources(gen_repo: Path) -> tuple[dict, dict, list[dict]]` (reads the three files).

- [ ] **Step 1: Write fixtures** — minimal 2-beat slice.

`tools/tests/fixtures/frame-plan.json`:
```json
{"title":"x","frames":[
 {"global_frame":1,"beat_order":1,"frame_in_beat":1,"role":"establish","section":"I","beat":"headache_studio","pacing_role":"cut-busy","target_filename":"0001 - establish - headache_studio.jpg"},
 {"global_frame":2,"beat_order":1,"frame_in_beat":2,"role":"anchor-prop","section":"I","beat":"headache_studio","pacing_role":"cut-busy","target_filename":"0002 - anchor-prop - headache_studio.jpg"},
 {"global_frame":3,"beat_order":2,"frame_in_beat":1,"role":"establishing-empty-road","section":"I","beat":"section_break_I","pacing_role":"hold-long","target_filename":"0145 - establishing-empty-road - section_break_I.jpg"}
]}
```

`tools/tests/fixtures/dialogue.json`:
```json
{"headache_studio":[
 {"speaker":"narrator","line":"The headache had been living behind Alex Reeves's left eye for six days.","direction":"intimate literary","timing":"0:00-0:04"},
 {"speaker":"jen","line":"Alex. You're doing it wrong again.","direction":"warm alto","timing":"0:05-0:08"}
]}
```

`tools/tests/fixtures/story-index.csv`:
```csv
global_frame,section,clip_index,beat,role,characters,description,dialogue
1,I,1,headache_studio,entry,"alex, jen, narrator","Extreme close-up, Alex's fingers pressed hard against his left temple.","[]"
2,I,1,headache_studio,mid,"alex, jen, narrator","Wide shot of cluttered mixing desk.","[]"
3,I,2,section_break_I,entry,"","Empty road under basalt silhouette.","[]"
```

- [ ] **Step 2: Write the failing test** — `tools/tests/test_manifest.py`

```python
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
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tools/tests/test_manifest.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tools.comic.manifest'`

- [ ] **Step 4: Implement `tools/comic/manifest.py`**

```python
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
```

- [ ] **Step 5: Run tests to verify pass**

Run: `.venv/Scripts/python -m pytest tools/tests/test_manifest.py -v`
Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add tools/comic/manifest.py tools/tests/test_manifest.py tools/tests/fixtures/
git commit -m "feat(comic): build structural manifest from metadata join"
```

---

### Task 3: `build-comic-manifest.py` CLI

**Files:**
- Create: `tools/build-comic-manifest.py`
- Create: `tools/tests/test_build_cli.py`

**Interfaces:**
- Consumes: `load_sources`, `build_manifest` from Task 2.
- Produces: CLI writing `assets/comic/act1.comic.json`. Importable `main(argv: list[str]) -> int`.

- [ ] **Step 1: Write the failing test** — `tools/tests/test_build_cli.py`

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tools/tests/test_build_cli.py -v`
Expected: FAIL (file not found / module load error)

- [ ] **Step 3: Implement `tools/build-comic-manifest.py`**

```python
"""CLI: build assets/comic/act1.comic.json from generation-repo metadata."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.comic.manifest import build_manifest, load_sources

DEFAULT_GEN = "../../ai-video-photo/The Void is Crimson"
DEFAULT_OUT = "assets/comic/act1.comic.json"


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--gen-repo", default=DEFAULT_GEN)
    p.add_argument("--out", default=DEFAULT_OUT)
    args = p.parse_args(argv)

    manifest = build_manifest(*load_sources(Path(args.gen_repo)))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(manifest['beats'])} beats -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the test to verify pass**

Run: `.venv/Scripts/python -m pytest tools/tests/test_build_cli.py -v`
Expected: 1 passed

- [ ] **Step 5: Generate the real manifest + sanity check**

Run:
```bash
.venv/Scripts/python tools/build-comic-manifest.py
.venv/Scripts/python -c "import json; m=json.load(open('assets/comic/act1.comic.json',encoding='utf-8')); print(len(m['beats']),'beats', sum(len(b['panels']) for b in m['beats']),'panels')"
```
Expected: ~180 beats, ~1006 panels.

- [ ] **Step 6: Commit**

```bash
git add tools/build-comic-manifest.py tools/tests/test_build_cli.py assets/comic/act1.comic.json
git commit -m "feat(comic): add manifest build CLI + generate act1.comic.json"
```

---

### Task 4: `pack-comic-strips.py` — pack beats into WebP strips

**Files:**
- Create: `tools/comic/strips.py`
- Create: `tools/pack-comic-strips.py`
- Create: `tools/tests/test_strips.py`

**Interfaces:**
- Consumes: manifest dict from Task 2/3; frame images in `frames-generated/`.
- Produces: `tools/comic/strips.py` →
  `pack_beat(panel_files: list[Path], out_path: Path, panel_w: int = 1280, panel_h: int = 720) -> list[dict]`
  returning per-panel offsets `[{"x":0,"y":0,"w":1280,"h":720}, ...]` (vertical stack), writing a WebP at `out_path`.
- Produces: `augment_manifest(manifest: dict, frames_dir: Path, strips_dir: Path, web_prefix: str) -> dict`
  adding to each beat: `"strip": "<web_prefix>/<slug>.webp"`, `"strip_w"`, `"strip_h"`, and `"rect"` per panel.

- [ ] **Step 1: Write the failing test** — `tools/tests/test_strips.py`

```python
from pathlib import Path
from PIL import Image
from tools.comic.strips import pack_beat, augment_manifest


def _img(path, color):
    Image.new("RGB", (1280, 720), color).save(path)


def test_pack_beat_stacks_vertically(tmp_path):
    a, b = tmp_path / "a.jpg", tmp_path / "b.jpg"
    _img(a, (255, 0, 0)); _img(b, (0, 255, 0))
    out = tmp_path / "beat.webp"
    rects = pack_beat([a, b], out)
    assert out.exists()
    assert rects == [{"x": 0, "y": 0, "w": 1280, "h": 720},
                     {"x": 0, "y": 720, "w": 1280, "h": 720}]
    assert Image.open(out).size == (1280, 1440)


def test_augment_manifest_adds_strip_and_rects(tmp_path):
    frames = tmp_path / "frames"; frames.mkdir()
    _img(frames / "0001 - establish - headache_studio.jpg", (10, 10, 10))
    strips = tmp_path / "strips"
    manifest = {"act": "I", "title": "t", "beats": [
        {"beat": "headache_studio", "slug": "headache_studio", "panels": [
            {"file": "0001 - establish - headache_studio.jpg", "role": "establish", "alt": "x"}]}]}
    out = augment_manifest(manifest, frames, strips, "assets/comic/strips/act1")
    beat = out["beats"][0]
    assert beat["strip"] == "assets/comic/strips/act1/headache_studio.webp"
    assert beat["strip_w"] == 1280 and beat["strip_h"] == 720
    assert beat["panels"][0]["rect"] == {"x": 0, "y": 0, "w": 1280, "h": 720}
    assert (strips / "headache_studio.webp").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tools/tests/test_strips.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tools.comic.strips'`

- [ ] **Step 3: Implement `tools/comic/strips.py`**

```python
"""Pack a beat's frames into one vertical WebP sprite strip."""
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
        files = [Path(frames_dir) / p["file"] for p in beat["panels"]]
        out_path = Path(strips_dir) / f"{beat['slug']}.webp"
        rects = pack_beat(files, out_path)
        beat["strip"] = f"{web_prefix}/{beat['slug']}.webp"
        beat["strip_w"] = PANEL_W
        beat["strip_h"] = PANEL_H * len(rects)
        for panel, rect in zip(beat["panels"], rects):
            panel["rect"] = rect
    return manifest
```

- [ ] **Step 4: Run tests to verify pass**

Run: `.venv/Scripts/python -m pytest tools/tests/test_strips.py -v`
Expected: 2 passed

- [ ] **Step 5: Implement `tools/pack-comic-strips.py` CLI**

```python
"""CLI: pack frames into per-beat WebP strips and augment the manifest in place."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.comic.strips import augment_manifest

DEFAULT_MANIFEST = "assets/comic/act1.comic.json"
DEFAULT_FRAMES = "frames-generated"
DEFAULT_STRIPS = "assets/comic/strips/act1"
WEB_PREFIX = "assets/comic/strips/act1"


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", default=DEFAULT_MANIFEST)
    p.add_argument("--frames", default=DEFAULT_FRAMES)
    p.add_argument("--strips", default=DEFAULT_STRIPS)
    args = p.parse_args(argv)

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    augment_manifest(manifest, Path(args.frames), Path(args.strips), WEB_PREFIX)
    Path(args.manifest).write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"packed {len(manifest['beats'])} strips -> {args.strips}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 6: Run the real packing + sanity check**

Run:
```bash
.venv/Scripts/python tools/build-comic-manifest.py
.venv/Scripts/python tools/pack-comic-strips.py
ls assets/comic/strips/act1 | wc -l
.venv/Scripts/python -c "import json; m=json.load(open('assets/comic/act1.comic.json',encoding='utf-8')); b=m['beats'][0]; print(b['strip'], b['strip_w'], b['strip_h'], b['panels'][0]['rect'])"
```
Expected: ~180 `.webp` files; first beat prints a strip path, width 1280, height = 720×panel_count, and a rect.

- [ ] **Step 7: Commit**

```bash
git add tools/comic/strips.py tools/pack-comic-strips.py tools/tests/test_strips.py assets/comic/strips/act1/ assets/comic/act1.comic.json
git commit -m "feat(comic): pack per-beat WebP sprite strips + augment manifest"
```

---

### Task 5: `validate-comic-manifest.py` — integrity + itch.io limits

**Files:**
- Create: `tools/comic/validate.py`
- Create: `tools/validate-comic-manifest.py`
- Create: `tools/tests/test_validate.py`

**Interfaces:**
- Consumes: packed manifest (Task 4); the web repo root for file-count/size checks.
- Produces: `tools/comic/validate.py` →
  `validate(manifest: dict, strips_dir: Path, deploy_files: list[Path]) -> list[str]`
  returning a list of human-readable error strings (empty = valid). Checks:
  every beat has ≥1 panel; every panel has a `rect`; each beat `strip` file exists;
  beats non-empty; all `slug` values are slug-safe; itch limits — `len(deploy_files) <= 1000`,
  each path `<= 240` chars, each file `<= 200 MB`, total `<= 500 MB`.

- [ ] **Step 1: Write the failing test** — `tools/tests/test_validate.py`

```python
from pathlib import Path
from PIL import Image
from tools.comic.validate import validate


def _strip(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (1280, 720), (0, 0, 0)).save(path, "WEBP")


def _ok_manifest(strips_dir):
    _strip(strips_dir / "headache_studio.webp")
    return {"beats": [{"beat": "headache_studio", "slug": "headache_studio",
                       "strip": "assets/comic/strips/act1/headache_studio.webp",
                       "panels": [{"file": "x.jpg", "role": "establish", "alt": "a",
                                   "rect": {"x": 0, "y": 0, "w": 1280, "h": 720}}]}]}


def test_valid_manifest_has_no_errors(tmp_path):
    m = _ok_manifest(tmp_path)
    assert validate(m, tmp_path, [tmp_path / "headache_studio.webp"]) == []


def test_missing_rect_is_error(tmp_path):
    m = _ok_manifest(tmp_path)
    del m["beats"][0]["panels"][0]["rect"]
    errs = validate(m, tmp_path, [tmp_path / "headache_studio.webp"])
    assert any("rect" in e for e in errs)


def test_too_many_files_is_error(tmp_path):
    m = _ok_manifest(tmp_path)
    files = [tmp_path / f"f{i}" for i in range(1001)]
    errs = validate(m, tmp_path, files)
    assert any("1000" in e for e in errs)


def test_bad_slug_is_error(tmp_path):
    m = _ok_manifest(tmp_path)
    m["beats"][0]["slug"] = "Bad Slug"
    errs = validate(m, tmp_path, [tmp_path / "headache_studio.webp"])
    assert any("slug" in e for e in errs)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tools/tests/test_validate.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tools.comic.validate'`

- [ ] **Step 3: Implement `tools/comic/validate.py`**

```python
"""Validate a packed comic manifest + itch.io deploy constraints."""
import re
from pathlib import Path

SLUG_RE = re.compile(r"^[a-z0-9_-]+$")
MAX_FILES = 1000
MAX_PATH = 240
MAX_FILE_BYTES = 200 * 1024 * 1024
MAX_TOTAL_BYTES = 500 * 1024 * 1024


def validate(manifest, strips_dir, deploy_files):
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
        rel = str(f)
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
```

- [ ] **Step 4: Implement `tools/validate-comic-manifest.py` CLI**

```python
"""CLI: validate manifest + the set of files that would ship to itch.io."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.comic.validate import validate

DEFAULT_MANIFEST = "assets/comic/act1.comic.json"
DEFAULT_STRIPS = "assets/comic/strips/act1"
# Files that ship to itch.io (relative to web root). Excludes frames-generated/ (gitignored source).
DEPLOY_GLOBS = ["*.html", "assets/css/*.css", "assets/js/*.js", "assets/vendor/*.js",
                "assets/comic/*.json", "assets/comic/strips/act1/*.webp",
                "assets/comic/narration/act1/*.mp3", "assets/audio/**/*.ogg",
                "assets/audio/**/*.mp3", "assets/video/*.mp4"]


def collect_deploy_files(root: Path):
    files = []
    for g in DEPLOY_GLOBS:
        files.extend(sorted(root.glob(g)))
    return files


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", default=DEFAULT_MANIFEST)
    p.add_argument("--strips", default=DEFAULT_STRIPS)
    p.add_argument("--root", default=".")
    args = p.parse_args(argv)

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    files = collect_deploy_files(Path(args.root))
    errors = validate(manifest, Path(args.strips), files)
    if errors:
        print(f"INVALID ({len(errors)} errors):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK: {len(manifest['beats'])} beats, {len(files)} deploy files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run tests + real validation**

Run:
```bash
.venv/Scripts/python -m pytest tools/tests/test_validate.py -v
.venv/Scripts/python tools/validate-comic-manifest.py
```
Expected: 4 passed; CLI prints `OK: ~180 beats, <N> deploy files` (N well under 1000).

- [ ] **Step 6: Commit**

```bash
git add tools/comic/validate.py tools/validate-comic-manifest.py tools/tests/test_validate.py
git commit -m "feat(comic): add manifest + itch.io constraint validator"
```

---

### Task 6: `package-itch.py` — assemble the itch.io zip

**Files:**
- Create: `tools/package-itch.py`
- Create: `tools/tests/test_package_itch.py`

**Interfaces:**
- Consumes: `collect_deploy_files` + `validate` (Task 5); manifest.
- Produces: CLI writing `dist/void-itch.zip` with `index.html` at the zip root; runs validation first and aborts on errors. Importable `main(argv) -> int`.

- [ ] **Step 1: Write the failing test** — `tools/tests/test_package_itch.py`

```python
import zipfile
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("pkg_itch", ROOT / "tools/package-itch.py")
pkg_itch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pkg_itch)


def test_zip_has_index_at_root(tmp_path):
    root = tmp_path / "site"
    (root / "assets/comic").mkdir(parents=True)
    (root / "index.html").write_text("<html></html>")
    (root / "assets/comic/act1.comic.json").write_text('{"beats":[]}')
    out = tmp_path / "out.zip"

    rc = pkg_itch.main(["--root", str(root), "--out", str(out), "--skip-validate"])

    assert rc == 0
    with zipfile.ZipFile(out) as z:
        assert "index.html" in z.namelist()
        assert not any(n.startswith("site/") for n in z.namelist())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tools/tests/test_package_itch.py -v`
Expected: FAIL (module load / attribute error)

- [ ] **Step 3: Implement `tools/package-itch.py`**

```python
"""CLI: assemble an itch.io-ready zip (index.html at root) after validation."""
import argparse
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.comic.validate import validate

# Everything that ships. Relative to --root. frames-generated/ is intentionally excluded.
INCLUDE_GLOBS = ["*.html", "assets/css/*.css", "assets/js/*.js", "assets/vendor/*.js",
                 "assets/comic/*.json", "assets/comic/strips/act1/*.webp",
                 "assets/comic/narration/act1/*.mp3", "assets/audio/**/*",
                 "assets/video/*.mp4", "Media/*.wav"]


def _collect(root: Path):
    files = []
    for g in INCLUDE_GLOBS:
        files.extend(p for p in root.glob(g) if p.is_file())
    # de-dup, stable order
    seen, out = set(), []
    for p in files:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--out", default="dist/void-itch.zip")
    p.add_argument("--manifest", default="assets/comic/act1.comic.json")
    p.add_argument("--strips", default="assets/comic/strips/act1")
    p.add_argument("--skip-validate", action="store_true")
    args = p.parse_args(argv)

    root = Path(args.root)
    files = _collect(root)

    if not args.skip_validate:
        manifest = json.loads((root / args.manifest).read_text(encoding="utf-8"))
        errors = validate(manifest, root / args.strips, files)
        if errors:
            print(f"ABORT: manifest invalid ({len(errors)} errors). Run validate-comic-manifest.py.")
            return 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, arcname=str(f.relative_to(root)).replace("\\", "/"))
    print(f"wrote {len(files)} files -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify pass**

Run: `.venv/Scripts/python -m pytest tools/tests/test_package_itch.py -v`
Expected: 1 passed

- [ ] **Step 5: Full pipeline smoke test**

Run:
```bash
.venv/Scripts/python -m pytest tools/tests -v
.venv/Scripts/python tools/build-comic-manifest.py
.venv/Scripts/python tools/pack-comic-strips.py
.venv/Scripts/python tools/validate-comic-manifest.py
```
Expected: all tests pass; validator prints `OK`.

- [ ] **Step 6: Commit**

```bash
git add tools/package-itch.py tools/tests/test_package_itch.py
git commit -m "feat(comic): add itch.io zip packaging step"
```

---

### Task 7: `.gitignore` + README for the pipeline

**Files:**
- Modify: `.gitignore` (web repo root)
- Create: `tools/README.md`

**Interfaces:** none (housekeeping).

- [ ] **Step 1: Add ignores** — append to `.gitignore`:

```
# comic build pipeline
.venv/
tools/**/__pycache__/
.pytest_cache/
dist/
```

- [ ] **Step 2: Verify strips + manifest are NOT ignored**

Run: `git check-ignore assets/comic/act1.comic.json assets/comic/strips/act1; echo "exit:$?"`
Expected: no output, `exit:1` (i.e. these ARE tracked, not ignored).

- [ ] **Step 3: Write `tools/README.md`**

```markdown
# Comic Build Pipeline

Run from the web repo root with the venv python (`.venv/Scripts/python`):

1. `build-comic-manifest.py` — joins generation-repo metadata (`--gen-repo`,
   default `../../ai-video-photo/The Void is Crimson`) into `assets/comic/act1.comic.json`.
2. `pack-comic-strips.py` — packs each beat's frames from `frames-generated/` into one
   WebP strip under `assets/comic/strips/act1/` and writes per-panel `rect`s into the manifest.
3. `validate-comic-manifest.py` — checks manifest integrity + itch.io limits (≤1000 files etc).
4. `package-itch.py` — assembles `dist/void-itch.zip` (index.html at root) after validation.

Tests: `.venv/Scripts/python -m pytest tools/tests -v`

Narration (`narration` field) stays `"pending"` here; Plan 2 fills section S1.
```

- [ ] **Step 4: Commit**

```bash
git add .gitignore tools/README.md
git commit -m "chore(comic): ignore build artifacts; document pipeline"
```

---

## Self-Review

**Spec coverage** (against `2026-06-23-act1-motion-comic-design.md`):
- §4 build tools: `build-comic-manifest.py` (T2-3), `pack-comic-strips.py` (T4), `validate-comic-manifest.py` (T5), `package-itch.py` (T6) ✓
- §6 sprite-strip rendering data (strip + per-panel offsets): T4 `augment_manifest` writes `strip`/`rect` ✓
- §7 alt text from story-index description: T2 `_beat_descriptions` ✓ (beat-level, per data-granularity note)
- §10 narration `pending` default: T2 ✓ (S1 ready-marking deferred to Plan 2, as intended)
- §12 itch.io limits (1000 files / 240 chars / 200MB / 500MB / slug-safe / relative): T5 validator + T6 packager ✓
- Decisions: all-frames kept (every frame → panel, T2) ✓; WebP committed, frames-generated excluded (T6 globs, T7 ignore) ✓
- **Out of scope (Plan 2, intentional):** prose `data-beat` anchoring, `comic-engine.js`, `mode-controller.js`, `comic.css`, vendored `three.min.js`, narration transcode/wiring, browser testing.

**Placeholder scan:** no TBD/TODO; every code step shows full code; every run step shows expected output. ✓

**Type consistency:** `slugify` (T1) used in T2/T5; `build_manifest`/`load_sources` (T2) used in T3; `augment_manifest`/`pack_beat` (T4) consume T2 manifest; `validate`/`collect_deploy_files` (T5) consumed by T6. Manifest keys (`beats`, `slug`, `panels`, `strip`, `strip_w`, `strip_h`, `rect`) are written in T4 and asserted identically in T5. ✓
