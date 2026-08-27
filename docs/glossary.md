# Glossary

## Executive Summary

This glossary explains the main terms used across the `pyntlp` documentation.
Some terms are electricity-network terms, while others are package-specific
contract names.

## PyNTLP

`PyNTLP` stands for Python for Network Tariff to Load Profile.

The package estimates how a network tariff design may change a load profile
under explicit modelling assumptions.

## Network Tariff

A network tariff is a charging structure for use of the electricity network.
Tariffs can encourage different customer behaviour depending on when, where, or
how electricity is imported or exported.

Examples include:

- time-of-use tariffs
- demand tariffs
- export tariffs
- location-based tariffs
- Solar Sharer Offer style tariffs

## Solar Sharer Offer

The Solar Sharer Offer, or SSO, is the first tariff structure implemented in
`pyntlp`.

It encourages eligible customers to move flexible electricity use into a daytime
window when local solar generation is more available.

## Load Profile

A load profile is a time series showing electricity demand across intervals in a
day or representative day.

In `pyntlp`, the baseline profile is the starting point. The model returns a
delta profile that can be added to the baseline.

## Baseline

The baseline is the original load profile before the tariff impact is applied.

The package does not create the baseline. It assumes the caller already has one.

## Delta

A delta is a change from the baseline.

In this package, `delta_mw` is the additive megawatt change for each interval:

```text
post_tariff_demand_mw = baseline_demand_mw + delta_mw
```

## Energy Neutral

Energy neutral means the model shifts energy across time without creating or
destroying daily energy within a model group.

For an energy-neutral group:

```text
sum(delta_mw * interval_hours) = 0
```

Positive intervals are balanced by negative intervals.

## Policy Window

The policy window is the target time window where the tariff is expected to
encourage extra electricity use.

For SSO, this is the Solar Sharer daytime window.

## Donor Window

The donor window is where shifted energy is removed from.

If no explicit donor window is supplied, `pyntlp` treats intervals outside the
policy window as donor intervals.

## Interval

An interval is a numbered time step in the representative day.

For 30-minute data, a day has 48 intervals. The package maps clock-time windows
to these interval numbers using `interval_minutes` and `intervals_per_day`.

## NMI

NMI stands for National Metering Identifier. It identifies a connection point in
the Australian electricity market.

In `pyntlp`, NMI-level inputs are used to build eligibility metrics by
`lga_segment`.

## Smart Meter

A smart meter is a metering type used as part of the eligibility calculation.

The package compares `meter_type_code` with the configured `smart_meter_code`.

## LGA Segment

`lga_segment` is the customer population segment used by the model. It is the
join key between baseline profile rows and eligibility metrics.

The full string is used for:

- residential eligibility pattern matching
- DER group suffix inference
- shiftability parameter lookup

## DER

DER stands for Distributed Energy Resource.

The current SSO model supports these DER suffix groups:

- `No_DER`
- `Solar`
- `Solar_Battery`

## `fc_object_id`

`fc_object_id` identifies the network or forecast object represented by a
baseline profile row.

The model output keeps this dimension. Participant caps are not calculated per
`fc_object_id`; they are calculated once per `lga_segment` population and then
allocated back to `fc_object_id` groups.

## FCY

`fcy` means forecast calendar year or forecast year, depending on the upstream
forecasting convention used by the caller.

The SSO model uses `fcy` to apply the adoption ramp.

## Adoption Ramp

The adoption ramp controls how uptake grows across forecast years.

Before `ramp_start_fcy`, the ramp is zero. From `ramp_full_fcy` onward, the ramp
is one. Between those years, it increases linearly.

## Participant Cap

The participant cap limits the amount of energy shifted based on the estimated
number of participating customers and `cap_kwh_per_day`.

This prevents modelled shifted energy from exceeding the population-based daily
cap.

## PMA

PMA refers to the planning/model adjustment output expected by the surrounding
forecasting workflow. In `pyntlp`, the PMA output is represented as interval
`delta_mw` values.
