# AGENTS.md

## Project Overview

`openwisp-utils` provides shared utilities, QA tooling, test helpers, admin utilities, storage helpers, API utilities, and release tooling used across OpenWISP Python packages.

Core code lives in `openwisp_utils/`:

- `qa.py`, `openwisp-qa-format`, and `openwisp-qa-check` implement formatting and QA tooling.
- `releaser/` contains release and commitizen utilities.
- `api/`, `admin_theme/`, `db/`, `metric_collection/`, `storage.py`, and `utils.py` provide reusable Django and Python helpers.
- Tests live in `openwisp_utils/tests/` and `tests/`.

## Source of Truth

- Use `docs/developer/installation.rst` and `docs/developer/index.rst` for local setup, utilities, and baseline test commands.
- Use `.github/workflows/ci.yml` for CI-tested dependencies, QA/test commands, env vars, and supported Python/Django versions.
- Use GitHub issue/PR templates when asked to open issues or PRs.

Follow the DRY principle: do not duplicate information or code across files.

If instructions conflict, repository config and CI workflows win first, official docs next, and this file is supplemental.

## Development Notes

- Keep changes focused. Avoid unrelated refactors and formatting churn.
- Preserve public APIs, CLI behavior, reusable workflow contracts, migrations, and integration points unless explicitly required.
- Place imports at the top of the file. Only defer imports when necessary (e.g., Django model imports inside functions or methods where the app registry is not yet ready).
- Avoid unnecessary blank lines inside function and method bodies.
- Update docs when behavior, settings, public APIs, setup steps, QA rules, or supported versions change.

## Testing and QA

- Add or update tests for every behavior change.
- For bug fixes, write the regression test first, run it against the unfixed code, confirm it fails for the expected reason, then implement the fix.
- Run `openwisp-qa-format` after editing.
- Run `./run-qa-checks` before considering the change complete. Treat failures as blocking unless confirmed unrelated and reported.
- Use targeted tests while iterating, then run the documented full test command.

## Coverage Notes

- Prefer in-process tests so coverage tools can measure changed code.
- Some tests invoke external commands with `subprocess.run`; `openwisp_utils/releaser/tests/test_commitizen_rules.py` is the clearest example.
- Code reached only through subprocesses is invisible to the parent coverage process. Add direct unit tests when changing that code, following `openwisp_utils/releaser/tests/test_commitizen_unit.py` where applicable.
- When checking coverage for a changed module, use `python -m pytest <test_path> --cov=<dotted.module.path> --cov-report=term-missing`.

## Security and Review Notes

- Watch for unsafe file paths, unsafe subprocess usage, token or secret exposure, and changes that could weaken QA or release safeguards.
- Write comments and docstrings only when they explain why code is shaped a certain way. Put comments before the relevant code block instead of scattering them inside it.

## Troubleshooting

- If setup, QA, or tests fail, check docs first, then compare with CI. If commands diverge, follow CI.
