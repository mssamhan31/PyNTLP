from __future__ import annotations

import copy

import pytest

from pyntlp import build_segment_metrics, load_params


def test_build_segment_metrics_computes_expected_eligibility_rates(spark, base_params):
    params = load_params(copy.deepcopy(base_params))

    segment_attributes_df = spark.createDataFrame(
        [
            ("nmi-1", "Residential", "No_DER"),
            ("nmi-2", "Residential", "Solar"),
            ("nmi-3", "Residential", "Solar_Battery"),
            ("nmi-4", "Residential", "Solar"),
            ("nmi-5", "Commercial", "No_DER"),
        ],
        ["nmi", "segment", "der_type"],
    )
    smart_meter_df = spark.createDataFrame(
        [
            ("nmi-1", "SM"),
            ("nmi-2", "SM"),
            ("nmi-3", "SM"),
            ("nmi-4", "LEGACY"),
            ("nmi-5", "SM"),
        ],
        ["nmi", "meter_type_code"],
    )

    metrics_rows = {
        row["segment"]: row.asDict()
        for row in build_segment_metrics(segment_attributes_df, smart_meter_df, params).collect()
    }

    assert metrics_rows["Residential"]["n_total"] == 4
    assert metrics_rows["Residential"]["n_eligible"] == 3
    assert metrics_rows["Residential"]["n_eligible_no_der"] == 1
    assert metrics_rows["Residential"]["n_eligible_solar"] == 1
    assert metrics_rows["Residential"]["n_eligible_solar_battery"] == 1
    assert metrics_rows["Residential"]["eligibility_rate"] == 3.0 / 4.0
    assert metrics_rows["Residential"]["eligibility_rate_no_der"] == 1.0 / 4.0
    assert metrics_rows["Residential"]["eligibility_rate_solar"] == 1.0 / 4.0
    assert metrics_rows["Residential"]["eligibility_rate_solar_battery"] == 1.0 / 4.0

    assert metrics_rows["Commercial"]["n_total"] == 1
    assert metrics_rows["Commercial"]["n_eligible"] == 0
    assert metrics_rows["Commercial"]["n_eligible_no_der"] == 0
    assert metrics_rows["Commercial"]["eligibility_rate"] == 0.0


def test_build_segment_metrics_rejects_nmi_mapped_to_multiple_der_groups(spark, base_params):
    params = load_params(copy.deepcopy(base_params))

    segment_attributes_df = spark.createDataFrame(
        [
            ("nmi-1", "Residential", "No_DER"),
            ("nmi-1", "Residential", "Solar"),
        ],
        ["nmi", "segment", "der_type"],
    )
    smart_meter_df = spark.createDataFrame(
        [("nmi-1", "SM")],
        ["nmi", "meter_type_code"],
    )

    with pytest.raises(ValueError, match="multiple DER eligibility groups"):
        build_segment_metrics(segment_attributes_df, smart_meter_df, params)
