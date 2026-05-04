# Assumptions And Limitations

## Executive Summary

This page documents what the current `pyntlp` implementation assumes, what it
does not yet model, and what should be treated carefully when interpreting
results.

The current implementation is a first public SSO model. It is intentionally
small, explicit, and testable. It is not yet a general tariff simulation engine,
although the project goal is to support broader network tariff structures over
time.

## Current Tariff Coverage

The implemented model covers the Solar Sharer Offer workflow.

The package name is broader than SSO because the intended direction is to
support other tariff structures in future versions. Those future structures may
need different eligibility rules, allocation methods, validation checks, and
output contracts.

## Behavioural Assumptions

The SSO model uses explicit assumptions rather than estimating customer
behaviour from first principles.

Important behavioural inputs include:

- eligible customer patterns
- smart-meter eligibility
- DER-group uptake assumptions
- shiftable load share by segment
- response multiplier
- forecast-year adoption ramp
- daily participant cap

The model output is only as reliable as those assumptions and the input data
used with them.

## Energy Accounting

The current engine supports energy-neutral shifting.

This means energy added to the SSO policy window is removed from donor
intervals. The model does not currently represent net new daily energy use from
rebound, comfort takeback, or additional appliance usage.

Optional rebound-related configuration keys are accepted for public contract
stability, but they are not used by the v0.1 calculation.

## Window Shape

The current model supports flat allocation only:

- `window_shape: flat`
- `donor_shape: flat`

Flat allocation means the model spreads shifted energy evenly across receiving
intervals and removes energy evenly from donor intervals.

It does not yet model:

- shaped uptake within the SSO window
- customer-specific response curves
- weather-sensitive shifting
- different weekday/weekend response shapes
- rebound after the policy window

## Eligibility Grain

Eligibility is calculated at `lga_segment` grain.

This keeps the public model compact, but it also means the package does not
model individual-customer behaviour. NMI-level data is used to summarise
eligibility, then the model applies those summaries to baseline profile groups.

## Participant Cap Grain

Participant caps are applied once per `lga_segment` population and model
scenario, excluding `fc_object_id`.

This assumes the same `lga_segment` population should not be counted again just
because it appears under multiple network objects. The capped amount is
allocated back to each `fc_object_id` by its share of uncapped shift energy.

## Missing Coverage

Missing metrics coverage is non-breaking.

If a baseline `lga_segment` has no metrics row:

- the output rows are retained
- eligibility is treated as zero
- `delta_mw` is zero

This protects output shape, but it can hide data-quality issues if callers do
not report missing coverage. Wrapper notebooks should surface missing coverage
as an operational diagnostic.

## Data Quality

The package validates required columns and duplicate model keys, but it does
not prove that source data is semantically correct.

Callers should still check:

- source row counts
- null rates in key columns
- unexpected `lga_segment` labels
- unsupported DER suffixes
- smart-meter code distributions
- baseline demand ranges
- duplicate source records before aggregation

## Interpretation Limits

PyNTLP estimates load-profile impacts under stated assumptions. It does not
decide:

- whether a tariff should be adopted
- whether a tariff is fair
- whether customer uptake assumptions are realistic
- whether the result is commercially optimal
- whether the modelled outcome will occur in practice

Those questions require policy, regulatory, customer, and commercial analysis
outside this package.

## Extension Direction

Future tariff structures may need:

- additional public compute functions
- tariff-specific parameter sections
- non-flat allocation shapes
- optional rebound modelling
- export-side profile impacts
- stronger scenario metadata
- richer validation reports

When extending the package, keep the public contracts explicit and document
which assumptions are tariff-specific versus shared across tariff models.
