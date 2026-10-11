"""Opt-in smoke tests for the locally built MatFlow/DAMASK image."""

import json
import os
import shutil
import subprocess

import pytest


@pytest.fixture
def combined_image():
    """Select a supplied image without building or pulling it during the test."""
    image = os.environ.get("MATFLOW_TEST_CONTAINER_IMAGE")
    if not image or not shutil.which("docker"):
        pytest.skip("Set MATFLOW_TEST_CONTAINER_IMAGE and install Docker")
    return image


@pytest.mark.integration
def test_combined_container_entrypoints(combined_image):
    """Expose MatFlow by default and preserve the base image's working DAMASK executable."""
    for command, expected in [("--version", "MatFlow"), ("--help", "DAMASK")]:
        entrypoint = [] if command == "--version" else ["--entrypoint", "DAMASK_grid"]
        result = subprocess.run(
            ["docker", "run", "--rm", *entrypoint, combined_image, command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert expected in result.stdout


@pytest.mark.integration
def test_combined_container_wrapper(combined_image):
    """Export a MatFlow-namespaced host wrapper pointing to the combined image."""
    result = subprocess.run(
        ["docker", "run", "--rm", combined_image, "install"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"[string]$Image = '{combined_image}'" in result.stdout
    assert "__APP_NAME_" not in result.stdout
    assert "__MATFLOW_JOBSCRIPT_PATH__" in result.stdout
    assert "[int]$NotebookPort = 8888" in result.stdout


@pytest.mark.integration
def test_combined_container_workflow_persistence(combined_image, tmp_path):
    """Create and reload a workflow using MatFlow and Python 3.13 in a shared host mount."""
    code = """
import json, os, sys
from pathlib import Path
import jupyterlab, ipykernel, ssl, sqlite3, bz2, lzma, ctypes
import damask, damask_parse
import matflow as mf
assert sys.version_info[:2] == (3, 13)
assert sys.executable.startswith('/opt/venv/')
assert sys.base_prefix == '/usr'
assert mf.app.run_time_info.container_image == os.environ['MATFLOW_CONTAINER']
assert Path('/opt/ucx/lib').is_dir()
assert os.environ['OMP_NUM_THREADS'] == '1'
record = Path('/work/workflow.json')
if record.exists():
    data = json.loads(record.read_text())
    assert mf.Workflow(data['path']).id_ == data['id']
else:
    workflow = mf.Workflow.from_template(
        mf.WorkflowTemplate(name='container-check'), path='/work'
    )
    record.write_text(json.dumps({'id': workflow.id_, 'path': workflow.path}))
print('workflow-persistence-ok')
"""
    args = [
        "--mount",
        f"type=bind,source={tmp_path},target=/work",
        "--env",
        "MATFLOW_CONFIG_DIR=/work/config",
        "--env",
        "XDG_CACHE_HOME=/work/cache",
        "--env",
        "XDG_DATA_HOME=/work/data",
        "--entrypoint",
        "python",
    ]
    for _ in range(2):
        result = subprocess.run(
            ["docker", "run", "--rm", *args, combined_image, "-c", code],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "workflow-persistence-ok" in result.stdout
    data = json.loads((tmp_path / "workflow.json").read_text())
    assert (tmp_path / data["path"].removeprefix("/work/")).is_dir()
