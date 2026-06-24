# Act I Web Runtime + S1 Narration — Implementation Plan (Plan 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Turn `act1-fifth-harmonic.html` into the illustrated experience: keep the prose, inject the per-beat comic panels (from Plan 1's manifest + strips), add a Read / Read+Atmosphere / Narrated mode switcher, and wire per-shot narration for the S1 shots that have audio.

**Architecture:** A data layer (Python, extends Plan 1's `tools/`) annotates the prose with `data-beat` anchors and builds a narration index from the video project's shot map + transcoded S1 audio. A runtime layer (vanilla JS IIFE + CSS) reads `act1.comic.json` and the narration index, injects panel clusters after each anchored paragraph, animates them on scroll via the existing IntersectionObserver pattern, and a mode controller manages audio. The existing horror-trigger prose and engines are untouched.

**Tech Stack:** Python 3.10 + Pillow + pytest (data tools, extends Plan 1), ffmpeg (audio transcode), vanilla ES (IIFE, `'use strict'`), vanilla CSS, Three.js r160 (vendored), Howler.js (existing).

## Global Constraints

- Plan 1 is DONE and merged: `assets/comic/act1.comic.json` (180 beats, 1005 panels, every panel has a `rect`, `narration:"pending"`), 180 strips at `assets/comic/strips/act1/<slug>.webp`, and `tools/` pipeline (slugs, manifest, strips, validate, deploy, package-itch). Run pytest from repo root: `.venv/Scripts/python -m pytest tools/tests -v`.
- No JS test framework in this project — JS/CSS/HTML tasks are verified by **manual browser testing** with the specific observations named in each task. Python tasks use pytest (TDD).
- Generation repo (read-only source) default path: `../../ai-video-photo/The Void is Crimson` (override `--gen-repo`).
- Narration is **per-shot**: `src/act1-video-shots-S1.json` maps each shot (e.g. `S1-01`) to 1–2 beats. Audio mixes exist only for `S1-01/02/03` (`generated/videos/_narr/<shot>_mixed.wav`), covering beats `headache_studio`, `jen_voice`, `therapist`, `coordinates_write`. A shot's clip starts when any of its beats enters view and is NOT restarted while scrolling within the same shot.
- Vanilla CSS only; IIFE + `'use strict'` for JS; maintain the horror/dark aesthetic; Three.js r160; pixel-ratio cap 1.5×; honor `prefers-reduced-motion`; keep the existing `horror-effects.js`/`horror-samples.js` and all existing `data-horror`/`data-stinger`/etc. prose attributes untouched.
- Panels render from a beat's sprite strip via per-panel `rect` (background-image + background-position), one strip request per beat.
- itch.io limits still hold (≤1000 files etc.); the validator/packager (Plan 1) enforce them and must still pass after new assets are added.
- Commit after each task with the shown message.

---

### Task 1: Vendor Three.js r160 locally

**Files:**
- Create: `assets/vendor/three.min.js`
- Modify: `act1-fifth-harmonic.html` (the Three.js `<script>` tag, ~line 47)

**Interfaces:** none (asset + tag swap).

- [ ] **Step 1: Download the exact pinned version**

Run (Git Bash):
```bash
cd "C:/Users/edk7c/ENGINEERING-PROJECTS/ACTIVE-PROJECTS/web/the-void-is-crimson"
mkdir -p assets/vendor
curl -fsSL "https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.0/three.min.js" -o assets/vendor/three.min.js
ls -l assets/vendor/three.min.js
```
Expected: a file ~600 KB. If curl is unavailable, report BLOCKED (do not substitute a different version — r160 is required).

- [ ] **Step 2: Verify it is the expected library**

Run: `grep -o "REVISION:\"[0-9]*\"\|REVISION=\"[0-9]*\"\|'160'" assets/vendor/three.min.js | head -1` (or `grep -c "THREE" assets/vendor/three.min.js`)
Expected: non-empty (the file contains the THREE namespace). Confirm size > 100 KB.

- [ ] **Step 3: Swap the CDN tag to local (keep the fallback)**

In `act1-fifth-harmonic.html`, replace the line:
```html
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.0/three.min.js" onerror="window.handleThreeJSLoadError()"></script>
```
with:
```html
    <script src="./assets/vendor/three.min.js" onerror="window.handleThreeJSLoadError()"></script>
```
Leave the `window.handleThreeJSLoadError` definition above it unchanged.

- [ ] **Step 4: Manual browser verify**

Open `act1-fifth-harmonic.html` in a browser (file:// is fine). Expected: the background WebGL canvas renders (vortex/starfield as before); DevTools Console shows NO "Three.js failed to load" error and NO request to cdnjs for three.

- [ ] **Step 5: Commit**

```bash
git add assets/vendor/three.min.js act1-fifth-harmonic.html
git commit -m "feat(comic): vendor Three.js r160 locally for itch.io robustness"
```

---

### Task 2: Prose beat-anchoring tool

**Files:**
- Create: `tools/comic/anchor.py`
- Create: `tools/anchor-prose-beats.py`
- Create: `tools/tests/test_anchor.py`
- Modify (by running the tool): `act1-fifth-harmonic.html`

**Interfaces:**
- Consumes: `act1.comic.json` (for the ordered beat list + each beat's `dialogue`).
- Produces: `tools/comic/anchor.py` →
  `anchor_text(beat: dict) -> str | None` (the matchable phrase for a beat = first non-empty dialogue `line`, normalized; None if the beat has no dialogue);
  `normalize(s: str) -> str` (lowercase, collapse whitespace, strip non-alphanumerics to spaces);
  `annotate_html(html: str, beats: list[dict]) -> tuple[str, list[str], list[str]]` returning `(new_html, matched_beats, unmatched_beats)`. For each beat with an `anchor_text`, find the FIRST `<p ...>...</p>` whose normalized inner text contains the normalized anchor text and does not already carry a `data-beat`; insert `data-beat="<beat>"` into that `<p>`'s attributes. Beats already anchored or without a unique match go to `unmatched`.

- [ ] **Step 1: Write the failing test** — `tools/tests/test_anchor.py`

```python
from tools.comic.anchor import normalize, anchor_text, annotate_html


def test_normalize_strips_and_lowers():
    assert normalize("The HEADACHE,  behind his eye!") == "the headache behind his eye"


def test_anchor_text_is_first_dialogue_line():
    beat = {"beat": "b", "dialogue": [{"speaker": "narrator", "line": "The headache had been living."}]}
    assert anchor_text(beat) == "the headache had been living"


def test_anchor_text_none_when_no_dialogue():
    assert anchor_text({"beat": "b", "dialogue": []}) is None


def test_annotate_inserts_data_beat_on_matching_p():
    html = "<article><p>Intro line.</p><p>The headache had been living behind his eye.</p></article>"
    beats = [{"beat": "headache_studio", "dialogue": [{"speaker": "narrator", "line": "The headache had been living"}]}]
    out, matched, unmatched = annotate_html(html, beats)
    assert 'data-beat="headache_studio"' in out
    assert out.count('data-beat=') == 1  # only the matching paragraph
    assert matched == ["headache_studio"] and unmatched == []


def test_unmatched_when_no_paragraph_contains_text():
    html = "<article><p>Nothing relevant.</p></article>"
    beats = [{"beat": "ghost", "dialogue": [{"speaker": "x", "line": "totally absent phrase"}]}]
    out, matched, unmatched = annotate_html(html, beats)
    assert matched == [] and unmatched == ["ghost"]
    assert "data-beat" not in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tools/tests/test_anchor.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tools.comic.anchor'`

- [ ] **Step 3: Implement `tools/comic/anchor.py`**

```python
"""Annotate the prose HTML with data-beat anchors by matching dialogue lines to paragraphs."""
import re

_P = re.compile(r"<p\b([^>]*)>(.*?)</p>", re.IGNORECASE | re.DOTALL)
_TAG = re.compile(r"<[^>]+>")
_NONWORD = re.compile(r"[^a-z0-9]+")


def normalize(s):
    text = _TAG.sub(" ", s).lower()
    return _NONWORD.sub(" ", text).strip()


def anchor_text(beat):
    for line in beat.get("dialogue", []):
        norm = normalize(line.get("line", ""))
        if norm:
            return norm
    return None


def annotate_html(html, beats):
    matched, unmatched = [], []
    # Track which (start,end) spans already got a data-beat so two beats don't share one <p>.
    used_spans = set()

    for beat in beats:
        text = anchor_text(beat)
        if not text:
            unmatched.append(beat["beat"])
            continue
        hit = None
        for m in _P.finditer(html):
            attrs, inner = m.group(1), m.group(2)
            if "data-beat" in attrs:
                continue
            if (m.start(), m.end()) in used_spans:
                continue
            if text in normalize(inner):
                hit = m
                break
        if hit is None:
            unmatched.append(beat["beat"])
            continue
        used_spans.add((hit.start(), hit.end()))
        new_tag = f'<p data-beat="{beat["beat"]}"{hit.group(1)}>{hit.group(2)}</p>'
        html = html[:hit.start()] + new_tag + html[hit.end():]
        matched.append(beat["beat"])

    return html, matched, unmatched
```

Note: each insertion shifts offsets, so recompute matches against the updated `html` on each beat (the loop re-runs `finditer` over the current `html`); `used_spans` is recomputed implicitly because we re-scan — drop `used_spans` if the `data-beat in attrs` guard already prevents reuse. Keep the guard; it is sufficient because the just-anchored `<p>` now contains `data-beat`.

- [ ] **Step 4: Simplify per the note — final `annotate_html`**

Replace the loop body's span tracking with the attribute guard only:

```python
def annotate_html(html, beats):
    matched, unmatched = [], []
    for beat in beats:
        text = anchor_text(beat)
        if not text:
            unmatched.append(beat["beat"]); continue
        hit = None
        for m in _P.finditer(html):
            if "data-beat" in m.group(1):
                continue
            if text in normalize(m.group(2)):
                hit = m; break
        if hit is None:
            unmatched.append(beat["beat"]); continue
        html = (html[:hit.start()]
                + f'<p data-beat="{beat["beat"]}"{hit.group(1)}>{hit.group(2)}</p>'
                + html[hit.end():])
        matched.append(beat["beat"])
    return html, matched, unmatched
```

- [ ] **Step 5: Run tests to verify pass**

Run: `.venv/Scripts/python -m pytest tools/tests/test_anchor.py -v`
Expected: 5 passed.

- [ ] **Step 6: Implement `tools/anchor-prose-beats.py` CLI**

```python
"""CLI: insert data-beat anchors into the prose page; report coverage."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.comic.anchor import annotate_html

DEFAULT_HTML = "act1-fifth-harmonic.html"
DEFAULT_MANIFEST = "assets/comic/act1.comic.json"


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--html", default=DEFAULT_HTML)
    p.add_argument("--manifest", default=DEFAULT_MANIFEST)
    args = p.parse_args(argv)

    beats = json.loads(Path(args.manifest).read_text(encoding="utf-8"))["beats"]
    html = Path(args.html).read_text(encoding="utf-8")
    new_html, matched, unmatched = annotate_html(html, beats)
    Path(args.html).write_text(new_html, encoding="utf-8")
    print(f"anchored {len(matched)}/{len(beats)} beats; {len(unmatched)} unmatched")
    if unmatched:
        print("UNMATCHED (need manual data-beat placement):")
        for b in unmatched:
            print(f"  - {b}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 7: Run on the real page + record coverage**

Run:
```bash
.venv/Scripts/python tools/anchor-prose-beats.py
grep -c 'data-beat=' act1-fifth-harmonic.html
```
Expected: prints `anchored N/180 beats` and lists unmatched. The S1 beats `headache_studio`, `jen_voice`, `therapist`, `coordinates_write` MUST be in the matched set (they have dialogue lines that appear verbatim in the prose). Record N and the unmatched list in the task report — unmatched beats are deferred to manual placement (a follow-up), not a failure here.

- [ ] **Step 8: Commit**

```bash
git add tools/comic/anchor.py tools/anchor-prose-beats.py tools/tests/test_anchor.py act1-fifth-harmonic.html
git commit -m "feat(comic): anchor prose paragraphs to beats via data-beat"
```

---

### Task 3: Narration index + transcode S1 audio

**Files:**
- Create: `tools/comic/narration.py`
- Create: `tools/build-narration-index.py`
- Create: `tools/tests/test_narration.py`
- Create (by running): `assets/comic/narration/act1/*.mp3`, `assets/comic/act1.narration.json`

**Interfaces:**
- Consumes: `src/act1-video-shots-S1.json` (shot→beats), the `_narr/<shot>_mixed.wav` files, `dialogue.json` (per-beat lines+timing).
- Produces: `tools/comic/narration.py` →
  `build_index(shots: list[dict], available_shots: set[str], web_prefix: str) -> dict`.
  Index shape:
  ```json
  {"shots": [{"shot":"S1-01","beats":["headache_studio","jen_voice"],
              "audio":"assets/comic/narration/act1/S1-01.mp3","status":"ready"}],
   "beat_to_shot": {"headache_studio":"S1-01","jen_voice":"S1-01"}}
  ```
  A shot is `"ready"` if its id ∈ `available_shots` else `"pending"` (and `audio` is null).

- [ ] **Step 1: Write the failing test** — `tools/tests/test_narration.py`

```python
from tools.comic.narration import build_index

SHOTS = [
    {"shot_id": "S1-01", "beats": ["headache_studio/entry", "jen_voice/exit"]},
    {"shot_id": "S1-99", "beats": ["far_future/entry"]},
]


def test_ready_shot_gets_audio_path():
    idx = build_index(SHOTS, {"S1-01"}, "assets/comic/narration/act1")
    s = idx["shots"][0]
    assert s["status"] == "ready"
    assert s["audio"] == "assets/comic/narration/act1/S1-01.mp3"
    assert s["beats"] == ["headache_studio", "jen_voice"]


def test_pending_shot_has_no_audio():
    idx = build_index(SHOTS, {"S1-01"}, "assets/comic/narration/act1")
    s = idx["shots"][1]
    assert s["status"] == "pending" and s["audio"] is None


def test_beat_to_shot_maps_each_beat():
    idx = build_index(SHOTS, {"S1-01"}, "assets/comic/narration/act1")
    assert idx["beat_to_shot"]["headache_studio"] == "S1-01"
    assert idx["beat_to_shot"]["far_future"] == "S1-99"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tools/tests/test_narration.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `tools/comic/narration.py`**

```python
"""Build the per-shot narration index from the video-project shot map."""


def _beats_of(shot):
    seen, out = set(), []
    for b in shot.get("beats", []):
        name = b.split("/")[0]
        if name not in seen:
            seen.add(name); out.append(name)
    return out


def build_index(shots, available_shots, web_prefix):
    out_shots, beat_to_shot = [], {}
    for shot in shots:
        sid = shot["shot_id"]
        beats = _beats_of(shot)
        ready = sid in available_shots
        out_shots.append({
            "shot": sid,
            "beats": beats,
            "audio": f"{web_prefix}/{sid}.mp3" if ready else None,
            "status": "ready" if ready else "pending",
        })
        for b in beats:
            beat_to_shot[b] = sid
    return {"shots": out_shots, "beat_to_shot": beat_to_shot}
```

- [ ] **Step 4: Run tests to verify pass**

Run: `.venv/Scripts/python -m pytest tools/tests/test_narration.py -v`
Expected: 3 passed.

- [ ] **Step 5: Confirm ffmpeg is available**

Run: `ffmpeg -version | head -1`
Expected: prints a version. If absent, report BLOCKED with the message "ffmpeg required to transcode narration" — do NOT commit WAVs (too large / uncompressed).

- [ ] **Step 6: Implement `tools/build-narration-index.py` CLI (transcodes ready shots + writes index)**

```python
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
```

- [ ] **Step 7: Run for real + verify**

Run:
```bash
.venv/Scripts/python tools/build-narration-index.py
ls assets/comic/narration/act1
.venv/Scripts/python -c "import json;i=json.load(open('assets/comic/act1.narration.json',encoding='utf-8'));print('ready:',[s['shot'] for s in i['shots'] if s['status']=='ready']);print('headache->',i['beat_to_shot'].get('headache_studio'))"
```
Expected: three MP3s (`S1-01.mp3`, `S1-02.mp3`, `S1-03.mp3`); index prints `ready: ['S1-01','S1-02','S1-03']` and `headache-> S1-01`.

- [ ] **Step 8: Add narration MP3 + json to the deploy set**

Confirm Plan 1's canonical globs already include them: `assets/comic/*.json` covers `act1.narration.json`, and `assets/comic/narration/act1/*.mp3` is already in `tools/comic/deploy.py` `DEPLOY_GLOBS`. Run `.venv/Scripts/python tools/validate-comic-manifest.py` — expect `OK` with the deploy-file count now including 3 MP3s + 1 json (still well under 1000).

- [ ] **Step 9: Commit**

```bash
git add tools/comic/narration.py tools/build-narration-index.py tools/tests/test_narration.py assets/comic/narration/act1/ assets/comic/act1.narration.json
git commit -m "feat(comic): per-shot narration index + transcode S1 mixes to MP3"
```

---

### Task 4: `comic.css` — panels, mobile, switcher, motion

**Files:**
- Create: `assets/css/comic.css`
- Modify: `act1-fifth-harmonic.html` (add the `<link>` in `<head>`, after `act1-custom.css`)

**Interfaces:** consumed by Tasks 5–7 via class names: `.comic-cluster`, `.comic-cluster[data-pacing="hold-long|standard|cut-busy"]`, `.comic-panel`, `.comic-caption`, `.comic-bubble`, `.comic-mode-switch`, `.comic-divider`, body classes `mode-read|mode-atmosphere|mode-narrated`.

- [ ] **Step 1: Write `assets/css/comic.css`**

```css
/* Comic layer — illustrated full-text. Panels render from a beat's sprite strip. */
.comic-cluster {
  display: grid;
  gap: 0.6rem;
  margin: 2.2rem auto;
  max-width: 1100px;
}
.comic-cluster[data-pacing="hold-long"] { grid-template-columns: 1fr; }
.comic-cluster[data-pacing="standard"]  { grid-template-columns: repeat(2, 1fr); }
.comic-cluster[data-pacing="cut-busy"]  { grid-template-columns: repeat(3, 1fr); }

.comic-panel {
  position: relative;
  aspect-ratio: 16 / 9;
  background-repeat: no-repeat;
  background-size: 100% auto;        /* strip is full-width; position selects the panel cell */
  border: 1px solid rgba(180, 30, 30, 0.35);
  box-shadow: 0 0 22px rgba(120, 0, 0, 0.25);
  opacity: 0;
  transform: scale(1.04);
  transition: opacity 900ms ease, transform 1400ms ease;
}
.comic-panel.is-visible { opacity: 1; transform: scale(1); }

.comic-divider {
  width: 100%;
  margin: 3rem 0;
  aspect-ratio: 21 / 9;
  background-size: cover;
  background-position: center;
  filter: saturate(1.1) contrast(1.05);
}

.comic-caption, .comic-bubble {
  font-family: 'Cormorant Garamond', serif;
  color: #e7d7d7;
  padding: 0.5rem 0.8rem;
  backdrop-filter: blur(3px);
}
.comic-caption { background: rgba(10, 5, 5, 0.6); border-left: 3px solid #7a0010; font-style: italic; }
.comic-bubble  { background: rgba(30, 6, 6, 0.7); border-radius: 10px; }

.comic-mode-switch {
  position: fixed; top: 12px; right: 12px; z-index: 50;
  display: flex; gap: 4px;
  background: rgba(10, 5, 5, 0.7); padding: 5px; border-radius: 10px;
  backdrop-filter: blur(6px); border: 1px solid rgba(180, 30, 30, 0.4);
}
.comic-mode-switch button {
  font: inherit; color: #d8c4c4; background: transparent;
  border: 1px solid transparent; border-radius: 7px; padding: 4px 9px; cursor: pointer;
}
.comic-mode-switch button[aria-pressed="true"] { color: #fff; border-color: #7a0010; background: rgba(120, 0, 0, 0.35); }
.comic-mode-switch button:disabled { opacity: 0.4; cursor: not-allowed; }

/* Mobile: single-column webtoon flow regardless of pacing */
@media (max-width: 720px) {
  .comic-cluster[data-pacing] { grid-template-columns: 1fr; }
  .comic-mode-switch { top: auto; bottom: 10px; right: 10px; }
}

@media (prefers-reduced-motion: reduce) {
  .comic-panel { transition: opacity 300ms ease; transform: none; }
  .comic-panel.is-visible { transform: none; }
}
```

- [ ] **Step 2: Link it in the page**

In `act1-fifth-harmonic.html` `<head>`, after the `act1-custom.css` link, add:
```html
    <link rel="stylesheet" href="./assets/css/comic.css">
```

- [ ] **Step 3: Manual browser verify (structural)**

Open the page. Expected: no layout breakage from the new CSS yet (no `.comic-*` elements exist until Task 5). The page still renders prose + background as before. (Panels appear after Task 5.)

- [ ] **Step 4: Commit**

```bash
git add assets/css/comic.css act1-fifth-harmonic.html
git commit -m "feat(comic): comic-layer stylesheet (panels, mobile, switcher)"
```

---

### Task 5: `comic-engine.js` — inject + animate panels

**Files:**
- Create: `assets/js/comic-engine.js`
- Modify: `act1-fifth-harmonic.html` (add `<script defer>` after the horror scripts)

**Interfaces:**
- Consumes: `assets/comic/act1.comic.json`; `[data-beat]` anchors in the page (Task 2).
- Produces: global `window.ComicEngine` with `{ ready: Promise, beatsByName: Map }` for Task 6 to await. Renders, into each `[data-beat]` paragraph's following sibling position, a `.comic-cluster[data-pacing]` containing `.comic-panel` divs (strip via `background-image`, `background-position` derived from `rect`) plus `.comic-caption`/`.comic-bubble` from `dialogue`. Adds `.is-visible` via IntersectionObserver.

- [ ] **Step 1: Implement `assets/js/comic-engine.js`**

```javascript
/* Comic engine: inject per-beat panel clusters after their prose anchors. */
(function () {
  'use strict';

  var MANIFEST_URL = './assets/comic/act1.comic.json';

  function panelBackground(beat, rect) {
    // strip is full-width (strip_w); show one 16:9 cell by shifting vertically.
    var pct = beat.strip_h > rect.h ? (rect.y / (beat.strip_h - rect.h)) * 100 : 0;
    return {
      backgroundImage: 'url("./' + beat.strip + '")',
      backgroundPositionY: pct + '%'
    };
  }

  function buildCluster(beat) {
    if (beat.is_section_break) {
      var div = document.createElement('div');
      div.className = 'comic-divider';
      div.style.backgroundImage = 'url("./' + beat.strip + '")';
      div.setAttribute('role', 'img');
      div.setAttribute('aria-label', (beat.panels[0] && beat.panels[0].alt) || beat.beat);
      return div;
    }
    var cluster = document.createElement('div');
    cluster.className = 'comic-cluster';
    cluster.setAttribute('data-pacing', beat.pacing_role || 'standard');
    beat.panels.forEach(function (p) {
      var panel = document.createElement('div');
      panel.className = 'comic-panel';
      panel.setAttribute('role', 'img');
      panel.setAttribute('aria-label', p.alt || '');
      var bg = panelBackground(beat, p.rect);
      panel.style.backgroundImage = bg.backgroundImage;
      panel.style.backgroundPositionY = bg.backgroundPositionY;
      cluster.appendChild(panel);
    });
    (beat.dialogue || []).forEach(function (d) {
      var el = document.createElement('div');
      el.className = d.speaker === 'narrator' ? 'comic-caption' : 'comic-bubble';
      el.textContent = d.line;
      cluster.appendChild(el);
    });
    return cluster;
  }

  function observe(nodes) {
    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('is-visible'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -10% 0px' });
    nodes.forEach(function (n) {
      if (reduce) { n.classList.add('is-visible'); }
      else { n.querySelectorAll ? n.classList.add('comic-panel') : 0; io.observe(n); }
    });
  }

  function render(manifest) {
    var beatsByName = new Map();
    var injected = [];
    manifest.beats.forEach(function (beat) {
      beatsByName.set(beat.beat, beat);
      var anchor = document.querySelector('[data-beat="' + beat.beat + '"]');
      if (!anchor) { return; }                 // unanchored beat: skip (manual placement pending)
      var cluster = buildCluster(beat);
      anchor.parentNode.insertBefore(cluster, anchor.nextSibling);
      injected.push(cluster);
    });
    // observe panels (and dividers) for entry animation
    var panels = [];
    injected.forEach(function (c) {
      if (c.classList.contains('comic-divider')) { panels.push(c); }
      else { c.querySelectorAll('.comic-panel').forEach(function (p) { panels.push(p); }); }
    });
    observePanels(panels);
    return beatsByName;
  }

  function observePanels(panels) {
    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce) { panels.forEach(function (p) { p.classList.add('is-visible'); }); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('is-visible'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px' });
    panels.forEach(function (p) { io.observe(p); });
  }

  var ready = fetch(MANIFEST_URL)
    .then(function (r) { return r.json(); })
    .then(function (m) { return { beatsByName: render(m) }; })
    .catch(function (err) { console.error('ComicEngine failed:', err); return { beatsByName: new Map() }; });

  window.ComicEngine = { ready: ready };
})();
```

(Remove the stray `observe`/`nodes` helper — `observePanels` is the one used; delete the unused `observe` function before committing.)

- [ ] **Step 2: Clean up the dead `observe` helper**

Delete the `function observe(nodes) { ... }` block (superseded by `observePanels`). Re-read the file to confirm only `observePanels` remains.

- [ ] **Step 3: Include the script in the page**

In `act1-fifth-harmonic.html`, after the horror-effects script tag, add:
```html
    <script src="./assets/js/comic-engine.js" defer></script>
```

- [ ] **Step 4: Manual browser verify**

Open the page; scroll. Expected: after each anchored paragraph (at minimum `headache_studio`, `jen_voice`, `therapist`, `coordinates_write`), a comic cluster of panels appears and fades/scales in on scroll; section breaks render as a wide divider; captions/bubbles show the dialogue. DevTools: no console errors; exactly one network request per beat strip (`.webp`). Toggle "reduce motion" in DevTools rendering → panels appear without the scale animation.

- [ ] **Step 5: Commit**

```bash
git add assets/js/comic-engine.js act1-fifth-harmonic.html
git commit -m "feat(comic): inject + scroll-animate panel clusters from manifest"
```

---

### Task 6: `mode-controller.js` — Read / Atmosphere / Narrated

**Files:**
- Create: `assets/js/mode-controller.js`
- Modify: `act1-fifth-harmonic.html` (add the switcher markup + script include)

**Interfaces:**
- Consumes: `window.ComicEngine.ready`; `assets/comic/act1.narration.json`; existing `window.Howl` (Howler) for audio; existing horror engine (already auto-runs on scroll).
- Produces: a fixed `.comic-mode-switch` with three buttons; body class `mode-read|mode-atmosphere|mode-narrated`; mode persisted in `localStorage['void-mode']`.

- [ ] **Step 1: Implement `assets/js/mode-controller.js`**

```javascript
/* Mode controller: Read / Read+Atmosphere / Narrated (per-shot audio). */
(function () {
  'use strict';

  var MODES = ['read', 'atmosphere', 'narrated'];
  var LABELS = { read: 'Read', atmosphere: 'Atmosphere', narrated: 'Narrated' };
  var NARR_URL = './assets/comic/act1.narration.json';
  var STORAGE = 'void-mode';

  var state = { mode: 'read', narration: null, sounds: {}, currentShot: null };

  function setBodyMode(mode) {
    MODES.forEach(function (m) { document.body.classList.remove('mode-' + m); });
    document.body.classList.add('mode-' + mode);
  }

  function buildSwitch(onPick, narrationReady) {
    var nav = document.createElement('nav');
    nav.className = 'comic-mode-switch';
    nav.setAttribute('aria-label', 'Reading mode');
    MODES.forEach(function (m) {
      var b = document.createElement('button');
      b.textContent = LABELS[m];
      b.setAttribute('aria-pressed', String(m === state.mode));
      if (m === 'narrated' && !narrationReady) { b.disabled = true; b.title = 'Narration coming soon'; }
      b.addEventListener('click', function () { onPick(m); });
      nav.appendChild(b);
    });
    document.body.appendChild(nav);
    return nav;
  }

  function refreshButtons(nav) {
    Array.prototype.forEach.call(nav.querySelectorAll('button'), function (b) {
      b.setAttribute('aria-pressed', String(b.textContent === LABELS[state.mode]));
    });
  }

  function shotForBeat(beat) {
    return state.narration ? state.narration.beat_to_shot[beat] : null;
  }
  function shotMeta(shotId) {
    return state.narration.shots.filter(function (s) { return s.shot === shotId; })[0];
  }

  function playShot(shotId) {
    if (!shotId || shotId === state.currentShot) { return; }
    var meta = shotMeta(shotId);
    if (!meta || meta.status !== 'ready') { return; }   // pending shot: stay silent (Atmosphere continues)
    Object.keys(state.sounds).forEach(function (k) { state.sounds[k].stop(); });
    if (!state.sounds[shotId]) {
      state.sounds[shotId] = new window.Howl({ src: ['./' + meta.audio], html5: true, volume: 0.9 });
    }
    state.sounds[shotId].play();
    state.currentShot = shotId;
  }

  function watchBeatsForNarration() {
    var io = new IntersectionObserver(function (entries) {
      if (state.mode !== 'narrated') { return; }
      entries.forEach(function (e) {
        if (e.isIntersecting) { playShot(shotForBeat(e.target.getAttribute('data-beat'))); }
      });
    }, { rootMargin: '0px 0px -45% 0px', threshold: 0.1 });
    document.querySelectorAll('[data-beat]').forEach(function (n) { io.observe(n); });
  }

  function stopAllAudio() {
    Object.keys(state.sounds).forEach(function (k) { state.sounds[k].stop(); });
    state.currentShot = null;
  }

  function applyMode(mode) {
    state.mode = mode;
    setBodyMode(mode);
    localStorage.setItem(STORAGE, mode);
    if (mode !== 'narrated') { stopAllAudio(); }
    // Atmosphere/Read: the existing horror engine runs on scroll regardless; Read users can mute
    // via the page's existing audio controls. No teardown needed here.
  }

  function init() {
    state.mode = localStorage.getItem(STORAGE) || 'read';
    fetch(NARR_URL).then(function (r) { return r.json(); }).catch(function () { return null; })
      .then(function (narr) {
        state.narration = narr;
        var ready = !!(narr && narr.shots.some(function (s) { return s.status === 'ready'; }));
        if (state.mode === 'narrated' && !ready) { state.mode = 'read'; }
        var nav = buildSwitch(function (m) { applyMode(m); refreshButtons(nav); }, ready);
        setBodyMode(state.mode);
        watchBeatsForNarration();
      });
  }

  if (window.ComicEngine && window.ComicEngine.ready) {
    window.ComicEngine.ready.then(init);
  } else {
    document.addEventListener('DOMContentLoaded', init);
  }
})();
```

- [ ] **Step 2: Include the script**

In `act1-fifth-harmonic.html`, after `comic-engine.js`:
```html
    <script src="./assets/js/mode-controller.js" defer></script>
```

- [ ] **Step 3: Manual browser verify (the vertical slice)**

Open the page. Expected:
- A mode switcher (top-right) with **Read / Atmosphere / Narrated**; reload persists the last choice.
- **Read:** no horror SFX auto-plays from the switcher logic.
- **Atmosphere:** scrolling triggers the existing horror audio (unchanged behavior).
- **Narrated:** scroll to the opening — when `headache_studio` enters view, `S1-01.mp3` begins (after a user gesture, per autoplay rules — clicking the Narrated button counts); scrolling from `headache_studio` into `jen_voice` (same shot S1-01) does NOT restart the clip; reaching `therapist` starts `S1-02.mp3`. Beats whose shot is pending play nothing (Atmosphere-style silence). Audio gated behind the click; no console errors.

- [ ] **Step 4: Commit**

```bash
git add assets/js/mode-controller.js act1-fifth-harmonic.html
git commit -m "feat(comic): mode switcher + per-shot narration playback (S1 slice)"
```

---

### Task 7: Final integration pass + itch package

**Files:**
- Modify: `act1-fifth-harmonic.html` (verify script order, switcher present, triggers intact)
- Run: validator + itch packager

**Interfaces:** none (integration + verification).

- [ ] **Step 1: Verify script load order + integrity**

Confirm in `act1-fifth-harmonic.html` the deferred script order is: `howler.min.js` → `horror-samples.js` → `horror-effects.js` → `comic-engine.js` → `mode-controller.js`, and Three.js is the local vendored file. Confirm NO existing `data-horror`/`data-stinger`/`data-whisper`/`data-buildup` attribute or prose paragraph was removed (compare `grep -c 'data-horror\|data-stinger\|data-whisper\|data-buildup' act1-fifth-harmonic.html` against the value before Plan 2 — it must be unchanged).

- [ ] **Step 2: Full manual pass (desktop + mobile width)**

In the browser at desktop width and at ≤720px (DevTools device toolbar): prose reads top-to-bottom with comic clusters interleaved; multi-panel clusters collapse to a single column on mobile; all three modes behave per Task 6; horror triggers still fire in Atmosphere/Narrated; reduced-motion disables panel scaling. No console errors.

- [ ] **Step 3: Validate + build the itch zip**

Run:
```bash
.venv/Scripts/python -m pytest tools/tests -q
.venv/Scripts/python tools/validate-comic-manifest.py
.venv/Scripts/python tools/package-itch.py
```
Expected: all tests pass; validator prints `OK` (deploy count now includes 3 narration MP3s, `act1.narration.json`, vendored `three.min.js`, `comic.css`, `comic-engine.js`, `mode-controller.js` — still well under 1000); packager writes `dist/void-itch.zip` and its file count equals the validator's deploy count.

- [ ] **Step 4: Commit**

```bash
git add act1-fifth-harmonic.html
git commit -m "chore(comic): finalize Act I integration; verify modes, triggers, itch package"
```

---

## Self-Review

**Spec coverage** (against `2026-06-23-act1-motion-comic-design.md`, build-pipeline parts done in Plan 1):
- §4 runtime files: `comic-engine.js` (T5), `mode-controller.js` (T6), `comic.css` (T4), vendored `three.min.js` (T1) ✓
- §5 prose↔beat anchoring via `data-beat`: T2 (auto-match + unmatched report for manual fill) ✓
- §6 sprite-strip rendering via `rect`/`background-position`; pacing-driven grid; section-break dividers; mobile single-column: T4 CSS + T5 engine ✓
- §7 three modes + per-shot narration with no-restart-within-shot + pending fallback + localStorage + reduced-motion + gesture-gated audio: T6 ✓
- §8 alt from panel `alt`; reduced-motion; lazy strip requests: T4/T5 ✓
- §10 Phase 1 = vertical slice with S1 narration (S1-01/02/03): T3 + T6 ✓
- §12 itch: vendored three.js (T1), validator/packager still pass with new assets (T3 step 8, T7 step 3) ✓
- **Deferred (not a gap):** beats Task 2 could not auto-anchor (no dialogue line) need manual `data-beat` placement — reported by the tool; S2–V narration is Phase 2 data-fill.

**Placeholder scan:** none — every step has full code or an exact command + expected output. (Two cleanup steps explicitly remove the noted dead `observe` helper — T5 Step 2 — and adopt the simplified `annotate_html` — T2 Step 4.)

**Type/identifier consistency:** manifest keys read by the engine (`beats`, `beat`, `slug`, `strip`, `strip_h`, `pacing_role`, `is_section_break`, `panels[].rect{x,y,w,h}`, `panels[].alt`, `dialogue[].speaker/line`) match Plan 1's writer. Narration index keys (`shots[].shot/beats/audio/status`, `beat_to_shot`) are written in T3 and read identically in T6. `window.ComicEngine.ready` produced in T5, awaited in T6.
