# pyntlp

`pyntlp` is a public Spark-native Python package for converting an SSO policy definition into an additive interval PMA delta profile, `pma_sso_mw`.

## Context

This repository contains the reusable modelling package only. It is intended for workflows where a notebook or job reads organisation-specific source tables, normalises them into the package contract, runs the model, and then handles storage outside the package.

The package boundary is deliberate:

- `pyntlp` owns modelling logic, Spark DataFrame APIs, parameter validation, and documentation.
- `pyntlp` does not own organisation-specific table names, Databricks paths, secrets, or write targets.

## Tool Objective

The tool objective is to take:

- normalised Spark DataFrames for baseline profiles, segment attributes, and smart-meter eligibility
- a YAML parameter set with `constants` and `parameters`

and return:

- a deterministic Spark DataFrame with one row per baseline input row
- an additive interval delta column, `pma_sso_mw`
- a validation report for schema and energy-neutrality checks

Runtime targets:

- Python `3.12`
- PySpark `4.x`

## How To Use

For local development from this repository:

```bash
pip install -e .[dev]
```

Core API:

```python
from pyntlp import (
    build_segment_metrics,
    compute_pma_sso,
    load_params,
    validate_pma,
)
```

Typical flow:

```python
params = load_params("params.yaml")

segment_metrics_df = build_segment_metrics(
    segment_attributes_df=segment_attributes_df,
    smart_meter_df=smart_meter_df,
    params=params,
)

pma_delta_df = compute_pma_sso(
    baseline_profiles_df=baseline_profiles_df,
    segment_metrics_df=segment_metrics_df,
    params=params,
)

validation_report_df = validate_pma(pma_delta_df, params)
```

The package ships a public YAML template at `src/pyntlp/resources/pyntlp_template.yaml`.

Further documentation:

- [Docs index](docs/README.md)
- [Repo structure](docs/repo-structure.md)
- [API and contracts](docs/api-contracts.md)
- [Model overview](docs/model-overview.md)
- [Development notes](docs/development.md)

## Contributor

Contributors should keep this repository generic and public. Changes should avoid organisation-specific data assets, preserve the package contract, and update tests and documentation when behaviour changes.

## Invitation To Contribute

If you find unclear documentation, bugs, or feature requests, please use GitHub Issues and Pull Requests so the discussion and changes stay visible in the repo history.
