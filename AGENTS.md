# Repository Guidelines

## Project Structure & Module Organization
- CLI entrypoint in `inv_scr/cli.py` with operations mapped in `OPERATIONS`.
- Shared helpers in `inv_scr/core/`; per-resource logic in `inv_scr/operations/` (each exposes `add_operation_args` + `run`); legacy reference scripts in `legacy_operations/`.
- Tests live in `tests/` (`test_cli.py`, `test_operations.py`, `test_core.py`, `test_integration.py`, `test_argument_parsing.py`); demo data and coverage artifacts in `demo_shared_test_data.py` and `htmlcov/`.
- Build/test helpers at repo root: `Makefile`, `requirements.txt`, `validate_tests.py`, `run_enhanced_tests.py`, and testing docs.

## Build, Test, and Development Commands
- `make install` or `pip install -e .` sets up dev mode; `inv_scr list` smoke-tests the entrypoint.
- Inspect arguments with `inv_scr <operation> --help`.
- Core tests: `make unittest`; fast check: `make test-quick`; coverage: `make coverage`; clean artifacts: `make clean`.
- Enhanced flows: `make test-enhanced-validate`, `make test-enhanced-quick`, `make test-enhanced-all` (run when touching AWS-facing logic).
- Alternative runner: `python3 -m unittest discover tests -v` if `make` is unavailable.

## Coding Style & Naming Conventions
- Python 3, 4-space indentation; prefer type hints and small, testable functions.
- Use `snake_case` for modules/functions/vars, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- New operations belong in `inv_scr/operations/<resource>.py`; implement `add_operation_args` + `run` and register in `OPERATIONS` in `inv_scr/cli.py`.
- Reuse `inv_scr/core/ArgumentsClass.py` helpers; keep logging through the standard `logging` module and match existing formatter.

## Testing Guidelines
- Place tests in `tests/test_<area>.py`; name methods `test_<behavior>`.
- Prefer deterministic fixtures and shared demo data over live AWS calls; keep mock outputs current.
- Run `make test-quick` before pushing, `make unittest` (plus relevant enhanced targets) before opening a PR; maintain coverage when adjusting CLI defaults or output.

## Commit & Pull Request Guidelines
- Use imperative, descriptive commit messages; reference issue IDs when available.
- PR checklist: summary of changes, operations affected, tests run (commands + notable output), and any doc/config updates.
- For CLI behavior changes, include example invocations and expected output shape; screenshots only when formatting is the focus.

## Security & Configuration Tips
- Never commit AWS credentials, account numbers, or customer data; rely on AWS profiles/env vars and keep local configs ignored.
- Redact ARNs, account IDs, and tokens in logs/fixtures; prefer mocked inventories over real exports.
