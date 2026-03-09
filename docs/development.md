# Development Notes

This page explains how to work on the `pyntlp` repository locally.

## Runtime Targets

- Python `3.12`
- PySpark `4.x`

## Local Setup

From the repository root:

```bash
pip install -e .[dev]
```

This installs:

- the package in editable mode
- `pytest` for the test suite
- package runtime dependencies including `PyYAML` and `pyspark`

## Tests

Run all tests with:

```bash
pytest
```

Test coverage currently includes:

- import smoke checks
- parameter validation
- interval window logic
- segment eligibility
- model neutrality and cap behaviour
- small Spark integration flow

## Spark Test Requirement

Spark-backed tests need a working Java runtime in the local environment.

If Java is not available:

- pure-Python tests still run
- Spark tests are skipped

This is expected behaviour on machines without `JAVA_HOME` or `java` on the path.

## Packaging

The package uses `setuptools` with `pyproject.toml`.

Important packaging details:

- source layout uses `src/`
- package name is `pyntlp`
- YAML resources are shipped from `src/pyntlp/resources/`

## Documentation Expectations

When public behaviour changes, update:

- the top-level `README.md`
- the relevant `docs/` page
- tests that cover the changed behaviour

Keep documentation public-facing and generic. Organisation-specific notebooks, tables, and deployment instructions belong outside this repository.
