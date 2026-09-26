# Release v1.1.1

## Objective

Fix Claude Code marketplace packaging and close the remaining
lifecycle-validation gaps in Planscope v1.1.x without introducing
new architecture.

## Acceptance Criteria

- Claude marketplace points to a valid plugin root.
- Claude plugin metadata includes a valid plugin.json.
- Plugin-distributed Planscope skill is mechanically generated from
  the canonical `.agents/skills/planscope/` source.
- Distribution drift can be detected automatically.
- Normal release close rejects missing PLAN.md.
- Normal release close rejects a PLAN with zero phases.
- Doctor detects drift in all PLAN → INDEX projection fields.
- `plan sync` repairs all supported INDEX projection drift.
- Public documentation no longer claims filesystem-level atomicity.
- Existing project installation remains backward compatible.
- Full regression test suite passes.
- Claude marketplace installation is verified in a clean environment.

## Status

complete

## Current

Phase:
P3

Task:
T-316 complete — full regression suite passed (76 passed, 1 skipped),
doctor 0 failures / 0 warnings, plugin payload in sync.

## Phases

### P1 Claude Distribution Fix

Status:
complete

Tasks:

- [x] T-111 Introduce valid Claude plugin root
- [x] T-112 Add plugin.json
- [x] T-113 Generate plugin skill from canonical source
- [x] T-114 Fix marketplace source
- [x] T-115 Add distribution drift check
- [x] T-116 Preserve existing direct installation behavior

### P2 Lifecycle Validation Hardening

Status:
complete

Tasks:

- [x] T-211 Require PLAN.md on normal close
- [x] T-212 Require at least one Phase on normal close
- [x] T-213 Validate full INDEX projection drift
- [x] T-214 Verify full plan sync projection
- [x] T-215 Normalize empty-release INDEX state
- [x] T-216 Replace atomic terminology

### P3 Verification and Release

Status:
complete

Tasks:

- [x] T-311 Add plugin packaging tests
- [x] T-312 Add close edge-case tests
- [x] T-313 Add projection-drift tests
- [x] T-314 Run official Claude plugin validation
- [x] T-315 Verify marketplace fresh install
- [x] T-316 Run full regression suite
- [x] T-317 Semantic release close
- [x] T-318 Publish v1.1.1

## Blockers

None.

## Next Action

None.
