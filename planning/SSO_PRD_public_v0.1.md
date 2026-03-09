# PRD v0.1 — pyntlp (Public Package)

Version: v0.1 (Draft)  
Product type: Public Spark-native Python package  
Package name: `pyntlp`  
Meaning: Python for Network Tariff to Load Profile  
Purpose: Provide a reusable, parameter-driven modelling toolkit that converts an SSO policy definition (free window + adoption ramp + behavioural response) into an additive interval PMA delta profile `pma_sso_mw`, suitable for downstream “baseline + PMA” workflows.

## 1) Product boundary
This PRD covers the public installable package only.

The public package owns:
- modelling logic
- Spark DataFrame APIs
- YAML template and parameter validation
- output schema contract
- unit and integration tests
- package build and versioning
- public documentation

The public package does **not** own:
- organisation-specific table names
- notebook paths
- Databricks catalog / schema / Unity Catalog settings
- internal write targets
- environment-specific defaults
- secrets, cluster config, or job orchestration

Those deployment and data-source responsibilities belong in the Databricks integration PRD.

## 2) Objective
Build `pyntlp` as a reusable, parameter-driven toolkit that can be installed with `pip install`, accept normalised Spark DataFrames plus a YAML config, and produce a deterministic `pma_sso_mw` delta table with no hard-coded organisation-specific assets.

## 3) Users and user needs
Primary developer user: a modeller or data scientist who wants a publishable, reusable methodology implemented as a Spark-native Python package.

Primary runtime user: a Databricks notebook or job that loads source tables, normalises them to the package contract, calls the package API, and writes outputs.

## 4) Final deliverables and formats
D1. Public Python package `pyntlp` (Spark-native), installable via `pip install`.

D2. Public YAML template shipped with the package. The template must contain placeholders and comments, but no organisation-specific table names or internal data locations.

D3. Package documentation that describes:
- required input DataFrame schemas
- YAML contract
- public API usage
- validation rules
- expected output schema

D4. Automated tests covering the minimal model.

## 5) Output data product
### 5.1 Output schema (MUST)
The package must return a Spark DataFrame with exactly this schema:

- `fc_run_year` (int)
- `version` (string)
- `fc_object_id` (int)
- `segment` (string)
- `fcy` (int)
- `forecast_scenario` (string)
- `poe` (string)
- `representative_day` (string)
- `season` (string)
- `day_type` (string)
- `interval` (int)
- `pma_sso_mw` (double)

Interpretation: `pma_sso_mw` is an additive delta (MW) at interval granularity. Downstream systems combine it with `underlying_demand_mw`.

## 6) Input contracts
The public package must consume **normalised** Spark DataFrames. It must not require any specific upstream table names.

### 6.1 Baseline profiles input (MUST)
Required columns:
- `fc_run_year`
- `version`
- `fc_object_id`
- `segment`
- `fcy`
- `forecast_scenario`
- `poe`
- `representative_day`
- `season`
- `day_type`
- `interval`
- `underlying_demand_mw`

Run scope:
- FCY range = whatever exists in the supplied baseline DataFrame.
- Output rows = one `pma_sso_mw` value for every baseline input row.

### 6.2 Customer / segment attributes input (MUST)
Required columns in the normalised segment-attribute DataFrame:
- `nmi`
- `segment`
- `der_type`

Optional extension columns:
- `lga`
- `lga_segment`
- other future segment attributes

### 6.3 Smart meter input (MUST for eligibility)
Required columns in the normalised smart-meter DataFrame:
- `nmi`
- `meter_type_code`

Join rule:
- `smart_meter_df.nmi` joins to `segment_attributes_df.nmi` to derive segment-level eligibility.

## 7) Constraints and assumptions (v0.1)
C1. Segment definitions may expand materially. The toolkit must not assume a fixed segment list.

C2. Eligibility for v0.1 modelling is:
- residential segment, identified from `segment` via configurable patterns
- smart meter, identified via configurable meter code
- eligible DER type, identified via configurable `der_type`

C3. The toolkit computes only the additive delta `pma_sso_mw`. Final post-policy demand is handled downstream.

C4. The toolkit returns a DataFrame. It does not write to storage directly.

## 8) YAML contract
The package must ship a YAML template with two top-level sections:

### 8.1 `constants:`
Rarely changed modelling and schema settings, for example:
- `model_name`
- `model_tier`
- `interval_minutes`
- `intervals_per_day`
- `timezone`
- `segment_column`
- `output_value_column`
- schema-version notes
- optional column-mapping placeholders for normalised in-memory DataFrames only

### 8.2 `parameters:`
Changeable policy and model knobs, with YAML comments describing usage and tier availability.

Required minimal knobs:
- `eligible_resi_patterns`
- `smart_meter_code`
- `eligible_der_type`
- `window_start`
- `window_end`
- `cap_kwh_per_day`
- `u_segment`
- `ramp_start_fcy`
- `ramp_full_fcy`
- `s_segment`
- `k_response`
- `window_shape`
- `donor_shape`
- `energy_accounting`

Optional enhanced knobs that may exist in the template but are not required for minimal execution:
- `season_modifiers`
- `daytype_modifiers`
- `rebound_share`
- `rebound_shape`

The public template must use placeholders or generic examples only.

## 9) Minimal viable model design (v0.1)
### 9.1 Segment-level eligibility rate
For each segment, compute:
- `n_total`: count of NMIs in segment
- `n_eligible`: count of NMIs matching all configured eligibility rules
- `eligibility_rate = n_eligible / n_total`

### 9.2 Adoption and participation rate
For each segment and FCY:
- `adoption_rate = eligibility_rate * u(segment) * r(fcy)`

Where:
- `u(segment)` is the uptake ceiling (0–1)
- `r(fcy)` is a linear ramp from 0 to 1:
  - `0` for `fcy < ramp_start_fcy`
  - `1` for `fcy >= ramp_full_fcy`
  - linear in-between

### 9.3 Energy shift amount
For each baseline group rowset (same keys as output except `interval`), compute:
- `E_day = Σ_interval underlying_demand_mw * interval_hours`
- `E_shift = E_day * s(segment) * k_response * adoption_rate`

Cap application:
- `participants = n_total * adoption_rate`
- `E_cap_total = participants * cap_kwh_per_day / 1000`
- `E_shift_capped = min(E_shift, E_cap_total)`

### 9.4 Interval allocation rules (minimal)
Let W be the set of window intervals and D all other intervals.

Minimal allocation:
- in-window uplift is flat across W
- donor reduction is flat across D
- deltas are energy-neutral within each baseline group

Conversion to MW:
- `pma_sso_mw(i) = delta_mwh(i) / interval_hours`

## 10) Public package design
Package name: `pyntlp`.

Required public API (minimum):
- `load_params(path_or_dict) -> dict`
- `build_segment_metrics(segment_attributes_df, smart_meter_df, params, segment_col="segment") -> segment_metrics_df`
- `compute_pma_sso(baseline_profiles_df, segment_metrics_df, params) -> pma_delta_df`
- `validate_pma(pma_delta_df, params) -> validation_report_df`

Recommended helper APIs:
- `get_window_intervals(params) -> (W, D, interval_hours)`
- `resolve_segment_parameter(segment, mapping, default_value)`

Engineering requirements:
- deterministic outputs for a given input snapshot + YAML
- semantic versioning
- unit tests for YAML validation, window mapping, energy-neutrality, cap binding, and ineligible-zero logic
- small sample integration test runnable in Spark

## 11) Acceptance criteria (v0.1)
A1. `pyntlp` produces one output row per baseline input row, with the required output schema.

A2. Segments failing configured eligibility rules have `pma_sso_mw == 0` for all intervals.

A3. Minimal model does not condition behaviour on `season`, `day_type`, or `representative_day`, even though outputs retain those dimensions.

A4. Public docs and YAML template contain no organisation-specific table names or private data references.

A5. The package can be installed into Databricks with `pip install` and called from a notebook using only normalised DataFrames plus YAML parameters.
