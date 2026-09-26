# Release v1.1.1 Summary

**Codename:** Distribution Fix
**Type:** Patch
**Date:** 2026-09-27

## What shipped

A focused distribution and validation patch for the v1.1 hardening
release. No new planning concepts, no architecture expansion.

### Distribution (P1)

- New conventional Claude plugin root at `plugins/planscope/` with a
  minimal `.claude-plugin/plugin.json` (v1.1.1).
- Plugin skill payload at `plugins/planscope/skills/planscope/` is
  mechanically generated from the canonical
  `.agents/skills/planscope/` source via `install.py --build-plugin`
  (byte-identical, `__pycache__`/`*.pyc` excluded).
- `install.py --check-plugin` reports `PLUGIN IN SYNC` /
  `PLUGIN DRIFTED`; drift fails the release gate.
- `.claude-plugin/marketplace.json` now points at `./plugins/planscope`.
- `install.py --project` behavior unchanged (T-116): still installs
  `.agents/skills/` + `.claude/skills/` in one command.

### Lifecycle validation (P2)

- Normal `plan close` rejects a missing PLAN.md (T-211) and a
  zero-phase PLAN (T-212); `--force` bypasses both, as documented.
- `plan doctor` now detects drift on every PLAN → INDEX projection
  field: Current Phase, Current Focus, Next Action, Current Blockers
  (T-213). All repaired mechanically by `plan sync` (T-214).
- Canonical empty-release INDEX representation locked by test (T-215).
- Public documentation no longer claims filesystem-level atomicity;
  transitions are described as coherent working-set rewrites (T-216).

### Verification (P3)

- New `tests/test_plugin.py` enforces the canonical-source invariant
  (manifest, marketplace pointer, byte-identical payload, drift check).
- Close edge-case tests (missing PLAN, zero phases, force bypass).
- Doctor drift tests for all four fields plus sync-repairs-all.
- Official validation: `claude plugin validate ./plugins/planscope`
  and `claude plugin validate .` both pass (Claude Code CLI v2.1.283).
- Fresh marketplace install verified in an isolated config dir +
  temp project: marketplace add → plugin install → skill discovery →
  init → open → status → doctor.
- Full regression: 76 passed, 1 skipped; repo doctor 0/0.

## Decisions

- D-001: The plugin payload is a generated artifact, never edited by
  hand; only `plugin.json` inside `plugins/planscope/` is
  hand-maintained. Keeps one canonical skill source.
- D-002: Historical `atomic` wording inside `.planning/archive/` is
  left untouched (archive boundary); the term is corrected only in
  current public docs and code comments.

## Known notes

- After `plan open`, doctor warns that INDEX current state is stale
  until the first `plan sync` — pre-existing, by design (PLAN is the
  source; INDEX is its projection).
