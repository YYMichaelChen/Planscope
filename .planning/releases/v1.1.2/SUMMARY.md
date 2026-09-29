# Release v1.1.2 Summary

**Type:** Patch (behavior-level skill update)
**Spec:** docs/v1.1.2-governance-boundary-hardening.md

## Objective

Make the boundary between `.planning/` execution context and
authoritative repository knowledge explicit and enforceable, without
turning Planscope into a documentation framework or repository
governance engine.

## Delivered

### Skill semantics (P1)

- SKILL.md gained two core rules: **Project Authority Boundary**
  (`.planning/` owns execution context and non-recoverable working
  knowledge; durable project truth belongs to tracked repository
  artifacts) and the **Recoverability Rule** (generalized from
  KNOWLEDGE to PROJECT/PLAN/KNOWLEDGE alike).
- PROJECT.md redefined as a routing-first document with an
  `## Authority Map`; the template no longer invites duplicating
  specs, architecture docs, runbooks or contracts.
- KNOWLEDGE findings gained an explicit promotion target and
  temporary/promoted status; PLAN must name the authoritative artifact
  a task changes; semantic close promotes each durable item to its
  best destination instead of defaulting to PROJECT.md.

### CLI structural enforcement (P2)

- `plan close` now refuses a release whose PLAN `## Closeout`
  checklist is missing or has unchecked/missing required items
  (error lists the items); `--force` still bypasses.
- `plan doctor` validates the closeout schema structurally: warns on
  legacy plans without the section, fails on missing required items,
  and fails when a release marked `complete` has unchecked items.

### Verification

- New tests/test_closeout.py (10 tests); full suite: 86 passed,
  1 skipped; repo doctor 0/0; plugin payload rebuilt and in sync.

## Important Decisions

- Closeout enforcement is mechanical only (checklist presence and
  checkmarks) — the CLI never attempts semantic repository analysis.
- A missing `## Closeout` section warns in doctor instead of failing,
  so pre-v1.1.2 active plans can migrate without a hard breakage.

## Promoted Knowledge

- Governance boundary design -> docs/v1.1.2-governance-boundary-hardening.md
- Authority routing example -> .planning/PROJECT.md (Authority Map)
- CLI behavior -> SKILL.md Release Closing + README authority boundary

## Known Limitations

- The CLI cannot judge whether a checked closeout item is true; it only
  creates the lifecycle checkpoint.
- INDEX.md template unchanged; project-authority pointers in INDEX
  remain an agent-level convention, not a mechanical field.

## Follow-Up Candidates

- Per v1.1.0 spec section 36: real-usage observation before any v2
  architecture (context size, compaction frequency, INDEX drift).
