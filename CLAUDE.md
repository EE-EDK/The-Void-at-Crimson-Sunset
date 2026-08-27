# CLAUDE.md

## Project Overview

"The Void is Crimson" — an interactive cosmic horror web experience with a three-act narrative structure. The playable web experience is a pure static site, no build tools. A separate Python toolchain (`tools/`) builds and validates a comic/itch.io export — see "Comic / itch.io export pipeline" below.

### State as of 2026-08-27

25 commits landed 2026-05-02 through 2026-08-14 (`git log --since=2026-05-02 --format="%h %ad %s" --date=short`). The bulk (2026-06-23/24) built the comic/itch.io export pipeline end to end: manifest build from generation-repo metadata, per-beat WebP strip packing, manifest + itch.io-constraint validation, and itch.io zip packaging — plus an Act I motion-comic design spec in `docs/`. Also landed: a mobile viewport-inflation fix so the acts read correctly on a phone (`1e0e1a5`, 2026-08-06), and the doc-standard remediation that added `AGENTS.md`/`GROK.md`/`.grok` load rule (`d5d346d`, 2026-08-14).

## Project Structure

```
index.html                          # Title/landing page with vortex effect
act1-fifth-harmonic.html            # Act I
act2-first-weave.html               # Act II
act3-new-rebirth.html               # Act III
conclusion.html                     # Conclusion video page
assets/
  css/
    shared-styles.css               # Core styles, CSS custom properties
    act1-custom.css                 # Red theme overrides
    act2-custom.css                 # Red→blue transition theme
    act3-custom.css                 # Blue theme overrides
  js/
    howler.min.js                   # Howler.js audio library (core + spatial)
    horror-samples.js               # Howler-based sample engine (58 sounds)
    horror-effects.js               # Audio synthesis, visual horror triggers
    visuals-engine.js               # WebGL shader engine (Three.js r160)
  audio/
    stingers/                       # 16 stinger sounds (OGG + MP3)
    buildups/                       # 16 build-up sounds (OGG + MP3)
    atmospheres/                    # 16 atmosphere loops (OGG + MP3)
    extras/                         # 10 custom sounds (OGG + MP3)
  video/
    Horror-Finale.mp4
  comic/                             # Comic pipeline output: act1.comic.json manifest, strips/, narration/
docs/                               # Technical docs, guides, audits, archive/
_development/                       # Dev sources, howler-Javascript, Temp tests
tools/                               # Comic/itch.io export pipeline (Python + pytest) — see below
frames-generated/                   # Source comic frame images, keyed by beat (input to tools/pack-comic-strips.py)
dist/                               # itch.io zip build output (gitignored — see .gitignore)
```

## Tech Stack

- **HTML5/CSS3/Vanilla JS** — no frameworks, no bundler, no npm
- **Three.js r160** — loaded from CDN (cdnjs.cloudflare.com) with fallback
- **Web Audio API** — custom synthesis for horror audio (drone, whispers, impacts)
- **Howler.js** — 58 pre-recorded horror samples with spatial audio, format fallback (OGG/MP3)
- **Google Fonts** — Cormorant Garamond (300/400/700)

## Development

The playable web experience has no build step: edit files directly and test in browser, manual testing only. The comic/itch.io export side has its own Python build+test toolchain — see "Comic / itch.io export pipeline" below.

## Comic / itch.io export pipeline

A Python toolchain in `tools/` builds a comic-strip export of Act I and packages it for itch.io. Built 2026-06-23/24 (see "State as of 2026-08-27"). Tests run with `pytest` from the project root (`pytest.ini` points `testpaths` at `tools/tests`); **21/21 pass** (verified 2026-08-27).

CLI scripts (`tools/*.py`), run in pipeline order:
- `build-comic-manifest.py` — build `assets/comic/act1.comic.json` from generation-repo metadata.
- `pack-comic-strips.py` — pack frames into per-beat WebP strips and augment the manifest in place.
- `validate-comic-manifest.py` — validate manifest + the set of files that would ship to itch.io.
- `package-itch.py` — assemble an itch.io-ready zip (index.html at root) after validation.

Supporting modules (`tools/comic/`):
- `manifest.py` — join frame-plan + dialogue + story-index into a structural comic manifest.
- `slugs.py` — slug helpers for itch.io-safe, case-stable asset names.
- `strips.py` — pack a beat's frames into one vertical WebP sprite strip.
- `validate.py` — validate a packed comic manifest + itch.io deploy constraints.
- `deploy.py` — canonical list of files that ship to itch.io (also the set size/count-validated).

Tests live in `tools/tests/` (`test_build_cli.py`, `test_manifest.py`, `test_package_itch.py`, `test_slugs.py`, `test_strips.py`, `test_validate.py`), one file per module above plus the CLI entry points.

### Deployment (Self-Host)

Served via Self-Host on kunz-ai-hub (Caddy + Tailscale Funnel). Static site only, no API backend.
- **Live URL:** `https://kunz-ai-hub.tailb1d0b7.ts.net/void/app/`

After pushing changes to GitHub:
- **Automatic:** `autodeploy.timer` on kunz-ai-hub polls every 5 min and deploys if changed.
- **Instant:** From KunzPrime, run `ENGINEERING-PROJECTS/Self-Host/scripts/deploy-remote.sh`.
- **Manual:** On kunz-ai-hub, run `~/ENGINEERING-PROJECTS/Self-Host/scripts/deploy.sh`.

## Key Architecture

- **visuals-engine.js**: Full-screen fragment shader on a Three.js plane. Renders vortex/black hole (main page only), starfield, nebula, and fluid effects. Key uniforms: `u_time`, `u_tension`, `u_scroll`, `u_themeColor`, `u_isMainPage`. IIFE pattern.
- **horror-effects.js**: Audio synthesis (dissonant chords, binaural beating, metal scrapes) and visual effects (chromatic aberration, screen breathing, film grain). Triggered via CSS classes and data attributes (`data-horror="scramble"`, `data-whisper="..."`). Creates shared AudioContext with Howler.js and routes through limiter. IntersectionObserver calls `HorrorSamples.handleTriggerElement()` for sample layers.
- **horror-samples.js**: Howler.js integration module. Manages 48 Ulrich Wehner sounds (CC-BY 4.0) + 10 custom extras. Provides atmosphere crossfading, stinger playback, build-up management, ducking, spatial audio, and combination recipes. Triggered via HTML data attributes: `data-stinger`, `data-buildup`, `data-atmosphere`, `data-extra`, `data-extra2`, `data-recipe`.
- **Audio bus topology**: `Howler.masterGain -> sampleBus(0.50) -> master(0.30) -> limiter(-6dB) -> destination`. Sub-buses: atmosphereBus(0.25), stingerBus(0.70). Ducking: atmosphere ducks 30% when stingers fire.
- **CSS**: Custom properties in `:root` for theming. Act-specific overrides in separate files. Glassmorphism, fluid typography with `clamp()`.

## Coding Standards

- Maintain the horror/dark aesthetic in all visual updates
- Vanilla CSS only — no frameworks
- Three.js r160 for all 3D/WebGL effects
- IIFE pattern for JS scope isolation, `'use strict'`
- Verify asset paths after any structural changes
- Pixel ratio capped at 1.5x for WebGL performance
- Adaptive particle counts (1000 mobile, 2000 desktop)
- Script load order: howler.min.js -> horror-samples.js -> horror-effects.js (all deferred)
- Audio samples by Ulrich Wehner licensed CC-BY 4.0, attribution required in page footer

## TODO
- [ ] No open items recorded (section rebuilt 2026-08-27; the previous list duplicated the Development and Coding Standards sections verbatim).

## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- After modifying code files in this session, run `python3 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"` to keep the graph current
