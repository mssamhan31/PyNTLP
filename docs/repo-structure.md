# Repo structure

The repository uses a `src/` layout, so the reusable package stays separate from its tests, its
documentation and the research code for papers.

| path | what it holds |
|---|---|
| `src/pyntlp/` | the installable package |
| `src/pyntlp/resources/pyntlp_template.yaml` | the public parameter template |
| `tests/` | unit and integration tests |
| `docs/` | this documentation site's pages |
| `mkdocs.yml` | the site's configuration |
| `.github/workflows/` | continuous integration (`ci.yml`) and the site build (`docs-pages.yml`) |
| `publication/` | research code and artefacts for papers, not imported by the package |
| `README.md`, `CHANGELOG.md`, `CITATION.cff`, `LICENSE` | the repository's landing page, changes, citation and licence |

/// details | Show details
    type: more

## Top level

- `README.md`: the public landing page of the repository.
- `CHANGELOG.md`: release-facing summary of notable changes.
- `CITATION.cff` and `.zenodo.json`: citation and archive metadata.
- `pyproject.toml`: package metadata, dependencies, packaging configuration and pytest settings.
- `LICENSE`: the MIT licence.
- `mkdocs.yml`: the documentation site's configuration.
- `planning/`: the planning documents that defined the public package scope and build sequence.
- `docs/`: the documentation site's pages.
- `src/`: the installable Python package.
- `tests/`: unit and integration-style tests.
- `publication/`: standalone research code and artefacts for papers. Not imported by the package
  and not covered by the package test suite; each subfolder has its own README and dependencies.

There is no Databricks notebook wrapper in this repository. Production or project-specific
notebooks live outside `pyntlp` and import the package API instead of embedding package logic.

## Documentation site

- `docs/index.md`: the Home page, written for a general reader as raw HTML.
- `docs/assets/css/site.css`: the site's palette, type and Home page components.
- `docs/overview.md`: the Documentation landing page and the full page list.
- `docs/usage-guide.md`: the workflow for calling the package from a job, notebook or pipeline.
- `docs/model-overview.md`: the SSO calculation and its modelling grain.
- `docs/api-contracts.md`: public function, input, output and validation contracts.
- `docs/troubleshooting.md`: common symptoms, likely causes and checks.
- `docs/papers.md`: the papers and how to cite the software.
- `docs/assumptions-and-limitations.md`: model scope, assumptions and interpretation limits.
- `docs/glossary.md`: tariff, load-profile and package terms.
- `docs/development.md`: setup, tests, documentation and review checklist.
- `docs/repo-structure.md`: this repository map.
- `docs/aqf.md`: the separate AQF study.

## Package source

The package code lives under `src/pyntlp/`.

- `__init__.py`: the public exports.
- `params.py`: YAML and dictionary parameter loading plus contract validation.
- `windows.py`: interval-window utilities, including start-inclusive and end-exclusive window mapping.
- `metrics.py`: `lga_segment`-level eligibility calculations from normalised customer inputs.
- `model.py`: the PMA SSO computation that turns baseline demand and segment metrics into interval deltas.
- `validation.py`: output schema and energy-neutrality checks.
- `schema.py`: shared schema definitions and canonical column lists.
- `utils.py`: shared helper functions.

## Package resources

Resources live under `src/pyntlp/resources/`.

- `pyntlp_template.yaml`: the public example template for the parameter contract.
- `__init__.py`: marks the resources directory as a package so the template ships with the
  distribution.

## Tests

Tests live under `tests/`.

- `conftest.py`: pytest fixtures and Spark-session setup.
- `test_import_smoke.py`: import-level smoke check.
- `test_params.py`: parameter loading and validation tests.
- `test_windows.py`: interval and window boundary tests.
- `test_metrics.py`: eligibility-rate tests.
- `test_model.py`: model behaviour tests for neutrality, caps and ineligible segments.
- `test_integration.py`: an end-to-end Spark flow on small normalised sample DataFrames.

## Research code

- `publication/1_conference/`: the code, data and figures of the AQF conference paper, a separate
  study (see [AQF](aqf.md)).

## Planning documents

The `planning/` folder holds the original product framing for the public MVP.

- `SSO_PRD_public_v0.1.md`: product requirements for the public package.
- `pyntlp_build_plan_v0.1.md`: the chunked build plan used to implement the MVP.

///
