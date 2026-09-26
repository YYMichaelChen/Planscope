"""Tests for `plan.py close` and `plan.py compact`."""

from conftest import init_project, run_plan


def _fresh_release(tmp_path):
    planning = init_project(tmp_path)
    run_plan("open", "v0.1", cwd=tmp_path)
    return planning, planning / "releases" / "v0.1"


def test_close_blocked_by_unfinished_phases(tmp_path):
    _fresh_release(tmp_path)
    result = run_plan("close", "v0.1", cwd=tmp_path)
    assert result.returncode == 2
    assert "not complete" in result.stderr


def test_close_blocked_by_missing_summary(tmp_path):
    _, release = _fresh_release(tmp_path)
    plan = release / "PLAN.md"
    text = plan.read_text(encoding="utf-8").replace("in_progress", "complete").replace("pending", "complete")
    plan.write_text(text, encoding="utf-8")
    result = run_plan("close", "v0.1", cwd=tmp_path)
    assert result.returncode == 2
    assert "SUMMARY.md" in result.stderr


def test_close_archives_release(tmp_path):
    planning, release = _fresh_release(tmp_path)
    (release / "SUMMARY.md").write_text("# Release v0.1 Summary\n", encoding="utf-8")
    result = run_plan("close", "v0.1", "--force", cwd=tmp_path)
    assert result.returncode == 0, result.stderr

    assert not release.exists()
    archived = planning / "archive" / "v0.1"
    assert (archived / "PLAN.md").is_file()
    assert (archived / "SUMMARY.md").is_file()

    index_text = (planning / "INDEX.md").read_text(encoding="utf-8")
    assert "releases/v0.1" not in index_text

    # doctor must stay green after closing
    doctor = run_plan("doctor", cwd=tmp_path)
    assert doctor.returncode == 0, doctor.stdout


def test_close_missing_release_fails(tmp_path):
    init_project(tmp_path)
    result = run_plan("close", "v9.9", cwd=tmp_path)
    assert result.returncode == 2
    assert "No active release" in result.stderr


def test_compact_clean_project(tmp_path):
    init_project(tmp_path)
    run_plan("open", "v0.1", cwd=tmp_path)
    result = run_plan("compact", cwd=tmp_path)
    assert result.returncode == 0
    assert "within budget" in result.stdout


def test_compact_rotates_oversized_log(tmp_path):
    planning, release = _fresh_release(tmp_path)
    log = release / "LOG.md"
    header = "# Work Log\n\n## Current State\n\nPhase:\nP1\n\nTask:\nT-001\n\nNext:\nnothing\n\nBlockers:\nNone.\n"
    activity = "\n## Recent Activity\n\n" + "\n".join(f"entry {i}" for i in range(300))
    log.write_text(header + activity, encoding="utf-8")

    result = run_plan("compact", cwd=tmp_path)
    assert result.returncode == 0
    assert "Rotated" in result.stdout

    rotated = list((planning / "archive" / "logs").glob("v0.1-LOG-*.md"))
    assert len(rotated) == 1
    new_log = log.read_text(encoding="utf-8")
    assert "## Current State" in new_log
    assert len(new_log.splitlines()) < 180


def test_compact_reports_illegal_files(tmp_path):
    planning = init_project(tmp_path)
    (planning / "todo-next.md").write_text("x", encoding="utf-8")
    result = run_plan("compact", cwd=tmp_path)
    assert result.returncode == 0  # compact reports, doctor enforces
    assert "ILLEGAL: todo-next.md" in result.stdout
