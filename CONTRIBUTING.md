# Contributing to FileMind

Thanks for your interest in improving FileMind.

## Development setup

1. Use Python 3.10 or newer.
2. Create a virtual environment: `python -m venv .venv`.
3. Activate it (`source .venv/bin/activate` on bash/zsh, or `source .venv/bin/activate.fish` on Fish).
4. Install development dependencies: `python -m pip install -e ".[dev]"`.
5. Run the tests: `python -m pytest -v`.

## Before opening a pull request

- Add or update tests for behavior changes.
- Run the full test suite.
- Run `git diff --check`.
- Update README documentation when commands or safety behavior change.
- Never include personal files, virtual environments, credentials, or generated caches.
- Do not weaken file-operation safety to make a test pass.

## Reporting bugs

Include your operating system, Python version, the command you ran, the expected behavior, and the actual error. Do not attach private documents or sensitive file contents.
