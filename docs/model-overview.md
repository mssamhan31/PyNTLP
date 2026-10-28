# Model overview

The model turns Solar Sharer Offer policy assumptions into additive interval deltas, `delta_mw`.
It does not produce a forecast by itself; it produces the change to add to an existing one:

```text
post_sso_demand_mw = baseline_demand_mw + delta_mw
```

## The calculation in eight steps

1. Load and validate parameters with `load_params(...)`.
2. Build `lga_segment` eligibility metrics from NMI and smart-meter attributes.
3. Join the metrics to baseline profile rows by `lga_segment`.
4. Calculate uncapped shift energy for each baseline model group.
5. Apply the participant cap once per `lga_segment` population.
6. Allocate the capped shift energy back to the baseline output grain.
7. Spread the shifted energy flat across the free window and take it flat from the donor
   intervals.
8. Validate schema, required values and energy neutrality.

## Shift energy

For each baseline model group:

```text
daily_energy_mwh   = sum(baseline_demand_mw * interval_hours)
adoption_rate      = eligible_uptake_rate * ramp_rate
uncapped_shift_mwh = daily_energy_mwh * s_lga_segment * k_response * adoption_rate
```

`eligible_uptake_rate` weights the uptake assumption for each DER group (`No_DER`, `Solar`,
`Solar_Battery`) by that group's eligibility rate; `ramp_rate` rises linearly from 0 before
`ramp_start_fcy` to 1 from `ramp_full_fcy`. The shift is then capped at `cap_kwh_per_day` per
participant. The calculation is energy-neutral: positive deltas fall flat across the free window
and matching negative deltas fall flat across the donor intervals, so each group's daily energy is
unchanged.

The model's assumptions and what it does not represent are set out in
[Assumptions and limitations](assumptions-and-limitations.md).

/// details | Show details
    type: more

## Eligibility metrics

`build_lga_segment_metrics(...)` takes two normalised Spark DataFrames:

- `lga_segment_attributes_df`, with `nmi` and `lga_segment`
- `smart_meter_df`, with `nmi` and `meter_type_code`

It returns one row per `lga_segment` with:

- `n_total`: distinct NMI count
- `n_eligible`: eligible NMI count
- `eligibility_rate`: eligible share of `n_total`
- `n_eligible_no_der`, `n_eligible_solar`, `n_eligible_solar_battery`: eligible NMI counts by DER
  group
- `eligibility_rate_no_der`, `eligibility_rate_solar`, `eligibility_rate_solar_battery`

Residential eligibility is matched against the full `lga_segment` string using
`eligible_resi_patterns`. Smart-meter eligibility compares the normalised `meter_type_code` with
`smart_meter_code`.

The DER group is inferred from the suffix of `lga_segment`: `No_DER`, `Solar` or
`Solar_Battery`. If one NMI appears in more than one inferred DER group, the function raises an
error, so the same customer cannot be counted under two DER classes.

## Baseline model grain

The baseline input carries the network object (`fc_object_id`), the population segment
(`lga_segment`), the scenario dimensions (`fcy`, `forecast_scenario`, `season`, `day_type`,
`representative_day`, `coincident_type`, `poe`), the `interval`, the value
`baseline_demand_mw`, and the carried attribute `customer_type`.

The grouping grain for energy and neutrality is:

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

`customer_type` is not a model dimension. It must be present so the output mirrors the baseline
table, but it may be null and is carried through only as an attribute.

## Uptake and shiftable share

The weighted DER eligibility rate uses `u_eligible_der_group.No_DER`,
`u_eligible_der_group.Solar` and `u_eligible_der_group.Solar_Battery` with the corresponding
eligibility rates from the metrics. The forecast-year ramp is:

```text
ramp_rate = 0 before ramp_start_fcy
ramp_rate = 1 from ramp_full_fcy onward
ramp_rate = linear interpolation between those years
```

`s_lga_segment` supports exact segment overrides and a `default` fallback; a segment not listed
explicitly takes the default.

## Participant cap

The participant cap stops the model shifting more energy than the estimated eligible population
could contribute. Eligibility metrics are at `lga_segment` grain, so the cap is applied once per
`lga_segment` population, not once per `fc_object_id`. The cap grain is the model grain without
`fc_object_id`:

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
participants                = n_total * adoption_rate
population_cap_mwh          = participants * cap_kwh_per_day / 1000
population_capped_shift_mwh = min(population_uncapped_shift_mwh, population_cap_mwh)
```

The capped shift is allocated back to each `fc_object_id` by its share of the uncapped shift:

```text
object_share             = object_uncapped_shift_mwh / population_uncapped_shift_mwh
object_capped_shift_mwh  = population_capped_shift_mwh * object_share
```

With no allocatable uncapped shift, the allocated capped shift is zero, which avoids a division by
zero and keeps uncovered or ineligible segments neutral.

## Window and donor allocation

The free window receives the positive `delta_mw` values and the donor intervals the matching
negative values. Window boundaries are start-inclusive, end-exclusive and aligned to
`interval_minutes`. If `donor_window_start` and `donor_window_end` are given, only intervals in
that window donate energy; if they are omitted, every interval outside the free window donates.

The package supports `window_shape: flat`, `donor_shape: flat` and
`energy_accounting: energy_neutral`: shifted energy is spread evenly across the receiving intervals
and removed evenly from the donor intervals.

## Missing metrics coverage

`compute_pma_sso(...)` left-joins the metrics to the baseline by `lga_segment`. If a segment has
no metrics, its baseline rows stay in the output, the metrics are treated as zero, adoption and
shift energy are zero, and `delta_mw` is zero. The behaviour is deliberately non-breaking so no
baseline rows are dropped; pipelines should still report missing coverage so data gaps are
visible.

## Output

The output holds exactly `fc_object_id`, `lga_segment`, `customer_type`, `fcy`,
`forecast_scenario`, `season`, `day_type`, `representative_day`, `coincident_type`, `poe`,
`interval` and `delta_mw`. Positive and negative values are expected. A valid energy-neutral run
sums to approximately zero MWh within each model group after multiplying by `interval_hours`.

## Debugging a run

1. Confirm parameter validation passes.
2. Inspect the metrics output and count missing baseline `lga_segment` values.
3. Check `n_total`, the eligibility rates and the DER suffix inference for suspicious segments.
4. Compare uncapped and capped shift energy, especially where one `lga_segment` appears under
   several `fc_object_id` values.
5. Check the free-window and donor-window interval counts.
6. Run `validate_pma(...)` and inspect any `fail` rows.

///
