# Development Notes

## Executive Summary

This page explains how to work on `pyntlp` locally without changing its public
contract accidentally.

The development rule of thumb is simple: package code should stay reusable,
Spark-native, and table-agnostic. Databricks notebooks, source table names,
widgets, dashboard writes, and environment-specific orchestration belong outside
the package.

## Runtime Targets

The package targets:

- Python `3.12`
- PySpark `4.x`

Spark-backed tests require Java because PySpark starts a local JVM. Pure-Python
tests can still run without Java.

## Local Setup

From the repository root:

```bash
pip install -e .[dev]
```

This installs:

- the package in editable mode
- `pytest` for the test suite
- runtime dependencies including `PyYAML` and `pyspark`

Editable install is useful because local source edits are immediately visible to
test runs and notebook wrappers that import the local package.

## Verification Commands

Run the full test suite:

```bash
python -m pytest
```

Check Python syntax for package modules:

```bash
python -m compileall src tests
```

Check whitespace and patch hygiene before committing:

```bash
git diff --check
```

Use all three commands for behaviour changes. For Markdown-only changes,
`git diff --check` is usually enough unless the documentation change is tied to
an unverified code change.

## Test Coverage

The tests cover:

- import smoke checks
- parameter loading and validation
- interval and window boundary logic
- `lga_segment` eligibility metrics
- duplicate baseline-key detection
- missing metrics coverage producing zero deltas
- participant-cap behaviour across one or more `fc_object_id` values
- model energy neutrality
- a small end-to-end Spark flow

When changing model logic, add or update tests at the same grain as the changed
behaviour. For example, cap changes should be tested across multiple
`fc_object_id` values that share a `lga_segment`, because that is where
over-counting risk appears.

## Spark Test Requirement

Spark-backed tests need a working Java runtime in the local environment.

If Java is not available:

- pure-Python tests still run
- Spark tests are skipped

This is expected behaviour on machines without `JAVA_HOME` or `java` on the
path. A skipped Spark test is not the same as a passed Spark test, so any logic
change that depends on Spark transformations should eventually be run in an
environment with Java.

## Packaging

The package uses `setuptools` with `pyproject.toml`.

Important packaging details:

- source layout uses `src/`
- package name is `pyntlp`
- YAML resources are shipped from `src/pyntlp/resources/`
- public exports are controlled through `src/pyntlp/__init__.py`

Keep package resources small and generic. Production configuration files,
secrets, table names, and one-off notebooks should not be added to the package
resource directory.

## Documentation Expectations

When public behaviour changes, update:

- the top-level `README.md`
- the relevant `docs/` page
- tests that cover the changed behaviour
- `CHANGELOG.md` if the change is release-facing

Documentation should explain:

- what the section of the model does
- what inputs it expects
- what output grain it returns
- which assumptions affect the result
- what to inspect when debugging

Keep documentation public-facing and generic. Organisation-specific notebooks,
tables, catalogs, deployment instructions, and dashboard targets belong in the
wrapper repository or deployment documentation, not in `pyntlp`.

## Review Checklist

Before treating a change as ready, check:

- public function signatures are unchanged unless the release explicitly allows
  a breaking change
- output column order still matches the public contract
- `customer_type` remains a carried attribute, not a model dimension
- cap logic still applies once per `lga_segment` population grain
- missing metrics coverage still preserves output rows with zero deltas
- validation still reports energy-neutrality failures
- docs and tests describe the same behaviour
