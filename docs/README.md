# Docs

## Executive Summary

This folder contains the deeper documentation for the public `pyntlp` package.
Start with the top-level [README](../README.md) for the executive summary and
end-to-end flow, then use these pages when you need implementation detail.

Recommended reading order:

1. [Glossary](glossary.md): defines the modelling and package terms used across
   the documentation.
2. [Assumptions and limitations](assumptions-and-limitations.md): explains what
   the current SSO model does and does not claim.
3. [Usage guide](usage-guide.md): walks through the normal package workflow from
   parameters to validation.
4. [Model overview](model-overview.md): explains the PMA calculation, model
   grain, eligibility metrics, participant cap, missing coverage behaviour, and
   debugging sequence.
5. [API and contracts](api-contracts.md): lists public functions, required
   columns, parameter keys, output columns, and validation report shape.
6. [Troubleshooting](troubleshooting.md): maps common symptoms to likely causes
   and checks.
7. [Development notes](development.md): explains local setup, test commands,
   Spark requirements, documentation expectations, and review checklist.
8. [Repo structure](repo-structure.md): maps the main files and folders to their
   responsibilities.

Use the guide pages when trying to understand the model as a user. Use the API
and development pages when changing code, writing wrappers, or reviewing
behaviour.

The docs intentionally avoid production table names, Databricks widgets, and
environment-specific deployment instructions. Those details belong in wrapper
notebooks or operational documentation outside this reusable package.
