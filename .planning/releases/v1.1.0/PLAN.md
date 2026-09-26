# Release v1.1.0

## Objective

Harden Planscope's release lifecycle, active-context consistency,
context routing, and four-tool distribution without expanding the
core architecture.

## Acceptance Criteria

- Opening and closing releases atomically updates active context.
- Exactly zero or one active release is permitted.
- Invalid or incomplete phase state can never pass normal close.
- INDEX and PLAN state can be mechanically synchronized.
- Archived LOG files cannot be overwritten.
- Doctor validates all core planning invariants.
- Normal development prefers section-level retrieval over full-file reads.
- Project installation supports all four target tools from one command.
- Full automated test suite passes.
- Fresh install verified manually in all four supported tools.

## Status

in_progress

## Current

Phase:
P4

Task:
T-403

## Phases

### P1 Core Lifecycle Hardening

Status:
complete

Tasks:

- [x] T-101 Atomic release activation (`activate_release`)
- [x] T-102 Atomic release clearing (`clear_active_release`)
- [x] T-103 Single active release invariant
- [x] T-104 Strict phase status validation
- [x] T-105 Correct release close lifecycle
- [x] T-106 Collision-safe LOG rotation
- [x] T-107 Expand doctor invariants

### P2 Context Efficiency

Status:
complete

Tasks:

- [x] T-201 Add `plan sync`
- [x] T-202 Search-before-full-read routing
- [x] T-203 Clarify recovery protocol
- [x] T-204 Move legacy development specification to `docs/`

### P3 Distribution

Status:
complete

Tasks:

- [x] T-301 Unified project installation (`.agents/` + `.claude/`)
- [x] T-302 Claude distribution manifest (`.claude-plugin/marketplace.json`)
- [x] T-303 Patch version support (vX.Y.Z)

### P4 Verification

Status:
in_progress

Tasks:

- [x] T-401 Add lifecycle regression tests (53 passed, 1 skipped)
- [x] T-402 Run full automated suite
- [x] T-403 Verify Claude Code (this session: full CLI walkthrough + dogfooded
  v1.1 close/open round-trip in-repo)
- [ ] T-404 Verify Codex CLI (fresh install, clean temp repo)
- [ ] T-405 Verify opencode (fresh install, clean temp repo)
- [ ] T-406 Verify Kimi Code (fresh install, clean temp repo)
- [ ] T-407 Dogfood release close and archive (v1.1 closed 2026-09-27 with the
  new CLI; final v1.1.0 close happens at release time)

## Blockers

None.

## Next Action

T-404 Verify v1.1.0 in Codex CLI from a fresh install in a clean
temporary repository: skill discovery, `plan init/open/status/sync/
compact/doctor`, release close round-trip.
