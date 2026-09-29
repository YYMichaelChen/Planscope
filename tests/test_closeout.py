"""Tests for the v1.1.2 governance boundary closeout gate.

Normal `plan close` requires a `## Closeout` checklist in PLAN.md with
every canonical item present and checked; `plan doctor` validates the
closeout schema structurally.
"""

from conftest import init_project, run_plan


def _open(tmp_path):
    planning = init_project(tmp_path)
    run_plan("open", "v0.1", cwd=tmp_path)
    return planning, planning / "releases" / "v0.1"


def _complete_plan(release):
    """Mark phases and release Status complete and create SUMMARY.md."""
    plan = release / "PLAN.md"
    text = plan.read_text(encoding="utf-8")
    text = (
        text.replace("## Status\n\nin_progress", "## Status\n\ncomplete")
        .replace("Status:\nin_progress", "Status:\ncomplete")
        .replace("Status:\npending", "Status:\ncomplete")
    )
    plan.write_text(text, encoding="utf-8")
    (release / "SUMMARY.md").write_text("# Summary\n", encoding="utf-8")
    return plan


def _check_closeout(plan):
    text = plan.read_text(encoding="utf-8")
    plan.write_text(text.replace("- [ ]", "- [x]"), encoding="utf-8")


def _strip_closeout_section(plan):
    text = plan.read_text(encoding="utf-8")
    plan.write_text(text[: text.index("## Closeout")], encoding="utf-8")


# ---- close gate ---------------------------------------------------------------

def test_open_template_includes_closeout(tmp_path):
    _, release = _open(tmp_path)
    text = (release / "PLAN.md").read_text(encoding="utf-8")
    assert "## Closeout" in text
    assert "- [ ] Acceptance criteria verified" in text
    assert "- [ ] SUMMARY.md created" in text


def test_close_blocked_by_unchecked_closeout(tmp_path):
    _, release = _open(tmp_path)
    _complete_plan(release)
    result = run_plan("close", "v0.1", cwd=tmp_path)
    assert result.returncode == 2
    assert "closeout is incomplete" in result.stderr
    assert "Durable findings classified" in result.stderr
    assert release.is_dir()


def test_close_blocked_by_missing_closeout_section(tmp_path):
    """Legacy pre-v1.1.2 plan: no Closeout section at all."""
    _, release = _open(tmp_path)
    plan = _complete_plan(release)
    _strip_closeout_section(plan)
    result = run_plan("close", "v0.1", cwd=tmp_path)
    assert result.returncode == 2
    assert "no '## Closeout' checklist" in result.stderr
    assert release.is_dir()


def test_close_blocked_by_missing_closeout_item(tmp_path):
    """A required canonical item dropped from the section counts as unchecked."""
    _, release = _open(tmp_path)
    plan = _complete_plan(release)
    text = plan.read_text(encoding="utf-8")
    text = text.replace("- [ ] ROADMAP.md updated\n", "")
    plan.write_text(text, encoding="utf-8")
    _check_closeout(plan)
    result = run_plan("close", "v0.1", cwd=tmp_path)
    assert result.returncode == 2
    assert "closeout is incomplete" in result.stderr
    assert "ROADMAP.md updated" in result.stderr
    assert release.is_dir()


def test_close_succeeds_with_complete_closeout(tmp_path):
    planning, release = _open(tmp_path)
    plan = _complete_plan(release)
    _check_closeout(plan)
    result = run_plan("close", "v0.1", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert not release.exists()
    assert (planning / "archive" / "v0.1").is_dir()


def test_force_close_bypasses_closeout(tmp_path):
    planning, release = _open(tmp_path)
    (release / "SUMMARY.md").write_text("# Summary\n", encoding="utf-8")
    result = run_plan("close", "v0.1", "--force", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert not release.exists()
    assert (planning / "archive" / "v0.1").is_dir()


# ---- doctor closeout schema ----------------------------------------------------

def test_doctor_fails_complete_release_with_unchecked_closeout(tmp_path):
    _, release = _open(tmp_path)
    _complete_plan(release)
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 1
    assert "closeout items are unchecked" in result.stdout


def test_doctor_fails_missing_closeout_items(tmp_path):
    _, release = _open(tmp_path)
    plan = release / "PLAN.md"
    text = plan.read_text(encoding="utf-8")
    text = text.replace("- [ ] Acceptance criteria verified\n", "")
    plan.write_text(text, encoding="utf-8")
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 1
    assert "Closeout missing required items" in result.stdout
    assert "Acceptance criteria verified" in result.stdout


def test_doctor_warns_missing_closeout_section(tmp_path):
    """Legacy plans without Closeout warn but do not fail doctor."""
    _, release = _open(tmp_path)
    _strip_closeout_section(release / "PLAN.md")
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 0, result.stdout
    assert "WARN" in result.stdout
    assert "Closeout" in result.stdout


def test_doctor_ok_closeout_complete(tmp_path):
    _, release = _open(tmp_path)
    plan = _complete_plan(release)
    _check_closeout(plan)
    result = run_plan("doctor", cwd=tmp_path)
    assert result.returncode == 0, result.stdout
    assert "closeout checklist complete" in result.stdout
