# PyNTLP

`pyntlp` is a Spark-native Python package for converting SSO policy assumptions into additive PMA interval deltas using `lga_segment` eligibility metrics.

The FC2026 public contract mirrors the baseline table shape:

- baseline input uses the baseline dimensions plus `baseline_demand_mw`
- NMI attributes use only `nmi` and `lga_segment`
- PMA output uses the same dimensions, replacing `baseline_demand_mw` with `delta_mw`

`customer_type` is an output attribute only. It must be present in the
baseline input so it can be carried to the PMA output, but it may be null and
is not used for eligibility, adoption, energy-neutrality grouping, or delta
allocation.

## API

```python
from pyntlp import (
    build_lga_segment_metrics,
    compute_pma_sso,
    load_params,
    validate_pma,
)

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

## Required Input Columns

Baseline profiles:

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

NMI attributes:

- `nmi`
- `lga_segment`

Smart meter attributes:

- `nmi`
- `meter_type_code`

## Output Columns

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

`delta_mw` is an additive MW delta at interval granularity.
