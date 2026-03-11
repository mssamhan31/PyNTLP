# Model Overview

This page describes how the v0.1 `pyntlp` model works.

## Scope

The model converts an SSO policy definition into an additive interval PMA delta profile named `pma_sso_mw`.

The model does not:

- write output tables
- manage environment-specific configuration
- combine the PMA delta with baseline demand

## Step 1: Segment Eligibility

`build_segment_metrics(...)` computes segment-level eligibility using:

- residential segment matching from `eligible_resi_patterns`
- smart-meter matching from `smart_meter_code`
- DER-type cohort matching from `eligible_der_groups`

For each segment, the package computes:

- `n_total`
- `n_eligible`
- `eligibility_rate = n_eligible / n_total`
- `n_eligible_no_der`
- `n_eligible_solar`
- `n_eligible_solar_battery`
- `eligibility_rate_no_der`
- `eligibility_rate_solar`
- `eligibility_rate_solar_battery`

Rules:

- all three eligible cohorts still require a residential segment match and a smart meter
- one NMI cannot contribute to more than one DER cohort

## Step 2: Adoption Ramp

Inside `compute_pma_sso(...)`, adoption is calculated by segment and FCY as:

`adoption_rate = weighted_eligibility_uptake * ramp(fcy)`

Where:

- `weighted_eligibility_uptake = eligibility_rate_no_der * u(No_DER) + eligibility_rate_solar * u(Solar) + eligibility_rate_solar_battery * u(Solar_Battery)`
- `ramp(fcy)` is a linear rollout from `ramp_start_fcy` to `ramp_full_fcy`

Ramp rules:

- `0` before the start year
- `1` at or after the full-rollout year
- linear interpolation between those years

## Step 3: Daily Shift Energy

For each baseline group, the package first computes daily baseline energy:

`E_day = sum(underlying_demand_mw * interval_hours)`

Then it computes uncapped shift energy:

`E_shift = E_day * s(segment) * k_response * adoption_rate`

Where:

- `s(segment)` is the segment shiftable share
- `k_response` is the behavioural response multiplier

## Step 4: Participant Cap

Participants are estimated as:

`participants = n_total * adoption_rate`

Then the daily cap is applied:

- `E_cap_total = participants * cap_kwh_per_day / 1000`
- `E_shift_capped = min(E_shift, E_cap_total)`

## Step 5: Interval Allocation

The v0.1 model uses a flat allocation on both sides:

- flat uplift inside the configured free window
- flat donor reduction across the configured donor intervals

Window convention:

- start-inclusive
- end-exclusive
- interval numbering is 1-based
- overnight windows are supported

Donor-window convention:

- if `donor_window_start` and `donor_window_end` are omitted, donor intervals are the complement of the free window
- if an explicit donor window is supplied, only those donor intervals are reduced
- intervals outside both the free window and the explicit donor window stay at zero
- donor windows must not overlap the free window

The model converts allocated interval energy into MW by dividing by `interval_hours`.

## Step 6: Energy Neutrality

The PMA profile is intended to be energy-neutral within each baseline group:

- in-window uplift equals donor-window reduction
- group-level neutrality is checked by `validate_pma(...)`

## Current v0.1 Simplifications

The current public MVP intentionally keeps the model narrow:

- no season-specific behaviour adjustments
- no day-type-specific behaviour adjustments
- no representative-day-specific behaviour adjustments
- no rebound allocation logic
- only `flat` window and donor shapes
- only `energy_neutral` accounting

Those fields may exist in the YAML contract for future tiers, but they are not active in the v0.1 engine.
