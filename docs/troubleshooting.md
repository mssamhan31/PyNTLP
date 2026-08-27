# Troubleshooting

## Executive Summary

This page lists common issues when using `pyntlp`, what they usually mean, and
where to look first. It is aimed at notebook authors, analysts, and developers
debugging a model run.

## Parameter Loading Fails

Symptoms:

- `load_params(...)` raises an error before any Spark calculation runs
- a required key is reported missing
- a mode such as window shape or donor shape is rejected

Likely causes:

- the YAML file is missing a required `constants` or `parameters` key
- a numeric parameter is outside the accepted range
- a required mapping does not contain all expected DER groups
- `window_shape`, `donor_shape`, or `energy_accounting` is unsupported

What to check:

- compare the file with `src/pyntlp/resources/pyntlp_template.yaml`
- confirm `window_start` and `window_end` use `HH:MM` format
- confirm optional donor windows are supplied as a pair or both omitted
- confirm `s_lga_segment` contains a `default` value

## Missing Column Error

Symptoms:

- `ensure_required_columns(...)` reports missing columns
- the package fails at the start of metrics or model computation

Likely causes:

- source data has different column names
- a wrapper notebook did not rename columns before calling the package
- a source select dropped a required field

What to check:

- compare the DataFrame columns with [API contracts](api-contracts.md)
- inspect `df.columns` immediately before the package call
- keep source-to-package column mapping in one visible wrapper section

## Duplicate Baseline Key Error

Symptoms:

- `compute_pma_sso(...)` rejects duplicate baseline keys
- duplicates may appear even if `customer_type` differs

Likely causes:

- baseline data has more than one row for the same model interval key
- `customer_type` was expected to distinguish rows, but it is not a model key
- upstream aggregation did not collapse rows to the required grain

What to check:

- group the baseline by the model key listed in [API contracts](api-contracts.md)
- count keys with more than one row
- decide upstream whether duplicate rows should be summed, filtered, or fixed

## All Deltas Are Zero

Symptoms:

- `delta_mw` is zero for every row
- validation may still pass because zero deltas are energy-neutral

Likely causes:

- metrics coverage is missing for all baseline `lga_segment` values
- no segments match `eligible_resi_patterns`
- `meter_type_code` does not match `smart_meter_code`
- forecast year is before `ramp_start_fcy`
- `s_lga_segment.default` or `k_response` is zero
- there are no policy-window or donor-window intervals

What to check:

- count missing baseline segments after joining to metrics
- inspect `n_total`, `n_eligible`, and eligibility rates
- check the forecast years in `fcy`
- check window boundaries and interval settings
- compare the configured smart-meter code with source values

## Some Segments Have Zero Deltas

Symptoms:

- only particular `lga_segment` values produce zero deltas

Likely causes:

- those segments have no metrics coverage
- those segments are not residential under the configured patterns
- those segments have no smart-meter eligible customers
- the segment-specific `s_lga_segment` value is zero

What to check:

- left anti-join baseline segments against metrics segments
- inspect raw `lga_segment` strings for spelling or suffix differences
- check exact segment overrides in `s_lga_segment`

## Deltas Look Too Large

Symptoms:

- positive window deltas look larger than expected
- participant caps do not appear to be reducing enough

Likely causes:

- baseline daily energy is high for the group
- `s_lga_segment` is too high
- `k_response` is too high
- DER uptake assumptions are too high
- `cap_kwh_per_day` is high enough that it is not binding
- the same `lga_segment` appears under multiple objects and total uncapped
  energy is being allocated across them

What to check:

- compare uncapped shift energy with capped shift energy
- check whether the cap is binding
- confirm the cap is being interpreted at the segment population grain
- check whether the policy window has very few intervals, which concentrates
  shifted energy into larger MW changes

## Energy Neutrality Fails

Symptoms:

- `validate_pma(...)` reports a grouped energy-neutrality failure
- `sum(delta_mw * interval_hours)` is not close to zero for one or more groups

Likely causes:

- output rows were filtered after model computation
- output rows were duplicated after model computation
- interval duration in validation does not match the model parameters
- custom wrapper logic changed `delta_mw`

What to check:

- run validation immediately after `compute_pma_sso(...)`
- check for row-count changes after joins
- group by the model grain and sum `delta_mw * interval_hours`
- confirm the same `params` object is used for compute and validation

## Spark Tests Are Skipped

Symptoms:

- `python -m pytest` reports skipped Spark tests
- skip messages mention Java

Likely causes:

- Java is not installed
- `JAVA_HOME` is not set
- `java` is not on the system path

What to check:

- run `java -version`
- configure Java before relying on Spark-backed test results
- treat skipped Spark tests as unverified Spark behaviour, not as passing Spark
  behaviour

## Output Schema Does Not Match

Symptoms:

- validation reports missing columns, extra columns, or schema mismatch

Likely causes:

- wrapper code added columns before validation
- wrapper code changed column order
- `delta_mw` was renamed
- output was joined with another table before package validation

What to check:

- validate the direct output of `compute_pma_sso(...)`
- perform downstream joins after validation
- compare columns with the PMA output contract in [API contracts](api-contracts.md)
