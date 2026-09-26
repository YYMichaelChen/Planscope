"""T-106 collision-safe LOG rotation tests."""

from conftest import init_project, run_plan


def _oversized_log(tmp_path, marker):
    planning = init_project(tmp_path)
    run_plan("open", "v0.1", cwd=tmp_path)
    log = planning / "releases" / "v0.1" / "LOG.md"
    header = "# Work Log\n\n## Current State\n\nPhase:\nP1\n\nTask:\nT-001\n\nNext:\nnothing\n\nBlockers:\nNone.\n"
    activity = "\n## Recent Activity\n\n" + "\n".join(
        f"{marker} entry {i}" for i in range(300)
    )
    log.write_text(header + activity, encoding="utf-8")
    return planning, log


def test_multiple_log_rotations_do_not_overwrite(tmp_path):
    planning, log = _oversized_log(tmp_path, "first")

    first = run_plan("compact", cwd=tmp_path)
    assert first.returncode == 0
    archives = sorted((planning / "archive" / "logs").glob("v0.1-LOG-*.md"))
    assert len(archives) == 1
    first_archive = archives[0]
    assert "first entry 0" in first_archive.read_text(encoding="utf-8")

    # Rotate again the same day: the log is oversized again because the
    # rotation keeps a tail, so grow it back past the hard limit.
    activity = "\n".join(f"second entry {i}" for i in range(300))
    text = log.read_text(encoding="utf-8")
    log.write_text(text + "\n" + activity, encoding="utf-8")

    second = run_plan("compact", cwd=tmp_path)
    assert second.returncode == 0
    archives = sorted((planning / "archive" / "logs").glob("v0.1-LOG-*.md"))
    assert len(archives) == 2
    assert first_archive in archives  # original archive untouched
    names = [a.name for a in archives]
    assert len(set(names)) == 2  # collision-safe, distinct names
    assert all("second entry 299" not in a.read_text(encoding="utf-8") or a != first_archive
               for a in archives)
    second_archive = [a for a in archives if a != first_archive][0]
    assert "second entry 299" in second_archive.read_text(encoding="utf-8")
    assert "first entry 0" in first_archive.read_text(encoding="utf-8")
