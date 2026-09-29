"""T-311 Claude plugin packaging tests.

The plugin payload at plugins/planscope/skills/planscope/ is a generated
distribution artifact of the canonical .agents/skills/planscope/ source;
these tests enforce the canonical-source invariant byte for byte.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

from conftest import REPO_ROOT, SKILL_DIR

INSTALL_PY = REPO_ROOT / "install.py"
MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"
PLUGIN_ROOT = REPO_ROOT / "plugins" / "planscope"
MANIFEST = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
PLUGIN_SKILL = PLUGIN_ROOT / "skills" / "planscope"


def _payload_files(root: Path):
    return sorted(
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    )


def _run_install(*args, cwd):
    # Always invoke the install.py that lives in *cwd*'s repo — the real
    # repository's copy would target the real repository regardless of cwd.
    script = Path(cwd) / "install.py"
    if not script.is_file():
        script = INSTALL_PY
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


# ---- manifest / marketplace ---------------------------------------------------

def test_plugin_manifest_exists():
    assert MANIFEST.is_file()


def test_plugin_manifest_name():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["name"] == "planscope"


def test_plugin_manifest_version():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["version"] == "1.1.2"


def test_marketplace_points_to_plugin_root():
    data = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    plugins = {p["name"]: p for p in data["plugins"]}
    assert plugins["planscope"]["source"] == "./plugins/planscope"


# ---- canonical source invariant ------------------------------------------------

def test_plugin_skill_exists():
    assert (PLUGIN_SKILL / "SKILL.md").is_file()


def test_plugin_skill_matches_canonical():
    assert (SKILL_DIR / "SKILL.md").read_bytes() == (PLUGIN_SKILL / "SKILL.md").read_bytes()


def test_plugin_templates_match_canonical():
    for name in ("INDEX.md", "PROJECT.md", "ROADMAP.md", "PLAN.md",
                 "KNOWLEDGE.md", "LOG.md", "SUMMARY.md"):
        assert (PLUGIN_SKILL / "templates" / name).read_bytes() == \
            (SKILL_DIR / "templates" / name).read_bytes(), name


def test_plugin_scripts_match_canonical():
    assert (PLUGIN_SKILL / "scripts" / "plan.py").read_bytes() == \
        (SKILL_DIR / "scripts" / "plan.py").read_bytes()
    for name in ("__init__.py", "commands.py", "core.py"):
        assert (PLUGIN_SKILL / "scripts" / "spwf" / name).read_bytes() == \
            (SKILL_DIR / "scripts" / "spwf" / name).read_bytes(), name


def test_plugin_payload_file_set_matches_canonical():
    assert _payload_files(PLUGIN_SKILL) == _payload_files(SKILL_DIR)


# ---- build / drift commands (isolated fake repo) --------------------------------

def _fake_repo(tmp_path):
    repo = tmp_path / "fake-repo"
    src = repo / ".agents" / "skills" / "planscope"
    (src / "templates").mkdir(parents=True)
    (src / "SKILL.md").write_text("# canonical skill\n", encoding="utf-8")
    (src / "templates" / "INDEX.md").write_text("# index template\n", encoding="utf-8")
    shutil.copyfile(INSTALL_PY, repo / "install.py")
    return repo, src


def test_build_plugin_generates_payload(tmp_path):
    repo, src = _fake_repo(tmp_path)
    result = _run_install("--build-plugin", cwd=repo)
    assert result.returncode == 0, result.stderr
    payload = repo / "plugins" / "planscope" / "skills" / "planscope"
    assert (payload / "SKILL.md").read_bytes() == (src / "SKILL.md").read_bytes()
    assert (payload / "templates" / "INDEX.md").read_bytes() == \
        (src / "templates" / "INDEX.md").read_bytes()
    # No transient files leak into the distribution artifact.
    assert not list(payload.rglob("__pycache__"))
    assert not list(payload.rglob("*.pyc"))

    check = _run_install("--check-plugin", cwd=repo)
    assert check.returncode == 0, check.stdout
    assert "PLUGIN IN SYNC" in check.stdout


def test_check_plugin_detects_drift(tmp_path):
    repo, _ = _fake_repo(tmp_path)
    assert _run_install("--build-plugin", cwd=repo).returncode == 0
    payload = repo / "plugins" / "planscope" / "skills" / "planscope"
    (payload / "SKILL.md").write_text("drifted\n", encoding="utf-8")
    check = _run_install("--check-plugin", cwd=repo)
    assert check.returncode == 1
    assert "PLUGIN DRIFTED" in check.stdout


def test_check_plugin_reports_missing_payload(tmp_path):
    repo, _ = _fake_repo(tmp_path)
    check = _run_install("--check-plugin", cwd=repo)
    assert check.returncode == 1
    assert "PLUGIN DRIFTED" in check.stdout


def test_repo_plugin_payload_is_in_sync():
    """Release gate: the committed payload must match the canonical source."""
    check = _run_install("--check-plugin", cwd=REPO_ROOT)
    assert check.returncode == 0, check.stdout
    assert "PLUGIN IN SYNC" in check.stdout
