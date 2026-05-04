# PyNTLP

## Executive Summary

`pyntlp` is a Spark-native Python package that converts Solar Sharer Offer
policy assumptions into additive PMA interval deltas.

At a high level, the package:

- reads validated policy/model parameters from YAML or a Python dictionary
- builds `lga_segment` eligibility metrics from NMI attributes and smart-meter data
- computes interval-level `delta_mw` values that mirror the FC2026 baseline shape
- keeps each model group energy-neutral by adding energy in the policy window and removing matching energy from donor intervals
- caps shifted energy once per `lga_segment` model population, then allocates that capped amount back across `fc_object_id` slices
- returns a small Spark validation report for schema, required values, and energy neutrality

The package deliberately does not know about Databricks tables, Ausgrid table
names, widgets, or dashboard write targets. Those belong in wrapper notebooks or
pipeline code. `pyntlp` owns the reusable model contract and Spark
transformations.

## What The Package Does

`pyntlp` turns a baseline demand profile into a PMA delta profile.

The baseline input contains one row per interval and model dimension, including
`baseline_demand_mw`. The PMA output preserves the same dimensional shape and
replaces the baseline value with `delta_mw`.

`delta_mw` is additive:

```text
post_sso_demand_mw = baseline_demand_mw + delta_mw
```

Positive `delta_mw` values are allocated into the configured Solar Sharer Offer
window. Negative `delta_mw` values are allocated into donor intervals. The sum
of `delta_mw * interval_hours` is expected to be zero within each model group.

## What The Package Does Not Do

`pyntlp` is deliberately narrow. It does not:

- read or write Databricks tables
- own production table names or catalog paths
- create dashboard tables
- apply notebook widgets
- decide whether a validation warning should stop an operational pipeline
- apply organisation-specific column mappings before the package API is called

That separation is intentional. The package is easier to test when it only
receives normalised Spark DataFrames and returns normalised Spark DataFrames.
Notebook or pipeline wrappers can then handle table IO, environment selection,
extra audit checks, and reporting.

## Public API

The public API is intentionally small:

```python
from pyntlp import (
    build_lga_segment_metrics,
    compute_pma_sso,
    load_params,
    validate_pma,
)
```

Typical usage:

```python
params = load_params("params.yaml")

lga_segment_metrics_df = build_lga_segment_metrics(
    lga_segment_attributes_df=nmi_info_df.select("nmi", "lga_segment"),
    smart_meter_df=customers_info_df.select("nmi", "meter_type_code"),
    params=params,
)

pma_delta_df = compute_pma_sso(
    baseline_profiles_df=baseline_profiles_df,
    lga_segment_metrics_df=lga_segment_metrics_df,
    params=params,
)

validation_report_df = validate_pma(pma_delta_df, params)
```

## End-To-End Flow

The package is normally used in four steps:

1. Load parameters with `load_params(...)`.
2. Build eligibility metrics with `build_lga_segment_metrics(...)`.
3. Compute PMA deltas with `compute_pma_sso(...)`.
4. Validate the output with `validate_pma(...)`.

The caller is responsible for reading/writing tables, applying source column
mappings, and deciding whether validation failures should stop a pipeline.

## Input Contracts

### Baseline Profiles

`compute_pma_sso(...)` requires these columns:

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
- `baseline_demand_mw`

`customer_type` is required by presence so the output can mirror the baseline
shape, but its value may be null. It is carried through as an output attribute
only. It is not used for eligibility, adoption, duplicate-key checks,
energy-neutrality grouping, or delta allocation.

### LGA Segment Attributes

`build_lga_segment_metrics(...)` requires:

- `nmi`
- `lga_segment`

The full `lga_segment` string is used for residential eligibility pattern
matching and DER suffix inference.

### Smart Meter Attributes

`build_lga_segment_metrics(...)` also requires:

- `nmi`
- `meter_type_code`

`meter_type_code` is compared with the configured `smart_meter_code` after
normalisation.

## Output Contract

`compute_pma_sso(...)` returns exactly:

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

The output is at interval granularity and is designed to mirror the baseline
dimensions.

## Model Logic

### Eligibility Metrics

Eligibility is calculated at `lga_segment` grain.

For each `lga_segment`, `build_lga_segment_metrics(...)` computes:

- total distinct NMI count
- eligible NMI count
- eligible counts by DER group
- eligibility rates by DER group
- total eligibility rate

Residential eligibility is matched against the full `lga_segment` string using
`eligible_resi_patterns`.

DER group is inferred from the suffix of `lga_segment`. Supported suffixes are:

- `No_DER`
- `Solar`
- `Solar_Battery`

If one NMI maps to multiple inferred DER groups, the package raises an error
instead of guessing which group should win.

### Adoption And Shift Energy

For each model group, the package calculates:

```text
daily_energy_mwh = sum(baseline_demand_mw * interval_hours)
eligible_uptake_rate = weighted DER eligibility rate
ramp_rate = linear ramp from ramp_start_fcy to ramp_full_fcy
adoption_rate = eligible_uptake_rate * ramp_rate
uncapped_shift_mwh = daily_energy_mwh * s_lga_segment * k_response * adoption_rate
```

`s_lga_segment` can provide exact lga_segment overrides. If no exact override is
present, `default` is used.

### Participant Cap

Participant caps are applied once per `lga_segment` model population, not once
per `fc_object_id`.

This matters when the same `lga_segment` appears under multiple `fc_object_id`
values. Eligibility metrics count the customer population once at
`lga_segment` grain, so the participant cap is also calculated once for that
population:

```text
participants = n_total * adoption_rate
population_cap_mwh = participants * cap_kwh_per_day / 1000
population_capped_shift_mwh = min(population_uncapped_shift_mwh, population_cap_mwh)
```

The capped population shift is then allocated back to `fc_object_id` groups by
their share of uncapped shift energy. This prevents the same segment-level
customer count from being multiplied across several network objects.

### Window And Donor Allocation

The policy window is start-inclusive and end-exclusive. Window times must align
to `interval_minutes`.

If `donor_window_start` and `donor_window_end` are supplied, only that explicit
donor window donates energy. If they are omitted, every interval outside the
policy window is a donor interval.

Shifted energy is allocated flatly across policy-window intervals and removed
flatly from donor intervals. The current public engine supports:

- `window_shape: flat`
- `donor_shape: flat`
- `energy_accounting: energy_neutral`

### Missing Metrics Coverage

If a baseline `lga_segment` has no matching metrics row, the model keeps the
baseline row and treats eligibility as zero for that segment. This preserves
output shape and produces zero deltas for uncovered segments.

Callers should still surface missing coverage operationally. The package keeps
the model permissive, while wrapper notebooks or pipelines can report missing
metrics as non-breaking validation information.

## Parameter Contract

Parameters can be loaded from a YAML path or dictionary:

```python
params = load_params("params.yaml")
```

Required `constants`:

- `model_name`
- `model_tier`
- `interval_minutes`
- `intervals_per_day`
- `timezone`

Required `parameters`:

- `eligible_resi_patterns`
- `smart_meter_code`
- `window_start`
- `window_end`
- `cap_kwh_per_day`
- `u_eligible_der_group`
- `ramp_start_fcy`
- `ramp_full_fcy`
- `s_lga_segment`
- `k_response`
- `window_shape`
- `donor_shape`
- `energy_accounting`

Optional accepted parameters:

- `donor_window_start`
- `donor_window_end`
- `season_modifiers`
- `daytype_modifiers`
- `rebound_share`
- `rebound_shape`

The optional modifier/rebound fields are accepted as part of the public
configuration surface, but the v0.1 engine does not use them in the PMA delta
calculation.

An example template is shipped at:

```text
src/pyntlp/resources/pyntlp_template.yaml
```

## Validation

`validate_pma(pma_delta_df, params)` returns a Spark DataFrame with:

- `check_name`
- `status`
- `detail`

Current package validation checks:

- exact output schema and column order
- missing or extra output columns
- required non-null output columns
- grouped energy neutrality

Package validation is intentionally small and portable. Operational wrappers can
add table-read checks, row-count checks, missing metrics coverage, dashboard
coverage, or audit-specific validations.

## Debugging A Run

When a PMA run does not look right, debug it in this order:

1. Check parameter loading first.

   `load_params(...)` validates the shape of the YAML/dictionary and rejects
   unsupported window shapes, donor shapes, and energy-accounting modes. If this
   fails, the model has not started yet.

2. Check metrics coverage next.

   `build_lga_segment_metrics(...)` returns one row per `lga_segment`. If a
   baseline segment has no metrics row, `compute_pma_sso(...)` keeps the output
   shape but produces zero deltas for that segment. That behaviour is
   non-breaking by design, but callers should report missing coverage so it is
   visible.

3. Check daily energy and uptake assumptions.

   Large or small deltas usually come from baseline energy, DER eligibility
   rates, `s_lga_segment`, `k_response`, ramp year, or `cap_kwh_per_day`.

4. Check the participant cap grain.

   The cap is calculated once for the `lga_segment` population at the model
   scenario grain, excluding `fc_object_id`. The capped energy is then allocated
   back to each `fc_object_id` by its share of uncapped shift energy. This is the
   expected behaviour when multiple network objects share the same segment.

5. Check energy neutrality last.

   `validate_pma(...)` groups output rows at the model grain and checks that
   `sum(delta_mw * interval_hours)` is approximately zero. A failure here means
   the output should not be treated as a valid energy-neutral PMA delta set.

## Installation And Development

Install locally in editable mode:

```bash
pip install -e .[dev]
```

Run tests:

```bash
python -m pytest
```

Spark-backed tests require Java. If Java is not available, pure-Python tests run
and Spark tests are skipped.

## Repository Layout

```text
PyNTLP/
|-- README.md
|-- pyproject.toml
|-- src/pyntlp/
|   |-- params.py
|   |-- metrics.py
|   |-- model.py
|   |-- validation.py
|   |-- windows.py
|   |-- schema.py
|   `-- resources/
|-- tests/
`-- docs/
```

Key modules:

- `params.py`: parameter loading and contract validation
- `metrics.py`: NMI and smart-meter eligibility metrics
- `model.py`: PMA delta calculation and cap allocation
- `validation.py`: package-level output validation
- `windows.py`: interval/window mapping
- `schema.py`: shared column and schema constants

## Further Documentation

More detail is available in:

- [API contracts](docs/api-contracts.md)
- [Model overview](docs/model-overview.md)
- [Development notes](docs/development.md)
- [Repository structure](docs/repo-structure.md)
