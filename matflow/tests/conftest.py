"""
Configuration and standard fixtures for PyTest.
"""
import pytest
import matflow as mf


def pytest_addoption(parser):
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run integration-like workflow submission tests",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration-like workflow submission test to run",
    )
    mf.run_time_info.in_pytest = True


def pytest_collection_modifyitems(config, items):
    if config.getoption("--integration"):
        # --integration in CLI: only run these tests
        for item in items:
            if "integration" not in item.keywords:
                item.add_marker(
                    pytest.mark.skip(reason="remove --integration option to run")
                )
    else:
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(
                    pytest.mark.skip(reason="add --integration option to run")
                )


def pytest_unconfigure(config):
    mf.run_time_info.in_pytest = False


@pytest.fixture
def null_config(tmp_path):
    if not mf.is_config_loaded:
        mf.load_config(config_dir=tmp_path)
    mf.run_time_info.in_pytest = True


@pytest.fixture
def new_null_config(tmp_path):
    mf.load_config(config_dir=tmp_path)
    mf.load_template_components(warn=False)
    mf.run_time_info.in_pytest = True
