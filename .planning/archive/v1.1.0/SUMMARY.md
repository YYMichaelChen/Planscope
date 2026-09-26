# Release v1.1.0 Summary

## Outcome

Planscope v1.1.0 (Hardening) shipped: the v1.0 scoped-planning model is
now deterministic in lifecycle, internally consistent, and cheaper to
recover, without any new architecture.

## What shipped

- **Atomic lifecycle** (T-101/T-102): `plan open` / `plan close`
  rewrite the entire INDEX working set — no stale focus, phase, task,
  blocker or path can survive a release switch.
- **Single active release** (T-103): opening a second release fails;
  doctor treats multiple release directories as a hard failure.
- **Strict status model** (T-104): phases allow only
  `pending | in_progress | complete`; close uses a positive completion
  check plus a required release-level `Status: complete`.
- **Corrected close** (T-105): semantic close (SUMMARY, knowledge
  promotion, roadmap, PLAN status) is a documented prerequisite;
  `plan close` is the final mechanical commit.
- **Collision-safe LOG rotation** (T-106): archives are named
  `{release}-LOG-YYYYMMDD-NNN.md`; same-day rotations never overwrite.
- **Expanded doctor** (T-107): root structure, release file presence,
  PLAN schema, status validation, illegal directories, and INDEX/PLAN
  drift detection (`WARN` + `plan sync`).
- **`plan sync`** (T-201): PLAN is the canonical work source; INDEX is
  its mechanical routing projection.
- **Routing rules** (T-202/T-203): search-before-full-read and a
  tightened recovery protocol, enforced via SKILL.md.
- **Docs cleanup** (T-204): legacy specs moved under `docs/`.
- **Unified install** (T-301): `install.py --project` installs both
  `.agents/` and `.claude/` surfaces with canonical-source protection.
- **Distribution** (T-302): `.claude-plugin/marketplace.json` for
  Claude Code GitHub installs; one canonical SKILL.md, no forks.
- **Patch versions** (T-303): `vX.Y.Z` accepted everywhere.

## Verification

- 53 tests passed, 1 skipped (symlink test, Windows); 24 new
  regression tests across lifecycle, doctor, sync, rotation, install,
  and versioning.
- Clean-repo walkthrough: init → open → drift → sync → double LOG
  rotation → complete → close, all green.
- Dogfooded: stale release v1.1 closed and archived with the new CLI;
  v1.1.0 development itself was managed under `.planning/` throughout.

## Deferred

Real-host fresh-install verification in Codex CLI, opencode and Kimi
Code (T-404..T-406) moved to post-release usage per spec §36 and is
tracked in ROADMAP.md.

## Knowledge

F-001 (pytest `--basetemp=.pytest-tmp` required on this machine)
promoted to PROJECT.md Development Conventions.
