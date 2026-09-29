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

## Project Authority Boundary

Planscope is not the authoritative project documentation system.

`.planning/` owns:

- active release execution state;
- current task/phase/blocker/next-action state;
- temporary recovery context;
- release-scoped findings that cannot yet be promoted;
- compact cross-release context that has no better authoritative home.

Tracked repository artifacts should own durable project truth when
available, including product requirements, architecture contracts,
public procedures, schemas, compatibility policy, release evidence,
and source-controlled facts.

Do not duplicate an authoritative project rule into `.planning/`
merely for convenience. Route to the authoritative source instead.

When a planning finding becomes durable, promote it to the best
authoritative project destination. Use `PROJECT.md` only when no
better recoverable source exists.

## Recoverability Rule

Before writing durable information into `.planning/`, ask:

1. Is this information already recoverable from source, tests,
   configuration, tracked documentation, Git history, or another
   authoritative artifact?
2. If yes, store only a route/reference when planning context needs it.
3. If no, keep it in the narrowest planning scope that can preserve it.
4. When an authoritative destination later exists, promote it there
   and remove the duplicate planning copy.

This rule applies to `PROJECT.md`, `PLAN.md` and `KNOWLEDGE.md` alike,
not only to knowledge findings.

## Helper CLI

A lightweight helper ships at `scripts/plan.py` next to this SKILL.md.
Run it with Python 3 (standard library only):

```
python <directory containing this SKILL.md>/scripts/plan.py <command>
```

Commands:

- `init` — create `.planning/` with INDEX, PROJECT, ROADMAP
- `status` — show active release, current phase/task, file budgets
- `open <version>` — start a new release (e.g. `open v0.8`, `open v1.1.0`);
  refuses while another release is active
- `sync` — project PLAN current state into INDEX (mechanical)
- `compact` — mechanical hygiene: budget checks, illegal-file
  detection, INDEX pointer validation, LOG rotation
- `close <version>` — final mechanical commit of a finished release:
  verifies phases, PLAN status, SUMMARY and the closeout checklist,
  then archives it and clears the active working set
- `doctor` — validate planning invariants, non-zero exit on failure

The CLI performs mechanical operations only. Semantic work —
summarizing phases, merging findings, promoting knowledge — is your
job, guided by the rules below.

## Single Active Release

Planscope supports at most one active release. Close the current
release before opening another. If `open` refuses, close or resolve
the existing release first — never work around it by hand-editing
INDEX release pointers.

## PLAN Authority

PLAN is the canonical source for the active release's current phase,
task, blockers and next action. INDEX is a compact routing projection
and should be kept synchronized.

After manually editing PLAN current state, run `sync` to project the
changes into INDEX mechanically. Do not hand-edit INDEX current-state
fields when `sync` can derive them.

## Context Routing

Do not read all planning files automatically.

Before loading planning context, classify the current task.

### Search before full read

Prefer search and bounded section reads over full planning-file reads.

A planning file is a retrieval source, not a single indivisible
context unit:

- For PLAN, prioritize `Current`, the active phase, `Blockers` and
  `Next Action`. Do not automatically read every completed phase.
  Read the full PLAN mainly for planning, replanning, release review
  or recovery.
- For KNOWLEDGE, search first by Task ID, Phase ID, Finding ID,
  Decision ID or keywords, then read the relevant sections. Do not
  read the entire KNOWLEDGE file by default.
- For PROJECT, read only when architecture, stable constraints,
  cross-release decisions or project conventions matter.
- Never automatically load archive content.

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

INDEX may also carry one or two compact project-authority pointers in
the Context Map when the active release directly depends on them. Do
not turn INDEX into a documentation table of contents — the full
authority map belongs in PROJECT.md or the project's own tracked
documentation.

### PROJECT.md

A compact cross-release routing and residual-context document — not
the default destination for all durable knowledge.

Use for:

- project authority routing (`## Authority Map`);
- compact cross-release constraints that are not reliably encoded
  elsewhere;
- durable decisions whose authoritative project destination does not
  yet exist;
- short context needed to interpret multiple releases.

Prefer links or repository-relative paths to authoritative tracked
artifacts.

Do not duplicate:

- product specifications;
- architecture documents;
- public runbooks;
- schemas/contracts;
- release evidence;
- test manuals;
- facts already directly recoverable from source/configuration.

Do not store temporary task or release information here.

### ROADMAP.md

High-level future direction only.

Do not put implementation details or task checklists here.

### PLAN.md

The active release plan.

It should mostly describe unfinished work.

Completed phases should be compressed into short summaries.

PLAN describes intended release work and acceptance criteria. When a
task changes a durable project rule, PLAN should name the
authoritative artifact that must be updated. PLAN must not become the
final specification for that rule unless the consuming project
explicitly defines it as such.

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

Each durable finding should also name a promotion target — the
authoritative project destination it moves to once that destination
exists (`pending` until known) — and a status (`temporary` /
`promoted`).

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
- run `sync` to mirror PLAN current state into INDEX
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
- promote durable knowledge to its best authoritative destination
  when appropriate
- rotate old LOG content
- refresh INDEX

Preserve information that would affect future decisions.

## Release Closing

Complete semantic release work BEFORE running the mechanical close
command. `close` is the final commit of a release, not a cleanup step.

Semantic close (your job), in order:

1. verify the release acceptance criteria
2. create SUMMARY.md
3. review release findings and decisions
4. promote each durable item to its best authoritative project
   destination (product specification, architecture document,
   runbook, contract/schema, release-evidence location, or the
   source itself)
5. use PROJECT.md only for cross-release context with no better
   recoverable home
6. remove or compress planning copies that would compete with the
   promoted authority
7. update ROADMAP.md
8. set PLAN `## Status` to `complete`
9. complete every item of the PLAN `## Closeout` checklist

Mechanical close (CLI):

10. run `plan.py close <version>` — it verifies that PLAN.md exists
    and defines at least one phase, that every phase is `complete`,
    that PLAN `## Status` is `complete`, that SUMMARY.md exists, and
    that the `## Closeout` checklist exists with all required items
    checked; then it archives the release and clears the active
    working set. `--force` bypasses these gates for exceptional
    recovery only.

## Archive Boundary

After close, archived content is historical and must not remain part
of the active working context. Do not reopen archive to perform normal
promotion or planning work — that work belongs to semantic close.

## Recovery

After context loss or a new session:

1. read INDEX.md
2. read the active PLAN.md current state (`Current`, active phase,
   `Blockers`, `Next Action`)
3. inspect Git state if useful
4. search relevant KNOWLEDGE.md sections
5. read recent LOG.md only if execution continuity requires it
6. continue from the recorded next action

Recovery must not automatically expand into PROJECT.md, ROADMAP.md,
full KNOWLEDGE.md or archive — load those only when the task requires
them. Do not recover by loading all planning history.

## Core Principle

Persistent memory is not the same as active context.

Store information durably, but return only relevant information to the
working context.
