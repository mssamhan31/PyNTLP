from __future__ import annotations

import copy

from pyntlp import build_segment_metrics, load_params


def test_build_segment_metrics_computes_expected_eligibility_rates(spark, base_params):
    params = load_params(copy.deepcopy(base_params))

    segment_attributes_df = spark.createDataFrame(
        [
            ("nmi-1", "Residential", "EV"),
            ("nmi-2", "Residential", "EV"),
            ("nmi-3", "Residential", "SOLAR"),
            ("nmi-4", "Commercial", "EV"),
        ],
        ["nmi", "segment", "der_type"],
    )
    smart_meter_df = spark.createDataFrame(
        [
            ("nmi-1", "SM"),
            ("nmi-2", "LEGACY"),
            ("nmi-3", "SM"),
            ("nmi-4", "SM"),
        ],
        ["nmi", "meter_type_code"],
    )

    metrics_rows = {
        row["segment"]: row.asDict()
        for row in build_segment_metrics(segment_attributes_df, smart_meter_df, params).collect()
    }

    assert metrics_rows["Residential"]["n_total"] == 3
    assert metrics_rows["Residential"]["n_eligible"] == 1
    assert metrics_rows["Residential"]["eligibility_rate"] == 1.0 / 3.0

    assert metrics_rows["Commercial"]["n_total"] == 1
    assert metrics_rows["Commercial"]["n_eligible"] == 0
    assert metrics_rows["Commercial"]["eligibility_rate"] == 0.0

