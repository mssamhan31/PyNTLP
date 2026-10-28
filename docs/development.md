# Development

Package code stays reusable, Spark-native and table-agnostic. Databricks notebooks, source table
names, widgets, dashboard writes and environment-specific orchestration belong outside the package.

## Environment

Python 3.12 and PySpark 4.x; Spark-backed tests need Java 17.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
```

## Verification

```powershell
python -m pytest
python -m compileall src tests
git diff --check
```

Use all three for behaviour changes. For Markdown-only changes, `git diff --check` and
`mkdocs build --strict` are enough.

/// details | Show details
    type: more

## What the editable install gives you

The package in editable mode, so local source edits are immediately visible to tests and notebook
wrappers; `pytest`; and the runtime dependencies, including `PyYAML` and `pyspark`.

## Test coverage

The tests cover import smoke checks, parameter loading and validation, interval and window boundary
logic, `lga_segment` eligibility metrics, duplicate baseline-key detection, missing metrics
coverage producing zero deltas, participant-cap behaviour across one or more `fc_object_id` values,
model energy neutrality, and a small end-to-end Spark flow.

When changing model logic, add or update tests at the same grain as the changed behaviour. Cap
changes, for example, should be tested across several `fc_object_id` values that share an
`lga_segment`, because that is where over-counting risk appears.

## Spark tests need Java

PySpark starts a local JVM. Without Java, pure-Python tests still run and Spark tests are skipped;
that is expected on machines without `JAVA_HOME` or `java` on the path. A skipped Spark test is not
a passed one, so any change that depends on Spark transformations must eventually run in an
environment with Java.

## Packaging

The package uses `setuptools` with `pyproject.toml`: a `src/` layout, the package name `pyntlp`,
YAML resources shipped from `src/pyntlp/resources/`, and public exports controlled through
`src/pyntlp/__init__.py`. Keep package resources small and generic; production configuration
files, secrets, table names and one-off notebooks do not belong in the resource directory.

## Documentation

```powershell
python -m pip install "mkdocs<2" "mkdocs-material<10"
mkdocs serve -a 127.0.0.1:8000     # local preview at http://127.0.0.1:8000/PyNTLP/
mkdocs build --strict
```

`docs-pages.yml` builds the site on every pull request to `main` and publishes it to GitHub Pages
at <https://mssamhan31.github.io/PyNTLP/> when `main` changes. It installs only MkDocs and the
Material theme, not the package, so the build never pulls in pyspark.

The Home page (`docs/index.md`) is written for a general reader as raw HTML; its styles live in
`docs/assets/css/site.css`. Every documentation page shows what an analyst running the package needs
first and puts the rest in one `/// details | Show details` block (type `more`) at its foot. Pages
left out of the menu are listed under `not_in_nav` in `mkdocs.yml` and reached from the Overview's
full page list.

When public behaviour changes, update the top-level `README.md`, the relevant `docs/` page, the
tests that cover the change, and `CHANGELOG.md` if the change is release-facing. Documentation
should say what a part of the model does, what inputs it expects, what output grain it returns,
which assumptions affect the result and what to inspect when debugging. Keep it public-facing and
generic: organisation-specific notebooks, tables, catalogs, deployment instructions and dashboard
targets belong in the wrapper repository or deployment documentation.

## Review checklist

Before treating a change as ready, check that:

- public function signatures are unchanged, unless the release explicitly allows a breaking change
- the output column order still matches the public contract
- `customer_type` remains a carried attribute, not a model dimension
- cap logic still applies once per `lga_segment` population grain
- missing metrics coverage still keeps output rows with zero deltas
- validation still reports energy-neutrality failures
- the documentation and the tests describe the same behaviour

///
