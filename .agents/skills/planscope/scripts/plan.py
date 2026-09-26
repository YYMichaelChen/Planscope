#!/usr/bin/env python3
"""planscope helper CLI.

Usage:
    python plan.py <command> [args]

Commands:
    init                 Create .planning/ with INDEX, PROJECT, ROADMAP
    status               Show active release, current work, file budgets
    open <version>       Start a new release (e.g. v0.8, v1.1.0)
    sync                 Project PLAN state into INDEX (mechanical)
    compact              Mechanical hygiene: budgets, illegal files, LOG rotation
    close <version>      Archive a finished release
    doctor               Validate planning structure (non-zero exit on failure)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from spwf import __version__, commands  # noqa: E402
from spwf.core import PlanError  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="plan",
        description="planscope — scoped planning with files",
    )
    parser.add_argument("--version", action="version", version=f"planscope {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="create .planning/ structure")
    p_init.add_argument("path", nargs="?", default=".", help="project root (default: cwd)")
    p_init.set_defaults(func=commands.cmd_init)

    p_status = sub.add_parser("status", help="show current planning status")
    p_status.set_defaults(func=commands.cmd_status)

    p_open = sub.add_parser("open", help="open a new release")
    p_open.add_argument("version", help="release version, e.g. v0.8 or v1.1.0")
    p_open.set_defaults(func=commands.cmd_open)

    p_sync = sub.add_parser("sync", help="project PLAN state into INDEX")
    p_sync.set_defaults(func=commands.cmd_sync)

    p_compact = sub.add_parser("compact", help="mechanical compaction checks")
    p_compact.set_defaults(func=commands.cmd_compact)

    p_close = sub.add_parser("close", help="close and archive a release")
    p_close.add_argument("version", help="release version, e.g. v0.8")
    p_close.add_argument("--force", action="store_true",
                         help="close despite unfinished phases or missing SUMMARY")
    p_close.set_defaults(func=commands.cmd_close)

    p_doctor = sub.add_parser("doctor", help="validate planning structure")
    p_doctor.set_defaults(func=commands.cmd_doctor)

    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except PlanError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
