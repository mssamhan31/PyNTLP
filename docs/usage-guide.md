# Usage guide

`pyntlp` is called from another Python job, notebook or pipeline. The caller has already prepared
normalised Spark DataFrames with the column names the package requires; the package does not read
production tables.

## Six steps

```python
from pyspark.sql import functions as F
from pyntlp import (build_lga_segment_metrics, compute_pma_sso,
                    load_params, validate_pma)

# 1. Parameters: start from the shipped template, src/pyntlp/resources/pyntlp_template.yaml
params = load_params("params.yaml")

# 2. Inputs: three normalised Spark DataFrames (columns under Show details below)
#    baseline_profiles_df, lga_segment_attributes_df, smart_meter_df

# 3. One eligibility row per lga_segment
lga_segment_metrics_df = build_lga_segment_metrics(lga_segment_attributes_df, smart_meter_df, params)

# 4. Additive interval deltas, delta_mw
pma_delta_df = compute_pma_sso(baseline_profiles_df, lga_segment_metrics_df, params)

# 5. Validate before anything else touches the output
validation_report_df = validate_pma(pma_delta_df, params)
validation_report_df.filter("status = 'fail'").show(truncate=False)

# 6. Add the deltas to the baseline, outside the package
keys = ["fc_object_id", "lga_segment", "customer_type", "fcy", "forecast_scenario", "season",
        "day_type", "representative_day", "coincident_type", "poe", "interval"]
post_sso_df = (
    baseline_profiles_df.join(pma_delta_df, on=keys, how="left")
    .fillna({"delta_mw": 0.0})
    .withColumn("post_sso_demand_mw", F.col("baseline_demand_mw") + F.col("delta_mw"))
)
```

## Set the window to the tariff's hours

The free window is a parameter, not a constant. The shipped template sets `window_start: "10:00"`
and `window_end: "15:00"`, with a donor window of 16:00 to 20:00. For the Solar Sharer Offer in New
South Wales, which includes Ausgrid's area, the free hours are 11:00 to 14:00, so set
`window_start: "11:00"` and `window_end: "14:00"`. Windows are start-inclusive, end-exclusive and
must align to `interval_minutes`.

/// details | Show details
    type: more

## Parameters as a dictionary

Parameters can come from a YAML file or from a Python dictionary, which is useful in tests:

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

The values above are the template's illustrative defaults, not calibrated estimates.

## Input columns

Baseline profile columns: `fc_object_id`, `lga_segment`, `customer_type`, `fcy`,
`forecast_scenario`, `season`, `day_type`, `representative_day`, `coincident_type`, `poe`,
`interval`, `baseline_demand_mw`.

LGA segment attribute columns: `nmi`, `lga_segment`.

Smart-meter attribute columns: `nmi`, `meter_type_code`.

If the source system uses different column names, rename them before calling the package:

```python
baseline_profiles_df = raw_baseline_df.select(
    "fc_object_id", "lga_segment", "customer_type", "fcy", "forecast_scenario", "season",
    "day_type", "representative_day", "coincident_type", "poe", "interval", "baseline_demand_mw",
)
lga_segment_attributes_df = raw_nmi_df.select("nmi", "lga_segment")
smart_meter_df = raw_meter_df.select("nmi", "meter_type_code")
```

## Checking the eligibility metrics

Useful columns to inspect after step 3: `n_total`, `n_eligible`, `eligibility_rate`,
`eligibility_rate_no_der`, `eligibility_rate_solar`, `eligibility_rate_solar_battery`.

If they look wrong, check:

- whether `lga_segment` strings contain the expected residential labels
- whether `lga_segment` strings end with supported DER suffixes
- whether `meter_type_code` values match `smart_meter_code`
- whether an NMI appears under multiple DER groups

## What the deltas contain

The result of step 4 holds the baseline dimensions, `customer_type` carried through as an
attribute, `interval` and `delta_mw`. `delta_mw` is meant to be added to the baseline; it is never
a new profile on its own.

Validation in step 5 checks the exact output schema and column order, missing or extra columns,
non-null requirements, and grouped energy neutrality.

## Operational checks around the package

Wrappers and notebooks should add their own checks:

- row counts before and after source mapping
- missing baseline `lga_segment` coverage in the metrics
- duplicate source keys before calling `compute_pma_sso(...)`
- the number of non-zero delta rows
- the largest positive and negative `delta_mw`
- validation report failures
- energy-neutrality summaries by forecast scenario and segment

These checks sit outside the package because different projects fail, warn or report them
differently.

///
