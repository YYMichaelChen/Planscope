# Four-Tool Compatibility Matrix

The canonical skill lives at `.agents/skills/planscope/SKILL.md`.
This document records the skill-loading rules of each supported tool and the
constraints the canonical source must satisfy. `tests/test_compat.py`
enforces the mechanical parts of this contract.

## Discovery paths

| Tool | Project-level | Global | Notes |
|---|---|---|---|
| Claude Code | `.claude/skills/<name>/SKILL.md` | `~/.claude/skills/<name>/SKILL.md` | Does **not** scan `.agents/skills/` — `install.py` mirrors the skill there |
| Codex CLI | `.agents/skills/<name>/SKILL.md` (scanned upward to repo root) | `~/.agents/skills/<name>/SKILL.md` | Symlinks supported; optional `agents/openai.yaml` for UI metadata |
| opencode | `.opencode/skills/`, `.claude/skills/`, `.agents/skills/` | `~/.config/opencode/skills/`, `~/.claude/skills/`, `~/.agents/skills/` | Walks up from cwd to git worktree root |
| Kimi Code | `.kimi-code/skills/`, `.agents/skills/` | `~/.kimi-code/skills/`, `~/.agents/skills/` | Priority: Project > User > Extra (`extra_skill_dirs`) > Built-in |

`.agents/skills/` is the common denominator of Codex, opencode and Kimi Code,
so it holds the canonical source. Only Claude Code needs a mirror.

Since v1.1.0, `python install.py --project <path>` installs **both**
project-level surfaces in one command: the `.agents/skills/planscope`
copy (skipped with `SKIP canonical source already present` when the
destination is the Planscope repository itself) and the
`.claude/skills/planscope` mirror. `--check --project <path>` validates
both.

## Claude Code: two distribution paths

Both paths deliver the same canonical Planscope skill — they differ only
in packaging:

1. **Direct skill path** — `install.py` copies the canonical source to
   `.claude/skills/planscope/`. Claude Code discovers
   `.claude/skills/<name>/SKILL.md` directly.
2. **Plugin path** (v1.1.1) — `.claude-plugin/marketplace.json` points at
   `./plugins/planscope`, a conventional Claude plugin root containing
   `.claude-plugin/plugin.json` and `skills/planscope/SKILL.md`. The
   payload under `plugins/planscope/skills/planscope/` is generated from
   the canonical source by `install.py --build-plugin` and must stay
   byte-identical to it; `install.py --check-plugin` reports
   `PLUGIN IN SYNC` or `PLUGIN DRIFTED` and is part of the release gate.

The plugin path exists specifically for Claude marketplace/plugin
consumption; ordinary project installs continue to use the direct skill
path and are unchanged.

### Verified with (T-314)

As of v1.1.1, validated with the official Claude Code CLI (v2.1.283):

```
claude plugin validate ./plugins/planscope     # plugin manifest + components
claude plugin validate .                       # marketplace manifest
```

Both pass (`Validation passed`). Re-run these commands after changing
`plugin.json` or `marketplace.json`.

## Frontmatter rules

| Field | Claude Code | Codex CLI | opencode | Kimi Code |
|---|---|---|---|---|
| `name` | required | required | required; must match directory name; regex `^[a-z0-9]+(-[a-z0-9]+)*$` | required (case-insensitive) |
| `description` | required | required | required; ≤ 1024 chars | required |
| `license` | ignored | ignored | optional | ignored |
| `compatibility` | ignored | ignored | optional | ignored |
| `metadata` | ignored | ignored | optional (string map) | ignored |
| `allowed-tools` | optional | ignored | ignored | ignored |
| `type` / `disableModelInvocation` / `arguments` | ignored | ignored | ignored | optional |

Every tool ignores unknown fields, so one superset frontmatter serves all four.

## Portability rules for the canonical source

1. `name: planscope` — lowercase-hyphen, matches the directory name.
2. `description` stays under 1024 characters (opencode hard limit).
3. No tool-specific placeholders in the body (`${KIMI_SKILL_DIR}`,
   `$ARGUMENTS`, ...). Scripts are referenced as
   `python <directory containing SKILL.md>/scripts/plan.py <command>`.
4. Scripts use Python 3 standard library only, invoked via `python`
   (not `./plan`), so they work on Windows and Unix alike.
5. Filenames are exact-case: `SKILL.md`, templates in `templates/`,
   scripts in `scripts/`.

## Invocation differences

- Claude Code / Codex / opencode: the skill is triggered implicitly from
  `description`, or explicitly by the user.
- Kimi Code: also supports explicit `/skill:planscope`; implicit triggering
  is on by default (`disableModelInvocation` not set).

## Verified with

Documented behavior as of 2026-09 (opencode docs, Codex skills docs,
kimi-code customization/skills docs, Claude Code skill docs). Re-run
`tests/test_compat.py` after editing SKILL.md frontmatter.
