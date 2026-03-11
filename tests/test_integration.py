from __future__ import annotations

import copy

from pyntlp import build_segment_metrics, compute_pma_sso, load_params, validate_pma


def test_end_to_end_package_flow_runs_on_normalised_data(spark, base_params):
    params = load_params(copy.deepcopy(base_params))

    baseline_profiles_df = spark.createDataFrame(
        [
            (2026, "v1", 1001, "Residential", 2026, "base", "POE50", "weekday", "summer", "business", 1, 1.0),
            (2026, "v1", 1001, "Residential", 2026, "base", "POE50", "weekday", "summer", "business", 2, 1.0),
            (2026, "v1", 1001, "Residential", 2026, "base", "POE50", "weekday", "summer", "business", 3, 1.0),
            (2026, "v1", 1001, "Residential", 2026, "base", "POE50", "weekday", "summer", "business", 4, 1.0),
        ],
        [
            "fc_run_year",
            "version",
            "fc_object_id",
            "segment",
            "fcy",
            "forecast_scenario",
            "poe",
            "representative_day",
            "season",
            "day_type",
            "interval",
            "underlying_demand_mw",
        ],
    )
    segment_attributes_df = spark.createDataFrame(
        [
            ("nmi-1", "Residential", "No_DER"),
            ("nmi-2", "Residential", "No_DER"),
        ],
        ["nmi", "segment", "der_type"],
    )
    smart_meter_df = spark.createDataFrame(
        [
            ("nmi-1", "SM"),
            ("nmi-2", "SM"),
        ],
        ["nmi", "meter_type_code"],
    )

    segment_metrics_df = build_segment_metrics(segment_attributes_df, smart_meter_df, params)
    pma_delta_df = compute_pma_sso(baseline_profiles_df, segment_metrics_df, params)
    validation_report_df = validate_pma(pma_delta_df, params)

    assert pma_delta_df.count() == 4
    assert pma_delta_df.columns == [
        "fc_run_year",
        "version",
        "fc_object_id",
        "segment",
        "fcy",
        "forecast_scenario",
        "poe",
        "representative_day",
        "season",
        "day_type",
        "interval",
        "pma_sso_mw",
    ]
    assert {row["status"] for row in validation_report_df.collect()} == {"PASS"}
