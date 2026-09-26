"""Shared helpers for planscope tests."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "planscope"
PLAN_PY = SKILL_DIR / "scripts" / "plan.py"


def run_plan(*args, cwd):
    """Run plan.py in *cwd* and return the CompletedProcess."""
    return subprocess.run(
        [sys.executable, str(PLAN_PY), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",  # tolerate localized OS error text (GBK) on Windows
    )


def init_project(tmp_path):
    result = run_plan("init", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    return tmp_path / ".planning"
