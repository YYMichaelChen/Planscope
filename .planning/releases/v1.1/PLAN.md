# Release v1.1

## Objective

Publish Planscope v1.0 publicly and verify the skill end-to-end in all
four supported tools from a fresh GitHub install.

## Acceptance Criteria

- Repository pushed to GitHub with a public v1.0 tag.
- Claude Code can install the skill from GitHub (plugin marketplace manifest).
- Skill discovery and `plan.py` round-trip verified manually in Claude Code,
  Codex CLI, opencode and Kimi Code.

## Status

in_progress

## Current

Phase:
P1

Task:
T-002

## Phases

### P1 GitHub Release

Status:
in_progress

Tasks:

- [x] T-001 Push repository to GitHub and tag v1.0
- [ ] T-002 Add .claude-plugin/marketplace.json for Claude Code GitHub install

### P2 Four-Tool Verification

Status:
pending

Tasks:

- [ ] T-003 Verify install + skill discovery + plan.py round-trip in Claude Code
- [ ] T-004 Verify in Codex CLI
- [ ] T-005 Verify in opencode
- [ ] T-006 Verify in Kimi Code (/skill:planscope + implicit trigger)

## Blockers

None.

## Next Action

T-002 Add .claude-plugin/marketplace.json for Claude Code GitHub install.
