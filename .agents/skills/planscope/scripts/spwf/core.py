"""Core helpers for the planscope CLI.

All filesystem access goes through pathlib with explicit UTF-8
encoding so behaviour is identical on Windows and Unix.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

PLANNING_DIR = ".planning"

# Whitelist of legal planning filenames (design doc section 30).
ALLOWED_FILENAMES = {
    "INDEX.md",
    "PROJECT.md",
    "ROADMAP.md",
    "PLAN.md",
    "KNOWLEDGE.md",
    "LOG.md",
    "SUMMARY.md",
}

# Files that live at the top level of .planning/.
TOP_LEVEL_FILES = {"INDEX.md", "PROJECT.md", "ROADMAP.md"}

# Files allowed inside a single release directory.
RELEASE_FILES = {"PLAN.md", "KNOWLEDGE.md", "LOG.md", "SUMMARY.md"}

# Document budgets: filename -> (soft limit, hard review) in lines.
BUDGETS = {
    "INDEX.md": (80, 120),
    "PROJECT.md": (250, 400),
    "ROADMAP.md": (150, 250),
    "PLAN.md": (200, 300),
    "KNOWLEDGE.md": (200, 300),
    "LOG.md": (120, 180),
    "SUMMARY.md": (100, 150),
}

VERSION_RE = re.compile(r"^v\d+\.\d+$")

# Lines rotated out of LOG.md are kept here; archive/ is excluded from
# the illegal-filename check.
LOG_ROTATE_DIR = "archive/logs"

# LOG rotation keeps the Current State section plus at most this many
# trailing lines of Recent Activity.
LOG_KEEP_LINES = 60


class PlanError(Exception):
    """User-facing CLI error."""


def find_planning_root(start: Path) -> Optional[Path]:
    """Walk upward from *start* looking for a .planning directory.

    Stops at the git worktree root (a directory containing .git) after
    checking it: planning context must not leak across project boundaries.
    """
    current = start.resolve()
    for candidate in (current, *current.parents):
        planning = candidate / PLANNING_DIR
        if planning.is_dir():
            return planning
        if (candidate / ".git").exists():
            return None
    return None


def require_planning_root(start: Path) -> Path:
    root = find_planning_root(start)
    if root is None:
        raise PlanError(
            f"No {PLANNING_DIR}/ directory found from {start} upward. "
            "Run `plan.py init` first."
        )
    return root


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def count_lines(path: Path) -> int:
    return len(read_text(path).splitlines())


def section_body(text: str, heading: str) -> Optional[str]:
    """Return the body of a `## heading` section, or None.

    Matching is case-sensitive and ignores the heading level relative
    to deeper subsections: the body ends at the next heading of the
    same or higher level.
    """
    lines = text.splitlines()
    start = None
    level = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#"):
            hashes = len(stripped) - len(stripped.lstrip("#"))
            title = stripped[hashes:].strip()
            if start is None:
                if title == heading:
                    start = i + 1
                    level = hashes
            elif hashes <= level:
                return "\n".join(lines[start:i]).strip()
    if start is None:
        return None
    return "\n".join(lines[start:]).strip()


def first_value(body: str) -> str:
    """First non-empty, non-bracket-placeholder line of a section body."""
    for line in body.splitlines():
        value = line.strip()
        if value and not (value.startswith("[") and value.endswith("]")):
            return value
    return ""


@dataclass
class IndexInfo:
    active_release: str
    release_path: str
    current_focus: str
    current_phase: str
    next_action: str
    blockers: str


def parse_index(index_path: Path) -> IndexInfo:
    text = read_text(index_path)

    active_body = section_body(text, "Active Release") or ""
    active_lines = [l.strip() for l in active_body.splitlines() if l.strip()]
    active_release = ""
    release_path = ""
    for i, line in enumerate(active_lines):
        if line.startswith("[") and line.endswith("]"):
            continue  # unfilled template placeholder
        if line == "Path:" and i + 1 < len(active_lines):
            candidate = active_lines[i + 1].rstrip("/")
            if not (candidate.startswith("[") and candidate.endswith("]")):
                release_path = candidate
            continue
        if not active_release and line != "Path:" and line != release_path:
            active_release = line

    def value_of(heading: str) -> str:
        body = section_body(text, heading)
        return first_value(body) if body is not None else ""

    return IndexInfo(
        active_release=active_release,
        release_path=release_path,
        current_focus=value_of("Current Focus"),
        current_phase=value_of("Current Phase"),
        next_action=value_of("Next Action"),
        blockers=value_of("Current Blockers"),
    )


@dataclass
class PlanInfo:
    status: str
    current_phase: str
    current_task: str
    next_action: str
    open_phases: list  # phase headings whose Status is pending/in_progress


def parse_plan(plan_path: Path) -> PlanInfo:
    text = read_text(plan_path)

    def value_of(heading: str) -> str:
        body = section_body(text, heading)
        return first_value(body) if body is not None else ""

    current_body = section_body(text, "Current") or ""
    current_lines = [l.strip() for l in current_body.splitlines() if l.strip()]
    phase = task = ""
    for i, line in enumerate(current_lines):
        if line == "Phase:" and i + 1 < len(current_lines):
            phase = current_lines[i + 1]
        elif line == "Task:" and i + 1 < len(current_lines):
            task = current_lines[i + 1]

    open_phases = []
    for match in re.finditer(r"^###\s+(\S+.*)$", text, re.MULTILINE):
        heading = match.group(1).strip()
        body = section_body(text, heading) or ""
        status_match = re.search(r"^Status:\s*\n?(\S+)?", body)
        status = ""
        if status_match:
            status = (status_match.group(1) or "").strip()
            if not status:
                following = body[status_match.end():].strip().splitlines()
                status = following[0].strip() if following else ""
        if status in ("pending", "in_progress"):
            open_phases.append(heading)

    return PlanInfo(
        status=value_of("Status"),
        current_phase=phase,
        current_task=task,
        next_action=value_of("Next Action"),
        open_phases=open_phases,
    )


def budget_state(filename: str, lines: int) -> str:
    soft, hard = BUDGETS.get(filename, (0, 0))
    if not soft:
        return "OK"
    if lines > hard:
        return "MUST COMPACT"
    if lines > soft:
        return "COMPACT RECOMMENDED"
    return "OK"


def illegal_planning_files(planning_root: Path) -> list:
    """Files that violate the planning filename whitelist.

    Checked at the top level of .planning/ and inside each release
    directory. archive/ content is exempt (historical material).
    """
    illegal = []
    for child in sorted(planning_root.iterdir()):
        if child.is_file() and child.name not in ALLOWED_FILENAMES:
            illegal.append(child.relative_to(planning_root).as_posix())
    for group in ("releases",):
        group_dir = planning_root / group
        if not group_dir.is_dir():
            continue
        for release in sorted(group_dir.iterdir()):
            if not release.is_dir():
                illegal.append(release.relative_to(planning_root).as_posix())
                continue
            for child in sorted(release.iterdir()):
                if child.is_file() and child.name not in RELEASE_FILES:
                    illegal.append(child.relative_to(planning_root).as_posix())
                elif child.is_dir():
                    illegal.append(child.relative_to(planning_root).as_posix() + "/")
    return illegal


def templates_dir() -> Path:
    # core.py -> spwf/ -> scripts/ -> planscope/ -> templates/
    return Path(__file__).resolve().parents[2] / "templates"


def render_template(name: str, version: str = "") -> str:
    text = read_text(templates_dir() / name)
    if version:
        text = text.replace("[version]", version)
    return text


def validate_version(version: str) -> str:
    if not VERSION_RE.match(version):
        raise PlanError(
            f"Invalid version {version!r}. Expected format: vX.Y (e.g. v0.8)."
        )
    return version
