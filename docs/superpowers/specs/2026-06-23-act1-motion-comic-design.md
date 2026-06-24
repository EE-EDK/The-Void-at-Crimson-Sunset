# Act I Motion Comic — Design Spec

**Date:** 2026-06-23
**Project:** The Void is Crimson
**Status:** Approved design, pending implementation plan
**Scope:** Convert `act1-fifth-harmonic.html` ("The Fifth Harmonic") into a scroll-driven motion comic.

---

## 1. Summary

Replace the long-form prose in `act1-fifth-harmonic.html` with a **scroll-driven motion
comic**. The story's 180 narrative beats render as comic-grid panels built from the 1006
pre-generated frames, with caption/speech boxes distilled from existing dialogue metadata,
panels animating in on scroll, and the existing horror audio/visual trigger system preserved.

The build is **manifest-driven**: a small Python step joins three existing source files from
the generation repo into one runtime manifest the page consumes. Acts II and III stay as
untouched prose (they have no beat/dialogue metadata yet); the manifest approach lets them
drop in later as data-only work.

---

## 2. Decisions (locked)

| Decision | Choice | Rationale |
|---|---|---|
| Core experience | **Motion comic** | Shot-type frame naming was authored for this |
| Integration | **Replace prose in-place** in `act1-fifth-harmonic.html` | One canonical experience; prose recoverable from git |
| Scope | **Act I only** (= full Fifth Harmonic story, 180 beats / 1006 frames, sections EP + I–V) | Only Act I has frame-plan + dialogue + pacing metadata |
| Paradigm | **Scroll-driven webcomic** | Reuses existing IntersectionObserver + progress bar + horror engine; reader-paced; mobile-friendly |
| Panel density | **All frames, pacing-sized** | Fully data-driven; rhythm comes from `pacing_role`, not manual culling |
| Dialogue audio | **Phase 2** (visuals + captions + existing horror SFX first) | De-risks core build |
| Optimized assets | **Commit optimized WebP** to this repo; 218 MB originals stay gitignored in generation repo | Static site deploys from git |
| Mobile | **Responsive single source** — CSS collapses grid to single-column webtoon flow on phones | No duplicated content, no divergence; fits vanilla-CSS constraint |

---

## 3. Source assets (verified)

All in the generation repo `ACTIVE-PROJECTS/ai-video-photo/The Void is Crimson/`:

| Asset | Provides |
|---|---|
| `generated/frames-generated/*.jpg` (1006, **1280×720**) | Panel art, named `#### - role - beat.jpg` |
| `output/act1-1006-frame-plan.json` | Per-frame `beat`, `role`, `section`, `pacing_role` (`hold-long` / `standard` / `cut-busy`), `target_filename` |
| `output/act1-story-index.csv` | Per-frame `description` (→ alt text), `characters`, `dialogue` |
| `src/act1-dialogue.json` | Per-beat `speaker`, `line`, `direction`, `timing` (→ caption/speech text; `timing` used in Phase 2 audio) |

The web repo's own `frames-generated/` is a gitignored copy of the same 1006 frames.

**Verified facts:**
- Frames are 1280×720 (16:9).
- `frames-generated/` is gitignored in the web repo (`git check-ignore` → match).
- `horror-effects.js` drives all triggers through one `IntersectionObserver`
  (~line 1030) observing `.horror-trigger` elements and calling
  `HorrorSamples.handleTriggerElement(el)` — reused unchanged.
- All 180 beats (including late beats: Hole 17, "on three", recruitment, awakening, Venn)
  belong to `act1-fifth-harmonic.html`. Acts II/III are separate, shorter stories.

---

## 4. Architecture

```
the-void-is-crimson/
  act1-fifth-harmonic.html       # rewritten: <article> prose → comic shell + loader
  assets/
    js/comic-engine.js           # NEW: fetch manifest, render panels, wire observer
    css/comic.css                # NEW: panel grid, caption boxes, animations, mobile collapse
    comic/
      act1.comic.json            # NEW: built manifest (committed)
      frames/act1/*.webp         # NEW: optimized panels (committed)
  tools/
    build-comic-manifest.py      # NEW: joins frame-plan + dialogue + story-index → manifest
    optimize-comic-frames.py     # NEW: 1280×720 JPG → WebP (~1280w) + LQIP placeholders
    validate-comic-manifest.py   # NEW: every panel resolves; every beat ≥1 panel; triggers matched
```

Source-of-truth frames + metadata remain in the generation repo. This repo receives only the
optimized, deployable derivatives plus the build/validate tooling.

### Components & boundaries

- **`build-comic-manifest.py`** — pure data join. Input: the three source files (path
  configurable). Output: `act1.comic.json`. No rendering concerns.
- **`optimize-comic-frames.py`** — image pipeline only. JPG → WebP + tiny blurred LQIP
  data-URI placeholders. Idempotent; skips already-optimized frames.
- **`comic-engine.js`** — runtime renderer (IIFE, `'use strict'`). Input: manifest. Builds
  DOM panels per beat, applies pacing-driven layout classes, attaches horror-trigger
  attributes, registers panels with the existing observer. Knows nothing about how the
  manifest was built.
- **`comic.css`** — all layout/animation. Desktop grid + mobile single-column via media
  queries. Honors `prefers-reduced-motion`.

---

## 5. Manifest schema (`act1.comic.json`)

```jsonc
{
  "act": "I",
  "title": "The Fifth Harmonic",
  "sections": [
    {
      "id": "I",
      "break_frame": "0145 - establishing-empty-road - section_break_I.webp", // nullable
      "beats": [
        {
          "beat": "headache_studio",
          "pacing_role": "cut-busy",
          "panels": [
            {
              "src": "frames/act1/0001 - establish - headache_studio.webp",
              "lqip": "data:image/...",           // tiny blur placeholder
              "role": "establish",
              "alt": "Extreme close-up, Alex's fingers pressed to his temple...", // from story-index description
              "size": "wide"                        // derived from role + pacing_role
            }
            // ...remaining frames for this beat
          ],
          "captions": [
            { "speaker": "narrator", "text": "The headache had been living behind Alex Reeves's left eye for six days.", "kind": "narration" },
            { "speaker": "jen", "text": "Alex, you're doing it wrong again.", "kind": "bubble", "direction": "affectionate exasperation" }
          ],
          "triggers": {                              // re-mapped from prose horror attributes
            "data-horror": "heartbeat",
            "data-whisper": "the pattern remembers you",
            "data-stinger": "emptyHallways"
          }
        }
      ]
    }
  ]
}
```

---

## 6. Panel & layout model

- Each **beat** is a comic cluster. `pacing_role` drives layout:
  - `hold-long` → single full-width **splash panel**
  - `standard` → 2–3 panel row
  - `cut-busy` → tight 4–6 panel grid (staccato rhythm)
- `role` tunes per-panel emphasis: `establish`/`establishing-*` = wide; `character-close` =
  portrait focus crop; `vfx-onset`/`vfx-composite` = receives existing chromatic-aberration /
  bleed treatment from `horror-effects.js`; `resolution` = held, larger.
- **Section breaks** (EP, I–V) render as full-bleed chapter dividers using the
  `section_break_*` / `S1-*` frames.
- Mobile: all multi-panel beats collapse to a **single vertical column** (one panel per row,
  full-width). Pacing conveyed via panel size + inter-panel spacing rather than grid columns.

---

## 7. Captions & accessibility

- `dialogue.json` lines → **narration boxes** (`speaker: narrator`) and **speech bubbles**
  (named speakers), styled to the horror aesthetic, placed over/adjacent to panels.
- `story-index.csv` `description` → panel `alt` text (accessibility gain over prose page).
- Retain: "skip to content" link, reading-progress bar (repurposed as scroll progress),
  semantic landmarks.
- Honor `prefers-reduced-motion`: disable Ken Burns/parallax, panels appear without motion.

---

## 8. Animation

Vanilla CSS/JS, no new dependencies:
- Panel entry: fade + subtle **Ken Burns** (scale/pan) + light **parallax**, triggered on
  entry by the **same IntersectionObserver** used for horror triggers.
- VFX-role panels invoke existing `horror-effects.js` visual effects (chromatic aberration,
  bleed) rather than new code.

---

## 9. Horror-trigger preservation

The prose's tuned attributes — `data-horror`, `data-stinger`, `data-whisper`, `data-buildup`,
plus volume/pan/rate variants — are **re-mapped onto their matching beat** (matched by beat
id; e.g. the `coordinates_write` whisper trigger attaches to that beat's coordinate caption).
A one-time extraction pass reads the current prose page, associates each existing trigger with
its nearest beat, and records it in the manifest's `triggers` field. **No changes to
`horror-effects.js` or `horror-samples.js`** — only the host elements change.

---

## 10. Performance

- `optimize-comic-frames.py`: 1280×720 JPG → **WebP (~1280w)** + tiny LQIP blur placeholder
  (data-URI in manifest). Only the optimized set is committed (far below 218 MB).
- Panels lazy-load (`loading="lazy"` + observer); per-section lazy DOM mounting so all 1006
  panels are not in the DOM simultaneously.
- Retain WebGL pixel-ratio cap (1.5×) and adaptive particle counts already in the codebase.

---

## 11. Validation & testing

Per project norm (no test framework):
- `tools/validate-comic-manifest.py`: every manifest panel `src` resolves to an existing
  WebP; every beat has ≥1 panel; every prose trigger was matched to a beat (no orphans);
  section ordering matches `frame-plan` `beat_order`.
- Manual browser pass: desktop grid + mobile single-column; reduced-motion; horror triggers
  fire; deploy to Self-Host staging URL.

---

## 12. Phasing

- **Phase 1 (this spec):** manifest build + frame optimization + comic-engine + comic.css +
  rewritten `act1-fifth-harmonic.html` + horror-trigger re-mapping + responsive mobile +
  validation. Captions + existing horror SFX only.
- **Phase 2 (later):** layer generated character dialogue audio, synced to panels via
  `dialogue.json` `timing` fields, routed through the existing Howler bus.
- **Future:** Acts II/III become data-only once their beat/dialogue/pacing metadata exists.

---

## 13. Risks

- **Replacing prose is destructive** to hand-tuned horror triggers → mitigated by the
  beat-matching re-mapping pass (§9) and git recoverability of the prose.
- **1006 panels** is a large DOM/asset set → mitigated by per-section lazy mounting, WebP,
  LQIP, lazy-load.
- **Beat/trigger matching** between prose and frame-plan may have edge cases (triggers not
  cleanly on a beat boundary) → validation step flags orphans for manual placement.
- **Caption text source**: `dialogue.json` is distilled, not full prose; some narrative
  nuance from the prose is intentionally dropped (motion-comic tradeoff, accepted).
