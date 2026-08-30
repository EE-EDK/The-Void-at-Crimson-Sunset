# AGENTS.md — The Void is Crimson — Agent Startup Brief

> **All AI agents read this first.** Project-scoped startup brief for any agent \
> (Claude, Gemini, Grok, Cursor, etc.) entering this project.

## Session Startup

Read project docs in this order (load only what the task needs):

1. **`GROK.md`** — Grok execution context and project mandates (**read first in Grok sessions**)
2. **`AGENTS.md`** — this startup brief
3. **`CLAUDE.md`** — build commands, directory structure, conventions

Load only what is scoped to this project; do **not** import sibling project context — in particular, `ACTIVE-PROJECTS/ai-video-photo/The Void is Crimson` is a **different codebase** (a Python AI frame-generation pipeline, separate remote `Void-is-Crimson-Film.git`) that shares only the name and theme.

**Doc precedence (same tier):** `GROK.md` → `AGENTS.md` → `CLAUDE.md`

## Project Identity

**The Void is Crimson** is an immersive interactive horror experience — a hand-built, multi-act static web app (`act1-fifth-harmonic.html`, `act2-first-weave.html`, `act3-new-rebirth.html`, `conclusion.html`) using **Three.js (r160)** for shader-based visual effects and the **Web Audio API** for procedural drone/binaural synthesis, layered with **Howler.js** for spatial playback of 58 pre-recorded horror samples. No build tools, no framework — vanilla HTML/CSS/JS served as a static site.

## Red Lines

- No destructive file operations without explicit user confirmation.
- No commits or pushes without explicit user authorization (END SESSION counts as authorization for its defined scope).
- **Historical preservation:** annotate stale items, never delete resolved records.
- Surgical changes only — minimize blast radius; do not refactor surrounding code unless asked.
- No invented specs, values, or configurations; ground all decisions in datasheets or empirical data. This project shares the category-level performance budget of **>20 FPS and <200 draw calls** per `ACTIVE-PROJECTS/web/CLAUDE.md`.

## Commit Rules

See workspace-level protocol at root `AGENTS.md` (`ENGINEERING-PROJECTS/AGENTS.md`) §Commit Rules.
Summary: do **not** infer "commit and push everything" unless the user explicitly requests it or triggers END SESSION.

## Validation Before Completion

- No build step and no automated test framework — validate by manual browser testing (open the relevant act HTML file directly, verify visuals/audio behave as expected).
- Never claim success without exercising the change in a browser.

## Parent Context

Workspace-level agent rules: root `AGENTS.md` (`ENGINEERING-PROJECTS/AGENTS.md`)
Category context: `ACTIVE-PROJECTS/web/AGENTS.md` / `ACTIVE-PROJECTS/web/CLAUDE.md`
Technical Editor Protocol v5.4: `ENGINEERING-PROJECTS/templates/technical_editor_protocol_v5.4.md`
