# Release Knowledge

## F-001

Title:
Pytest basetemp must live inside the repo on this machine

Scope:
project

Related:
[T-401]

Finding:

`python -m pytest tests/` with the default temp root fails with
`PermissionError [WinError 5]` on `C:\Users\41315\AppData\Local\Temp
\pytest-of-41315`. The suite is run with `--basetemp=.pytest-tmp`
instead.

Source:

Local test run, 2026-09-27.

Impact:

Any future agent running the test suite must use
`python -m pytest tests/ --basetemp=.pytest-tmp` (or another writable
root), or every test errors during tmp_path setup.
