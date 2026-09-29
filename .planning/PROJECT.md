# Project Context

## Authority Map

- Product requirements: docs/design.md (v1.0 design), docs/v1.1.0-specification.md, docs/v1.1.2-governance-boundary-hardening.md
- Architecture: docs/design.md (section 4)
- Release / compatibility policy: docs/compatibility.md
- Test instructions: README.md (`python -m pytest tests/ --basetemp=.pytest-tmp`)
- Operational runbooks: README.md (Install / Distribution paths)
- Version / release evidence: Git tags + GitHub Releases; .planning/archive/<version>/SUMMARY.md

## Cross-Release Constraints

- `.agents/skills/` is the discovery path shared by Codex, opencode and
  Kimi Code; Claude Code requires a mirror under `.claude/skills/`.
- All four tools ignore unknown SKILL.md frontmatter fields — keep one
  superset frontmatter, never per-tool forks.
- Helper CLI (`scripts/plan.py`) is Python 3 standard library only and
  must run on Windows and Unix.
- The CLI performs mechanical operations only; semantic compaction and
  knowledge promotion remain agent work.
- pytest temp root: use `--basetemp=.pytest-tmp` (the default temp
  root is not writable on the primary Windows dev machine).

## Stable Context

Planning for this repo itself lives in `.planning/` (dogfooding).

## Long-Term Decisions

### D-001

Decision:
Canonical skill source lives at `.agents/skills/planscope/`.

Authoritative destination:
docs/compatibility.md

Reason:
It is the only project-level path discovered natively by three of the
four supported tools; Claude Code is served by a sync script.

### D-002

Decision:
Skill renamed from working name `scoped-planning-with-files` to `planscope`.

Authoritative destination:
PROJECT.md — no better source

Reason:
Matches the repository name; satisfies opencode's name-equals-directory rule.

### D-003

Decision:
Markdown stays the only canonical planning state — no `state.json`,
database or shadow caches in v1.x.

Authoritative destination:
PROJECT.md — no better source

Reason:
Mechanical consistency (release transitions, status validation, INDEX
projection) belongs to `scripts/plan.py`; a second machine-readable
state layer would drift from the Markdown source of truth.
