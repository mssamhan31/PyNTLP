# Usage Guide

## Executive Summary

This guide shows how to use `pyntlp` from another Python job, notebook, or
pipeline. It assumes the caller has already prepared normalised input data with
the column names required by the package.

The usual workflow is:

1. Load model parameters.
2. Build eligibility metrics by `lga_segment`.
3. Compute PMA SSO deltas from the baseline profile.
4. Validate the output.
5. Join or add the deltas back to the baseline outside the package.

`pyntlp` does not read production tables directly. The caller is responsible for
data access, source column mapping, and writing outputs.

## Prerequisites

Install the package locally:

```bash
pip install -e .[dev]
```

In code, import the public API:

```python
from pyntlp import (
    build_lga_segment_metrics,
    compute_pma_sso,
    load_params,
    validate_pma,
)
```

## Step 1: Load Parameters

Parameters can come from a YAML file:

```python
params = load_params("params.yaml")
```

They can also come from a Python dictionary, which is useful in tests:

```python
params = load_params(
    {
        "constants": {
            "model_name": "pyntlp",
            "model_tier": "public",
            "interval_minutes": 30,
            "intervals_per_day": 48,
            "timezone": "Australia/Sydney",
        },
        "parameters": {
            "eligible_resi_patterns": ["Large Res", "Med Res", "Small Res", "Apartment"],
            "smart_meter_code": "SMART",
            "window_start": "10:00",
            "window_end": "15:00",
            "cap_kwh_per_day": 4.0,
            "u_eligible_der_group": {
                "No_DER": 0.25,
                "Solar": 0.05,
                "Solar_Battery": 0.10,
            },
            "ramp_start_fcy": 2026,
            "ramp_full_fcy": 2028,
            "s_lga_segment": {"default": 0.05},
            "k_response": 0.80,
            "window_shape": "flat",
            "donor_shape": "flat",
            "energy_accounting": "energy_neutral",
        },
    }
)
```

Use the shipped template as the starting point for a YAML file:

```text
src/pyntlp/resources/pyntlp_template.yaml
```

## Step 2: Prepare Input Data

The package expects normalised Spark DataFrames. If your source system uses
different column names, rename them before calling the package.

Baseline profile columns:

- `fc_object_id`
- `lga_segment`
- `customer_type`
- `fcy`
- `forecast_scenario`
- `season`
- `day_type`
- `representative_day`
- `coincident_type`
- `poe`
- `interval`
- `baseline_demand_mw`

LGA segment attribute columns:

- `nmi`
- `lga_segment`

Smart-meter attribute columns:

- `nmi`
- `meter_type_code`

Example source mapping:

```python
baseline_profiles_df = raw_baseline_df.select(
    "fc_object_id",
    "lga_segment",
    "customer_type",
    "fcy",
    "forecast_scenario",
    "season",
    "day_type",
    "representative_day",
    "coincident_type",
    "poe",
    "interval",
    "baseline_demand_mw",
)

lga_segment_attributes_df = raw_nmi_df.select(
    "nmi",
    "lga_segment",
)

smart_meter_df = raw_meter_df.select(
    "nmi",
    "meter_type_code",
)
```

## Step 3: Build Eligibility Metrics

Build one metrics row per `lga_segment`:

```python
lga_segment_metrics_df = build_lga_segment_metrics(
    lga_segment_attributes_df=lga_segment_attributes_df,
    smart_meter_df=smart_meter_df,
    params=params,
)
```

Useful columns to inspect:

- `n_total`
- `n_eligible`
- `eligibility_rate`
- `eligibility_rate_no_der`
- `eligibility_rate_solar`
- `eligibility_rate_solar_battery`

If these values look wrong, check:

- whether `lga_segment` strings contain the expected residential labels
- whether `lga_segment` strings end with supported DER suffixes
- whether `meter_type_code` values match `smart_meter_code`
- whether an NMI appears under multiple DER groups

## Step 4: Compute SSO Deltas

Compute additive interval deltas:

```python
pma_delta_df = compute_pma_sso(
    baseline_profiles_df=baseline_profiles_df,
    lga_segment_metrics_df=lga_segment_metrics_df,
    params=params,
)
```

The result contains:

- the baseline dimensions
- `customer_type`, carried through as an attribute
- `interval`
- `delta_mw`

`delta_mw` is meant to be added to the baseline:

```text
post_sso_demand_mw = baseline_demand_mw + delta_mw
```

## Step 5: Validate The Output

Run package validation:

```python
validation_report_df = validate_pma(pma_delta_df, params)
```

Inspect failed checks:

```python
validation_report_df.filter("status = 'fail'").show(truncate=False)
```

Current validation checks include:

- exact output schema and column order
- missing or extra output columns
- non-null requirements
- grouped energy neutrality

## Step 6: Combine With The Baseline

Joining deltas back to the baseline is a caller responsibility:

```python
post_sso_df = (
    baseline_profiles_df.join(
        pma_delta_df,
        on=[
            "fc_object_id",
            "lga_segment",
            "customer_type",
            "fcy",
            "forecast_scenario",
            "season",
            "day_type",
            "representative_day",
            "coincident_type",
            "poe",
            "interval",
        ],
        how="left",
    )
    .fillna({"delta_mw": 0.0})
    .withColumn("post_sso_demand_mw", F.col("baseline_demand_mw") + F.col("delta_mw"))
)
```

## Recommended Operational Checks

Wrappers and notebooks should add operational checks around the package:

- row counts before and after source mapping
- missing baseline `lga_segment` coverage in metrics
- duplicate source keys before calling `compute_pma_sso(...)`
- number of non-zero delta rows
- largest positive and negative `delta_mw`
- validation report failures
- energy-neutrality summaries by forecast scenario and segment

These checks are intentionally outside the package because different projects
may want to fail, warn, or report them differently.
