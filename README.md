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

plugins/planscope/            generated Claude plugin package (marketplace distribution)
├── .claude-plugin/plugin.json    plugin manifest (hand-maintained)
└── skills/planscope/         skill payload, byte-identical to the canonical source

.claude-plugin/marketplace.json   Claude Code plugin marketplace manifest
install.py                    syncs the skill into tool-specific directories
tests/                        pytest suite, incl. four-tool compliance checks
docs/                         product documentation (design, specs, compatibility)
.planning/                    active planning state (dogfooded with Planscope)
```

Ownership is explicit:

- `.agents/skills/planscope/` — canonical source. Edit here only.
- `plugins/planscope/skills/planscope/` — **generated** by
  `python install.py --build-plugin`; never edit by hand.
- `plugins/planscope/.claude-plugin/plugin.json` — the only hand-maintained
  file inside the plugin package.
- `.claude-plugin/marketplace.json` — marketplace index, points at
  `./plugins/planscope`.

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

# regenerate the Claude plugin package from the canonical source
python install.py --build-plugin

# fail with PLUGIN DRIFTED if the plugin payload diverges from the canonical source
python install.py --check-plugin
```

## Distribution paths

Three surfaces, one canonical skill:

| Surface | Mechanism | Audience |
|---|---|---|
| `.agents/skills/planscope/` | `install.py --project` (copy) | Codex CLI / opencode / Kimi Code (native) |
| `.claude/skills/planscope/` | `install.py --project` (mirror) | Claude Code (direct skill install) |
| `plugins/planscope/` | `install.py --build-plugin` + marketplace | Claude Code (plugin / marketplace install) |

The plugin package is how this repository is consumed through the
Claude Code plugin marketplace: `.claude-plugin/marketplace.json` points
at `./plugins/planscope`, whose `skills/planscope/` payload is
mechanically generated from the canonical source. `install.py
--check-plugin` enforces the canonical-source invariant (payload must be
byte-identical) and is part of the release gate.

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
