from __future__ import annotations

import copy
from math import isclose

from pyntlp import compute_pma_sso, load_params, validate_pma


def _baseline_profiles_df(spark):
    return _baseline_profiles_df_with_values(spark, [1.0, 1.0, 1.0, 1.0])


def _baseline_profiles_df_with_values(spark, underlying_values):
    return spark.createDataFrame(
        [
            (2026, "v1", 1001, "Residential", 2026, "base", "POE50", "weekday", "summer", "business", 1, underlying_values[0]),
            (2026, "v1", 1001, "Residential", 2026, "base", "POE50", "weekday", "summer", "business", 2, underlying_values[1]),
            (2026, "v1", 1001, "Residential", 2026, "base", "POE50", "weekday", "summer", "business", 3, underlying_values[2]),
            (2026, "v1", 1001, "Residential", 2026, "base", "POE50", "weekday", "summer", "business", 4, underlying_values[3]),
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


def _segment_metrics_df(
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
                "Residential",
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
            "segment",
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
        segment_metrics_df=_segment_metrics_df(spark, n_total=10, n_eligible_no_der=10),
        params=params,
    )

    deltas = {row["interval"]: row["pma_sso_mw"] for row in pma_delta_df.collect()}

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


def test_compute_pma_sso_outputs_pct_of_underlying_in_percent_units(spark, base_params):
    params = load_params(copy.deepcopy(base_params))

    pma_delta_df = compute_pma_sso(
        baseline_profiles_df=_baseline_profiles_df(spark),
        segment_metrics_df=_segment_metrics_df(spark, n_total=10, n_eligible_no_der=10),
        params=params,
    )

    pct_by_interval = {
        row["interval"]: row["pma_sso_pct_of_underlying"] for row in pma_delta_df.collect()
    }

    assert isclose(pct_by_interval[1], -50.0, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(pct_by_interval[2], 50.0, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(pct_by_interval[3], 50.0, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(pct_by_interval[4], -50.0, rel_tol=0.0, abs_tol=1e-12)


def test_compute_pma_sso_allows_null_pct_when_underlying_demand_is_zero(spark, base_params):
    params = load_params(copy.deepcopy(base_params))

    pma_delta_df = compute_pma_sso(
        baseline_profiles_df=_baseline_profiles_df_with_values(spark, [0.0, 1.0, 1.0, 1.0]),
        segment_metrics_df=_segment_metrics_df(spark, n_total=10, n_eligible_no_der=10),
        params=params,
    )

    rows_by_interval = {row["interval"]: row.asDict() for row in pma_delta_df.collect()}

    assert rows_by_interval[1]["pma_sso_mw"] < 0.0
    assert rows_by_interval[1]["pma_sso_pct_of_underlying"] is None
    assert rows_by_interval[2]["pma_sso_pct_of_underlying"] > 0.0

    validation_status = {
        row["check_name"]: row["status"] for row in validate_pma(pma_delta_df, params).collect()
    }
    assert validation_status["output_schema_exact"] == "PASS"
    assert validation_status["required_columns_non_null"] == "PASS"
    assert validation_status["group_energy_neutrality"] == "PASS"


def test_compute_pma_sso_respects_cap_binding(spark, base_params):
    capped_params = copy.deepcopy(base_params)
    capped_params["parameters"]["cap_kwh_per_day"] = 500.0
    capped_params["parameters"]["s_segment"]["Residential"] = 1.0
    capped_params["parameters"]["s_segment"]["default"] = 1.0
    params = load_params(capped_params)

    pma_delta_df = compute_pma_sso(
        baseline_profiles_df=_baseline_profiles_df(spark),
        segment_metrics_df=_segment_metrics_df(spark, n_total=1, n_eligible_no_der=1),
        params=params,
    )

    deltas = {row["interval"]: row["pma_sso_mw"] for row in pma_delta_df.collect()}

    assert isclose(deltas[2], 0.25, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(deltas[3], 0.25, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(deltas[1], -0.25, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(deltas[4], -0.25, rel_tol=0.0, abs_tol=1e-12)


def test_compute_pma_sso_returns_zero_for_ineligible_segments(spark, base_params):
    params = load_params(copy.deepcopy(base_params))

    pma_delta_df = compute_pma_sso(
        baseline_profiles_df=_baseline_profiles_df(spark),
        segment_metrics_df=_segment_metrics_df(spark, n_total=10),
        params=params,
    )

    deltas = [row["pma_sso_mw"] for row in pma_delta_df.collect()]

    assert all(isclose(delta, 0.0, rel_tol=0.0, abs_tol=1e-12) for delta in deltas)


def test_compute_pma_sso_uses_weighted_cohort_uptake_caps(spark, base_params):
    mixed_params = copy.deepcopy(base_params)
    mixed_params["parameters"]["u_eligible_der_group"] = {
        "No_DER": 1.0,
        "Solar": 0.5,
        "Solar_Battery": 0.25,
    }
    params = load_params(mixed_params)

    pma_delta_df = compute_pma_sso(
        baseline_profiles_df=_baseline_profiles_df(spark),
        segment_metrics_df=_segment_metrics_df(
            spark,
            n_total=10,
            n_eligible_no_der=2,
            n_eligible_solar=2,
            n_eligible_solar_battery=2,
        ),
        params=params,
    )

    deltas = {row["interval"]: row["pma_sso_mw"] for row in pma_delta_df.collect()}

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
        segment_metrics_df=_segment_metrics_df(spark, n_total=10, n_eligible_no_der=10),
        params=params,
    )

    deltas = {row["interval"]: row["pma_sso_mw"] for row in pma_delta_df.collect()}

    assert isclose(deltas[1], 0.0, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(deltas[2], 0.5, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(deltas[3], 0.5, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(deltas[4], -1.0, rel_tol=0.0, abs_tol=1e-12)
