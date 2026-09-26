# Project Context

## Architecture

Planscope is a Markdown-first agent skill. No database, no runtime,
no build step.

### Canonical skill source

`.agents/skills/planscope/` — the single source of truth
(SKILL.md + templates/ + scripts/).

### Distribution

`install.py` mirrors the canonical source into tool-specific skill
directories (copy, or junction/symlink with `--link`).

## Core Constraints

- `.agents/skills/` is the discovery path shared by Codex, opencode and
  Kimi Code; Claude Code requires a mirror under `.claude/skills/`.
- All four tools ignore unknown SKILL.md frontmatter fields — keep one
  superset frontmatter, never per-tool forks.
- Helper CLI (`scripts/plan.py`) is Python 3 standard library only and
  must run on Windows and Unix.
- The CLI performs mechanical operations only; semantic compaction and
  knowledge promotion remain agent work.

## Development Conventions

- `python -m pytest tests/` must stay green; `tests/test_compat.py` is
  the four-tool compliance guard.
- Planning for this repo itself lives in `.planning/` (dogfooding).

## Stable Domain Knowledge

See `docs/compatibility.md` for the four-tool skill-loading matrix
(discovery paths, frontmatter rules, portability constraints).

## Long-Term Decisions

### D-001

Decision:
Canonical skill source lives at `.agents/skills/planscope/`.

Reason:
It is the only project-level path discovered natively by three of the
four supported tools; Claude Code is served by a sync script.

### D-002

Decision:
Skill renamed from working name `scoped-planning-with-files` to `planscope`.

Reason:
Matches the repository name; satisfies opencode's name-equals-directory rule.

### D-003

Decision:
Markdown stays the only canonical planning state — no `state.json`,
database or shadow caches in v1.x.

Reason:
Mechanical consistency (release transitions, status validation, INDEX
projection) belongs to `scripts/plan.py`; a second machine-readable
state layer would drift from the Markdown source of truth.
