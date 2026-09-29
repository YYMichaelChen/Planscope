# Release v1.1.2

## Objective

Governance boundary hardening: make the boundary between `.planning/`
execution context and authoritative repository knowledge explicit and
enforceable, per docs/v1.1.2-governance-boundary-hardening.md.

## Acceptance Criteria

- SKILL.md explicitly states Planscope is not the authoritative project
  documentation system; the recoverability rule applies across planning
  files
- PROJECT.md is routing-first (Authority Map), no longer the default
  sink for durable knowledge
- Semantic close promotes durable items to their best authoritative
  destination, not automatically to PROJECT.md
- PLAN.md template includes an authority-reconciliation closeout
  checklist
- Normal `plan close` refuses an incomplete required closeout;
  `--force` still bypasses
- `plan doctor` detects structurally incomplete closeout state
- Archived releases need no retroactive migration; no repository-specific
  documentation layout is hard-coded
- Full test suite green; plugin payload in sync

## Status

complete

## Current

Phase:
P4

Task:
T-013

## Phases

### P1 Skill semantics

Status:
complete

Tasks:

- [x] T-001 Add Project Authority Boundary + Recoverability Rule core invariants to SKILL.md
- [x] T-002 Redefine PROJECT.md responsibility (routing-first) and update its template
- [x] T-003 Clarify INDEX/PLAN/KNOWLEDGE responsibilities; add promotion target to findings
- [x] T-004 Rewrite semantic close flow; update SUMMARY template guidance

### P2 CLI structural enforcement

Status:
complete

Tasks:

- [x] T-005 Parse PLAN `## Closeout` in core.py (CloseoutItem, unchecked_closeout)
- [x] T-006 `plan close` refuses missing/unchecked closeout without --force
- [x] T-007 `plan doctor` validates closeout schema structurally
- [x] T-008 Tests: closeout gate, doctor closeout checks, template coverage

### P3 Documentation

Status:
complete

Tasks:

- [x] T-009 Move governance spec into docs/v1.1.2-governance-boundary-hardening.md
- [x] T-010 README: authority boundary overview + spec link
- [x] T-011 Bump plugin manifest to 1.1.2; rebuild plugin payload

### P4 Dogfood verification

Status:
complete

Tasks:

- [x] T-012 Migrate .planning/PROJECT.md to Authority Map routing to docs/
- [x] T-013 Semantic close: SUMMARY, ROADMAP, closeout, mechanical close + tag

## Blockers

None.

## Next Action

T-013 complete semantic close and run plan close v1.1.2

## Closeout

- [x] Acceptance criteria verified
- [x] Durable findings classified
- [x] Durable project rules promoted to authoritative repository sources where applicable
- [x] Release evidence written to its durable destination where applicable
- [x] Superseded planning copies removed or compressed
- [x] PROJECT.md contains no avoidable duplicate of an authoritative project rule
- [x] ROADMAP.md updated
- [x] SUMMARY.md created
