# File formatting

Use LF (`\n`) line endings, not CRLF (`\r\n`), in every text file you create,
including on Windows.

# Testing

When running pytest directly, always load the project's pytest plugin:

```console
python -m pytest -p matflow.pytest_plugin matflow/tests/unit/test_cli.py -q
```

Use the configured Python interpreter and select the tests relevant to the change.
The plugin registers options required by the test fixtures, including `--slurm`
and `--repeat`. Without it, collection fails. The `matflow test` command loads
the plugin automatically.

When running integration tests, always pass `--configure-python-env` to configure
the matflow Python environment using the active Python environment:

```console
matflow test --integration --configure-python-env
```

When invoking pytest directly, include both `-p matflow.pytest_plugin` and
`--configure-python-env`.

Before running integration tests, read
`.github/instructions/local-testing.instructions.md` if it exists for
machine-specific test setup. This optional file is local and must not be committed.
