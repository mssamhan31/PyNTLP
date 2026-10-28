# Assumptions and limitations

The current `pyntlp` model is a first public Solar Sharer Offer model: small, explicit and
testable. It is not yet a general tariff simulation engine. Its output is only as reliable as the
assumptions and input data it is given.

## What the model assumes

- **Behaviour is set by parameters, not estimated.** Eligible customer patterns, smart-meter
  eligibility, uptake by DER group, the shiftable share of daily energy by segment, a response
  multiplier, a forecast-year adoption ramp and a daily cap per participant are all inputs.
- **Energy is neutral.** What the free window gains, the donor intervals lose; there is no net new
  daily energy.
- **Allocation is flat.** Shifted energy is spread evenly across the free window and removed evenly
  from the donor intervals.
- **Eligibility is at `lga_segment` grain**, not per customer.
- **The participant cap applies once per `lga_segment` population**, not per network object.
- **Missing metrics mean zero shift**, so uncovered segments keep their rows with zero deltas.

/// details | Show details
    type: more

## Current tariff coverage

The implemented model covers the Solar Sharer Offer workflow. The package name is broader because
the intended direction is to support other tariff structures in later versions, which may need
different eligibility rules, allocation methods, validation checks and output contracts.

## Behavioural assumptions

The model uses explicit assumptions rather than estimating customer behaviour from first
principles. The behavioural inputs are:

- eligible customer patterns
- smart-meter eligibility
- DER-group uptake assumptions
- shiftable load share by segment
- response multiplier
- forecast-year adoption ramp
- daily participant cap

## Energy accounting

The engine supports energy-neutral shifting only. Energy added to the free window is removed from
the donor intervals. The model does not represent net new daily energy use from rebound, comfort
takeback or additional appliance use. Rebound-related configuration keys are accepted for contract
stability but are not used by the calculation.

## Window shape

The model supports flat allocation only, `window_shape: flat` and `donor_shape: flat`. It does not
yet model:

- shaped uptake within the free window
- customer-specific response curves
- weather-sensitive shifting
- different weekday and weekend response shapes
- rebound after the free window

## Eligibility grain

Eligibility is calculated at `lga_segment` grain. This keeps the public model compact, but it also
means the package does not model individual customer behaviour: NMI-level data is summarised into
eligibility, and the model applies those summaries to baseline profile groups.

## Participant cap grain

Participant caps are applied once per `lga_segment` population and model scenario, excluding
`fc_object_id`, so the same population is not counted again because it appears under several
network objects. The capped amount is allocated back to each `fc_object_id` by its share of the
uncapped shift energy.

## Missing coverage

Missing metrics coverage is non-breaking: if a baseline `lga_segment` has no metrics row, its
output rows are kept, eligibility is treated as zero and `delta_mw` is zero. This protects the
output shape, but it can hide data-quality problems if callers do not report missing coverage.
Wrapper notebooks should surface it as an operational diagnostic.

## Data quality

The package validates required columns and duplicate model keys, but it does not prove that source
data is semantically correct. Callers should still check:

- source row counts
- null rates in key columns
- unexpected `lga_segment` labels
- unsupported DER suffixes
- smart-meter code distributions
- baseline demand ranges
- duplicate source records before aggregation

## Interpretation limits

PyNTLP estimates load-profile impacts under stated assumptions. It does not decide whether a tariff
should be adopted, whether it is fair, whether the uptake assumptions are realistic, whether the
result is commercially optimal, or whether the modelled outcome will occur in practice. Those
questions need policy, regulatory, customer and commercial analysis outside this package.

## Extension direction

Future tariff structures may need additional public compute functions, tariff-specific parameter
sections, non-flat allocation shapes, optional rebound modelling, export-side profile impacts,
stronger scenario metadata and richer validation reports. When extending the package, keep the
public contracts explicit and document which assumptions are tariff-specific and which are shared.

///
