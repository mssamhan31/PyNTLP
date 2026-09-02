# Model Overview

## Executive Summary

The `pyntlp` model converts Solar Sharer Offer policy assumptions into additive
PMA interval deltas named `delta_mw`.

The model does not produce a new demand forecast by itself. It produces the
change that can be added to an existing baseline:

```text
post_sso_demand_mw = baseline_demand_mw + delta_mw
```

The important modelling guarantees are:

- the output keeps the same interval and scenario shape as the baseline input
- positive deltas are placed inside the configured SSO policy window
- negative deltas are removed from donor intervals
- energy is neutral within each model group
- eligibility metrics are calculated at `lga_segment` grain
- participant caps are applied once per `lga_segment` population, not once per
  `fc_object_id`
- missing eligibility metrics are treated as zero uptake, preserving output
  shape while producing zero deltas for uncovered segments

## Data Flow

The model flow is intentionally linear:

1. Load and validate parameters with `load_params(...)`.
2. Build `lga_segment` eligibility metrics from NMI attributes and smart-meter
   attributes.
3. Join those metrics to baseline profile rows by `lga_segment`.
4. Calculate uncapped shift energy for each baseline model group.
5. Apply the participant cap at the segment population grain.
6. Allocate capped shift energy back to the baseline output grain.
7. Convert shifted energy into interval-level `delta_mw`.
8. Validate schema, required values, and energy neutrality.

This structure makes debugging easier because each stage has a clear input,
output, and grain.

## Eligibility Metrics

`build_lga_segment_metrics(...)` takes two normalised Spark DataFrames:

- `lga_segment_attributes_df`, with `nmi` and `lga_segment`
- `smart_meter_df`, with `nmi` and `meter_type_code`

The function returns one row per `lga_segment`. Each row contains:

- `n_total`: distinct NMI count
- `n_eligible`: eligible NMI count
- `eligibility_rate`: eligible share of `n_total`
- `n_eligible_no_der`: eligible NMI count for `No_DER`
- `n_eligible_solar`: eligible NMI count for `Solar`
- `n_eligible_solar_battery`: eligible NMI count for `Solar_Battery`
- `eligibility_rate_no_der`
- `eligibility_rate_solar`
- `eligibility_rate_solar_battery`

Residential eligibility is matched against the full `lga_segment` string using
`eligible_resi_patterns`. Smart-meter eligibility is calculated by comparing the
normalised `meter_type_code` value with `smart_meter_code`.

DER group is inferred from the suffix of `lga_segment`. Supported suffixes are:

- `No_DER`
- `Solar`
- `Solar_Battery`

If one NMI appears in multiple inferred DER groups, the metrics function raises
an error. That prevents the same customer from being counted under multiple DER
classes.

## Baseline Model Grain

The interval baseline input is expected to include:

- network object: `fc_object_id`
- population segment: `lga_segment`
- scenario dimensions: `fcy`, `forecast_scenario`, `season`, `day_type`,
  `representative_day`, `coincident_type`, `poe`
- interval: `interval`
- value: `baseline_demand_mw`
- carried attribute: `customer_type`

The model grouping grain for energy and neutrality is:

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
```

`customer_type` is intentionally not a model dimension. It is required by
presence so the output can mirror the baseline table, but it may be null and is
carried through only as an attribute.

## Shift Energy Calculation

For each baseline model group, the package calculates daily baseline energy:

```text
daily_energy_mwh = sum(baseline_demand_mw * interval_hours)
```

It then calculates a weighted DER eligibility rate using:

- `u_eligible_der_group.No_DER`
- `u_eligible_der_group.Solar`
- `u_eligible_der_group.Solar_Battery`
- the corresponding eligibility rates from `lga_segment_metrics_df`

Forecast-year ramping is linear:

```text
ramp_rate = 0 before ramp_start_fcy
ramp_rate = 1 from ramp_full_fcy onward
ramp_rate = linear interpolation between those years
```

The uncapped shift energy is:

```text
adoption_rate = eligible_uptake_rate * ramp_rate
uncapped_shift_mwh = daily_energy_mwh * s_lga_segment * k_response * adoption_rate
```

`s_lga_segment` supports exact segment overrides and a `default` fallback. If a
segment is not listed explicitly, the default value is used.

## Participant Cap

The participant cap protects against shifting more energy than the estimated
eligible customer population could reasonably contribute.

The key detail is the cap grain. Eligibility metrics are at `lga_segment` grain,
so the cap must also be applied once per `lga_segment` model population. It is
not applied separately for each `fc_object_id`.

The cap grain is the model grain with `fc_object_id` removed:

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

At that grain:

```text
participants = n_total * adoption_rate
population_cap_mwh = participants * cap_kwh_per_day / 1000
population_capped_shift_mwh = min(population_uncapped_shift_mwh, population_cap_mwh)
```

The capped population shift is then allocated back to each `fc_object_id` by its
share of uncapped shift energy:

```text
object_share = object_uncapped_shift_mwh / population_uncapped_shift_mwh
object_capped_shift_mwh = population_capped_shift_mwh * object_share
```

If there is no allocatable uncapped shift, the allocated capped shift is zero.
This fallback avoids division-by-zero behaviour and keeps uncovered or
ineligible segments neutral.

## Window And Donor Allocation

The configured SSO policy window receives the positive `delta_mw` values.
Donor intervals receive the matching negative `delta_mw` values.

Window boundaries are:

- start-inclusive
- end-exclusive
- aligned to `interval_minutes`

If `donor_window_start` and `donor_window_end` are supplied, only intervals in
that explicit donor window donate energy. If they are omitted, every interval
outside the policy window is eligible to donate.

The current public engine supports:

- `window_shape: flat`
- `donor_shape: flat`
- `energy_accounting: energy_neutral`

Flat allocation means shifted energy is spread evenly across eligible receiving
intervals and removed evenly from eligible donor intervals.

## Missing Metrics Coverage

`compute_pma_sso(...)` left-joins metrics to the baseline by `lga_segment`.

If metrics are missing for a segment:

- the baseline rows remain in the output
- metrics values are treated as zero
- adoption is zero
- shift energy is zero
- `delta_mw` is zero for those rows

That behaviour is intentionally non-breaking. It avoids silently dropping
baseline profile rows. Operational notebooks or pipelines should still report
missing coverage as a diagnostic so data-quality gaps are visible.

## Output

The output table contains exactly:

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

`delta_mw` is additive. Positive and negative values are expected. A valid
energy-neutral model run should sum to approximately zero MWh within each model
group after multiplying by `interval_hours`.

## Debugging Guide

Use this sequence when checking a run:

1. Confirm parameter validation passes.
2. Inspect the metrics output and count missing baseline `lga_segment` values.
3. Check `n_total`, eligibility rates, and DER suffix inference for suspicious
   segments.
4. Compare uncapped and capped shift energy, especially where one
   `lga_segment` appears under multiple `fc_object_id` values.
5. Check policy-window and donor-window interval counts.
6. Run `validate_pma(...)` and inspect any `fail` rows.
