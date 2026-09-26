"""Tests for `plan.py doctor`."""

from conftest import init_project, run_plan


def test_doctor_clean_project_passes(tmp_path):
    init_project(tmp_path)
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 0, result.stdout
    assert "0 failure(s)" in result.stdout


def test_doctor_after_open_passes(tmp_path):
    init_project(tmp_path)
    run_plan("open", "v0.1", cwd=tmp_path)
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 0, result.stdout


def test_doctor_without_planning_fails(tmp_path):
    (tmp_path / ".git").mkdir()  # git-root boundary: no upward leak
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 1
    assert ".planning" in result.stdout


def test_doctor_detects_illegal_files(tmp_path):
    planning = init_project(tmp_path)
    (planning / "dev_notes.md").write_text("notes", encoding="utf-8")
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 1
    assert "illegal planning file: dev_notes.md" in result.stdout


def test_doctor_detects_illegal_files_inside_release(tmp_path):
    planning = init_project(tmp_path)
    run_plan("open", "v0.1", cwd=tmp_path)
    (planning / "releases" / "v0.1" / "investigation.md").write_text("x", encoding="utf-8")
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 1
    assert "releases/v0.1/investigation.md" in result.stdout


def test_doctor_detects_missing_active_release_path(tmp_path):
    planning = init_project(tmp_path)
    index = planning / "INDEX.md"
    index.write_text(
        index.read_text(encoding="utf-8").replace(
            "[version or none]", "v9.9"
        ).replace("[release path]", "releases/v9.9"),
        encoding="utf-8",
    )
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 1
    assert "active release path invalid" in result.stdout


def test_doctor_detects_budget_overflow(tmp_path):
    planning = init_project(tmp_path)
    bloated = "\n".join(f"line {i}" for i in range(500))
    (planning / "PROJECT.md").write_text(bloated, encoding="utf-8")
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 1
    assert "PROJECT.md" in result.stdout
    assert "hard budget" in result.stdout


def test_doctor_ignores_archive_contents(tmp_path):
    planning = init_project(tmp_path)
    archived = planning / "archive" / "v0.0"
    archived.mkdir(parents=True)
    (archived / "anything.md").write_text("old", encoding="utf-8")
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 0, result.stdout
