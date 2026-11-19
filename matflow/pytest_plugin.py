"""Pytest plugin for test CLI options.

Note this was separated from `conftest.py` due to an issue with running tests from the
single-file Pyinstaller-built executable on Windows, where it would seemingly be invoked
twice (on GitHub actions at least), resulting in `addoption` failing, since the option
already existed.

If running tests via `python -m pytest` (instead of via the app `test` command), this
plugin module must be provided as follows: `python -m pytest -p matflow.pytest_plugin`

"""

import pytest
import matflow as mf


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--unit",
        action="store_true",
        default=False,
        help="run unit tests",
    )
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run integration tests",
    )
    parser.addoption(
        "--demo-workflows",
        action="store_true",
        default=False,
        help="run demo workflow tests",
    )
    parser.addoption(
        "--repeat",
        action="store",
        default=1,
        type=int,
        help="number of times to repeat each test",
    )
    parser.addoption(
        "--configure-python-env",
        action="store_true",
        default=False,
        help=(
            "Configure the app Python environment using the currently activate Python "
            "virtual (or conda) environment. This is necessary for running integration "
            "tests that use `script_data_in/out: direct`."
        ),
    )
    parser.addoption(
        "--with-env-source",
        action="store",
        help=(
            "Provide the path to an environment sources file to load into the app config "
            "during testing."
        ),
    )
    parser.addoption(
        "--fig-dir",
        action="store",
        default=None,
        help="Directory where matplotlib figures are saved",
    )
    parser.addoption(
        "--save-reference",
        action="store_true",
        default=False,
        help="Regenerate and overwrite reference data from demo workflows.",
    )


def pytest_configure(config: pytest.Config):
    config.addinivalue_line("markers", "unit: mark a unit test")
    config.addinivalue_line("markers", "integration: mark an integration test")
    config.addinivalue_line("markers", "demo_workflows: mark a demo workflow test")
    mf.run_time_info.in_pytest = True
