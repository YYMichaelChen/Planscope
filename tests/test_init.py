"""Tests for `plan.py init`."""

from conftest import init_project, run_plan


def test_init_creates_structure(tmp_path):
    planning = init_project(tmp_path)
    assert (planning / "INDEX.md").is_file()
    assert (planning / "PROJECT.md").is_file()
    assert (planning / "ROADMAP.md").is_file()
    assert (planning / "releases").is_dir()
    assert (planning / "archive").is_dir()


def test_init_twice_fails(tmp_path):
    init_project(tmp_path)
    result = run_plan("init", cwd=tmp_path)
    assert result.returncode == 2
    assert "already exists" in result.stderr
