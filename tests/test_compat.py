"""Frontmatter and naming compliance across Claude Code, Codex, opencode, Kimi.

These tests are the regression guard for four-tool compatibility:
if the canonical SKILL.md ever drifts out of any tool's rules, they fail.
"""

import re

from conftest import SKILL_DIR

OPENCODE_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def parse_frontmatter(text: str) -> dict:
    """Minimal YAML-frontmatter parser (plain scalars + folded `>` blocks)."""
    lines = text.splitlines()
    assert lines[0].strip() == "---", "SKILL.md must start with frontmatter"
    fields = {}
    i = 1
    while i < len(lines) and lines[i].strip() != "---":
        line = lines[i]
        match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$", line)
        if match:
            key, value = match.group(1), match.group(2)
            if value == ">":  # folded scalar: join indented continuation lines
                parts = []
                i += 1
                while i < len(lines) and (lines[i].startswith(" ") or lines[i].startswith("\t")):
                    parts.append(lines[i].strip())
                    i += 1
                fields[key] = " ".join(p for p in parts if p)
                continue
            fields[key] = value
        i += 1
    return fields


def test_skill_file_location_and_name():
    skill_md = SKILL_DIR / "SKILL.md"  # filename must be all-caps SKILL.md
    assert skill_md.is_file(), "SKILL.md missing (exact casing required)"
    assert SKILL_DIR.name == "planscope"


def test_required_fields_present():
    fields = parse_frontmatter((SKILL_DIR / "SKILL.md").read_text(encoding="utf-8"))
    assert fields.get("name"), "frontmatter 'name' is required by all four tools"
    assert fields.get("description"), "frontmatter 'description' is required by all four tools"


def test_name_matches_directory_and_opencode_regex():
    fields = parse_frontmatter((SKILL_DIR / "SKILL.md").read_text(encoding="utf-8"))
    name = fields["name"]
    assert OPENCODE_NAME_RE.match(name), f"name {name!r} violates opencode naming rules"
    assert name == SKILL_DIR.name, "opencode requires name == directory name"


def test_description_within_opencode_limit():
    fields = parse_frontmatter((SKILL_DIR / "SKILL.md").read_text(encoding="utf-8"))
    assert 1 <= len(fields["description"]) <= 1024


def test_no_tool_specific_placeholders_in_body():
    body = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    for placeholder in ("${KIMI_SKILL_DIR}", "$ARGUMENTS", "${CLAUDE_SKILL_DIR}"):
        assert placeholder not in body, f"tool-specific placeholder {placeholder} breaks portability"


def test_templates_exist():
    for name in ("INDEX.md", "PROJECT.md", "ROADMAP.md", "PLAN.md",
                 "KNOWLEDGE.md", "LOG.md", "SUMMARY.md"):
        assert (SKILL_DIR / "templates" / name).is_file(), f"template {name} missing"
