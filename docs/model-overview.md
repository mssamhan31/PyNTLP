# Model Overview

The model converts SSO policy settings into additive interval PMA deltas named `delta_mw`.

Eligibility metrics are calculated at `lga_segment` grain. The same string is used for:

- joining baseline profiles to NMI-derived eligibility metrics
- residential eligibility pattern matching
- DER group suffix inference
- optional `s_lga_segment` shiftable-load overrides

## Eligibility Metrics

`build_lga_segment_metrics(...)` uses:

- `nmi`
- `lga_segment`
- smart-meter status from `meter_type_code`

Residential eligibility is matched against the full `lga_segment` string. DER group is inferred from the `lga_segment` suffix:

- `No_DER`
- `Solar`
- `Solar_Battery`

## PMA Calculation

For each `lga_segment` and baseline profile group:

```text
daily_energy_mwh = sum(baseline_demand_mw * interval_hours)
eligible_uptake_rate = weighted DER eligibility rate
adoption_rate = eligible_uptake_rate * ramp_rate
e_shift_mwh = daily_energy_mwh * s_lga_segment * k_response * adoption_rate
```

Shifted energy is capped by participant count and `cap_kwh_per_day`, allocated into the free window, and removed from donor intervals so the group is energy-neutral.

The model group includes `fc_object_id`, `lga_segment`, `fcy`,
`forecast_scenario`, `season`, `day_type`, `representative_day`,
`coincident_type`, and `poe`. `customer_type` is carried to the output as an
attribute only; it may be null and does not change eligibility, adoption,
energy, or allocation logic.

## Output

The output table is:

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
