"""T-301 unified project installation tests.

The canonical-skip test uses a fixture copy of install.py plus a minimal
skill source inside tmp_path, so the real repository is never touched.
"""

import shutil
import subprocess
import sys
from pathlib import Path

from conftest import REPO_ROOT

INSTALL_PY = REPO_ROOT / "install.py"
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "planscope"


def run_install(*args, cwd):
    return subprocess.run(
        [sys.executable, str(INSTALL_PY), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_project_install_creates_both_surfaces(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    result = run_install("--project", str(project), cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert (project / ".agents" / "skills" / "planscope" / "SKILL.md").is_file()
    assert (project / ".claude" / "skills" / "planscope" / "SKILL.md").is_file()


def test_project_install_check_validates_both(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    assert run_install("--project", str(project), cwd=tmp_path).returncode == 0

    check = run_install("--check", "--project", str(project), cwd=tmp_path)
    assert check.returncode == 0, check.stdout
    assert ".agents" in check.stdout
    assert ".claude" in check.stdout

    # Drift on either surface must fail the check.
    claude_skill = project / ".claude" / "skills" / "planscope" / "SKILL.md"
    claude_skill.write_text("drifted", encoding="utf-8")
    check = run_install("--check", "--project", str(project), cwd=tmp_path)
    assert check.returncode == 1
    assert "DRIFTED" in check.stdout


def test_project_install_check_reports_missing(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    check = run_install("--check", "--project", str(project), cwd=tmp_path)
    assert check.returncode == 1
    assert check.stdout.count("MISSING") == 2


def test_install_skips_canonical_source(tmp_path):
    """install.py inside a repo must not overwrite its own skill source."""
    fake_repo = tmp_path / "fake-repo"
    src = fake_repo / ".agents" / "skills" / "planscope"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text("canonical\n", encoding="utf-8")
    shutil.copyfile(INSTALL_PY, fake_repo / "install.py")

    result = subprocess.run(
        [sys.executable, str(fake_repo / "install.py"), "--project", str(fake_repo)],
        cwd=fake_repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stderr
    assert "SKIP" in result.stdout
    # Canonical source untouched; the .claude mirror is still installed.
    assert (src / "SKILL.md").read_text(encoding="utf-8") == "canonical\n"
    assert (fake_repo / ".claude" / "skills" / "planscope" / "SKILL.md").is_file()


def test_install_skips_existing_link_to_canonical(tmp_path):
    fake_repo = tmp_path / "fake-repo"
    src = fake_repo / ".agents" / "skills" / "planscope"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text("canonical\n", encoding="utf-8")
    shutil.copyfile(INSTALL_PY, fake_repo / "install.py")
    claude_dest = fake_repo / ".claude" / "skills" / "planscope"
    claude_dest.parent.mkdir(parents=True)
    try:
        claude_dest.symlink_to(src, target_is_directory=True)
    except (OSError, NotImplementedError):
        import pytest
        pytest.skip("symlinks unavailable")

    result = subprocess.run(
        [sys.executable, str(fake_repo / "install.py"), "--project", str(fake_repo)],
        cwd=fake_repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.count("SKIP") == 2
    assert (src / "SKILL.md").read_text(encoding="utf-8") == "canonical\n"
