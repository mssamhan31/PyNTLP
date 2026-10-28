# Documentation

Python for Network: Tariff to Load Profile (PyNTLP) turns a tariff's assumptions into a change to
an existing load forecast. The `pyntlp` package implements one tariff, the Solar Sharer Offer
(SSO): it moves a share of each baseline profile's daily energy into the tariff's free window and
takes the same energy out of donor intervals, and returns the change as additive interval deltas.

```text
post_sso_demand_mw = baseline_demand_mw + delta_mw
```

The package is a library of Spark transformations. The caller owns all data access, table names
and orchestration, and passes in already-normalised Spark DataFrames.

## Install

Python 3.12, PySpark 4.x, and Java 17 for Spark. The package is installed from GitHub:

```powershell
python -m pip install "pyntlp @ git+https://github.com/mssamhan31/PyNTLP@v0.2.0"
```

## Four calls

```python
from pyntlp import (build_lga_segment_metrics, compute_pma_sso,
                    load_params, validate_pma)

params = load_params("params.yaml")
metrics = build_lga_segment_metrics(lga_segment_attributes_df, smart_meter_df, params)
pma_delta_df = compute_pma_sso(baseline_profiles_df, metrics, params)
report = validate_pma(pma_delta_df, params)
```

The [Usage guide](usage-guide.md) walks through each call; the [Model overview](model-overview.md)
explains what the model computes.

/// details | Show details
    type: more

## Where things are

Every page of the documentation, including those not in the menu.

| page | what it covers |
|---|---|
| [Usage guide](usage-guide.md) | the six steps from parameters to a post-SSO profile |
| [Model overview](model-overview.md) | the delta calculation, model grain, eligibility, participant cap, debugging |
| [API contracts](api-contracts.md) | every public function, required column, parameter key and output column |
| [Troubleshooting](troubleshooting.md) | common symptoms, likely causes and what to check |
| [Papers](papers.md) | the AQF conference paper, the journal article in preparation, how to cite |
| [Assumptions and limitations](assumptions-and-limitations.md) | what the model assumes and does not claim |
| [Glossary](glossary.md) | tariff, load-profile and package terms |
| [Repo structure](repo-structure.md) | the files and folders of the repository |
| [Development](development.md) | local setup, tests, Spark, documentation, review checklist |
| [AQF](aqf.md) | Adaptive Quantile Flexibility, a separate study, and where its code lives |

## Reading order for a new user

1. [Glossary](glossary.md), for the terms used throughout.
2. [Assumptions and limitations](assumptions-and-limitations.md), for what the model does and does
   not claim.
3. [Usage guide](usage-guide.md), for the normal workflow.
4. [Model overview](model-overview.md), for the calculation in detail.
5. [API contracts](api-contracts.md), when preparing inputs or reading outputs.

Use the usage guide and model overview to understand the model; use the API contracts and
development pages when changing code, writing wrappers or reviewing behaviour.

## What the documentation leaves out

The documentation avoids production table names, Databricks widgets and environment-specific
deployment instructions. Those belong in wrapper notebooks or operational documentation outside
this reusable package.

## Research code

Research code for papers lives under `publication/` in the repository and is not imported by the
package. The AQF conference paper's code is in
[`publication/1_conference/`](https://github.com/mssamhan31/PyNTLP/tree/main/publication/1_conference);
see [AQF](aqf.md).

///
