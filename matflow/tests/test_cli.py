from hpcflow import __version__ as hpcflow_version

import matflow


def test_version(cli_runner):
    result = cli_runner(["--version"])
    assert result.output.strip() == f"{matflow.app.name}, version {matflow.app.version}"


def test_hpcflow_version(cli_runner):
    result = cli_runner(["--hpcflow-version"])
    assert result.output.strip() == f"hpcFlow, version {hpcflow_version}"
