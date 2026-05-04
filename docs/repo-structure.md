# Repo Structure

## Executive Summary

This page explains the purpose of the main files and folders in the repository.
`pyntlp` uses a `src/` package layout so reusable model code stays separate from
tests, planning material, and documentation.

There is no active Databricks notebook wrapper in this package. Production or
project-specific notebooks should live outside `pyntlp` and import the package
API instead of embedding package logic.

## Top Level

- `README.md`: public landing page for the repository.
- `CHANGELOG.md`: release-facing summary of notable changes.
- `pyproject.toml`: package metadata, dependencies, packaging configuration, and pytest settings.
- `LICENSE`: repository license.
- `planning/`: source planning documents used to define the public package scope and build sequence.
- `docs/`: deeper repository and implementation documentation.
- `src/`: installable Python package source.
- `tests/`: unit and integration-style tests.

## Documentation

The docs folder is the technical manual for the package.

- `README.md`: documentation index and recommended reading order.
- `glossary.md`: definitions for tariff, load-profile, and package terms.
- `assumptions-and-limitations.md`: current model scope, assumptions, and interpretation limits.
- `usage-guide.md`: practical workflow for calling the package from a job, notebook, or pipeline.
- `model-overview.md`: detailed explanation of the SSO calculation and modelling grain.
- `api-contracts.md`: public function, input, output, and validation contracts.
- `troubleshooting.md`: common symptoms, likely causes, and checks.
- `development.md`: setup, tests, review checklist, and contribution notes.
- `repo-structure.md`: this repository map.

## Package Source

The package code lives under `src/pyntlp/`.

- `__init__.py`: public exports for the package API.
- `params.py`: YAML and dictionary parameter loading plus contract validation.
- `windows.py`: interval-window utilities, including start-inclusive and end-exclusive window mapping.
- `metrics.py`: lga_segment-level eligibility calculations from normalised customer inputs.
- `model.py`: PMA SSO computation logic that turns baseline demand and lga_segment metrics into interval deltas.
- `validation.py`: output schema and energy-neutrality checks.
- `schema.py`: shared schema definitions and canonical column lists.
- `utils.py`: shared helper functions used across modules.

## Package Resources

Resources live under `src/pyntlp/resources/`.

- `pyntlp_template.yaml`: public example YAML template for the model contract.
- `__init__.py`: marks the resources directory as a package so the template can be shipped with the distribution.

## Tests

Tests live under `tests/`.

- `conftest.py`: pytest fixtures and Spark-session setup.
- `test_import_smoke.py`: import-level smoke check.
- `test_params.py`: parameter loading and validation tests.
- `test_windows.py`: interval and window boundary tests.
- `test_metrics.py`: eligibility-rate tests.
- `test_model.py`: model behaviour tests for neutrality, caps, and ineligible segments.
- `test_integration.py`: end-to-end Spark flow using small normalised sample DataFrames.

## Planning Documents

The `planning/` folder captures the original product framing for the public MVP.

- `SSO_PRD_public_v0.1.md`: product requirements for the public package.
- `pyntlp_build_plan_v0.1.md`: chunked build plan used to implement the MVP.
