# Planscope v1.1.1 Development Plan

**Version:** v1.1.1
**Codename:** Distribution Fix
**Status:** Development Specification
**Release Type:** Patch
**Project:** Planscope

> Persistent memory. Small working context.

# 1. Overview

Planscope v1.1.1 is a focused patch release.

It does not introduce new planning concepts, new runtime architecture, or new user-facing workflows.

Its purpose is to close the remaining correctness and distribution gaps discovered after v1.1.0:

1. Claude Code marketplace packaging is not yet structured as a canonical Claude plugin.
2. `plan close` should independently reject missing or structurally empty PLAN state.
3. `plan doctor` should validate the full PLAN → INDEX projection rather than only part of it.
4. Documentation should avoid claiming filesystem-level atomicity where the implementation only guarantees coherent lifecycle rewrites.

The release objective is:

> **Make v1.1.x distribution and lifecycle validation fully consistent with Planscope's documented guarantees without expanding the architecture.**

# 2. Release Principles

v1.1.1 follows four constraints.

## 2.1 Patch only

Every change must fit one of:

```
bug fix
validation fix
distribution fix
documentation precision
test coverage
```

Do not add new product capabilities.

## 2.2 One canonical skill source

The canonical Planscope skill remains:

```
.agents/skills/planscope/
```

No manually maintained second SKILL implementation is permitted.

Any Claude-specific packaging must be generated or mechanically synchronized from the canonical source.

## 2.3 No new planning state

Do not introduce:

```
state.json
database
event log
cache state
manifest-backed plan state
```

Markdown remains the canonical planning state.

## 2.4 No architecture expansion

Explicitly out of scope:

```
hooks
semantic search
multi-agent coordination
automatic summarization
background services
task DAGs
vector storage
LLM-powered compaction
```

# 3. Scope

v1.1.1 contains three implementation phases:

```
P1 — Claude Distribution Fix
P2 — Lifecycle Validation Hardening
P3 — Verification and Release
```

# 4. P1 — Claude Distribution Fix

## T-111 — Introduce a Valid Claude Plugin Root

### Problem

The current marketplace entry points directly to:

```
.agents/skills/planscope/
```

That directory is the canonical skill directory.

It is not a conventional Claude Code plugin root.

A Claude plugin should have its own plugin-level structure and manifest while exposing Planscope as a skill component.

### Required structure

Add a Claude distribution wrapper:

```
plugins/
└── planscope/
    ├── .claude-plugin/
    │   └── plugin.json
    │
    └── skills/
        └── planscope/
            ├── SKILL.md
            ├── templates/
            │   ├── INDEX.md
            │   ├── PROJECT.md
            │   ├── ROADMAP.md
            │   ├── PLAN.md
            │   ├── KNOWLEDGE.md
            │   ├── LOG.md
            │   └── SUMMARY.md
            │
            └── scripts/
                ├── plan.py
                └── spwf/
```

This directory is a **distribution artifact**, not a second source of truth.

# 5. T-112 — Add Claude Plugin Manifest

Create:

```
plugins/planscope/.claude-plugin/plugin.json
```

Minimum fields:

```
{
  "name": "planscope",
  "version": "1.1.1",
  "description": "Scoped file-based planning for long-running software projects.",
  "author": {
    "name": "YYMichaelChen"
  },
  "homepage": "https://github.com/YYMichaelChen/Planscope",
  "repository": "https://github.com/YYMichaelChen/Planscope",
  "license": "MIT"
}
```

Keep the manifest intentionally minimal.

Do not duplicate operational Planscope configuration here.

# 6. T-113 — Generate Claude Plugin Skill from Canonical Source

### Principle

The following relationship must hold:

```
.agents/skills/planscope/
        │
        │ canonical
        ▼
packaging/sync step
        │
        ▼
plugins/planscope/skills/planscope/
```

Never:

```
canonical skill
+
separately edited Claude skill
```

### Required implementation

Add a mechanical helper, for example:

```
python install.py --build-plugin
```

or:

```
python scripts/build_plugin.py
```

Preferred approach:

extend the existing installer/build tooling rather than introducing a large new subsystem.

The command must:

1. create the Claude plugin directory if necessary;
2. copy the canonical skill tree;
3. exclude transient files such as:

```
__pycache__
*.pyc
```

1. preserve UTF-8 content;
2. produce deterministic output.

### Acceptance criteria

After build:

```
plugins/planscope/skills/planscope/SKILL.md
```

must be byte-equivalent to:

```
.agents/skills/planscope/SKILL.md
```

The same applies to templates and runtime scripts.

# 7. T-114 — Fix Marketplace Source

Update:

```
.claude-plugin/marketplace.json
```

so its plugin source points to:

```
./plugins/planscope
```

not:

```
./.agents/skills/planscope
```

Expected conceptual structure:

```
{
  "name": "planscope",
  "owner": {
    "name": "YYMichaelChen"
  },
  "plugins": [
    {
      "name": "planscope",
      "source": "./plugins/planscope",
      "description": "Scoped file-based planning for long-running software projects."
    }
  ]
}
```

Do not duplicate version or extensive metadata unless required.

The plugin-level manifest owns plugin metadata.

# 8. T-115 — Add Distribution Drift Check

Because the Claude plugin skill is generated from the canonical source, drift must be detectable.

Add a validation command or test such as:

```
python install.py --check-plugin
```

or equivalent test logic.

It should compare:

```
.agents/skills/planscope/
```

against:

```
plugins/planscope/skills/planscope/
```

Ignoring only explicitly allowed generated artifacts.

Expected output:

```
PLUGIN IN SYNC
```

or:

```
PLUGIN DRIFTED
```

A drifted distribution artifact must fail release validation.

# 9. T-116 — Preserve Existing Project Installation

The existing:

```
python install.py --project <path>
```

behavior should remain unchanged from the user's perspective.

It should continue to install:

```
<project>/.agents/skills/planscope/
<project>/.claude/skills/planscope/
```

The new `plugins/planscope/` wrapper exists specifically for Claude marketplace/plugin distribution.

Do not force ordinary project installs through the plugin packaging format.

This distinction should remain explicit:

```
.agents/skills/
= direct skill distribution

.claude/skills/
= direct Claude skill installation

plugins/planscope/
= Claude plugin / marketplace distribution
```

# 10. P2 — Lifecycle Validation Hardening

## T-211 — Close Must Require PLAN.md

### Problem

Normal `plan close` should be independently safe.

It must not rely on the user having run:

```
plan doctor
```

first.

If an active release directory exists but:

```
PLAN.md
```

is missing, normal close must fail.

### Required behavior

Before parsing:

```
if not plan_path.is_file():
    if not args.force:
        raise PlanError(...)
```

Suggested message:

```
error: PLAN.md missing for v1.1.1.
A release cannot be closed without its canonical plan.
```

### Acceptance criteria

This state:

```
releases/v1.1.1/
├── KNOWLEDGE.md
├── LOG.md
└── SUMMARY.md
```

must never pass normal close.

# 11. T-212 — Close Must Require at Least One Phase

### Problem

The positive completion rule:

```
all(phase.status == "complete" for phase in phases)
```

is vacuously true when:

```
phases == []
```

A PLAN with zero phases should not normally be closeable.

### Required behavior

Normal close requires:

```
len(plan.phases) >= 1
```

Suggested error:

```
error: PLAN.md contains no phases.
Define and complete at least one release phase before closing.
```

### Exception

`--force` may bypass this validation, consistent with existing force semantics.

### Acceptance criteria

This must fail:

```
## Status

complete

## Phases

## Next Action

None.
```

even when SUMMARY exists.

# 12. T-213 — Validate Full INDEX Projection Drift

### Current model

Planscope now defines:

```
PLAN
= canonical active release state

INDEX
= routing projection
```

Therefore projection validation should cover every mechanically synchronized field.

### Fields

Compare:

```
PLAN Current Phase
↔ INDEX Current Phase

PLAN Current Task
↔ INDEX Current Focus

PLAN Next Action
↔ INDEX Next Action

PLAN Blockers
↔ INDEX Current Blockers
```

### Doctor behavior

If one or more fields drift:

```
WARN
```

Suggested output:

```
WARN    INDEX Current Focus, Current Blockers are stale.
        Run: plan sync
```

The condition remains recoverable because:

```
plan sync
```

can repair it mechanically.

### Acceptance criteria

Doctor must detect independently:

- task drift;
- phase drift;
- next-action drift;
- blocker drift.

# 13. T-214 — Verify `plan sync` Full Projection

Ensure `plan sync` continues to synchronize exactly:

```
Current Task
Current Phase
Next Action
Blockers
```

into INDEX.

It must not synchronize:

```
release objective
acceptance criteria
complete phase summaries
historical LOG state
KNOWLEDGE
```

INDEX must remain a small router.

# 14. T-215 — Clarify Empty Release State

When no release is active, INDEX should use one consistent representation.

Recommended canonical values:

```
## Active Release

none

Path:

[none]

## Current Focus

None.

## Current Phase

None.

## Next Action

Open the next release or select new work.

## Current Blockers

None.
```

Context Map:

```
Active Plan:
[none]

Active Knowledge:
[none]

Recent Log:
[none]
```

Do not mix:

```
empty string
none
None
N/A
not active
```

across lifecycle operations.

The existing representation may be retained if consistent.

# 15. T-216 — Replace "Atomic" Terminology

### Problem

Current release transitions are coherent and deterministic at the application level, but they are not filesystem transactions.

For example:

```
create release directory
write PLAN
write KNOWLEDGE
write LOG
rewrite INDEX
```

can theoretically be interrupted between operations.

Therefore the term:

```
atomic
```

overstates the implementation guarantee.

### Required documentation update

Replace user-facing phrases such as:

```
atomic release activation
atomic lifecycle
atomic clearing
```

with:

```
coherent release activation
deterministic lifecycle transition
complete working-set rewrite
coherent active-context clearing
```

Internal task identifiers may remain unchanged if desired, but public docs should use precise language.

### Do not

Do not implement:

```
transaction journals
filesystem locking
rollback engine
event sourcing
```

solely to preserve the word "atomic."

That complexity is explicitly out of scope.

# 16. P3 — Verification and Release

## T-311 — Add Plugin Packaging Tests

Minimum tests:

```
test_plugin_manifest_exists
test_plugin_manifest_name
test_plugin_manifest_version
test_marketplace_points_to_plugin_root
test_plugin_skill_exists
test_plugin_skill_matches_canonical
test_plugin_templates_match_canonical
test_plugin_scripts_match_canonical
```

# 17. T-312 — Add Close Edge-Case Tests

Add:

```
test_close_rejects_missing_plan
test_close_rejects_zero_phases
test_force_close_can_bypass_missing_plan
test_force_close_can_bypass_zero_phases
```

Force behavior should be explicitly documented.

# 18. T-313 — Expand Doctor Drift Tests

Add:

```
test_doctor_warns_task_drift
test_doctor_warns_phase_drift
test_doctor_warns_next_action_drift
test_doctor_warns_blocker_drift
test_sync_repairs_all_projection_drift
```

# 19. T-314 — Validate Claude Plugin

Where Claude Code CLI supports plugin validation, perform the official validation against:

```
plugins/planscope/
```

and/or the marketplace.

Record the exact command in:

```
docs/compatibility.md
```

Do not claim marketplace compatibility based only on JSON presence.

The acceptance condition is:

> The plugin structure is accepted by Claude Code's actual plugin validation or installation path.

# 20. T-315 — Fresh Marketplace Install Test

Use a temporary project that does not already contain Planscope.

Verify:

```
marketplace registration
↓
plugin install
↓
Planscope skill discovery
↓
skill invocation
↓
plan init
↓
plan open
↓
plan status
```

The test should prove the marketplace route is distinct from:

```
install.py --project
```

and works independently.

# 21. T-316 — Run Complete Regression Suite

Before release:

```
python -m pytest tests/ --basetemp=.pytest-tmp
```

Expected:

```
0 failures
```

Then:

```
python .agents/skills/planscope/scripts/plan.py doctor
```

Expected:

```
0 failures
0 warnings
```

unless a warning is explicitly accepted and documented.

# 22. Updated v1.1.1 Release PLAN

Recommended `.planning/releases/v1.1.1/PLAN.md`:

```
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

in_progress

## Current

Phase:
P1

Task:
T-111

## Phases

### P1 Claude Distribution Fix

Status:
in_progress

Tasks:

- [ ] T-111 Introduce valid Claude plugin root
- [ ] T-112 Add plugin.json
- [ ] T-113 Generate plugin skill from canonical source
- [ ] T-114 Fix marketplace source
- [ ] T-115 Add distribution drift check
- [ ] T-116 Preserve existing direct installation behavior

### P2 Lifecycle Validation Hardening

Status:
pending

Tasks:

- [ ] T-211 Require PLAN.md on normal close
- [ ] T-212 Require at least one Phase on normal close
- [ ] T-213 Validate full INDEX projection drift
- [ ] T-214 Verify full plan sync projection
- [ ] T-215 Normalize empty-release INDEX state
- [ ] T-216 Replace atomic terminology

### P3 Verification and Release

Status:
pending

Tasks:

- [ ] T-311 Add plugin packaging tests
- [ ] T-312 Add close edge-case tests
- [ ] T-313 Add projection-drift tests
- [ ] T-314 Run official Claude plugin validation
- [ ] T-315 Verify marketplace fresh install
- [ ] T-316 Run full regression suite
- [ ] T-317 Semantic release close
- [ ] T-318 Publish v1.1.1

## Blockers

None.

## Next Action

T-111 Create a proper Claude plugin distribution root under
`plugins/planscope/`.
```

# 23. Recommended Implementation Order

Implement in this order:

```
T-111 Plugin root
   ↓
T-112 plugin.json
   ↓
T-113 packaging sync
   ↓
T-114 marketplace source
   ↓
T-115 drift detection
   ↓
T-311 packaging tests
   ↓
T-211 missing PLAN gate
   ↓
T-212 zero-phase gate
   ↓
T-213 doctor projection validation
   ↓
T-214 sync validation
   ↓
T-215 empty-state cleanup
   ↓
T-216 terminology cleanup
   ↓
T-312 / T-313 regression tests
   ↓
T-314 Claude validation
   ↓
T-315 fresh install
   ↓
T-316 full regression
```

Distribution should be fixed before the release is advertised.

# 24. Packaging Design

The intended repository architecture after v1.1.1:

```
Planscope/
│
├── .agents/
│   └── skills/
│       └── planscope/
│           ├── SKILL.md
│           ├── templates/
│           └── scripts/
│
├── plugins/
│   └── planscope/
│       ├── .claude-plugin/
│       │   └── plugin.json
│       └── skills/
│           └── planscope/
│               ├── SKILL.md
│               ├── templates/
│               └── scripts/
│
├── .claude-plugin/
│   └── marketplace.json
│
├── install.py
├── docs/
├── tests/
└── .planning/
```

Ownership:

```
.agents/skills/planscope/
= canonical source

plugins/planscope/
= generated Claude distribution package

.claude-plugin/marketplace.json
= marketplace index
```

This distinction must be explicit in README.

# 25. Canonical Source Invariant

The strongest new invariant in v1.1.1 is:

```
canonical source
==
generated plugin skill
```

For every file that belongs to the skill payload.

In conceptual terms:

```
SHA(canonical payload)
==
SHA(plugin payload)
```

A release must not proceed if this invariant fails.

# 26. README Changes

Update Repository Layout to explain:

```
.agents/skills/planscope/
canonical source

plugins/planscope/
generated Claude plugin package

.claude-plugin/marketplace.json
Claude marketplace index
```

Update Claude installation instructions to distinguish:

## Direct project install

```
python install.py --project /path/to/project
```

## Marketplace/plugin install

Document the tested Claude Code marketplace flow after T-315 succeeds.

Do not publish unverified marketplace commands before they are actually validated.

# 27. Compatibility Documentation

Update:

```
docs/compatibility.md
```

with two separate Claude Code paths:

### Direct skill path

```
.claude/skills/planscope/
```

### Plugin path

```
plugin root
└── skills/planscope/SKILL.md
```

State clearly that these are two distribution mechanisms for the same canonical Planscope skill.

# 28. Definition of Done

v1.1.1 is complete when all of the following are true:

### Distribution

```
marketplace.json
→ valid Claude plugin root
→ valid plugin manifest
→ Planscope skill discovered
```

### Canonical integrity

```
plugin skill payload
==
canonical skill payload
```

### Lifecycle safety

Normal `close` cannot succeed without:

```
PLAN.md
>= 1 phase
all phases complete
release Status complete
SUMMARY.md
```

### Projection integrity

Doctor can detect drift in:

```
Task
Phase
Next Action
Blockers
```

and:

```
plan sync
```

can repair all of it.

### Documentation accuracy

Planscope no longer claims transaction-level atomicity.

### Regression

All automated tests pass.

### Real verification

Claude marketplace install works in a clean test project.

# 29. Release Checklist

Before creating the v1.1.1 tag:

- Plugin root created
- `plugin.json` created
- Plugin payload generated from canonical skill
- Marketplace source corrected
- Distribution drift check added
- Missing PLAN close gate added
- Zero-phase close gate added
- Full projection drift validation added
- `plan sync` regression verified
- Atomic terminology removed from public docs
- Plugin packaging tests pass
- Lifecycle edge-case tests pass
- Doctor drift tests pass
- Official Claude plugin validation passes
- Clean marketplace install passes
- Full pytest suite passes
- `plan doctor` passes
- README updated
- compatibility docs updated
- SUMMARY generated
- project knowledge promotion reviewed
- ROADMAP updated
- PLAN marked complete
- `plan close v1.1.1`
- tag `v1.1.1`
- GitHub Release published

# 30. Release Notes Draft

## Planscope v1.1.1

Planscope v1.1.1 is a focused distribution and validation patch for the v1.1 hardening release.

### Fixed

- Correct Claude Code marketplace packaging with a proper plugin root and manifest.
- Marketplace distribution now packages the canonical Planscope skill without creating a second maintained implementation.
- Added distribution drift detection between the canonical skill and generated Claude plugin payload.
- `plan close` now rejects releases with a missing `PLAN.md`.
- `plan close` now rejects structurally empty plans with zero phases.
- `plan doctor` now detects Task and Blocker drift in addition to Phase and Next Action drift.
- Documentation now describes release transitions as coherent working-set rewrites rather than filesystem-atomic transactions.

### Unchanged

Planscope remains:

- Markdown-first;
- standard-library-only;
- single-active-release;
- runtime-free;
- database-free;
- hook-free;
- intentionally small.

> **Persistent memory. Small working context.**

# 31. Post-v1.1.1 Rule

After v1.1.1 ships:

> **Do not immediately start another feature release.**

Planscope should enter an observation period.

Use it in real projects and collect evidence about:

```
context size
archive reopen frequency
manual compaction frequency
sync frequency
document growth
recovery friction
```

The next product change should be driven by repeated real-world friction, not by architecture speculation.

# 32. Final Release Goal

The release succeeds when Planscope can truthfully make both claims:

```
One canonical skill source.
```

and:

```
Every supported distribution path delivers that same skill correctly.
```

At that point, the v1.x foundation should be considered stable.