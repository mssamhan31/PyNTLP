# API contracts

Callers pass normalised Spark DataFrames into the package and own all table IO, source mappings,
widgets and orchestration. `compute_pma_sso(...)` keeps the baseline's interval shape and returns
only additive deltas.

## Public functions

| function | what it does | returns |
|---|---|---|
| `load_params(path_or_dict)` | loads and validates parameters from a YAML path or a dictionary | a plain `dict`, used by every later call |
| `build_lga_segment_metrics(lga_segment_attributes_df, smart_meter_df, params)` | counts NMIs and eligibility rates by DER group | a Spark DataFrame, one row per `lga_segment` |
| `compute_pma_sso(baseline_profiles_df, lga_segment_metrics_df, params)` | computes the additive interval deltas | a Spark DataFrame of the baseline dimensions and `delta_mw` |
| `validate_pma(pma_delta_df, params)` | checks the output contract | a Spark DataFrame report: `check_name`, `status`, `detail` |
| `get_window_intervals(params)` | maps the configured windows to interval numbers | free-window intervals, donor intervals, interval hours |
| `resolve_lga_segment_parameter(lga_segment, mapping, default_value)` | resolves an exact-match segment override with a default fallback | a `float` |

## Configuration in brief

Parameters have two sections, `constants` and `parameters`. The supported calculation modes are
`window_shape: flat`, `donor_shape: flat` and `energy_accounting: energy_neutral`; any other mode is
rejected when the parameters load. The shipped template is
`src/pyntlp/resources/pyntlp_template.yaml`.

/// details | Show details
    type: more

## Function notes

`load_params(...)` validates the required `constants` and `parameters` sections and returns a plain
dictionary. Call it first, so the same validated object is used for metrics, model and validation.

`build_lga_segment_metrics(...)` takes `lga_segment_attributes_df` (NMI-to-segment attributes),
`smart_meter_df` (NMI-to-meter-type attributes) and the validated parameters, and returns a Spark
DataFrame at `lga_segment` grain with NMI counts and eligibility rates.

`compute_pma_sso(...)` takes the normalised baseline profile rows, the metrics output and the
parameters, and returns the canonical PMA output columns with `delta_mw`.

`validate_pma(...)` returns a small, portable report. It validates package-level contracts, not
organisation-specific pipeline rules.

`get_window_intervals(...)` returns the free-window intervals, the donor intervals and the
interval length in hours. With no explicit donor window, every interval outside the free window is
a donor; an explicit donor window may wrap overnight but must not overlap the free window.

`resolve_lga_segment_parameter(...)` is the scalar form of the segment-override rule, for tests and
other non-Spark callers.

## Config contract

Required `constants`: `model_name`, `model_tier`, `interval_minutes`, `intervals_per_day`,
`timezone`.

Required `parameters`: `eligible_resi_patterns`, `smart_meter_code`, `window_start`, `window_end`,
`cap_kwh_per_day`, `u_eligible_der_group`, `ramp_start_fcy`, `ramp_full_fcy`, `s_lga_segment`,
`k_response`, `window_shape`, `donor_shape`, `energy_accounting`.

Optional accepted `parameters`: `donor_window_start`, `donor_window_end`, `season_modifiers`,
`daytype_modifiers`, `rebound_share`, `rebound_shape`. The modifier and rebound fields are accepted
to keep the configuration surface stable, but the current calculation does not use them.

## Baseline input contract

`compute_pma_sso(...)` requires `fc_object_id`, `lga_segment`, `customer_type`, `fcy`,
`forecast_scenario`, `season`, `day_type`, `representative_day`, `coincident_type`, `poe`,
`interval` and `baseline_demand_mw`.

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

`customer_type` is required by presence so the output can mirror the baseline table shape. Its
value may be null. It is not used for eligibility, adoption, duplicate-key checks,
energy-neutrality grouping or delta allocation. Duplicate baseline rows are rejected when they
share the same model key, even if `customer_type` differs.

## Metrics input contracts

`build_lga_segment_metrics(...)` expects `lga_segment_attributes_df` to contain `nmi` and
`lga_segment`, and `smart_meter_df` to contain `nmi` and `meter_type_code`. Both should be
normalised before they enter the package; source-specific column names are mapped by the caller.

## Metrics output contract

One row per `lga_segment`, with `lga_segment`, `n_total`, `n_eligible`, `eligibility_rate`,
`n_eligible_no_der`, `n_eligible_solar`, `n_eligible_solar_battery`, `eligibility_rate_no_der`,
`eligibility_rate_solar` and `eligibility_rate_solar_battery`.

Residential eligibility is matched against the full `lga_segment` string using
`eligible_resi_patterns`. The DER group is inferred from the suffix of `lga_segment`: `No_DER`,
`Solar` or `Solar_Battery`. If an NMI appears under more than one inferred DER group, metrics
construction raises an error so the duplicated classification can be fixed upstream.

## PMA output contract

`compute_pma_sso(...)` returns exactly `fc_object_id`, `lga_segment`, `customer_type`, `fcy`,
`forecast_scenario`, `season`, `day_type`, `representative_day`, `coincident_type`, `poe`,
`interval` and `delta_mw`, in that order. The output is at interval granularity: it mirrors the
baseline dimensions and replaces `baseline_demand_mw` with the additive `delta_mw`.

## Cap and missing-coverage behaviour

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

That grain deliberately excludes `fc_object_id`. After the cap is calculated, the capped shift
energy is allocated back to the `fc_object_id` groups by their share of the uncapped shift energy.

If a baseline `lga_segment` has no matching metrics row, the output rows are kept, the metrics are
treated as zero, adoption is zero and `delta_mw` is zero. This is non-breaking package behaviour;
callers should add their own reporting if missing coverage needs to be visible in a notebook or
pipeline.

## Validation report contract

`validate_pma(...)` returns a Spark DataFrame with `check_name`, `status` and `detail`. The checks
cover the exact output schema and column order, missing output columns, extra output columns,
required non-null columns and grouped energy neutrality. Statuses are `pass` and `fail`. Wrappers
can add richer statuses, such as `pass with info` for non-breaking diagnostics; the package keeps
validation to the portable public contract.

///
