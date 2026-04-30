from __future__ import annotations

import copy

from pyntlp import build_lga_segment_metrics, compute_pma_sso, load_params, validate_pma


def test_end_to_end_package_flow_runs_on_normalised_data(spark, base_params):
    params = load_params(copy.deepcopy(base_params))

    baseline_profiles_df = spark.createDataFrame(
        [
            (1001, "Central Coast (NSW)_Large Res - NoOP - No_DER", "base", 2026, "summer", "business", "weekday", 1, 1.0),
            (1001, "Central Coast (NSW)_Large Res - NoOP - No_DER", "base", 2026, "summer", "business", "weekday", 2, 1.0),
            (1001, "Central Coast (NSW)_Large Res - NoOP - No_DER", "base", 2026, "summer", "business", "weekday", 3, 1.0),
            (1001, "Central Coast (NSW)_Large Res - NoOP - No_DER", "base", 2026, "summer", "business", "weekday", 4, 1.0),
        ],
        [
            "fc_object_id",
            "lga_segment",
            "scenario",
            "fcy",
            "season",
            "day_type",
            "representative_day",
            "interval",
            "baseline_demand_mw",
        ],
    )
    lga_segment_attributes_df = spark.createDataFrame(
        [
            ("nmi-1", "Central Coast (NSW)_Large Res - NoOP - No_DER"),
            ("nmi-2", "Central Coast (NSW)_Large Res - NoOP - No_DER"),
        ],
        ["nmi", "lga_segment"],
    )
    smart_meter_df = spark.createDataFrame(
        [
            ("nmi-1", "SM"),
            ("nmi-2", "SM"),
        ],
        ["nmi", "meter_type_code"],
    )

    lga_segment_metrics_df = build_lga_segment_metrics(lga_segment_attributes_df, smart_meter_df, params)
    pma_delta_df = compute_pma_sso(baseline_profiles_df, lga_segment_metrics_df, params)
    validation_report_df = validate_pma(pma_delta_df, params)

    assert pma_delta_df.count() == 4
    assert pma_delta_df.columns == [
        "fc_object_id",
        "lga_segment",
        "scenario",
        "fcy",
        "season",
        "day_type",
        "representative_day",
        "interval",
        "delta_mw",
    ]
    assert {row["status"] for row in validation_report_df.collect()} == {"PASS"}
