# Glossary

| term | meaning |
|---|---|
| PyNTLP | Python for Network: Tariff to Load Profile |
| Solar Sharer Offer (SSO) | a regulated retail electricity plan with three free hours in the middle of each day, the first tariff the package models |
| network tariff | a charging structure for use of the electricity network |
| load profile | electricity demand across the intervals of a day or representative day |
| baseline | the load profile before the tariff is applied; the caller supplies it |
| delta, `delta_mw` | the change to add to the baseline in each interval, in MW |
| energy neutral | energy is moved across the day, not created or destroyed |
| free window, policy window | the hours the tariff encourages use, which receive positive deltas |
| donor window | the intervals the shifted energy is taken from |
| interval | a numbered time step of the day; 48 for 30-minute data |
| NMI | National Metering Identifier, a connection point in the Australian market |
| smart meter | the meter type that makes a customer eligible |
| `lga_segment` | the customer population segment, the join key between baseline and metrics |
| DER | distributed energy resources; the segment suffix `No_DER`, `Solar` or `Solar_Battery` |
| `fc_object_id` | the network or forecast object a baseline row belongs to |
| FCY | forecast calendar year or forecast year, by the caller's convention |
| adoption ramp | how uptake grows across forecast years |
| participant cap | the most energy each participating customer can shift per day |
| PMA | post-model adjustment, the change applied to a forecast after the forecast model |

/// details | Show details
    type: more

## PyNTLP

PyNTLP stands for Python for Network: Tariff to Load Profile. The package estimates how a tariff
may change a load profile under explicit modelling assumptions.

## Solar Sharer Offer

The Solar Sharer Offer is a regulated electricity plan that retailers must offer from 1 July 2026
in the regions where the Default Market Offer applies: New South Wales, South East Queensland and
South Australia. It includes a three-hour period in the middle of each day when electricity is
free: 11:00 to 14:00 in New South Wales and South East Queensland, and 12:00 to 15:00 in South
Australia ([Energy Made Easy](https://www.energymadeeasy.gov.au/hot-topics/solar-sharer-offer-what-you-need-to-know)).
It is the first tariff structure implemented in `pyntlp`.

## Network tariff

A network tariff is a charging structure for use of the electricity network. Tariffs can encourage
different customer behaviour depending on when, where or how electricity is imported or exported.
Examples include time-of-use tariffs, demand tariffs, export tariffs, location-based tariffs and
free-window plans like the Solar Sharer Offer.

## Load profile and baseline

A load profile is a time series of electricity demand across the intervals of a day or
representative day. In `pyntlp` the baseline profile is the starting point: the original profile
before the tariff impact is applied. The package does not create the baseline; it assumes the
caller already has one, and returns a delta profile to add to it.

## Delta

A delta is a change from the baseline. In this package, `delta_mw` is the additive megawatt change
for each interval:

```text
post_tariff_demand_mw = baseline_demand_mw + delta_mw
```

## Energy neutral

Energy neutral means the model shifts energy across time without creating or destroying daily
energy within a model group. For an energy-neutral group:

```text
sum(delta_mw * interval_hours) = 0
```

Positive intervals are balanced by negative intervals.

## Free window and donor window

The free window, called the policy window in the code, is the period where the tariff is expected
to encourage extra electricity use. The donor window is where the shifted energy is removed from.
If no explicit donor window is supplied, `pyntlp` treats every interval outside the free window as
a donor interval.

## Interval

An interval is a numbered time step in the representative day. For 30-minute data a day has 48
intervals. The package maps clock-time windows to interval numbers using `interval_minutes` and
`intervals_per_day`.

## NMI and smart meter

NMI stands for National Metering Identifier; it identifies a connection point in the Australian
electricity market. In `pyntlp`, NMI-level inputs are used to build eligibility metrics by
`lga_segment`. A smart meter is the metering type used in the eligibility calculation: the package
compares `meter_type_code` with the configured `smart_meter_code`.

## LGA segment

`lga_segment` is the customer population segment used by the model and the join key between
baseline profile rows and eligibility metrics. The full string is used for residential eligibility
pattern matching, DER group suffix inference and shiftability parameter lookup.

## DER

DER stands for distributed energy resources. The model supports the DER suffix groups `No_DER`,
`Solar` and `Solar_Battery`.

## `fc_object_id`

`fc_object_id` identifies the network or forecast object a baseline profile row represents. The
output keeps this dimension. Participant caps are not calculated per `fc_object_id`; they are
calculated once per `lga_segment` population and then allocated back to the `fc_object_id` groups.

## FCY and adoption ramp

`fcy` means forecast calendar year or forecast year, depending on the caller's forecasting
convention. The model uses it for the adoption ramp: zero before `ramp_start_fcy`, one from
`ramp_full_fcy` onward, and a linear increase between.

## Participant cap

The participant cap limits the shifted energy by the estimated number of participating customers
and `cap_kwh_per_day`, so modelled shifted energy cannot exceed the population-based daily cap.

## PMA

PMA is the post-model adjustment, the change the surrounding forecasting workflow applies to a
forecast after the forecast model has run. In `pyntlp` it is the interval `delta_mw` values.

///
