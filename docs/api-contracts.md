# API Contracts

## Executive Summary

This page describes the public contracts for `pyntlp`: the functions callers
should use, the columns those functions expect, the parameters they validate,
and the shape of the Spark DataFrames they return.

The most important contract decisions are:

- callers pass normalised Spark DataFrames into the package
- callers own table IO, source mappings, widgets, and production orchestration
- `compute_pma_sso(...)` preserves baseline interval shape and returns only
  additive PMA deltas
- `customer_type` is carried through as an output attribute, not used as a
  model dimension
- participant caps are applied at the segment population grain, excluding
  `fc_object_id`
- missing `lga_segment` metrics are non-breaking and produce zero deltas

## Public Functions

### `load_params(path_or_dict) -> dict`

Loads model parameters from either:

- a YAML file path
- an in-memory Python dictionary

The function validates the required `constants` and `parameters` sections and
returns a plain dictionary. It should be called before metrics, model, or
validation functions so the same validated parameter object is used throughout
the run.

### `build_lga_segment_metrics(lga_segment_attributes_df, smart_meter_df, params)`

Builds one metrics row per `lga_segment`.

Inputs:

- `lga_segment_attributes_df`: NMI-to-segment attributes
- `smart_meter_df`: NMI-to-meter-type attributes
- `params`: validated parameter dictionary

Output:

- a Spark DataFrame at `lga_segment` grain with NMI counts and eligibility rates

### `compute_pma_sso(baseline_profiles_df, lga_segment_metrics_df, params)`

Computes additive interval-level PMA deltas.

Inputs:

- `baseline_profiles_df`: normalised baseline profile rows
- `lga_segment_metrics_df`: output from `build_lga_segment_metrics(...)`
- `params`: validated parameter dictionary

Output:

- a Spark DataFrame containing the canonical PMA output columns and `delta_mw`

### `validate_pma(pma_delta_df, params)`

Returns a Spark validation report.

The report is intentionally small and portable. It validates package-level
contracts, not organisation-specific pipeline rules.

## Config Contract

Parameters are expected to contain two top-level sections:

- `constants`
- `parameters`

Required `constants`:

- `model_name`
- `model_tier`
- `interval_minutes`
- `intervals_per_day`
- `timezone`

Required `parameters`:

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

Optional accepted `parameters`:

- `donor_window_start`
- `donor_window_end`
- `season_modifiers`
- `daytype_modifiers`
- `rebound_share`
- `rebound_shape`

The optional modifier and rebound fields are accepted to keep the configuration
surface stable, but the current v0.1 calculation does not use them in the PMA
delta calculation.

Supported calculation modes:

- `window_shape: flat`
- `donor_shape: flat`
- `energy_accounting: energy_neutral`

Unsupported modes are rejected during parameter validation.

## Baseline Input Contract

`compute_pma_sso(...)` requires these columns:

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

The model key is:

```text
fc_object_id
lga_segment
fcy
forecast_scenario
season
day_type
representative_day
coincident_type
poe
interval
```

`customer_type` is required by presence so the output can mirror the baseline
table shape. Its value may be null. It is not used for eligibility, adoption,
duplicate-key checks, energy-neutrality grouping, or delta allocation.

Duplicate baseline rows are rejected when they share the same model key, even
if `customer_type` differs.

## Metrics Input Contracts

`build_lga_segment_metrics(...)` expects `lga_segment_attributes_df` to contain:

- `nmi`
- `lga_segment`

It expects `smart_meter_df` to contain:

- `nmi`
- `meter_type_code`

Both inputs should be normalised before they enter the package. For example,
source-specific column names should be mapped by the caller or wrapper notebook.

## Metrics Output Contract

The metrics output is one row per `lga_segment`.

Expected columns are:

- `lga_segment`
- `n_total`
- `n_eligible`
- `eligibility_rate`
- `n_eligible_no_der`
- `n_eligible_solar`
- `n_eligible_solar_battery`
- `eligibility_rate_no_der`
- `eligibility_rate_solar`
- `eligibility_rate_solar_battery`

Residential eligibility is matched against the full `lga_segment` string using
`eligible_resi_patterns`.

DER group is inferred from the suffix of `lga_segment`. Supported suffixes are:

- `No_DER`
- `Solar`
- `Solar_Battery`

If an NMI appears under multiple inferred DER groups, metrics construction
raises an error so the duplicated classification can be fixed upstream.

## PMA Output Contract

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

The output is at interval granularity. It mirrors the baseline dimensions and
replaces `baseline_demand_mw` with the additive `delta_mw` value.

## Cap And Missing-Coverage Behaviour

Participant caps are calculated at the population cap grain:

```text
lga_segment
fcy
forecast_scenario
season
day_type
representative_day
coincident_type
poe
```

That grain deliberately excludes `fc_object_id`. After the cap is calculated,
the capped shift energy is allocated back to `fc_object_id` groups by their
share of uncapped shift energy.

If a baseline `lga_segment` has no matching metrics row:

- the output rows are retained
- metrics are treated as zero
- adoption is zero
- `delta_mw` is zero

This is non-breaking package behaviour. Callers should add operational
reporting if missing metrics coverage needs to be visible in a notebook or
pipeline validation report.

## Validation Report Contract

`validate_pma(...)` returns a Spark DataFrame with:

- `check_name`
- `status`
- `detail`

Current package validation checks include:

- exact output schema and column order
- missing output columns
- extra output columns
- required non-null output columns
- grouped energy neutrality

Typical statuses are:

- `pass`
- `fail`

Wrappers can add richer statuses such as `pass with info` for non-breaking
operational diagnostics. The package itself keeps validation focused on the
portable public contract.
