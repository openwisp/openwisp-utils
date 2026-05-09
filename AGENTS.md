# Agent guidelines for openwisp-utils

Conventions for AI coding agents working in this repo. These sit on
top of the project's `CONTRIBUTING.rst` and the upstream
[OpenWISP contributing guidelines](http://openwisp.io/docs/developer/contributing.html);
read those first — everything below assumes them.

## QA tooling: format and lint before declaring done

The repo ships two scripts you must run before considering a change
complete:

- `openwisp-qa-format` — reformats Python (and adjacent) files in
  place. Run it after editing; do not hand-format.
- `./run-qa-checks` — runs `openwisp-qa-check` with the project's
  linter configuration (CSS, JS, migration paths). Treat any failure
  as blocking, even if the diff looks small.

If `./run-qa-checks` flags something `openwisp-qa-format` didn't fix,
investigate the rule rather than suppressing it.

## Bug fixes start with a failing test

When fixing a bug, write a test that reproduces it **before** writing
the fix. Run the test, confirm it fails for the reported reason, then
implement the fix and confirm the test goes green. This sequence is
what proves the test actually covers the bug — adding the test
afterwards risks writing one that passes against the buggy code too.
The PR description should reflect this order: failing test, then fix.

## Comments and docstrings: explain why, not what

Lean comments and docstrings toward human-level explanation:

- **Why** the code is shaped this way (constraints, trade-offs,
  references to issues or upstream behavior).
- **What problem** it solves at a level a reader would not get from
  the code itself.

Avoid comments that translate code into prose ("increment the
counter", "loop over results") — well-named identifiers already say
what; the reader gains nothing from the translation. If a function
needs a wall of comments to be understood, the function probably
needs a refactor, not more comments.

## Verify subprocess-based tests aren't hiding coverage gaps

Some test suites in this repo invoke external commands via
`subprocess.run` instead of importing the code under test in-process.
The clearest example is `openwisp_utils/releaser/tests/test_commitizen_rules.py`,
which drives the `OpenWispCommitizen` plugin through the `cz` CLI.

Coverage is configured for the parent test process only
(`.coveragerc` does not enable subprocess instrumentation via
`coverage.process_startup()`), so any code reached _only_ through a
subprocess call is invisible to coveralls. The file looks "tested" but
contributes 0% to the coverage report.

When adding a test or modifying code that is currently exercised through
a subprocess, do one of the following:

1. Prefer adding **in-process unit tests** that import the module and
   call its public methods directly. The subprocess test stays as an
   integration check; the unit tests give coverage tooling something to
   measure. See `openwisp_utils/releaser/tests/test_commitizen_unit.py`
   for the established pattern.
2. If in-process testing is impossible (the code only makes sense as a
   CLI invocation), explicitly note the coverage trade-off in the PR
   description so reviewers know not to chase the gap.

Before declaring a test suite complete, run with `--cov` against the
file under test and confirm the coverage number reflects what you
expect:

```bash
python -m pytest <test_path> --cov=<dotted.module.path> --cov-report=term-missing
```

A subprocess-only test will report ~0% with most of the file under
"Missing" — that is the signal to add in-process tests.
