"""T-101/T-102/T-103/T-104/T-105 lifecycle regression tests."""

from conftest import init_project, run_plan


def _open(tmp_path, version="v0.1"):
    planning = init_project(tmp_path)
    result = run_plan("open", version, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    return planning


def _make_closeable(planning, version="v0.1"):
    """Rewrite PLAN into a fully-complete, closeable state."""
    plan = planning / "releases" / version / "PLAN.md"
    text = plan.read_text(encoding="utf-8")
    text = (
        text.replace("## Status\n\nin_progress", "## Status\n\ncomplete")
        .replace("Status:\nin_progress", "Status:\ncomplete")
        .replace("Status:\npending", "Status:\ncomplete")
    )
    plan.write_text(text, encoding="utf-8")
    (planning / "releases" / version / "SUMMARY.md").write_text(
        "# Summary\n", encoding="utf-8"
    )


# ---- T-101 coherent activation -------------------------------------------------

def test_open_clears_stale_index_state(tmp_path):
    planning = _open(tmp_path)
    index = planning / "INDEX.md"
    # Simulate drift left behind by a previous release.
    index.write_text(
        index.read_text(encoding="utf-8").replace(
            "Not selected.", "T-014 stale task from v0.9"
        ).replace("Not started.", "P9 stale phase"),
        encoding="utf-8",
    )

    # Close the first release so a second can open (T-103).
    _make_closeable(planning)
    assert run_plan("close", "v0.1", cwd=tmp_path).returncode == 0
    # Keep a stale pointer around, as a drifted INDEX would.
    index.write_text(
        index.read_text(encoding="utf-8").replace(
            "## Current Focus\n\nNone.", "## Current Focus\n\nT-014 stale task"
        ),
        encoding="utf-8",
    )

    result = run_plan("open", "v0.2", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    text = index.read_text(encoding="utf-8")
    assert "T-014" not in text
    assert "P9" not in text
    assert "Not selected." in text
    assert "Not started." in text


def test_open_rewrites_context_map(tmp_path):
    planning = _open(tmp_path)
    _make_closeable(planning)
    assert run_plan("close", "v0.1", cwd=tmp_path).returncode == 0

    result = run_plan("open", "v0.2", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    text = (planning / "INDEX.md").read_text(encoding="utf-8")
    assert "releases/v0.2/PLAN.md" in text
    assert "releases/v0.2/KNOWLEDGE.md" in text
    assert "releases/v0.2/LOG.md" in text
    assert "releases/v0.1" not in text

    doctor = run_plan("doctor", cwd=tmp_path)
    assert doctor.returncode == 0, doctor.stdout


# ---- T-103 single active release ---------------------------------------------

def test_open_rejects_second_active_release(tmp_path):
    _open(tmp_path, "v0.1")
    result = run_plan("open", "v0.2", cwd=tmp_path)
    assert result.returncode == 2
    assert "Active release v0.1 already exists" in result.stderr
    assert "Close it before opening v0.2" in result.stderr


# ---- T-104 strict phase status validation ------------------------------------

def test_close_rejects_unknown_phase_status(tmp_path):
    planning = _open(tmp_path)
    plan = planning / "releases" / "v0.1" / "PLAN.md"
    text = plan.read_text(encoding="utf-8")
    text = (
        text.replace("## Status\n\nin_progress", "## Status\n\ncomplete")
        .replace("Status:\nin_progress", "Status:\nblocked")
        .replace("Status:\npending", "Status:\ncomplete")
    )
    plan.write_text(text, encoding="utf-8")
    (planning / "releases" / "v0.1" / "SUMMARY.md").write_text(
        "# Summary\n", encoding="utf-8"
    )

    result = run_plan("close", "v0.1", cwd=tmp_path)
    assert result.returncode == 2
    assert "not complete" in result.stderr


def test_close_rejects_missing_phase_status(tmp_path):
    planning = _open(tmp_path)
    plan = planning / "releases" / "v0.1" / "PLAN.md"
    text = plan.read_text(encoding="utf-8")
    text = (
        text.replace("## Status\n\nin_progress", "## Status\n\ncomplete")
        .replace("Status:\nin_progress", "")
        .replace("Status:\npending", "Status:\ncomplete")
    )
    plan.write_text(text, encoding="utf-8")
    (planning / "releases" / "v0.1" / "SUMMARY.md").write_text(
        "# Summary\n", encoding="utf-8"
    )

    result = run_plan("close", "v0.1", cwd=tmp_path)
    assert result.returncode == 2
    assert "not complete" in result.stderr


def test_close_requires_release_complete(tmp_path):
    """Phases all complete but PLAN ## Status not complete -> close fails."""
    planning = _open(tmp_path)
    plan = planning / "releases" / "v0.1" / "PLAN.md"
    text = plan.read_text(encoding="utf-8")
    text = (
        text.replace("Status:\nin_progress", "Status:\ncomplete")
        .replace("Status:\npending", "Status:\ncomplete")
    )
    plan.write_text(text, encoding="utf-8")  # ## Status stays in_progress
    (planning / "releases" / "v0.1" / "SUMMARY.md").write_text(
        "# Summary\n", encoding="utf-8"
    )

    result = run_plan("close", "v0.1", cwd=tmp_path)
    assert result.returncode == 2
    assert "Status" in result.stderr


# ---- T-102 coherent clearing ----------------------------------------------------

def test_close_clears_full_active_context(tmp_path):
    planning = _open(tmp_path)
    _make_closeable(planning)

    result = run_plan("close", "v0.1", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "Active release cleared." in result.stdout

    text = (planning / "INDEX.md").read_text(encoding="utf-8")
    assert "releases/v0.1" not in text
    assert "T-001" not in text
    assert "P1" not in text.split("## Current Phase")[1].split("##")[0]
    assert "none" in text

    doctor = run_plan("doctor", cwd=tmp_path)
    assert doctor.returncode == 0, doctor.stdout


# ---- T-215 canonical empty-release state ---------------------------------------

def test_cleared_index_uses_canonical_empty_state(tmp_path):
    planning = _open(tmp_path)
    _make_closeable(planning)

    result = run_plan("close", "v0.1", cwd=tmp_path)
    assert result.returncode == 0, result.stderr

    text = (planning / "INDEX.md").read_text(encoding="utf-8")
    # One consistent representation — never a mix of empty string,
    # none, None, N/A or "not active".
    assert "## Active Release\n\nnone" in text
    assert "Path:\n\n[none]" in text
    assert "## Current Focus\n\nNone." in text
    assert "## Current Phase\n\nNone." in text
    assert "Open the next release or select new work." in text
    assert "## Current Blockers\n\nNone." in text
    assert "Active Plan:\n[none]" in text
    assert "Active Knowledge:\n[none]" in text
    assert "Recent Log:\n[none]" in text
