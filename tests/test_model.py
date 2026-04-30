from __future__ import annotations

import copy
from math import isclose

import pytest

from pyntlp import compute_pma_sso, load_params, validate_pma

LGA_SEGMENT = "Central Coast (NSW)_Large Res - NoOP - No_DER"
OUTPUT_COLUMNS = [
    "fc_object_id",
    "lga_segment",
    "customer_type",
    "fcy",
    "forecast_scenario",
    "season",
    "day_type",
    "representative_day",
    "coincident_type",
    "poe",
    "interval",
    "delta_mw",
]
BASELINE_COLUMNS = [
    "fc_object_id",
    "lga_segment",
    "customer_type",
    "fcy",
    "forecast_scenario",
    "season",
    "day_type",
    "representative_day",
    "coincident_type",
    "poe",
    "interval",
    "baseline_demand_mw",
]


def _baseline_profiles_df(spark):
    return _baseline_profiles_df_with_values(spark, [1.0, 1.0, 1.0, 1.0])


def _baseline_profiles_df_with_values(spark, baseline_values):
    return spark.createDataFrame(
        [
            (
                1001,
                LGA_SEGMENT,
                "Residential",
                2026,
                "base",
                "summer",
                "business",
                "weekday",
                "local non-coincident",
                "poe50",
                1,
                baseline_values[0],
            ),
            (
                1001,
                LGA_SEGMENT,
                "Residential",
                2026,
                "base",
                "summer",
                "business",
                "weekday",
                "local non-coincident",
                "poe50",
                2,
                baseline_values[1],
            ),
            (
                1001,
                LGA_SEGMENT,
                "Residential",
                2026,
                "base",
                "summer",
                "business",
                "weekday",
                "local non-coincident",
                "poe50",
                3,
                baseline_values[2],
            ),
            (
                1001,
                LGA_SEGMENT,
                "Residential",
                2026,
                "base",
                "summer",
                "business",
                "weekday",
                "local non-coincident",
                "poe50",
                4,
                baseline_values[3],
            ),
        ],
        BASELINE_COLUMNS,
    )


def _lga_segment_metrics_df(
    spark,
    n_total,
    n_eligible_no_der=0,
    n_eligible_solar=0,
    n_eligible_solar_battery=0,
):
    n_eligible = n_eligible_no_der + n_eligible_solar + n_eligible_solar_battery
    eligibility_rate = n_eligible / n_total if n_total else 0.0
    eligibility_rate_no_der = n_eligible_no_der / n_total if n_total else 0.0
    eligibility_rate_solar = n_eligible_solar / n_total if n_total else 0.0
    eligibility_rate_solar_battery = n_eligible_solar_battery / n_total if n_total else 0.0

    return spark.createDataFrame(
        [
            (
                LGA_SEGMENT,
                n_total,
                n_eligible,
                eligibility_rate,
                n_eligible_no_der,
                n_eligible_solar,
                n_eligible_solar_battery,
                eligibility_rate_no_der,
                eligibility_rate_solar,
                eligibility_rate_solar_battery,
            )
        ],
        [
            "lga_segment",
            "n_total",
            "n_eligible",
            "eligibility_rate",
            "n_eligible_no_der",
            "n_eligible_solar",
            "n_eligible_solar_battery",
            "eligibility_rate_no_der",
            "eligibility_rate_solar",
            "eligibility_rate_solar_battery",
        ],
    )


def test_compute_pma_sso_is_energy_neutral_with_flat_allocation(spark, base_params):
    params = load_params(copy.deepcopy(base_params))

    pma_delta_df = compute_pma_sso(
        baseline_profiles_df=_baseline_profiles_df(spark),
        lga_segment_metrics_df=_lga_segment_metrics_df(spark, n_total=10, n_eligible_no_der=10),
        params=params,
    )

    deltas = {row["interval"]: row["delta_mw"] for row in pma_delta_df.collect()}

    assert isclose(deltas[1], -0.5, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(deltas[2], 0.5, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(deltas[3], 0.5, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(deltas[4], -0.5, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(sum(deltas.values()), 0.0, rel_tol=0.0, abs_tol=1e-12)

    validation_status = {
        row["check_name"]: row["status"] for row in validate_pma(pma_delta_df, params).collect()
    }
    assert validation_status["output_schema_exact"] == "PASS"
    assert validation_status["group_energy_neutrality"] == "PASS"


def test_compute_pma_sso_outputs_native_fc2026_columns(spark, base_params):
    params = load_params(copy.deepcopy(base_params))

    pma_delta_df = compute_pma_sso(
        baseline_profiles_df=_baseline_profiles_df(spark),
        lga_segment_metrics_df=_lga_segment_metrics_df(spark, n_total=10, n_eligible_no_der=10),
        params=params,
    )

    assert pma_delta_df.columns == OUTPUT_COLUMNS


def test_compute_pma_sso_preserves_baseline_shape_dimensions(spark, base_params):
    params = load_params(copy.deepcopy(base_params))
    baseline_profiles_df = spark.createDataFrame(
        [
            (1001, LGA_SEGMENT, "Residential", 2026, "base", "summer", "business", "weekday", "local non-coincident", "poe50", 1, 1.0),
            (1001, LGA_SEGMENT, "Residential", 2026, "base", "summer", "business", "weekday", "local non-coincident", "poe50", 2, 1.0),
            (1001, LGA_SEGMENT, "Residential", 2026, "base", "summer", "business", "weekday", "local non-coincident", "poe50", 3, 1.0),
            (1001, LGA_SEGMENT, "Residential", 2026, "base", "summer", "business", "weekday", "local non-coincident", "poe50", 4, 1.0),
            (1001, LGA_SEGMENT, "Small Business", 2026, "base", "summer", "business", "weekday", "local coincident", "poe10", 1, 2.0),
            (1001, LGA_SEGMENT, "Small Business", 2026, "base", "summer", "business", "weekday", "local coincident", "poe10", 2, 2.0),
            (1001, LGA_SEGMENT, "Small Business", 2026, "base", "summer", "business", "weekday", "local coincident", "poe10", 3, 2.0),
            (1001, LGA_SEGMENT, "Small Business", 2026, "base", "summer", "business", "weekday", "local coincident", "poe10", 4, 2.0),
        ],
        BASELINE_COLUMNS,
    )

    pma_delta_df = compute_pma_sso(
        baseline_profiles_df=baseline_profiles_df,
        lga_segment_metrics_df=_lga_segment_metrics_df(spark, n_total=10, n_eligible_no_der=10),
        params=params,
    )

    dimension_rows = {
        (
            row["customer_type"],
            row["forecast_scenario"],
            row["coincident_type"],
            row["poe"],
        )
        for row in pma_delta_df.select(
            "customer_type",
            "forecast_scenario",
            "coincident_type",
            "poe",
        ).distinct().collect()
    }

    assert dimension_rows == {
        ("Residential", "base", "local non-coincident", "poe50"),
        ("Small Business", "base", "local coincident", "poe10"),
    }

    validation_status = {
        row["check_name"]: row["status"] for row in validate_pma(pma_delta_df, params).collect()
    }
    assert validation_status["group_energy_neutrality"] == "PASS"


def test_compute_pma_sso_allows_null_customer_type_as_output_attribute(spark, base_params):
    params = load_params(copy.deepcopy(base_params))
    baseline_profiles_df = spark.createDataFrame(
        [
            (1001, LGA_SEGMENT, None, 2026, "base", "summer", "business", "weekday", "local non-coincident", "poe50", 1, 1.0),
            (1001, LGA_SEGMENT, "Residential", 2026, "base", "summer", "business", "weekday", "local non-coincident", "poe50", 2, 1.0),
            (1001, LGA_SEGMENT, "Residential", 2026, "base", "summer", "business", "weekday", "local non-coincident", "poe50", 3, 1.0),
            (1001, LGA_SEGMENT, "Residential", 2026, "base", "summer", "business", "weekday", "local non-coincident", "poe50", 4, 1.0),
        ],
        BASELINE_COLUMNS,
    )

    pma_delta_df = compute_pma_sso(
        baseline_profiles_df=baseline_profiles_df,
        lga_segment_metrics_df=_lga_segment_metrics_df(spark, n_total=10, n_eligible_no_der=10),
        params=params,
    )

    assert pma_delta_df.where("customer_type IS NULL").count() == 1
    validation_status = {
        row["check_name"]: row["status"] for row in validate_pma(pma_delta_df, params).collect()
    }
    assert validation_status["required_columns_non_null"] == "PASS"
    assert validation_status["group_energy_neutrality"] == "PASS"


def test_compute_pma_sso_rejects_duplicate_model_interval_keys(spark, base_params):
    params = load_params(copy.deepcopy(base_params))
    baseline_profiles_df = spark.createDataFrame(
        [
            (1001, LGA_SEGMENT, "Residential", 2026, "base", "summer", "business", "weekday", "local non-coincident", "poe50", 1, 1.0),
            (1001, LGA_SEGMENT, "Small Business", 2026, "base", "summer", "business", "weekday", "local non-coincident", "poe50", 1, 2.0),
        ],
        BASELINE_COLUMNS,
    )

    with pytest.raises(ValueError, match="duplicate rows on key"):
        compute_pma_sso(
            baseline_profiles_df=baseline_profiles_df,
            lga_segment_metrics_df=_lga_segment_metrics_df(spark, n_total=10, n_eligible_no_der=10),
            params=params,
        )


def test_compute_pma_sso_respects_cap_binding(spark, base_params):
    capped_params = copy.deepcopy(base_params)
    capped_params["parameters"]["cap_kwh_per_day"] = 500.0
    capped_params["parameters"]["s_lga_segment"][LGA_SEGMENT] = 1.0
    capped_params["parameters"]["s_lga_segment"]["default"] = 1.0
    params = load_params(capped_params)

    pma_delta_df = compute_pma_sso(
        baseline_profiles_df=_baseline_profiles_df(spark),
        lga_segment_metrics_df=_lga_segment_metrics_df(spark, n_total=1, n_eligible_no_der=1),
        params=params,
    )

    deltas = {row["interval"]: row["delta_mw"] for row in pma_delta_df.collect()}

    assert isclose(deltas[2], 0.25, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(deltas[3], 0.25, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(deltas[1], -0.25, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(deltas[4], -0.25, rel_tol=0.0, abs_tol=1e-12)


def test_compute_pma_sso_returns_zero_for_ineligible_lga_segments(spark, base_params):
    params = load_params(copy.deepcopy(base_params))

    pma_delta_df = compute_pma_sso(
        baseline_profiles_df=_baseline_profiles_df(spark),
        lga_segment_metrics_df=_lga_segment_metrics_df(spark, n_total=10),
        params=params,
    )

    deltas = [row["delta_mw"] for row in pma_delta_df.collect()]

    assert all(isclose(delta, 0.0, rel_tol=0.0, abs_tol=1e-12) for delta in deltas)


def test_compute_pma_sso_uses_weighted_der_uptake_caps(spark, base_params):
    mixed_params = copy.deepcopy(base_params)
    mixed_params["parameters"]["u_eligible_der_group"] = {
        "No_DER": 1.0,
        "Solar": 0.5,
        "Solar_Battery": 0.25,
    }
    params = load_params(mixed_params)

    pma_delta_df = compute_pma_sso(
        baseline_profiles_df=_baseline_profiles_df(spark),
        lga_segment_metrics_df=_lga_segment_metrics_df(
            spark,
            n_total=10,
            n_eligible_no_der=2,
            n_eligible_solar=2,
            n_eligible_solar_battery=2,
        ),
        params=params,
    )

    deltas = {row["interval"]: row["delta_mw"] for row in pma_delta_df.collect()}

    assert isclose(deltas[1], -0.175, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(deltas[2], 0.175, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(deltas[3], 0.175, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(deltas[4], -0.175, rel_tol=0.0, abs_tol=1e-12)


def test_compute_pma_sso_respects_explicit_donor_window(spark, base_params):
    explicit_donor_params = copy.deepcopy(base_params)
    explicit_donor_params["parameters"]["donor_window_start"] = "03:00"
    explicit_donor_params["parameters"]["donor_window_end"] = "04:00"
    params = load_params(explicit_donor_params)

    pma_delta_df = compute_pma_sso(
        baseline_profiles_df=_baseline_profiles_df(spark),
        lga_segment_metrics_df=_lga_segment_metrics_df(spark, n_total=10, n_eligible_no_der=10),
        params=params,
    )

    deltas = {row["interval"]: row["delta_mw"] for row in pma_delta_df.collect()}

    assert isclose(deltas[1], 0.0, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(deltas[2], 0.5, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(deltas[3], 0.5, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(deltas[4], -1.0, rel_tol=0.0, abs_tol=1e-12)
