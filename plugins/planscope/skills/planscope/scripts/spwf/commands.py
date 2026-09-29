"""Subcommand implementations for the planscope CLI.

Commands perform mechanical operations only. Semantic work —
summarizing phases, merging findings, promoting project knowledge —
is left to the agent, per the design doc (sections 33-34).

v1.1.0 lifecycle rules enforced here:

- exactly zero or one active release (T-103)
- coherent release activation / clearing (T-101, T-102)
- strict phase status model; positive completion check (T-104)
- mechanical close is the final commit of a release (T-105)
- collision-safe LOG rotation (T-106)
- PLAN is the work source; INDEX is its routing projection (T-201)

v1.1.2 governance boundary rules:

- normal close requires a complete PLAN closeout checklist, the
  mechanical proof that authority reconciliation happened
- doctor validates the closeout schema structurally (never semantically)
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
    PHASE_STATUSES,
    PLANNING_DIR,
    RELEASE_STATUSES,
    PlanError,
)

# Placeholders in templates/INDEX.md and the values used when a release
# is activated (T-101) or cleared (T-102).
INDEX_TEMPLATE_PLACEHOLDERS = (
    "[version or none]",
    "[release path]",
    "[task ID and short description]",
    "[phase ID and title]",
    "[single concrete next action]",
    "[release]/PLAN.md",
    "[release]/KNOWLEDGE.md",
    "[release]/LOG.md",
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

    # PLAN is the canonical work source; INDEX is only a routing
    # projection. Prefer PLAN values whenever an active PLAN exists (T-201).
    next_action = (plan.next_action if plan else "") or (index.next_action if index else "")
    print(f"Next:\n{next_action or '(none recorded)'}")
    blockers = (plan.blockers if plan else "") or (index.blockers if index else "")
    if blockers and blockers != "None.":
        print(f"\nBlockers:\n{blockers}")
    return 0


def _render_index(planning: Path, replacements: dict) -> None:
    """Rewrite INDEX.md from the template, preserving Critical Constraints.

    Every release-dependent field comes from the template plus the given
    replacements, so no stale value from a previous release can survive.
    The Critical Constraints section is carried over from the existing
    INDEX (it is user content, not release state).
    """
    index_path = planning / "INDEX.md"
    text = core.render_template("INDEX.md")
    for old, new in replacements.items():
        text = text.replace(old, new)

    constraints = None
    if index_path.is_file():
        constraints = core.section_body(core.read_text(index_path), "Critical Constraints")
    if constraints:
        text = text.replace(
            "- [only constraints immediately relevant to active work]", constraints
        )
    core.write_text(index_path, text)


def activate_release(planning: Path, version: str) -> None:
    """T-101: coherent release activation.

    Creates the release working set and rewrites every release-dependent
    INDEX field, leaving no reference to the previous release.
    """
    release_dir = planning / "releases" / version
    release_dir.mkdir(parents=True)
    for name in ("PLAN.md", "KNOWLEDGE.md", "LOG.md"):
        core.write_text(release_dir / name, core.render_template(name, version))

    _render_index(planning, {
        "[version or none]": version,
        "[release path]": f"releases/{version}",
        "[task ID and short description]": "Not selected.",
        "[phase ID and title]": "Not started.",
        "[single concrete next action]": "Define the release objective and first phase.",
        "[release]/PLAN.md": f"releases/{version}/PLAN.md",
        "[release]/KNOWLEDGE.md": f"releases/{version}/KNOWLEDGE.md",
        "[release]/LOG.md": f"releases/{version}/LOG.md",
    })


def clear_active_release(planning: Path) -> None:
    """T-102: coherent active-context clearing.

    After this, INDEX references no release content — archived or
    otherwise — anywhere in the active routing fields.
    """
    _render_index(planning, {
        "[version or none]": "none",
        "[release path]": "[none]",
        "[task ID and short description]": "None.",
        "[phase ID and title]": "None.",
        "[single concrete next action]": "Open the next release or select new work.",
        "[release]/PLAN.md": "[none]",
        "[release]/KNOWLEDGE.md": "[none]",
        "[release]/LOG.md": "[none]",
    })


def cmd_open(args) -> int:
    version = core.validate_version(args.version)
    planning = core.require_planning_root(Path.cwd())
    releases_dir = planning / "releases"

    # T-103: exactly zero or one active release. Refuse to open a second.
    existing = sorted(
        d.name for d in releases_dir.iterdir() if d.is_dir()
    ) if releases_dir.is_dir() else []
    if existing:
        raise PlanError(
            f"Active release {existing[0]} already exists. "
            f"Close it before opening {version}."
        )

    activate_release(planning, version)

    print(f"Opened release {version} at {releases_dir / version}")
    print("INDEX.md active working set synchronized.")
    print("Next: fill in the PLAN.md objective, acceptance criteria and phases.")
    return 0


def _replace_index_section(text: str, heading: str, new_body: str) -> str:
    """Replace the body of a `## heading` section in INDEX text."""
    body_re = re.compile(
        r"(## " + re.escape(heading) + r"\n)(.*?)(?=\n## |\Z)", re.DOTALL
    )
    replacement = lambda m: m.group(1) + "\n" + new_body.rstrip() + "\n"
    if not body_re.search(text):
        raise PlanError(f"INDEX.md has no '## {heading}' section.")
    return body_re.sub(replacement, text, count=1)


def cmd_sync(args) -> int:
    """T-201: project PLAN state into INDEX, mechanically.

    PLAN is the canonical source for the active release's current phase,
    task, blockers and next action; INDEX is a routing projection that
    must mirror it. No semantic inference happens here.
    """
    planning = core.require_planning_root(Path.cwd())
    index_path = planning / "INDEX.md"
    index = core.parse_index(index_path) if index_path.is_file() else None
    if not index or not index.active_release or index.active_release == "none":
        raise PlanError("No active release. Open one with `plan.py open vX.Y` first.")

    plan_path = planning / index.release_path / "PLAN.md"
    if not plan_path.is_file():
        raise PlanError(f"Active PLAN.md missing at {plan_path}.")
    plan = core.parse_plan(plan_path)

    text = core.read_text(index_path)
    text = _replace_index_section(
        text, "Current Focus", plan.current_task or "Not selected."
    )
    text = _replace_index_section(
        text, "Current Phase", plan.current_phase or "Not started."
    )
    text = _replace_index_section(
        text, "Next Action", plan.next_action or "(none recorded)"
    )
    text = _replace_index_section(
        text, "Current Blockers", plan.blockers or "None."
    )
    core.write_text(index_path, text)

    print(f"Synchronized INDEX.md from {index.release_path}/PLAN.md.")
    print(f"  Phase: {plan.current_phase or '?'}   Task: {plan.current_task or '?'}")
    return 0


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
    """T-106: rotate oversized LOGs into collision-safe archive names.

    Archives are named {release}-LOG-{YYYYMMDD}-{NNN}.md; the counter
    increments until the name is free, so repeated rotations on the same
    day never overwrite an existing archive.
    """
    rotated = []
    for log in sorted(planning.glob("releases/*/LOG.md")):
        lines = core.read_text(log).splitlines()
        _, hard = BUDGETS["LOG.md"]
        if len(lines) <= hard:
            continue
        stamp = date.today().strftime("%Y%m%d")
        dest_dir = planning / LOG_ROTATE_DIR
        dest_dir.mkdir(parents=True, exist_ok=True)
        n = 1
        dest = dest_dir / f"{log.parent.name}-LOG-{stamp}-{n:03d}.md"
        while dest.exists():
            n += 1
            dest = dest_dir / f"{log.parent.name}-LOG-{stamp}-{n:03d}.md"
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
    """T-105: mechanical close is the FINAL commit of a release.

    Semantic close (summary, knowledge promotion, roadmap update,
    PLAN Status = complete, closeout checklist) must already have
    happened; this command only verifies the gates, archives, and
    clears the active context.
    """
    version = core.validate_version(args.version)
    planning = core.require_planning_root(Path.cwd())
    release_dir = planning / "releases" / version
    archive_dir = planning / "archive" / version

    if not release_dir.is_dir():
        raise PlanError(f"No active release {version} at {release_dir}.")
    if archive_dir.exists():
        raise PlanError(f"Archive target {archive_dir} already exists.")

    plan = None
    plan_path = release_dir / "PLAN.md"
    if not plan_path.is_file():
        # T-211: normal close must be independently safe — it cannot rely
        # on the user having run `plan doctor` first. Without PLAN.md there
        # is no canonical plan to close against.
        if not args.force:
            raise PlanError(
                f"PLAN.md missing for {version}. "
                "A release cannot be closed without its canonical plan."
            )
    else:
        plan = core.parse_plan(plan_path)
        if not args.force:
            # T-212: the positive completion check below is vacuously true
            # for a phaseless PLAN; a structurally empty plan must not close.
            if not plan.phases:
                raise PlanError(
                    "PLAN.md contains no phases. "
                    "Define and complete at least one release phase "
                    "before closing, or re-run with --force."
                )
            # T-104: positive completion check — every phase must be exactly
            # 'complete'; anything else (pending, in_progress, unknown or
            # missing status) blocks normal close.
            blocked = plan.not_complete_phases
            if blocked:
                raise PlanError(
                    f"Release {version} has phases that are not complete: "
                    f"{', '.join(blocked)}. Finish them or re-run with --force."
                )
            if plan.status != "complete":
                raise PlanError(
                    f"PLAN ## Status is {plan.status!r}; set it to 'complete' "
                    "after semantic close, or re-run with --force."
                )

    summary = release_dir / "SUMMARY.md"
    if not summary.is_file() and not args.force:
        raise PlanError(
            f"SUMMARY.md missing for {version}. Generate the release summary "
            "first (see SKILL.md 'Release Closing'), or re-run with --force."
        )

    # v1.1.2: the closeout checklist is the final gate. The CLI checks
    # only that the required items exist and are checked — the semantic
    # reconciliation they represent is the agent's job.
    if plan is not None and not args.force:
        if plan.closeout is None:
            raise PlanError(
                f"PLAN.md for {version} has no '## Closeout' checklist. "
                "Add the closeout checklist (see templates/PLAN.md) and "
                "complete it, or re-run with --force."
            )
        unchecked = plan.unchecked_closeout
        if unchecked:
            raise PlanError(
                "PLAN closeout is incomplete:\n- " + "\n".join(unchecked)
            )

    archive_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(release_dir), str(archive_dir))

    index_path = planning / "INDEX.md"
    if index_path.is_file():
        index = core.parse_index(index_path)
        if index.active_release == version or index.release_path == f"releases/{version}":
            clear_active_release(planning)

    print(f"Closed {version}.")
    print("Release moved to archive.")
    print("Active release cleared.")
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

    # T-107: root structure.
    for name in ("INDEX.md", "PROJECT.md", "ROADMAP.md"):
        if (planning / name).is_file():
            ok(f"{name} exists")
        else:
            fail(f"{name} missing")
    for name in ("releases", "archive"):
        if (planning / name).is_dir():
            ok(f"{name}/ exists")
        else:
            fail(f"{name}/ missing")

    index_path = planning / "INDEX.md"
    if not index_path.is_file():
        index = None
    else:
        index = core.parse_index(index_path)

    releases_dir = planning / "releases"
    release_dirs = (
        [d for d in sorted(releases_dir.iterdir()) if d.is_dir()]
        if releases_dir.is_dir()
        else []
    )
    # T-103: more than one active release is a hard failure.
    if len(release_dirs) > 1:
        fail(f"multiple active release directories: {', '.join(d.name for d in release_dirs)}")
    elif len(release_dirs) == 1:
        ok(f"single active release directory: {release_dirs[0].name}")

    # Active release contents, PLAN schema and status validation.
    plan = None
    if release_dirs:
        active = release_dirs[0]
        for name in ("PLAN.md", "KNOWLEDGE.md", "LOG.md"):
            if (active / name).is_file():
                ok(f"active release has {name}")
            else:
                fail(f"active release missing {active.name}/{name}")

        plan_path = active / "PLAN.md"
        if plan_path.is_file():
            text = core.read_text(plan_path)
            required = ["Objective", "Acceptance Criteria", "Status", "Current",
                        "Phases", "Blockers", "Next Action"]
            missing = [s for s in required if core.section_body(text, s) is None]
            if missing:
                fail(f"PLAN.md missing sections: {', '.join(missing)}")
            else:
                ok("PLAN.md section schema valid")

            plan = core.parse_plan(plan_path)
            if plan.status not in RELEASE_STATUSES:
                fail(f"PLAN release Status is invalid: {plan.status!r}")
            else:
                ok(f"PLAN release Status valid: {plan.status}")
            for phase in plan.invalid_phases:
                fail(
                    f"phase {phase.heading!r} has invalid status "
                    f"{phase.status!r} (allowed: {sorted(PHASE_STATUSES)})"
                )
            if plan.phases and not plan.invalid_phases:
                ok(f"all {len(plan.phases)} phase statuses valid")

            # v1.1.2: structural closeout validation. A missing section
            # marks a legacy (pre-v1.1.2) plan — warn, don't fail, so
            # existing projects can migrate. Everything else is a hard
            # structural check; the CLI never judges item semantics.
            if plan.closeout is None:
                warn(
                    "PLAN.md has no '## Closeout' section (pre-v1.1.2 plan); "
                    "add the checklist before close"
                )
            else:
                present = {c.text for c in plan.closeout}
                missing_items = [
                    item for item in core.CLOSEOUT_ITEMS if item not in present
                ]
                if missing_items:
                    fail(
                        "PLAN.md Closeout missing required items: "
                        + ", ".join(missing_items)
                    )
                unchecked = [c.text for c in plan.closeout if not c.checked]
                if unchecked and plan.status == "complete":
                    fail(
                        "PLAN Status is 'complete' but closeout items are "
                        "unchecked: " + ", ".join(unchecked)
                    )
                elif not unchecked and not missing_items:
                    ok("PLAN closeout checklist complete")

    # INDEX <-> actual release directory consistency.
    if index is not None:
        if release_dirs:
            actual = release_dirs[0].name
            if not index.active_release or index.active_release == "none":
                warn(
                    f"INDEX active release is none but releases/{actual} exists; "
                    "resolve manually"
                )
            elif index.active_release != actual:
                fail(
                    f"INDEX active release {index.active_release} != "
                    f"actual release directory {actual}"
                )
            elif index.release_path != f"releases/{actual}":
                fail(f"INDEX release path {index.release_path!r} != releases/{actual}")
            else:
                ok("INDEX active release matches actual directory")
        elif index.active_release and index.active_release != "none":
            fail(f"active release path invalid: {index.release_path or '(empty)'}")

        if not index.next_action:
            warn("INDEX Next Action is empty")
        else:
            ok("INDEX Next Action present")

        # T-201/T-213: INDEX is a projection of PLAN — report drift on
        # every mechanically synchronized field, don't fail. `plan sync`
        # repairs all of it.
        if plan is not None and index.active_release and index.active_release != "none":
            drifted = []
            if plan.current_phase and index.current_phase != plan.current_phase:
                drifted.append("Current Phase")
            if plan.current_task and index.current_focus != plan.current_task:
                drifted.append("Current Focus")
            if plan.next_action and index.next_action != plan.next_action:
                drifted.append("Next Action")
            if plan.blockers and index.blockers != plan.blockers:
                drifted.append("Current Blockers")
            if drifted:
                warn(
                    f"INDEX {', '.join(drifted)} is stale. Run: plan sync"
                )
            else:
                ok("INDEX matches PLAN current state")

    illegal = core.illegal_planning_files(planning)
    if illegal:
        for name in illegal:
            fail(f"illegal planning file: {name}")
    else:
        ok("no illegal planning filenames")

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
