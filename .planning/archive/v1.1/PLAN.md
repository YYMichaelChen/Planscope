# Release v1.1

## Objective

Publish Planscope v1.0 publicly and verify the skill end-to-end in all
four supported tools from a fresh GitHub install.

## Acceptance Criteria

- Repository pushed to GitHub with a public v1.0 tag. (Done — v1.0
  tagged and GitHub Release published 2026-09-26.)
- Claude Code can install the skill from GitHub (plugin marketplace
  manifest). (Done — `.claude-plugin/marketplace.json` added; completed
  under v1.1.0 task T-302.)
- Skill discovery and `plan.py` round-trip verified manually in Claude
  Code, Codex CLI, opencode and Kimi Code. (Claude Code verified at
  v1.0; remaining three tools transferred to v1.1.0 P4, tasks
  T-404..T-406.)

## Status

complete

## Current

Phase:
P2

Task:
T-006 (transferred to v1.1.0)

## Phases

### P1 GitHub Release

Status:
complete

Tasks:

- [x] T-001 Push repository to GitHub and tag v1.0
- [x] T-002 Add .claude-plugin/marketplace.json for Claude Code GitHub
  install — completed under v1.1.0 task T-302

### P2 Four-Tool Verification

Status:
complete

Tasks:

- [x] T-003 Verify install + skill discovery + plan.py round-trip in
  Claude Code (verified at v1.0 publish)
- [x] T-004 T-005 T-006 — remaining Codex CLI / opencode / Kimi Code
  verification transferred to release v1.1.0 (tasks T-404..T-406) and
  tracked there

## Blockers

None.

## Next Action

None — release closed; continue in release v1.1.0.
