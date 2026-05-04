# Docs

## Executive Summary

This folder contains the deeper documentation for the public `pyntlp` package.
Start with the top-level [README](../README.md) for the executive summary and
end-to-end flow, then use these pages when you need implementation detail.

Available pages:

- [Model overview](model-overview.md): explains the PMA calculation, model
  grain, eligibility metrics, participant cap, missing coverage behaviour, and
  debugging sequence.
- [API and contracts](api-contracts.md): lists public functions, required
  columns, parameter keys, output columns, and validation report shape.
- [Development notes](development.md): explains local setup, test commands,
  Spark requirements, documentation expectations, and review checklist.
- [Repo structure](repo-structure.md): maps the main files and folders to their
  responsibilities.

The docs intentionally avoid production table names, Databricks widgets, and
environment-specific deployment instructions. Those details belong in wrapper
notebooks or operational documentation outside this reusable package.
