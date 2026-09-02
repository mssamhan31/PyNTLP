# Changelog

## Unreleased

## 0.2.0

- Added `pma_sso_pct_of_underlying` to the package PMA output schema.
- Updated the Databricks testing network peak table to use the network 17:00 row and scenario PMA values.
- Added the Adaptive Quantile Flexibility (AQF) conference paper pipeline under
  `publication/1_conference/`: experiment, estimators, metrics, figures, and the
  gold result tables. Standalone research code, not imported by the package.
- Added `CITATION.cff` and `.zenodo.json` so releases are archived and citable
  with correct authorship.
- Corrected the package author metadata in `pyproject.toml`.
- Pinned `publication/1_conference/requirements.txt` to the versions the
  committed artifacts were produced with, and added the missing `pillow`
  dependency used by the figure width check.
- Removed two unused figure functions from the AQF plotting module and corrected
  stale references to a renamed estimator function and a renamed results table.
- Documented the AQF stage in the root README and added `publication/` to the
  repository structure page.

## 0.1.0

- Initial public MVP for the `pyntlp` package.
- Added YAML parameter loading and validation.
- Added interval window utilities.
- Added lga_segment eligibility metrics.
- Added PMA SSO delta computation and validation helpers.
- Added unit and Spark integration tests.
