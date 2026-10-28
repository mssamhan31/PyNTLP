# Troubleshooting

Common problems with a `pyntlp` run, and where to look first.

| symptom | first thing to check |
|---|---|
| `load_params(...)` fails | compare the file with `src/pyntlp/resources/pyntlp_template.yaml`; times are `HH:MM` |
| missing column error | the DataFrame's columns against [API contracts](api-contracts.md), just before the call |
| duplicate baseline key error | rows sharing the model key; `customer_type` does not distinguish rows |
| every delta is zero | metrics coverage, `eligible_resi_patterns`, `smart_meter_code`, `fcy` against the ramp years |
| some segments have zero deltas | those segments' metrics rows and their `lga_segment` spelling |
| deltas look too large | whether the participant cap is binding, and how few intervals the window has |
| energy neutrality fails | rows filtered, duplicated or changed after `compute_pma_sso(...)` |
| Spark tests are skipped | Java: run `java -version` and set `JAVA_HOME` |
| output schema does not match | validate the direct output of `compute_pma_sso(...)`, before any join |

/// details | Show details
    type: more

## Parameter loading fails

Symptoms: `load_params(...)` raises an error before any Spark calculation runs; a required key is
reported missing; a mode such as window shape or donor shape is rejected.

Likely causes: the YAML file is missing a required `constants` or `parameters` key; a numeric
parameter is outside the accepted range; a required mapping does not contain all expected DER
groups; `window_shape`, `donor_shape` or `energy_accounting` is unsupported.

What to check:

- compare the file with `src/pyntlp/resources/pyntlp_template.yaml`
- confirm `window_start` and `window_end` use `HH:MM` format
- confirm optional donor windows are supplied as a pair or both omitted
- confirm `s_lga_segment` contains a `default` value

## Missing column error

Symptoms: `ensure_required_columns(...)` reports missing columns; the package fails at the start
of metrics or model computation.

Likely causes: the source data has different column names; a wrapper notebook did not rename
columns before calling the package; a source select dropped a required field.

What to check:

- compare the DataFrame columns with [API contracts](api-contracts.md)
- inspect `df.columns` immediately before the package call
- keep the source-to-package column mapping in one visible wrapper section

## Duplicate baseline key error

Symptoms: `compute_pma_sso(...)` rejects duplicate baseline keys, even when `customer_type`
differs.

Likely causes: the baseline has more than one row for the same model interval key;
`customer_type` was expected to distinguish rows, but it is not a model key; upstream aggregation
did not collapse rows to the required grain.

What to check:

- group the baseline by the model key listed in [API contracts](api-contracts.md)
- count keys with more than one row
- decide upstream whether duplicate rows should be summed, filtered or fixed

## All deltas are zero

Symptoms: `delta_mw` is zero for every row; validation may still pass, because zero deltas are
energy-neutral.

Likely causes: metrics coverage is missing for every baseline `lga_segment`; no segment matches
`eligible_resi_patterns`; `meter_type_code` does not match `smart_meter_code`; the forecast year is
before `ramp_start_fcy`; `s_lga_segment.default` or `k_response` is zero; there are no free-window
or donor-window intervals.

What to check:

- count missing baseline segments after joining to the metrics
- inspect `n_total`, `n_eligible` and the eligibility rates
- check the forecast years in `fcy`
- check the window boundaries and interval settings
- compare the configured smart-meter code with the source values

## Some segments have zero deltas

Symptoms: only particular `lga_segment` values produce zero deltas.

Likely causes: those segments have no metrics coverage; they are not residential under the
configured patterns; they have no smart-meter eligible customers; their segment-specific
`s_lga_segment` value is zero.

What to check:

- left anti-join the baseline segments against the metrics segments
- inspect the raw `lga_segment` strings for spelling or suffix differences
- check exact segment overrides in `s_lga_segment`

## Deltas look too large

Symptoms: positive window deltas look larger than expected; participant caps do not seem to reduce
them enough.

Likely causes: the group's baseline daily energy is high; `s_lga_segment`, `k_response` or the DER
uptake assumptions are too high; `cap_kwh_per_day` is high enough that it does not bind; the same
`lga_segment` appears under several objects and the total uncapped energy is being allocated
across them.

What to check:

- compare uncapped shift energy with capped shift energy
- check whether the cap binds
- confirm the cap is interpreted at the segment population grain
- check whether the free window has very few intervals, which concentrates the shifted energy into
  larger MW changes

## Energy neutrality fails

Symptoms: `validate_pma(...)` reports a grouped energy-neutrality failure;
`sum(delta_mw * interval_hours)` is not close to zero for one or more groups.

Likely causes: output rows were filtered or duplicated after model computation; the interval
duration in validation does not match the model parameters; custom wrapper logic changed
`delta_mw`.

What to check:

- run validation immediately after `compute_pma_sso(...)`
- check for row-count changes after joins
- group by the model grain and sum `delta_mw * interval_hours`
- confirm the same `params` object is used for compute and validation

## Spark tests are skipped

Symptoms: `python -m pytest` reports skipped Spark tests, with skip messages mentioning Java.

Likely causes: Java is not installed, `JAVA_HOME` is not set, or `java` is not on the system path.

What to check: run `java -version` and configure Java before relying on Spark-backed results. A
skipped Spark test is unverified Spark behaviour, not passing Spark behaviour.

## Output schema does not match

Symptoms: validation reports missing columns, extra columns or a schema mismatch.

Likely causes: wrapper code added columns or changed the column order before validation;
`delta_mw` was renamed; the output was joined with another table before package validation.

What to check:

- validate the direct output of `compute_pma_sso(...)`
- perform downstream joins after validation
- compare the columns with the PMA output contract in [API contracts](api-contracts.md)

///
