
# Repository Guidelines

## Repository Context Guidelines
- Only read files that are directly relevant to the current task
- Ask the user which specific files or directories to focus on before reading
- Use `glob` or `grep` to discover relevant files instead of reading everything
- Prioritize reading only the files mentioned in the user's question
- Avoid reading the entire repository upfront unless explicitly requested

## Files to Ignore
Do not read the following unless specifically requested:
- Documentation files (*.md, docs/)
- Test files (*test*, *spec*)
- Build artifacts (dist/, build/, node_modules/)
- Configuration files unless relevant to the task

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
- Read-only functionality should correlate to parameters that are prepended with a dash ("-"), while functionality that might be intrusive or make changes should be prepended with a plus ("+").
- All functions must include docstrings with a brief description, `Args:` section documenting each parameter, and `Returns:` section describing the return value structure.

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

## Context Loading Strategy
Use a lazy-loading approach:
- Start by asking the user which specific files or areas are relevant
- Use search tools (grep, glob) to locate relevant code
- Read only the specific files needed for the immediate task
- Request additional context only when needed to complete the task

## Task-Based Context
- For bug fixes: Only read the file with the bug and its direct dependencies
- For new features: Only read related modules and interfaces
- For documentation: Only read the specific code being documented
- Always prefer targeted file reads over broad repository scans
