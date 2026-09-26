"""Subcommand implementations for the planscope CLI.

Commands perform mechanical operations only. Semantic work —
summarizing phases, merging findings, promoting project knowledge —
is left to the agent, per the design doc (sections 33-34).
"""

from __future__ import annotations

import re
import shutil
from datetime import date
from pathlib import Path

from . import core
from .core import (
    ALLOWED_FILENAMES,
    BUDGETS,
    LOG_KEEP_LINES,
    LOG_ROTATE_DIR,
    PLANNING_DIR,
    PlanError,
)


def cmd_init(args) -> int:
    target = Path(args.path).resolve()
    planning = target / PLANNING_DIR
    if planning.exists():
        raise PlanError(f"{planning} already exists.")

    planning.mkdir(parents=True)
    for name in ("INDEX.md", "PROJECT.md", "ROADMAP.md"):
        core.write_text(planning / name, core.render_template(name))
    (planning / "releases").mkdir()
    (planning / "archive").mkdir()

    print(f"Initialized {planning}")
    print("Created: INDEX.md, PROJECT.md, ROADMAP.md, releases/, archive/")
    print("Next: fill in PROJECT.md and ROADMAP.md, then `plan.py open vX.Y`.")
    return 0


def cmd_status(args) -> int:
    planning = core.require_planning_root(Path.cwd())
    index_path = planning / "INDEX.md"

    if index_path.is_file():
        index = core.parse_index(index_path)
        print(f"Active release: {index.active_release or 'none'}")
    else:
        index = None
        print("Active release: unknown (INDEX.md missing)")

    plan = None
    if index and index.release_path:
        plan_path = planning / index.release_path / "PLAN.md"
        if plan_path.is_file():
            plan = core.parse_plan(plan_path)
            print(f"Current phase: {plan.current_phase or '?'}")
            print(f"Current task: {plan.current_task or '?'}")
    print()

    files = sorted(planning.glob("*.md"))
    if index and index.release_path:
        files += sorted((planning / index.release_path).glob("*.md"))
    for path in files:
        lines = core.count_lines(path)
        state = core.budget_state(path.name, lines)
        label = path.name if path.parent == planning else f"{index.release_path}/{path.name}"
        print(f"{label:<12} {lines:>5} lines   {state}")
    print()

    next_action = (plan.next_action if plan else "") or (index.next_action if index else "")
    print(f"Next:\n{next_action or '(none recorded)'}")
    return 0


def cmd_open(args) -> int:
    version = core.validate_version(args.version)
    planning = core.require_planning_root(Path.cwd())
    release_dir = planning / "releases" / version

    if release_dir.exists():
        raise PlanError(f"Release {version} already exists at {release_dir}.")

    release_dir.mkdir(parents=True)
    for name in ("PLAN.md", "KNOWLEDGE.md", "LOG.md"):
        core.write_text(release_dir / name, core.render_template(name, version))

    _update_index_active_release(planning / "INDEX.md", version, f"releases/{version}")

    print(f"Opened release {version} at {release_dir}")
    print("INDEX.md active release pointer updated.")
    print("Next: fill in the PLAN.md objective, acceptance criteria and phases.")
    return 0


def _update_index_active_release(index_path: Path, version: str, path: str) -> None:
    text = core.read_text(index_path) if index_path.is_file() else "# Planning Index\n"
    body_re = re.compile(
        r"(## Active Release\n)(.*?)(?=\n## |\Z)", re.DOTALL
    )
    new_body = f"## Active Release\n\n{version}\n\nPath:\n{path}\n"
    if body_re.search(text):
        text = body_re.sub(lambda _: new_body, text, count=1)
    else:
        text = text.rstrip() + "\n\n" + new_body
    core.write_text(index_path, text)


def cmd_compact(args) -> int:
    planning = core.require_planning_root(Path.cwd())
    problems = 0

    print("== Budget check ==")
    for path in sorted(planning.rglob("*.md")):
        if "archive" in path.relative_to(planning).parts:
            continue
        lines = core.count_lines(path)
        state = core.budget_state(path.name, lines)
        if state != "OK":
            problems += 1
            rel = path.relative_to(planning).as_posix()
            soft, hard = BUDGETS[path.name]
            print(f"  {rel}: {lines} lines ({state}; soft {soft}, hard {hard})")
    if problems == 0:
        print("  All planning files within budget.")

    print("== Illegal planning files ==")
    illegal = core.illegal_planning_files(planning)
    if illegal:
        for name in illegal:
            print(f"  ILLEGAL: {name} (allowed: {sorted(ALLOWED_FILENAMES)})")
    else:
        print("  None.")

    print("== INDEX pointers ==")
    index_path = planning / "INDEX.md"
    if not index_path.is_file():
        print("  ERROR: INDEX.md missing.")
        problems += 1
    else:
        index = core.parse_index(index_path)
        if index.release_path and not (planning / index.release_path).is_dir():
            problems += 1
            print(f"  ERROR: active release path missing: {index.release_path}")
        elif not index.next_action:
            print("  WARNING: INDEX Next Action is empty.")
        else:
            print("  OK.")

    print("== LOG rotation ==")
    rotated = _rotate_oversized_logs(planning)
    if rotated:
        for entry in rotated:
            print(f"  Rotated: {entry}")
    else:
        print("  No LOG.md over hard limit.")

    print()
    print("Semantic compaction (summarizing phases, merging findings,")
    print("promoting knowledge) is agent work — see SKILL.md 'Compaction'.")
    return 0


def _rotate_oversized_logs(planning: Path) -> list:
    rotated = []
    for log in sorted(planning.glob("releases/*/LOG.md")):
        lines = core.read_text(log).splitlines()
        _, hard = BUDGETS["LOG.md"]
        if len(lines) <= hard:
            continue
        stamp = date.today().isoformat()
        dest_dir = planning / LOG_ROTATE_DIR
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{log.parent.name}-LOG-{stamp}.md"
        shutil.copyfile(log, dest)

        current_state = core.section_body(core.read_text(log), "Current State") or ""
        tail = lines[-LOG_KEEP_LINES:]
        new_text = (
            "# Work Log\n\n## Current State\n\n"
            + current_state
            + "\n\n## Recent Activity\n\n"
            + f"(Older entries rotated to {LOG_ROTATE_DIR}/{dest.name} on {stamp}.)\n\n"
            + "\n".join(tail)
            + "\n"
        )
        core.write_text(log, new_text)
        rotated.append(f"{log.relative_to(planning).as_posix()} -> {dest.relative_to(planning).as_posix()}")
    return rotated


def cmd_close(args) -> int:
    version = core.validate_version(args.version)
    planning = core.require_planning_root(Path.cwd())
    release_dir = planning / "releases" / version
    archive_dir = planning / "archive" / version

    if not release_dir.is_dir():
        raise PlanError(f"No active release {version} at {release_dir}.")
    if archive_dir.exists():
        raise PlanError(f"Archive target {archive_dir} already exists.")

    plan_path = release_dir / "PLAN.md"
    if plan_path.is_file():
        plan = core.parse_plan(plan_path)
        unfinished = [p for p in plan.open_phases]
        if unfinished and not args.force:
            raise PlanError(
                f"Release {version} has unfinished phases: {', '.join(unfinished)}. "
                "Finish them or re-run with --force."
            )

    summary = release_dir / "SUMMARY.md"
    if not summary.is_file() and not args.force:
        raise PlanError(
            f"SUMMARY.md missing for {version}. Generate the release summary "
            "first (see SKILL.md 'Release Closing'), or re-run with --force."
        )

    archive_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(release_dir), str(archive_dir))

    index_path = planning / "INDEX.md"
    if index_path.is_file():
        index = core.parse_index(index_path)
        if index.active_release == version:
            _update_index_active_release(index_path, "none", "")
            print("INDEX.md active release cleared.")

    print(f"Closed {version}: moved to {archive_dir}")
    print()
    print("Remaining agent work (not automated):")
    print("  1. Promote project-scope KNOWLEDGE into PROJECT.md (deduplicate/merge).")
    print("  2. Update ROADMAP.md.")
    print("  3. Set INDEX Current Focus / Next Action, or open the next release.")
    return 0


def cmd_doctor(args) -> int:
    start = Path.cwd()
    failures = 0
    warnings = 0

    def fail(msg):
        nonlocal failures
        failures += 1
        print(f"FAIL    {msg}")

    def warn(msg):
        nonlocal warnings
        warnings += 1
        print(f"WARN    {msg}")

    def ok(msg):
        print(f"OK      {msg}")

    planning = core.find_planning_root(start)
    if planning is None:
        fail(f"{PLANNING_DIR}/ not found from {start} upward")
        print(f"\ndoctor: 1 failure, 0 warnings")
        return 1
    ok(f"{PLANNING_DIR}/ exists at {planning}")

    index_path = planning / "INDEX.md"
    if not index_path.is_file():
        fail("INDEX.md missing")
        index = None
    else:
        ok("INDEX.md exists")
        index = core.parse_index(index_path)

    releases_dir = planning / "releases"
    release_dirs = (
        [d for d in sorted(releases_dir.iterdir()) if d.is_dir()]
        if releases_dir.is_dir()
        else []
    )
    if len(release_dirs) > 1:
        warn(f"multiple active release directories: {', '.join(d.name for d in release_dirs)}")

    if index is not None:
        if index.active_release and index.active_release != "none":
            release_path = planning / index.release_path
            if release_path.is_dir():
                ok(f"active release path valid: {index.release_path}")
            else:
                fail(f"active release path invalid: {index.release_path or '(empty)'}")
            if release_dirs and index.active_release not in {d.name for d in release_dirs}:
                warn(f"INDEX active release {index.active_release} not found under releases/")
        else:
            warn("no active release recorded in INDEX")

        if not index.next_action:
            warn("INDEX Next Action is empty")
        else:
            ok("INDEX Next Action present")

    illegal = core.illegal_planning_files(planning)
    if illegal:
        for name in illegal:
            fail(f"illegal planning file: {name}")
    else:
        ok("no illegal planning filenames")

    if index is not None and index.release_path:
        plan_path = planning / index.release_path / "PLAN.md"
        if plan_path.is_file():
            text = core.read_text(plan_path)
            required = ["Objective", "Acceptance Criteria", "Status", "Phases", "Next Action"]
            missing = [s for s in required if core.section_body(text, s) is None]
            if missing:
                fail(f"PLAN.md missing sections: {', '.join(missing)}")
            else:
                ok("PLAN.md section schema valid")
        else:
            fail(f"active PLAN.md missing at {plan_path}")

    for path in sorted(planning.rglob("*.md")):
        if "archive" in path.relative_to(planning).parts:
            continue
        if path.name not in BUDGETS:
            continue
        lines = core.count_lines(path)
        state = core.budget_state(path.name, lines)
        rel = path.relative_to(planning).as_posix()
        if state == "MUST COMPACT":
            fail(f"{rel}: {lines} lines exceeds hard budget {BUDGETS[path.name][1]}")
        elif state == "COMPACT RECOMMENDED":
            warn(f"{rel}: {lines} lines exceeds soft budget {BUDGETS[path.name][0]}")

    print(f"\ndoctor: {failures} failure(s), {warnings} warning(s)")
    return 1 if failures else 0
