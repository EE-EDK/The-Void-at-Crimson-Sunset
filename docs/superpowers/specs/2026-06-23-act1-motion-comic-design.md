# Act I Illustrated Experience — Design Spec (v2)

**Date:** 2026-06-23
**Project:** The Void is Crimson
**Status:** Approved design (v2), pending implementation plan
**Scope:** Augment `act1-fifth-harmonic.html` ("The Fifth Harmonic") with interleaved comic
panels and a multi-mode reading/audio experience.

> **v2 supersedes v1.** v1 was a *text-replacing* motion comic with distilled captions. v2
> keeps the full prose as the spine, interleaves comic panels per beat, and adds a mode
> switcher (Read / Read + Atmosphere / Narrated). Caption distillation and horror-trigger
> re-mapping are **dropped** (see §2).

---

## 1. Summary

Keep the complete prose of `act1-fifth-harmonic.html` as the narrative spine and **interleave
comic panels** (built from the 1006 pre-generated frames) at their matching beats — an
illustrated-novel feel rather than a text-replacing comic. Add a **mode switcher**:

- **Read** — text + panels, silent.
- **Read + Atmosphere** — text + panels + the existing horror SFX/trigger engine.
- **Narrated** *(Phase 2)* — text + panels + per-character voiced narration synced to beats,
  consuming audio produced by the sibling video project.

The build is **manifest-driven**: a Python step joins existing generation-repo metadata into
one runtime manifest. Acts II/III stay as untouched prose (no metadata yet) and become
data-only work later.

---

## 2. Decisions (locked, v2)

| Decision | Choice | Rationale |
|---|---|---|
| Experience | **Illustrated full-text** — prose spine + interleaved panels | Preserves narrative nuance; keeps horror triggers on their original sentences |
| Integration | **Augment** `act1-fifth-harmonic.html` in-place (not replace) | Lower risk; prose + tuned triggers retained |
| Scope | **Act I only** (= full Fifth Harmonic story, 180 beats / 1006 frames, sections EP + I–V) | Only Act I has frame-plan + dialogue + pacing + narration metadata |
| Paradigm | **Scroll-driven** | Reuses existing IntersectionObserver + progress bar + horror engine; reader-paced |
| Panel density | **All frames, pacing-sized** | Data-driven; rhythm from `pacing_role`, no manual culling |
| Modes | **Read · Read+Atmosphere · Narrated** (no text-hidden comic-only mode) | User selection |
| Narration voicing | **Per-character voices + narrator** | Matches `_refs/` identities; narrator = `narrator-v4-5050.wav` |
| Narration audio source | **Reuse sibling video project `_narr/*_mixed.wav`** (and per-speaker stems) | Don't regenerate; single source of truth for audio |
| Narration phasing | **Phase 2, rolls out per section** (S1 ready today) | Only S1 narration produced so far |
| Optimized panel assets | **Commit optimized WebP**; 218 MB originals stay gitignored | Static site deploys from git |
| Mobile | **Responsive single source** — CSS collapses to single-column webtoon flow | No divergence; vanilla CSS |
| ~~Caption distillation~~ | **Dropped** | Full prose retained; captions unnecessary |
| ~~Horror-trigger re-mapping~~ | **Dropped** | Prose retained → triggers keep original anchors |

---

## 3. Source assets (verified)

Generation/video repo: `ACTIVE-PROJECTS/ai-video-photo/The Void is Crimson/`

| Asset | Provides |
|---|---|
| `generated/frames-generated/*.jpg` (1006, **1280×720**) | Panel art, `#### - role - beat.jpg` |
| `output/act1-1006-frame-plan.json` | Per-frame `beat`, `role`, `section`, `pacing_role`, `target_filename` |
| `output/act1-video-manifest.json` | Canonical 180-clip beat spine: `location`, `characters`, timing |
| `output/act1-story-index.csv` | Per-frame `description` (→ alt text), `characters`, `dialogue` |
| `src/act1-dialogue.json` | Per-beat `speaker`, `line`, `direction`, `timing` |
| `generated/videos/_narr/<clip>_mixed.wav` | **Per-beat narration mix** (Narrated mode audio) — S1 only so far |
| `generated/videos/_narr/<clip>_<n>_<speaker>.wav` | Per-speaker narration stems (optional finer control) |
| `generated/audio/dialogue/_refs/*.wav` | 13 character voice identities (alex, jen, morrison, iris, …) |

Web repo: `ACTIVE-PROJECTS/web/the-void-is-crimson/`

| Asset | Provides |
|---|---|
| `Media/narrator-v4-5050.wav` | **Narrator voice** (user preference) for the Narrated mode |
| `act1-fifth-harmonic.html` | Existing prose + tuned horror triggers (kept as spine) |
| `assets/js/horror-effects.js`, `horror-samples.js` | Trigger engine (reused unchanged) |

**Verified facts:** frames are 1280×720; `frames-generated/` is gitignored in the web repo;
`horror-effects.js` drives triggers through one IntersectionObserver (~line 1030) →
`HorrorSamples.handleTriggerElement(el)`; all 180 beats belong to `act1-fifth-harmonic.html`;
the sibling video project produces shared frames + per-beat narration (`act1.mp4`, 30 min) and
has completed only section S1 to date; `Stopmotion-AI` is an unrelated project.

---

## 4. Architecture

```
the-void-is-crimson/
  act1-fifth-harmonic.html        # augmented: prose kept; panel mounts + mode switcher added
  assets/
    js/
      comic-engine.js             # NEW: fetch manifest, inject panels at beat anchors, animate on scroll
      mode-controller.js          # NEW: Read / Atmosphere / Narrated switching + narration playback
    css/comic.css                 # NEW: panel grid, mobile collapse, switcher UI, animations
    comic/
      act1.comic.json             # NEW: built manifest (committed)
      frames/act1/*.webp          # NEW: optimized panels (committed)
      narration/act1/*.mp3        # NEW (Phase 2): transcoded per-beat narration mixes (committed)
  tools/
    build-comic-manifest.py       # NEW: join frame-plan + video-manifest + dialogue + story-index + narration index
    optimize-comic-frames.py      # NEW: 1280×720 JPG → WebP (~1280w) + LQIP
    validate-comic-manifest.py    # NEW: panels resolve; beats ≥1 panel; beat order matches; narration refs valid
```

### Components & boundaries
- **`build-comic-manifest.py`** — pure data join → `act1.comic.json`. Marks each beat's
  narration availability (`narration: "ready" | "pending"`).
- **`optimize-comic-frames.py`** — image pipeline only; idempotent.
- **`comic-engine.js`** (IIFE, `'use strict'`) — anchors prose paragraphs to beats and injects
  the beat's panel cluster after the matching paragraph; animates panels on scroll via the
  existing observer. Mode-agnostic.
- **`mode-controller.js`** (IIFE, `'use strict'`) — owns the switcher state and audio:
  - Read → no audio.
  - Read + Atmosphere → ensures horror engine active (existing triggers fire on scroll).
  - Narrated → plays the beat's narration mix as it enters view; falls back to Atmosphere
    for beats marked `pending`. Routed through the existing Howler bus.
- **`comic.css`** — all layout/animation; desktop grid + mobile single-column; switcher UI;
  honors `prefers-reduced-motion`.

---

## 5. Prose ↔ beat anchoring

The prose page is annotated so each beat's panels land at the right paragraph. Approach: add
`data-beat="<beat_id>"` to the paragraph(s) that open each beat (derived by matching the
existing prose against `dialogue.json` / `story-index` line text — a one-time authoring pass,
validated). `comic-engine.js` injects each beat's panel cluster immediately after its
`data-beat` anchor. Existing horror-trigger attributes on those paragraphs are untouched.

---

## 6. Panel & layout model

- Each beat = a comic cluster injected after its prose anchor. `pacing_role` drives layout:
  `hold-long` → full-width splash; `standard` → 2–3 panel row; `cut-busy` → tight 4–6 grid.
- `role` tunes emphasis (establish = wide; character-close = portrait focus; vfx-* = receives
  existing chromatic-aberration/bleed effects; resolution = held/larger).
- Section breaks (EP, I–V) → full-bleed chapter dividers using `section_break_*` / `S1-*`.
- Mobile: clusters collapse to a single vertical column; pacing conveyed via size/spacing.

---

## 7. Modes & switcher

A persistent control (top corner, glassmorphic, matches aesthetic) toggles:
- **Read** (default): silent.
- **Read + Atmosphere**: existing horror SFX/triggers active.
- **Narrated** *(Phase 2)*: per-beat narration plays on scroll-into-view; narrator lines use
  `narrator-v4-5050.wav`–derived voice, dialogue uses per-character stems; ducks atmosphere
  under speech (existing ducking bus). Beats without audio fall back to Atmosphere silently.

Mode persists in `localStorage`. Honors `prefers-reduced-motion` (no auto-advance; scroll-paced
regardless of mode). All audio gated behind a user gesture (existing AudioContext unlock).

---

## 8. Accessibility & performance

- Panel `alt` from `story-index` `description`; retain skip-link + progress bar + landmarks.
- `prefers-reduced-motion`: disable Ken Burns/parallax; panels appear without motion.
- WebP (~1280w) + LQIP placeholders; `loading="lazy"`; per-section lazy DOM mounting so all
  1006 panels aren't in the DOM at once. Retain WebGL pixel-ratio cap (1.5×) + adaptive
  particle counts.
- Narration committed as transcoded **MP3/OGG** (web-friendly) rather than raw WAV.

---

## 9. Validation & testing

No framework (project norm):
- `tools/validate-comic-manifest.py`: every panel `src` resolves; every beat ≥1 panel; beat
  order matches `frame-plan` `beat_order`; every `data-beat` anchor in the HTML exists in the
  manifest and vice-versa; narration refs (Phase 2) resolve or are marked `pending`.
- Manual browser pass: desktop grid + mobile column; all three modes; reduced-motion; horror
  triggers fire; deploy to Self-Host staging.

---

## 10. Phasing

- **Phase 1:** manifest build + frame optimization + prose beat-anchoring + `comic-engine.js`
  + `comic.css` + responsive mobile + **Read** and **Read + Atmosphere** modes + the switcher
  UI (with Narrated present but disabled/greyed) + validation.
- **Phase 2:** **Narrated** mode — transcode the video project's `_narr/*_mixed.wav` per beat,
  wire `mode-controller.js` playback, enable section-by-section as audio lands (S1 first).
- **Future:** Acts II/III become data-only once their beat/dialogue/narration metadata exists;
  optional text-hidden "comic-only" mode (would reintroduce caption distillation + trigger
  re-mapping).

---

## 11. Cross-project relationship

The web project (interactive illustrated experience) and the sibling
`ai-video-photo/The Void is Crimson` (frame + video + narration generation) **share assets**:
frames and per-beat narration originate in the video project; the web project consumes
optimized derivatives. Narration generation stays the video project's responsibility; the web
project never generates audio. This keeps a single source of truth and lets the 30-min video
render and the web comic evolve together.

---

## 12. Risks

- **Prose ↔ beat anchoring** may have edge cases (beats spanning multiple paragraphs, or
  paragraphs with no beat) → validation flags unmatched anchors for manual placement.
- **1006 panels** is a large asset/DOM set → per-section lazy mounting, WebP, LQIP, lazy-load.
- **Narration coverage** is incomplete (S1 only) → Narrated gated per section; graceful
  fallback to Atmosphere for `pending` beats.
- **Two-repo coupling** → build tools take the generation-repo path as a config arg; the build
  depends on that sibling repo being present.
