"""T-201 `plan sync` tests."""

from conftest import init_project, run_plan


def _open(tmp_path):
    planning = init_project(tmp_path)
    result = run_plan("open", "v0.1", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    return planning


def _edit_plan(planning, old, new):
    plan = planning / "releases" / "v0.1" / "PLAN.md"
    plan.write_text(
        plan.read_text(encoding="utf-8").replace(old, new),
        encoding="utf-8",
    )


def test_sync_updates_index_state(tmp_path):
    planning = _open(tmp_path)
    _edit_plan(planning, "Phase:\nP1", "Phase:\nP2")
    _edit_plan(planning, "Task:\nT-001", "Task:\nT-099")
    _edit_plan(
        planning,
        "## Next Action\n\nT-001 [single concrete action]",
        "## Next Action\n\nT-099 do the thing",
    )
    _edit_plan(planning, "## Blockers\n\nNone.", "## Blockers\n\nwaiting on API key")

    result = run_plan("sync", cwd=tmp_path)
    assert result.returncode == 0, result.stderr

    index = (planning / "INDEX.md").read_text(encoding="utf-8")
    assert "P2" in index
    assert "T-099" in index
    assert "do the thing" in index
    assert "waiting on API key" in index

    doctor = run_plan("doctor", cwd=tmp_path)
    assert doctor.returncode == 0, doctor.stdout
    assert "stale" not in doctor.stdout


def test_sync_requires_active_release(tmp_path):
    init_project(tmp_path)
    result = run_plan("sync", cwd=tmp_path)
    assert result.returncode == 2
    assert "No active release" in result.stderr


def test_sync_without_release_after_close(tmp_path):
    planning = _open(tmp_path)
    result = run_plan("close", "v0.1", "--force", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    result = run_plan("sync", cwd=tmp_path)
    assert result.returncode == 2
    assert "No active release" in result.stderr
