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
- `eligible_der_type`
- `window_start`
- `window_end`
- `cap_kwh_per_day`
- `u_segment`
- `ramp_start_fcy`
- `ramp_full_fcy`
- `s_segment`
- `k_response`
- `window_shape`
- `donor_shape`
- `energy_accounting`

Current v0.1 supported values:

- `window_shape: flat`
- `donor_shape: flat`
- `energy_accounting: energy_neutral`

Segment mappings are flat mappings, for example:

```yaml
u_segment:
  default: 0.25
  Residential: 0.35

s_segment:
  default: 0.10
  Residential: 0.15
```

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

Interpretation:

- `pma_sso_mw` is an additive interval delta in MW
- downstream systems combine it with baseline demand outside the package

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

