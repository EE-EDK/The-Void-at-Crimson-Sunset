# GROK.md — The Void is Crimson

## Project Identity

**The Void is Crimson** is an immersive interactive horror experience — a multi-act cinematic static web app combining procedural visual effects with a spatial audio system. No build tools, no framework: vanilla HTML/CSS/JS served directly.

## Four-Act Architecture

| Act | File |
|-----|------|
| Title / landing (vortex effect) | `index.html` |
| Act I: The Fifth Harmonic | `act1-fifth-harmonic.html` |
| Act II: The First Weave | `act2-first-weave.html` |
| Act III: The New Rebirth | `act3-new-rebirth.html` |
| Conclusion (video) | `conclusion.html` |

## Core Tech Stack

- **Three.js (r160)** — loaded from CDN, full-screen fragment shader for vortex/starfield/nebula/fluid effects.
- **Web Audio API** — custom synthesis engine for procedural drones, binaural beating, whispers, impacts.
- **Howler.js** — 58 pre-recorded horror samples (stingers/buildups/atmospheres/extras) with spatial audio, crossfading, ducking.

## Doc Precedence

`GROK.md` → `AGENTS.md` → `CLAUDE.md` (same tier). Root workspace mandates (`ENGINEERING-PROJECTS/AGENTS.md`) and category mandates (`ACTIVE-PROJECTS/web/CLAUDE.md`) win over this file. Do not import sibling-project context — `ai-video-photo/The Void is Crimson` is an unrelated codebase despite the shared name.
