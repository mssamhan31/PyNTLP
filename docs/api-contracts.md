# API Contracts

## Public Functions

- `load_params(path_or_dict) -> dict`
- `build_lga_segment_metrics(lga_segment_attributes_df, smart_meter_df, params)`
- `compute_pma_sso(baseline_profiles_df, lga_segment_metrics_df, params)`
- `validate_pma(pma_delta_df, params)`

## Config Contract

Required constants:

- `model_name`
- `model_tier`
- `interval_minutes`
- `intervals_per_day`
- `timezone`

Required parameters:

- `eligible_resi_patterns`
- `smart_meter_code`
- `window_start`
- `window_end`
- `cap_kwh_per_day`
- `u_eligible_der_group`
- `ramp_start_fcy`
- `ramp_full_fcy`
- `s_lga_segment`
- `k_response`
- `window_shape`
- `donor_shape`
- `energy_accounting`

## Input Contracts

Baseline profiles:

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

NMI attributes:

- `nmi`
- `lga_segment`

Smart meter attributes:

- `nmi`
- `meter_type_code`

## Output Contract

`compute_pma_sso(...)` returns exactly:

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
- `delta_mw`

## Classification

Residential eligibility is matched against the full `lga_segment` string using `eligible_resi_patterns`.

DER group is inferred from the suffix of `lga_segment`; supported suffixes are:

- `No_DER`
- `Solar`
- `Solar_Battery`
