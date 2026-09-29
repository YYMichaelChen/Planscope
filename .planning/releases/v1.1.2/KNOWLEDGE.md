# Release Knowledge

## F-001

Title:
.claude/skills/planscope is a junction to the canonical source on the dev machine

Scope:
project

Related:
T-011

Finding:

In this repository `.claude/skills/planscope` is a directory junction
to `.agents/skills/planscope` (installed with `--link`), so canonical
edits are visible to Claude Code immediately and `install.py --project .`
skips both surfaces. Only `plugins/planscope/` needs an explicit
`install.py --build-plugin` after canonical changes.

Source:

install.py output (`SKIP ... canonical source already present`)

Promotion target:

PROJECT.md — no better source

Status:
temporary

Impact:

Forgetting `--build-plugin` after editing the canonical source fails
the plugin release gate (`PLUGIN DRIFTED`) — run it before committing.
