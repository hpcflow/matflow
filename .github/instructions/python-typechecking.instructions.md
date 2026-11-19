---
description: "Use when adding or modifying Python code, including tests. Requires mypy validation before completing changes."
applyTo: "**/*.py"
---

# Python type checking

- Run mypy on new or modified Python files, including tests, before completing a code change.
- Use the configured project environment and existing mypy configuration. For focused validation, run `poetry run mypy <changed-files>` from the repository root.
- Fix type errors introduced by the change with appropriate annotations and narrowing, not blanket ignores or unnecessary casts.
- For changes affecting shared types or APIs, also run the CI command: `poetry run mypy hpcflow`.
- If validation is blocked or pre-existing errors remain, report the exact limitation rather than claiming the type check passed.
