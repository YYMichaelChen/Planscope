"""Tests for `plan.py status` and `plan.py open`."""

from conftest import init_project, run_plan


def test_status_without_planning_fails(tmp_path):
    (tmp_path / ".git").mkdir()  # git-root boundary: no upward leak
    result = run_plan("status", cwd=tmp_path)
    assert result.returncode == 2
    assert "init" in result.stderr


def test_open_creates_release_and_updates_index(tmp_path):
    planning = init_project(tmp_path)
    result = run_plan("open", "v0.1", cwd=tmp_path)
    assert result.returncode == 0, result.stderr

    release = planning / "releases" / "v0.1"
    for name in ("PLAN.md", "KNOWLEDGE.md", "LOG.md"):
        assert (release / name).is_file(), f"{name} missing"

    plan_text = (release / "PLAN.md").read_text(encoding="utf-8")
    assert "# Release v0.1" in plan_text

    index_text = (planning / "INDEX.md").read_text(encoding="utf-8")
    assert "v0.1" in index_text
    assert "releases/v0.1" in index_text


def test_open_rejects_bad_version(tmp_path):
    init_project(tmp_path)
    result = run_plan("open", "release-1", cwd=tmp_path)
    assert result.returncode == 2
    assert "vX.Y" in result.stderr


def test_open_duplicate_fails(tmp_path):
    init_project(tmp_path)
    run_plan("open", "v0.1", cwd=tmp_path)
    result = run_plan("open", "v0.1", cwd=tmp_path)
    assert result.returncode == 2
    assert "already exists" in result.stderr


def test_status_reports_active_release_and_budgets(tmp_path):
    init_project(tmp_path)
    run_plan("open", "v0.1", cwd=tmp_path)
    result = run_plan("status", cwd=tmp_path)
    assert result.returncode == 0
    assert "Active release: v0.1" in result.stdout
    assert "Current phase: P1" in result.stdout
    assert "Current task: T-001" in result.stdout
    assert "INDEX.md" in result.stdout
    assert "Next:" in result.stdout


def test_status_finds_planning_from_subdirectory(tmp_path):
    init_project(tmp_path)
    run_plan("open", "v0.1", cwd=tmp_path)
    nested = tmp_path / "src" / "deep"
    nested.mkdir(parents=True)
    result = run_plan("status", cwd=nested)
    assert result.returncode == 0
    assert "Active release: v0.1" in result.stdout
