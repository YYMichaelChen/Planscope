#!/usr/bin/env python3
"""Install/sync the planscope skill into tool-specific skill directories.

The canonical skill source lives at:

    .agents/skills/planscope/      (this repo)

That location is discovered natively by Codex CLI, opencode and
Kimi Code. Claude Code only scans .claude/skills/, so this script
mirrors the canonical source there (copy by default, directory
junction/symlink with --link for live development).

Usage:
    python install.py --project [PATH] [--link]   # -> PATH/.agents/skills/ + PATH/.claude/skills/
    python install.py --global [--link]           # -> ~/.claude/skills/planscope
    python install.py --global-agents [--link]    # -> ~/.agents/skills/planscope
    python install.py --check [--project PATH]    # report drift, no changes

--project installs BOTH project-level surfaces from one command:
the canonical copy at .agents/skills/planscope (native for Codex CLI,
opencode and Kimi Code) and the .claude/skills/planscope mirror Claude
Code requires. When the destination resolves to this repository's own
canonical source, the installer skips it instead of overwriting itself.
"""

from __future__ import annotations

import argparse
import filecmp
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SOURCE = REPO_ROOT / ".agents" / "skills" / "planscope"
SKILL_NAME = "planscope"


def fail(msg: str) -> "SystemExit":
    print(f"error: {msg}", file=sys.stderr)
    return SystemExit(2)


def require_source() -> Path:
    if not (SOURCE / "SKILL.md").is_file():
        raise fail(f"canonical skill not found at {SOURCE}")
    return SOURCE


def remove_existing(dest: Path) -> None:
    if dest.is_symlink():
        dest.unlink()
    elif _is_junction(dest):
        os.rmdir(dest)  # removes the junction only, never the target
    elif dest.is_dir():
        shutil.rmtree(dest)
    elif dest.exists():
        dest.unlink()


def _is_junction(path: Path) -> bool:
    # On Windows a directory junction is a reparse point that os.path.islink
    # does not detect; unlink() removes the junction without touching the target.
    if os.name != "nt" or not path.exists():
        return False
    attrs = getattr(path.stat(), "st_file_attributes", 0)
    return bool(attrs & 0x400)  # FILE_ATTRIBUTE_REPARSE_POINT


def link_dir(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    remove_existing(dest)
    if os.name == "nt":
        # Directory junction needs no admin rights, unlike symlinks.
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(dest), str(src)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise fail(f"mklink /J failed: {result.stdout.strip()} {result.stderr.strip()}")
    else:
        os.symlink(src, dest, target_is_directory=True)


def copy_dir(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    remove_existing(dest)
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def trees_equal(a: Path, b: Path) -> bool:
    if not b.is_dir():
        return False
    cmp = filecmp.dircmp(a, b, ignore=["__pycache__"])
    if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
        return False
    return all(trees_equal(Path(a, d), Path(b, d)) for d in cmp.common_dirs)


def install(dest: Path, link: bool, check: bool) -> int:
    src = require_source()
    # Canonical source protection: never overwrite the skill's own home.
    # This also covers a junction/symlink at dest that already points at
    # the canonical source (Path.resolve follows links on all platforms).
    if dest.resolve() == SOURCE.resolve():
        print(f"SKIP    {dest} (canonical source already present)")
        return 0
    if check:
        if not dest.exists():
            print(f"MISSING   {dest}")
            return 1
        if dest.is_symlink() or _is_junction(dest):
            print(f"LINKED    {dest} -> {src}")
            return 0
        if trees_equal(src, dest):
            print(f"IN SYNC   {dest}")
            return 0
        print(f"DRIFTED   {dest} (differs from {src})")
        return 1

    if link:
        link_dir(src, dest)
        print(f"linked    {dest} -> {src}")
    else:
        copy_dir(src, dest)
        print(f"copied    {src} -> {dest}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Install the planscope skill.")
    targets = parser.add_argument_group("targets (at least one required)")
    targets.add_argument("--project", nargs="?", const=".", default=None,
                         help="project root (default: cwd) -> .agents/skills/ + .claude/skills/")
    targets.add_argument("--global", dest="global_claude", action="store_true",
                         help="-> ~/.claude/skills/")
    targets.add_argument("--global-agents", action="store_true",
                         help="-> ~/.agents/skills/ (Codex/opencode/Kimi global)")
    parser.add_argument("--link", action="store_true",
                        help="junction/symlink instead of copy (live development)")
    parser.add_argument("--check", action="store_true",
                        help="report drift without changing anything")
    args = parser.parse_args(argv)

    if not any([args.project is not None, args.global_claude, args.global_agents]):
        parser.error("choose at least one target: --project, --global, --global-agents")

    rc = 0
    dests = []
    if args.project is not None:
        project = Path(args.project).resolve()
        # T-301: one command -> every supported project-level surface.
        dests.append(project / ".agents" / "skills" / SKILL_NAME)
        dests.append(project / ".claude" / "skills" / SKILL_NAME)
    if args.global_claude:
        dests.append(Path.home() / ".claude" / "skills" / SKILL_NAME)
    if args.global_agents:
        dests.append(Path.home() / ".agents" / "skills" / SKILL_NAME)

    for dest in dests:
        rc |= install(dest, link=args.link, check=args.check)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
