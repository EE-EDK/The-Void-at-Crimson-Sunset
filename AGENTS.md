# GEMINI Mandates — Agent Startup Brief

> **All AI agents read this first.** Project-scoped startup brief for any agent \
> (Claude, Gemini, Grok, Cursor, etc.) entering this project.

## Session Startup

Read project docs in this order (load only what the task needs):

1. **`GROK.md`** — Grok execution context and project mandates (**read first in Grok sessions**)
2. **`AGENTS.md`** — this startup brief
3. **`CLAUDE.md`** — build commands, directory structure, conventions
4. **`GEMINI.md`** — governance mandates (overrides CLAUDE within the same directory tier)

Load only what is scoped to this project; do **not** import sibling project context.


**Doc precedence (same tier):** `GROK.md` → `AGENTS.md` → `CLAUDE.md` → `GEMINI.md`

## Project Identity

- **HTML Files:** Located in the root directory.
- **CSS:** Located in `assets/css/`.
- **JavaScript:** Located in `assets/js/`.
- **Audio Samples:** Located in `assets/audio/` (stingers/, buildups/, atmospheres/, extras/).
- **Media (Video):** Located in `assets/video/`.
- **Documentation:** Located in `docs/`.

## Red Lines

- No destructive file operations without explicit user confirmation.
- No commits or pushes without explicit user authorization (END SESSION counts as authorization for its defined scope).
- **Historical preservation:** annotate stale items, never delete resolved records.
- Surgical changes only — minimize blast radius; do not refactor surrounding code unless asked.
- No invented specs, values, or configurations; ground all decisions in datasheets or empirical data.

## Commit Rules

See workspace-level protocol at `ENGINEERING-PROJECTS/root `AGENTS.md`` §Git commits.
Summary: do **not** infer "commit and push everything" unless the user explicitly requests it or triggers END SESSION.

## Validation Before Completion

- Always verify with tests, linters, DRC/ERC, or build scripts before declaring done.
- Never claim success without running the relevant verification suite.

## Parent Context

Workspace-level agent rules: `ENGINEERING-PROJECTS/root `AGENTS.md``
Technical Editor Protocol v5.4: `ENGINEERING-PROJECTS/templates/technical_editor_protocol_v5.4.md`


