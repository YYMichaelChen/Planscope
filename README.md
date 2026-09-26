# Planscope

**Scoped Planning with Files** — a lightweight, file-based planning skill for
AI coding agents working on long-running software projects.

> Persistent memory. Small working context.

Planscope keeps project context in layered Markdown files under `.planning/`
and routes each task to only the context it actually needs — instead of
loading the entire planning history into the agent's context window.

```
Persistent Knowledge → Scoped Storage → Context Routing → Small Working Set → Agent
```

See [docs/design.md](docs/design.md) for the full design rationale,
[docs/v1.1.0-specification.md](docs/v1.1.0-specification.md) for the
v1.1.0 hardening specification, and [docs/compatibility.md](docs/compatibility.md)
for the four-tool compatibility matrix.

## Repository layout

```
.agents/skills/planscope/     canonical skill source (single source of truth)
├── SKILL.md                  the skill, portable across all four tools
├── templates/                INDEX / PROJECT / ROADMAP / PLAN / KNOWLEDGE / LOG / SUMMARY
└── scripts/plan.py           helper CLI (Python 3, standard library only)

.claude-plugin/marketplace.json   Claude Code plugin marketplace manifest
install.py                    syncs the skill into tool-specific directories
tests/                        pytest suite, incl. four-tool compliance checks
docs/                         product documentation (design, specs, compatibility)
.planning/                    active planning state (dogfooded with Planscope)
```

`docs/` holds product documentation; `.planning/` holds active planning
state. Keep the two distinct — documentation is not execution context.

## Supported tools

One skill source, four agents:

| Tool | Project-level discovery |
|---|---|
| Claude Code | `.claude/skills/planscope/` (via `install.py`) |
| Codex CLI | `.agents/skills/planscope/` (native) |
| opencode | `.agents/skills/planscope/` (native) |
| Kimi Code | `.agents/skills/planscope/` (native) |

## Install

Clone this repository, then:

```bash
# into the current project for ALL supported tools:
# .agents/skills/ (Codex / opencode / Kimi Code, native) + .claude/skills/ (Claude Code)
python install.py --project .

# live development: junction/symlink instead of copy
python install.py --project . --link

# global, for every project (Claude Code)
python install.py --global

# global, shared .agents directory (Codex / opencode / Kimi Code)
python install.py --global-agents

# verify what is installed where
python install.py --check --project . --global --global-agents
```

When run inside the Planscope repository itself, the installer skips
the canonical source at `.agents/skills/planscope` instead of
overwriting it.

## Use

Once the skill is visible to your agent, just work. The agent reads
`.planning/INDEX.md` first and loads only what the current task needs.

The helper CLI handles the mechanical operations:

```bash
python .agents/skills/planscope/scripts/plan.py init        # create .planning/
python .agents/skills/planscope/scripts/plan.py open v0.1   # start a release
python .agents/skills/planscope/scripts/plan.py status      # where am I?
python .agents/skills/planscope/scripts/plan.py sync        # mirror PLAN state into INDEX
python .agents/skills/planscope/scripts/plan.py compact     # hygiene checks + LOG rotation
python .agents/skills/planscope/scripts/plan.py close v0.1  # final commit: archive + clear
python .agents/skills/planscope/scripts/plan.py doctor      # validate invariants
```

## Develop

```bash
python -m pytest tests/
```

`tests/test_compat.py` is the four-tool compliance guard: it validates the
SKILL.md frontmatter against the naming, description-length and portability
rules of Claude Code, Codex CLI, opencode and Kimi Code.

## License

MIT — see [LICENSE](LICENSE).
