from __future__ import annotations

import copy
from math import isclose

from pyntlp import compute_pma_sso, load_params, validate_pma


def _baseline_profiles_df(spark):
    return spark.createDataFrame(
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


def _segment_metrics_df(spark, n_total, n_eligible, eligibility_rate):
    return spark.createDataFrame(
        [("Residential", n_total, n_eligible, eligibility_rate)],
        ["segment", "n_total", "n_eligible", "eligibility_rate"],
    )


def test_compute_pma_sso_is_energy_neutral_with_flat_allocation(spark, base_params):
    params = load_params(copy.deepcopy(base_params))

    pma_delta_df = compute_pma_sso(
        baseline_profiles_df=_baseline_profiles_df(spark),
        segment_metrics_df=_segment_metrics_df(spark, n_total=10, n_eligible=10, eligibility_rate=1.0),
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


def test_compute_pma_sso_respects_cap_binding(spark, base_params):
    capped_params = copy.deepcopy(base_params)
    capped_params["parameters"]["cap_kwh_per_day"] = 500.0
    capped_params["parameters"]["s_segment"]["Residential"] = 1.0
    capped_params["parameters"]["s_segment"]["default"] = 1.0
    params = load_params(capped_params)

    pma_delta_df = compute_pma_sso(
        baseline_profiles_df=_baseline_profiles_df(spark),
        segment_metrics_df=_segment_metrics_df(spark, n_total=1, n_eligible=1, eligibility_rate=1.0),
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
        segment_metrics_df=_segment_metrics_df(spark, n_total=10, n_eligible=0, eligibility_rate=0.0),
        params=params,
    )

    deltas = [row["pma_sso_mw"] for row in pma_delta_df.collect()]

    assert all(isclose(delta, 0.0, rel_tol=0.0, abs_tol=1e-12) for delta in deltas)

