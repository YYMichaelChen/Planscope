# Work Log

## Current State

Phase:
P4

Task:
T-407

Next:
None — release closed and archived; tag v1.1.0 created.

Blockers:
None.

## Recent Activity

### 2026-09-27

Completed:
T-407 release close and archive; cleanup of outdated v1.1 planning
(archive/v1.1 removed — recoverable from git history at d1407de).

Changed:
Semantic close of v1.1.0: SUMMARY.md written; F-001 promoted to
PROJECT.md Development Conventions; ROADMAP.md updated (v1.1.0
complete, post-release observation items for §36, deferred T-404..T-406
moved to Later); PLAN Status complete. Outdated v1.1 archive deleted.

Validation:

`plan sync` + `plan close v1.1.0` + `plan doctor` — see below.

Result:
Pass.

### 2026-09-27

Completed:
P1 (T-101..T-107), P2 (T-201..T-204), P3 (T-301..T-303), T-401, T-402,
T-403, stale release v1.1 semantic close + archive.

Changed:
Implemented the full v1.1.0 hardening spec (`docs/v1.1.0-specification.md`):

- `spwf/core.py`: patch-version regex, canonical phase/release status
  sets, `parse_plan` phase detail, illegal-directory detection.
- `spwf/commands.py`: `activate_release` / `clear_active_release`
  (atomic INDEX rewrite preserving Critical Constraints), single-active
  release gate, strict close gates (all phases `complete` + PLAN Status
  `complete` + SUMMARY), expanded doctor (root structure, release file
  presence, schema, status validation, INDEX/PLAN drift WARN),
  collision-safe LOG archive names (`-LOG-YYYYMMDD-NNN`), new `cmd_sync`.
- `plan.py`: `sync` subcommand; version bumped to 1.1.0.
- `install.py`: `--project` installs both `.agents/` and `.claude/`
  surfaces; canonical-source SKIP protection (also covers existing
  junctions/symlinks).
- SKILL.md: single-active-release, PLAN-authority + sync, close
  ordering, archive boundary, search-before-full-read, new recovery
  protocol.
- Docs: `skill-development-plan.md` → `docs/design.md`, v1.1.0 spec →
  `docs/v1.1.0-specification.md`, README + compatibility updated.
- Added `.claude-plugin/marketplace.json` (T-302, canonical source
  referenced, no second SKILL implementation).

Validation:

`python -m pytest tests/ -q --basetemp=.pytest-tmp` — 53 passed,
1 skipped (symlink test skipped on Windows). Clean-repo walkthrough
(init → open v1.1.0 → drift → sync → double LOG rotation → complete →
close) all green; doctor 0 failures / 0 warnings after close.
`install.py --check --project .` — both surfaces SKIP (canonical /
linked), rc 0.

Dogfooding:
Closed stale release v1.1 with the new CLI (semantic close first:
T-002 completed via v1.1.0 T-302, T-004..T-006 transferred to P4 as
T-404..T-406; SUMMARY written; ROADMAP + PROJECT.md updated with
D-003). `plan close v1.1` archived it and cleared INDEX atomically.

Result:
Pass.
