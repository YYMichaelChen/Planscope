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


# ---- T-213 full PLAN -> INDEX projection drift -------------------------------

def _synced_release(tmp_path):
    """Open a release and sync INDEX so it mirrors PLAN exactly."""
    planning = init_project(tmp_path)
    run_plan("open", "v0.1", cwd=tmp_path)
    result = run_plan("sync", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    return planning


def _edit_index(planning, old, new):
    index = planning / "INDEX.md"
    index.write_text(
        index.read_text(encoding="utf-8").replace(old, new),
        encoding="utf-8",
    )


def test_doctor_warns_task_drift(tmp_path):
    planning = _synced_release(tmp_path)
    _edit_index(planning, "## Current Focus\n\nT-001", "## Current Focus\n\nT-999")
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 0  # drift is a warning, not a failure
    assert "WARN" in result.stdout
    assert "Current Focus" in result.stdout
    assert "stale" in result.stdout


def test_doctor_warns_phase_drift(tmp_path):
    planning = _synced_release(tmp_path)
    _edit_index(planning, "## Current Phase\n\nP1", "## Current Phase\n\nP9")
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 0
    assert "Current Phase" in result.stdout


def test_doctor_warns_next_action_drift(tmp_path):
    planning = _synced_release(tmp_path)
    _edit_index(
        planning,
        "## Next Action\n\nT-001 [single concrete next action]",
        "## Next Action\n\ndo something else",
    )
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 0
    assert "Next Action" in result.stdout


def test_doctor_warns_blocker_drift(tmp_path):
    planning = _synced_release(tmp_path)
    _edit_index(planning, "## Current Blockers\n\nNone.", "## Current Blockers\n\nghost blocker")
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 0
    assert "Current Blockers" in result.stdout


def test_sync_repairs_all_projection_drift(tmp_path):
    planning = _synced_release(tmp_path)
    # Break every synchronized field at once.
    _edit_index(planning, "## Current Focus\n\nT-001", "## Current Focus\n\nT-999")
    _edit_index(planning, "## Current Phase\n\nP1", "## Current Phase\n\nP9")
    _edit_index(
        planning,
        "## Next Action\n\nT-001 [single concrete next action]",
        "## Next Action\n\ndo something else",
    )
    _edit_index(planning, "## Current Blockers\n\nNone.", "## Current Blockers\n\nghost blocker")

    doctor = run_plan("doctor", cwd=tmp_path)
    assert doctor.returncode == 0
    for field in ("Current Focus", "Current Phase", "Next Action", "Current Blockers"):
        assert field in doctor.stdout

    sync = run_plan("sync", cwd=tmp_path)
    assert sync.returncode == 0, sync.stderr

    doctor = run_plan("doctor", cwd=tmp_path)
    assert doctor.returncode == 0, doctor.stdout
    assert "stale" not in doctor.stdout
