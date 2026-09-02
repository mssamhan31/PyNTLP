# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Two independent codebases in one repo

1. `src/pyntlp/` — the **production** package. Spark-native (PySpark 4.x, Python 3.12 only),
   implements the Solar Sharer Offer tariff-to-load-profile model. Installed as `pyntlp`.
2. `publication/1_conference/` — **standalone research code** for the IEEE PES ISGT Asia 2026
   paper on Adaptive Quantile Flexibility (AQF). Plain numpy/pandas/scipy/sklearn/matplotlib,
   **no Spark**, own `requirements.txt`. Its conventions are in "Conference paper (AQF)"
   below; `publication/1_conference/README.md` covers the folder layout.

Nothing in `publication/` is imported by the package, and `src/pyntlp/` must not be modified as
a side effect of paper work. The long-term intent is that AQF eventually replaces the
hand-picked `s_lga_segment` shiftable-share constant with a data-calibrated estimate; that port
has not been done.

## Commands

```powershell
pip install -e .[dev]          # editable install + pytest
python -m pytest               # full suite (testpaths = tests, addopts = -ra)
python -m pytest tests/test_model.py::test_name    # single test
python -m compileall src tests # syntax check for behaviour changes
git diff --check               # whitespace/patch hygiene before committing
```

There is no ruff/black/mypy configuration in this repo — the three commands above are the
verification set described in `docs/development.md`. CI (`.github/workflows/ci.yml`) splits the
suite into a **quick** job (`test_import_smoke`, `test_params`, `test_windows`, no Java) and a
**spark** job (`test_metrics`, `test_model`, `test_integration`, Java 17).

Spark tests need a JVM. The `spark` fixture in `tests/conftest.py` calls `pytest.skip` when
neither `JAVA_HOME` nor `java` on PATH is found, so on a machine without Java the Spark tests
report as skipped, not failed. **A skipped Spark test is not a passed one** — any model-logic
change must eventually run somewhere with Java before being called verified.

## Package architecture

The package is a library of pure Spark transformations, deliberately table-agnostic: callers own
all IO, table names, widgets, and orchestration, and pass in already-normalised DataFrames. Six
public functions are exported from `src/pyntlp/__init__.py`; everything else is internal.

The pipeline is linear and each stage has one grain:

1. `load_params(path_or_dict)` — validates the two-section YAML contract (`constants`,
   `parameters`) and returns a plain dict reused by every later call. It rejects unsupported
   calculation modes and also rejects *removed* legacy keys (`segment_column`,
   `output_value_column`, `eligible_der_groups`, `s_segment`) rather than ignoring them.
2. `build_lga_segment_metrics(lga_segment_attributes_df, smart_meter_df, params)` — collapses
   NMI-level attributes to one row per `lga_segment`, with counts and eligibility rates split by
   DER group (`No_DER`, `Solar`, `Solar_Battery`, inferred from the `lga_segment` suffix). An NMI
   appearing in more than one inferred DER group is an error, not a warning.
3. `compute_pma_sso(baseline_profiles_df, lga_segment_metrics_df, params)` — returns *additive*
   interval deltas, so the caller computes `post_sso_demand_mw = baseline_demand_mw + delta_mw`.
   It never returns a new profile.
4. `validate_pma(pma_delta_df, params)` — a small Spark report DataFrame
   (`check_name`, `status`, `detail`) checking schema, non-nulls, and energy neutrality.

### Invariants that the tests and the docs both enforce

- **`schema.py` is the single source of truth** for required columns, grouping keys, output
  ordering, and the output Spark schema. The other constant lists (`OUTPUT_KEY_COLUMNS`,
  `MODEL_INTERVAL_KEY_COLUMNS`, `GROUP_COLUMNS`) are derived from `OUTPUT_COLUMNS` by
  comprehension — change the base list, not the derivations. Output column order is part of the
  public contract.
- **`customer_type` is a carried attribute, not a model dimension.** It is required by presence,
  its value may be null, and it takes no part in eligibility, duplicate-key detection,
  energy-neutrality grouping, or delta allocation. Duplicate baseline rows are rejected on the
  model key even when `customer_type` differs.
- **The participant cap is applied once per `lga_segment` population**, excluding `fc_object_id`,
  then allocated back to the object-level groups. Applying it per `fc_object_id` would multiply
  the same segment NMI count across slices. This is the main over-counting hazard in `model.py`
  and is why cap changes must be tested across several `fc_object_id` values sharing one segment.
- **Missing `lga_segment` metrics are non-breaking**: a left join plus zero-fill, so uncovered
  segments keep their output rows with `delta_mw = 0`.
- Energy is neutral within each model group: positive deltas inside the policy window, matching
  negative deltas across donor intervals.

Some optional parameters (`season_modifiers`, `daytype_modifiers`, `rebound_share`,
`rebound_shape`, `donor_window_*`) are accepted by validation to keep the config surface stable
but are **not used** by the v0.1 delta calculation. Only `window_shape: flat`,
`donor_shape: flat`, and `energy_accounting: energy_neutral` are implemented.

## Conference paper (AQF)

Read this before touching anything under `publication/1_conference/`. The deadline is fixed
and the page limit is hard, so these are settled decisions, not preferences.

### This folder produces results, not prose

The manuscript-generation layer (`build_docx.py`, `references.py`, `preview.py`, the OMML
equation data and the vendored IEEE template) was **deliberately removed**. Manuscript text is
drafted by the author outside this repo; the paper is not built from code here, and no paper
prose belongs in a Python string literal. Do not reintroduce a document generator, a
bibliography module, or manuscript body text. What this folder owes the paper is figures,
tables and reproducible numbers — nothing else.

### Working conventions

- `src/config.py` is the **single source of truth** for every grid value, seed, and threshold.
  Add new constants there rather than inline.
- Every number quoted in the paper must be read from `data/3_gold/tables/*.csv`. Never
  hand-type a result into the manuscript.
- Data tiers: `1_bronze` raw simulated days (gitignored, regenerable) → `2_silver`
  per-scenario/replicate estimates → `3_gold` aggregated tables and figures.
- Figures use Arial, which is installed on this Windows machine. Do not change the font stack
  in `plotting.py`.
- Figures are authored at their FINAL printed width (`config.FIG_COL_W_IN` / `FIG_FULL_W_IN`,
  one IEEE column and both columns) and saved with `layout="constrained"` and **no**
  `bbox_inches="tight"`. Tight bboxes crop the canvas, so whatever places the image has to
  scale it back up and every point size in the figure silently changes.
  `plotting.check_widths()` asserts this and runs as part of `python plotting.py`.
- The paper prints `table3_headline_results.csv`; `table4_win_counts.csv` is quoted in prose.

### Claims that are easy to get wrong

- `estimators.identifiability_diagnostic` returns `kappa/sqrt(2)`, which is Ashman's D
  **rescaled by 1/sqrt(2)**:
  for a tied-variance mixture Ashman's own statistic evaluates to kappa itself, so gating at
  D >= 2 here is the stricter bar kappa >= 2.83, not Ashman's kappa > 2. The paper therefore
  says "a bimodality bar in the spirit of Ashman's D" and does not claim the statistic IS
  Ashman's D. Do not relabel it, and do not reinstate "the conventional requirement" wording.
  (Open option, not taken: define D = kappa with D_th = 2*sqrt(2); the blend weight is
  algebraically identical, so results would not change, but every figure annotation and slide
  would need editing.)
- Terminology is unified as "event frequency p" (never persistence), "event size kappa",
  "backbone", "candidate flexibility", "oracle-q". Oracle-q is deliberately NOT called an upper
  bound or ceiling — it takes an empirical quantile of D days, so AQF beats it on backbone
  error wherever kappa >= 4 (32 of 100 cells). The paper states this.
- `fallback_blend` in `estimators.py` clips the blended quantile at 0.5. Provably a no-op for
  the current q* form (empirical max q_used = 0.4875 over all 10,000 runs), so results are
  unchanged; it backs the paper's "capped at the median" claim.

### Regenerating everything

```powershell
cd publication\1_conference\src
python experiment.py          # -> bronze, silver, gold tables
python experiment.py tables   # -> gold tables only, from the existing recoverability summary
python plotting.py            # -> 5 figures (checks each PNG's printed width)
```

### Model recap (for orientation)

Fixed timestamp, D = 365 days: `L = B + Z*A + eps`, `Z ~ Bernoulli(p)`, `eps ~ N(0, sigma^2)`,
`kappa = A/sigma`. Backbone is estimated as a quantile of L. AQF picks the bias-minimising
quantile `q* = (1-p)/2 + p*Phi(-kappa)` from EM-estimated `p_hat, kappa_hat`, with an
identifiability check (`D = kappa/sqrt(2)`, threshold 2.0) and a soft blend toward
`q_default = 0.2` when separation is weak.

## Documentation contract

`docs/` is the technical manual and is expected to stay in step with the code: behaviour changes
update `README.md`, the relevant `docs/` page, the tests, and `CHANGELOG.md` for release-facing
changes. `docs/api-contracts.md` is the authoritative public contract; `docs/development.md`
carries the pre-merge review checklist. Keep all of it public-facing and generic — Ausgrid table
names, catalogs, notebooks, and deployment specifics belong in the wrapper repo, not here.
