from __future__ import annotations

import copy

import pytest

from pyntlp import build_lga_segment_metrics, load_params


def test_build_lga_segment_metrics_computes_expected_eligibility_rates(spark, base_params):
    params = load_params(copy.deepcopy(base_params))

    lga_segment_attributes_df = spark.createDataFrame(
        [
            ("nmi-1", "Central Coast (NSW)_Large Res - NoOP - No_DER"),
            ("nmi-2", "Central Coast (NSW)_Med Res - NoOP - Solar"),
            ("nmi-3", "Central Coast (NSW)_Small Res - NoOP - Solar_Battery"),
            ("nmi-4", "Central Coast (NSW)_Apartment - NoOP - Solar"),
            ("nmi-5", "Central Coast (NSW)_Large Bus - NoOP - No_DER"),
        ],
        ["nmi", "lga_segment"],
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
        row["lga_segment"]: row.asDict()
        for row in build_lga_segment_metrics(lga_segment_attributes_df, smart_meter_df, params).collect()
    }

    large_res = "Central Coast (NSW)_Large Res - NoOP - No_DER"
    med_res = "Central Coast (NSW)_Med Res - NoOP - Solar"
    small_res = "Central Coast (NSW)_Small Res - NoOP - Solar_Battery"
    apartment = "Central Coast (NSW)_Apartment - NoOP - Solar"
    large_bus = "Central Coast (NSW)_Large Bus - NoOP - No_DER"

    assert metrics_rows[large_res]["n_eligible"] == 1
    assert metrics_rows[large_res]["n_eligible_no_der"] == 1
    assert metrics_rows[med_res]["n_eligible"] == 1
    assert metrics_rows[med_res]["n_eligible_solar"] == 1
    assert metrics_rows[small_res]["n_eligible"] == 1
    assert metrics_rows[small_res]["n_eligible_solar_battery"] == 1

    assert metrics_rows[apartment]["n_total"] == 1
    assert metrics_rows[apartment]["n_eligible"] == 0
    assert metrics_rows[apartment]["n_eligible_solar"] == 0

    assert metrics_rows[large_bus]["n_total"] == 1
    assert metrics_rows[large_bus]["n_eligible"] == 0
    assert metrics_rows[large_bus]["n_eligible_no_der"] == 0
    assert metrics_rows[large_bus]["eligibility_rate"] == 0.0


def test_build_lga_segment_metrics_rejects_nmi_mapped_to_multiple_der_groups(spark, base_params):
    params = load_params(copy.deepcopy(base_params))

    lga_segment_attributes_df = spark.createDataFrame(
        [
            ("nmi-1", "Central Coast (NSW)_Large Res - NoOP - No_DER"),
            ("nmi-1", "Central Coast (NSW)_Large Res - NoOP - Solar"),
        ],
        ["nmi", "lga_segment"],
    )
    smart_meter_df = spark.createDataFrame(
        [("nmi-1", "SM")],
        ["nmi", "meter_type_code"],
    )

    with pytest.raises(ValueError, match="multiple DER eligibility groups"):
        build_lga_segment_metrics(lga_segment_attributes_df, smart_meter_df, params)
