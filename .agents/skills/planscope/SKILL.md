---
name: planscope
description: >
  Scoped file-based planning for long-running software projects.
  Maintains a small active working set through INDEX routing,
  release-scoped plans, selective knowledge loading, rolling logs,
  compaction, and release archiving. Use for multi-step development,
  ongoing projects, release planning, complex debugging, or work that
  needs durable context across sessions. Small local changes should
  bypass planning whenever possible.
license: MIT
compatibility: claude-code, codex, opencode, kimi-code
metadata:
  homepage: https://github.com/YYMichaelChen/Planscope
allowed-tools: Read Write Edit Bash Glob Grep
---

# Planscope — Scoped Planning with Files

Use persistent project files as durable memory without loading the
entire project history into context.

The primary rule is:

> Keep the active working set small.

## Planning Root

All planning state lives under:

`.planning/`

Only the following planning filenames are allowed:

- `INDEX.md`
- `PROJECT.md`
- `ROADMAP.md`
- `PLAN.md`
- `KNOWLEDGE.md`
- `LOG.md`
- `SUMMARY.md`

Do not invent additional planning filenames.

Templates for every planning file ship in the `templates/` directory
next to this SKILL.md. Copy them instead of improvising new layouts.

## Helper CLI

A lightweight helper ships at `scripts/plan.py` next to this SKILL.md.
Run it with Python 3 (standard library only):

```
python <directory containing this SKILL.md>/scripts/plan.py <command>
```

Commands:

- `init` — create `.planning/` with INDEX, PROJECT, ROADMAP
- `status` — show active release, current phase/task, file budgets
- `open <version>` — start a new release (e.g. `open v0.8`)
- `compact` — mechanical hygiene: budget checks, illegal-file
  detection, INDEX pointer validation, LOG rotation
- `close <version>` — archive a finished release, update INDEX
- `doctor` — validate planning structure, non-zero exit on failure

The CLI performs mechanical operations only. Semantic work —
summarizing phases, merging findings, promoting knowledge — is your
job, guided by the rules below.

## Context Routing

Do not read all planning files automatically.

Before loading planning context, classify the current task.

### Micro changes

Examples:

- typo fixes
- small CSS changes
- simple renames
- obvious local configuration edits

Planning may be skipped entirely.

If project context might matter, read only `.planning/INDEX.md`.

Do not update planning files unless the change affects the current
release state, project constraints, or future work.

### Local changes

Read:

1. `.planning/INDEX.md`
2. the relevant section of the active `PLAN.md`

Read `KNOWLEDGE.md` only when existing release knowledge is relevant.

### Feature or complex development

Read:

1. `.planning/INDEX.md`
2. active release `PLAN.md`
3. relevant sections of active release `KNOWLEDGE.md`

Read `PROJECT.md` only when architecture or stable project constraints matter.

### Planning or recovery

Read:

1. `INDEX.md`
2. active `PLAN.md`
3. relevant `KNOWLEDGE.md`
4. recent `LOG.md` content when execution continuity matters

Inspect Git state when useful.

Never automatically read archive content.

## File Responsibilities

### INDEX.md

The small routing document.

It contains:

- active release
- current focus
- current phase
- next action
- blockers
- context map
- critical constraints

Keep it concise.

### PROJECT.md

Stable cross-release project knowledge.

Use for:

- architecture
- long-term constraints
- stable conventions
- durable domain knowledge
- long-term decisions

Do not store temporary task or release information here.

### ROADMAP.md

High-level future direction only.

Do not put implementation details or task checklists here.

### PLAN.md

The active release plan.

It should mostly describe unfinished work.

Completed phases should be compressed into short summaries.

### KNOWLEDGE.md

Store information only when future work may need it and it cannot be
reliably recovered from ordinary source files.

Before writing a finding, ask:

"If this context disappeared, could a future agent make a wrong
decision because it did not know this?"

If no, do not record it.

Each important finding should use a stable ID:

`F-001`, `F-002`, ...

Allowed scopes:

- task
- release
- project

### LOG.md

A rolling execution log.

Keep only recent state, important validation, blockers, and temporary
context needed for recovery.

Do not duplicate Git history.

### SUMMARY.md

Created when a release closes.

It provides a compact historical overview so old PLAN, KNOWLEDGE, and
LOG files normally do not need to be reopened.

## IDs

Use stable IDs:

- Phase: `P1`, `P2`, ...
- Task: `T-001`, `T-002`, ...
- Finding: `F-001`, `F-002`, ...
- Decision: `D-001`, `D-002`, ...

Do not create custom ID formats.

## Update Rules

After meaningful progress:

- update PLAN when task or phase state changes
- update INDEX when current focus or next action changes
- update KNOWLEDGE only for reusable knowledge
- update LOG only when recent execution context is worth preserving

Do not write planning files merely because a tool was used.

## Completed Work

Plans are future-oriented.

When a phase completes, replace verbose completed checklists with a
short summary and references to important findings or decisions.

Do not allow completed work to dominate the active PLAN.

## Compaction

Compact planning files when they become large or repetitive.
`plan.py compact` reports what needs attention.

During compaction:

- summarize completed PLAN phases
- merge duplicate findings
- remove obsolete task-scoped knowledge
- promote durable project knowledge when appropriate
- rotate old LOG content
- refresh INDEX

Preserve information that would affect future decisions.

## Release Closing

When the active release is complete:

1. verify its acceptance criteria
2. create SUMMARY.md
3. review KNOWLEDGE.md
4. promote durable project-scoped knowledge into PROJECT.md
5. archive release planning files (`plan.py close <version>`)
6. update ROADMAP.md
7. update INDEX.md

Archived releases must not remain part of the default working context.

## Recovery

After context loss or a new session:

1. read INDEX.md
2. read the active PLAN.md
3. inspect Git state if useful
4. search relevant KNOWLEDGE.md
5. read recent LOG.md only if necessary
6. continue from the recorded next action

Do not recover by loading all planning history.

## Core Principle

Persistent memory is not the same as active context.

Store information durably, but return only relevant information to the
working context.
