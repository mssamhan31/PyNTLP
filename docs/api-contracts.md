# API And Contracts

This page describes the public API, required inputs, YAML contract, and output schema for `pyntlp`.

## Public API

The package exports these public functions:

- `load_params(path_or_dict) -> dict`
- `build_segment_metrics(segment_attributes_df, smart_meter_df, params, segment_col="segment")`
- `compute_pma_sso(baseline_profiles_df, segment_metrics_df, params)`
- `validate_pma(pma_delta_df, params)`
- `get_window_intervals(params) -> (W, D, interval_hours)`
- `resolve_segment_parameter(segment, mapping, default_value)`

## Parameter Contract

`load_params(...)` accepts either:

- a filesystem path to a YAML file
- a Python dictionary already loaded in memory

The top-level contract is:

```yaml
constants:
  ...
parameters:
  ...
```

### `constants`

Required keys:

- `model_name`
- `model_tier`
- `interval_minutes`
- `intervals_per_day`
- `timezone`
- `segment_column`
- `output_value_column`

Notes:

- `interval_minutes` must divide evenly into `1440`
- `intervals_per_day` must equal `1440 / interval_minutes`

### `parameters`

Required keys:

- `eligible_resi_patterns`
- `smart_meter_code`
- `eligible_der_groups`
- `window_start`
- `window_end`
- `cap_kwh_per_day`
- `u_eligible_der_group`
- `ramp_start_fcy`
- `ramp_full_fcy`
- `s_segment`
- `k_response`
- `window_shape`
- `donor_shape`
- `energy_accounting`

Optional donor-window keys:

- `donor_window_start`
- `donor_window_end`

Current v0.1 supported values:

- `window_shape: flat`
- `donor_shape: flat`
- `energy_accounting: energy_neutral`

`eligible_der_groups` is a required three-entry mapping from canonical cohort to raw source values:

```yaml
eligible_der_groups:
  No_DER: ["No_DER"]
  Solar: ["Solar"]
  Solar_Battery: ["Solar_Battery"]
```

Rules:

- the required cohort keys are exactly `No_DER`, `Solar`, and `Solar_Battery`
- raw source values are matched case-insensitively after trimming
- the same raw source value cannot appear in more than one cohort

`u_eligible_der_group` is a required three-entry mapping:

```yaml
u_eligible_der_group:
  No_DER: 0.25
  Solar: 0.05
  Solar_Battery: 0.10
```

`s_segment` remains a flat mapping with a required default:

```yaml
s_segment:
  default: 0.10
  Residential: 0.15
```

Donor-window rules:

- if `donor_window_start` and `donor_window_end` are omitted, donor intervals default to the complement of the free window
- if one donor-window key is supplied without the other, param loading fails
- explicit donor windows must not overlap the free window
- explicit donor windows use the same start-inclusive, end-exclusive, interval-alignment, and overnight rules as the free window

## Input DataFrames

The package consumes normalised Spark DataFrames. It does not read source tables directly.

### Baseline Profiles

Required columns:

- `fc_run_year`
- `version`
- `fc_object_id`
- `segment`
- `fcy`
- `forecast_scenario`
- `poe`
- `representative_day`
- `season`
- `day_type`
- `interval`
- `underlying_demand_mw`

Expected behaviour:

- FCY scope is whatever exists in the baseline DataFrame
- output row count should match baseline row count
- interval numbering is expected to be 1-based and aligned from midnight

### Segment Attributes

Required columns:

- `nmi`
- `segment`
- `der_type`

Optional extension columns may exist, but they are not required by the v0.1 package logic.

### Smart Meter Eligibility

Required columns:

- `nmi`
- `meter_type_code`

Join rule:

- `smart_meter_df.nmi` joins to `segment_attributes_df.nmi`

## Segment Metrics Output

`build_segment_metrics(...)` returns one row per segment with:

- `segment`
- `n_total`
- `n_eligible`
- `eligibility_rate`
- `n_eligible_no_der`
- `n_eligible_solar`
- `n_eligible_solar_battery`
- `eligibility_rate_no_der`
- `eligibility_rate_solar`
- `eligibility_rate_solar_battery`

Interpretation:

- `n_eligible` is the sum of the three cohort-specific counts
- all cohort-specific counts still require residential-segment matching and a smart meter
- one NMI cannot contribute to more than one DER cohort

## PMA Output

`compute_pma_sso(...)` returns a Spark DataFrame with exactly these columns:

- `fc_run_year`
- `version`
- `fc_object_id`
- `segment`
- `fcy`
- `forecast_scenario`
- `poe`
- `representative_day`
- `season`
- `day_type`
- `interval`
- `pma_sso_mw`
- `pma_sso_pct_of_underlying`

Column types:

- `fc_run_year`: `int`
- `version`: `string`
- `fc_object_id`: `int`
- `segment`: `string`
- `fcy`: `int`
- `forecast_scenario`: `string`
- `poe`: `string`
- `representative_day`: `string`
- `season`: `string`
- `day_type`: `string`
- `interval`: `int`
- `pma_sso_mw`: `double`
- `pma_sso_pct_of_underlying`: `double`

Interpretation:

- `pma_sso_mw` is an additive interval delta in MW
- `pma_sso_pct_of_underlying` is `100 * pma_sso_mw / underlying_demand_mw` for the same row
- `pma_sso_pct_of_underlying` is `null` when `underlying_demand_mw` is zero
- downstream systems combine `pma_sso_mw` with baseline demand outside the package

## Validation Report

`validate_pma(...)` returns a Spark DataFrame with:

- `check_name`
- `status`
- `detail`

Current checks:

- exact output schema match
- required output columns present
- null checks on required output columns
- group-level energy neutrality
