"""T-107 doctor invariant tests (additions to the v1.0 doctor suite)."""

from conftest import init_project, run_plan


def _open(tmp_path, version="v0.1"):
    result = run_plan("open", version, cwd=tmp_path)
    assert result.returncode == 0, result.stderr


def test_doctor_fails_multiple_releases(tmp_path):
    planning = init_project(tmp_path)
    releases = planning / "releases"
    for version in ("v0.1", "v0.2"):
        (releases / version).mkdir()
        for name in ("PLAN.md", "KNOWLEDGE.md", "LOG.md"):
            (releases / version / name).write_text("# x\n", encoding="utf-8")
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 1
    assert "multiple active release directories" in result.stdout


def test_doctor_requires_project_file(tmp_path):
    planning = init_project(tmp_path)
    (planning / "PROJECT.md").unlink()
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 1
    assert "PROJECT.md missing" in result.stdout


def test_doctor_requires_roadmap_file(tmp_path):
    planning = init_project(tmp_path)
    (planning / "ROADMAP.md").unlink()
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 1
    assert "ROADMAP.md missing" in result.stdout


def test_doctor_requires_release_files(tmp_path):
    planning = init_project(tmp_path)
    _open(tmp_path)
    (planning / "releases" / "v0.1" / "KNOWLEDGE.md").unlink()
    (planning / "releases" / "v0.1" / "LOG.md").unlink()
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 1
    assert "v0.1/KNOWLEDGE.md" in result.stdout
    assert "v0.1/LOG.md" in result.stdout


def test_doctor_detects_unknown_planning_directory(tmp_path):
    planning = init_project(tmp_path)
    (planning / "temp").mkdir()
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 1
    assert "illegal planning file: temp/" in result.stdout


def test_doctor_detects_unknown_directory_inside_release(tmp_path):
    planning = init_project(tmp_path)
    _open(tmp_path)
    (planning / "releases" / "v0.1" / "notes").mkdir()
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 1
    assert "releases/v0.1/notes/" in result.stdout


def test_doctor_detects_invalid_phase_status(tmp_path):
    planning = init_project(tmp_path)
    _open(tmp_path)
    plan = planning / "releases" / "v0.1" / "PLAN.md"
    plan.write_text(
        plan.read_text(encoding="utf-8").replace(
            "Status:\nin_progress", "Status:\ndone"
        ),
        encoding="utf-8",
    )
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 1
    assert "invalid status" in result.stdout


def test_doctor_warns_index_plan_drift(tmp_path):
    planning = init_project(tmp_path)
    _open(tmp_path)
    plan = planning / "releases" / "v0.1" / "PLAN.md"
    plan.write_text(
        plan.read_text(encoding="utf-8").replace(
            "## Next Action\n\nT-001 [single concrete action]",
            "## Next Action\n\nT-999 a different action",
        ),
        encoding="utf-8",
    )
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 0  # drift is a warning, not a failure
    assert "stale" in result.stdout
    assert "plan sync" in result.stdout
