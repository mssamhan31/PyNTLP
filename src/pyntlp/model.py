"""Core PMA SSO model that converts policy parameters into interval deltas."""

from __future__ import annotations

from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as F

from .schema import (
    BASELINE_REQUIRED_COLUMNS,
    GROUP_COLUMNS,
    OUTPUT_COLUMNS,
    SEGMENT_METRICS_REQUIRED_COLUMNS,
)
from .utils import ensure_required_columns, segment_parameter_expr
from .windows import get_window_intervals

DER_GROUP_RATE_COLUMNS = {
    "No_DER": "eligibility_rate_no_der",
    "Solar": "eligibility_rate_solar",
    "Solar_Battery": "eligibility_rate_solar_battery",
}


def compute_pma_sso(
    baseline_profiles_df: DataFrame,
    segment_metrics_df: DataFrame,
    params: dict,
) -> DataFrame:
    """Compute additive PMA SSO interval deltas from baseline and segment metrics."""

    ensure_required_columns(baseline_profiles_df, BASELINE_REQUIRED_COLUMNS, "baseline_profiles_df")
    ensure_required_columns(segment_metrics_df, SEGMENT_METRICS_REQUIRED_COLUMNS, "segment_metrics_df")

    window_intervals, donor_intervals, interval_hours = get_window_intervals(params)
    parameters = params["parameters"]

    k_response = float(parameters["k_response"])
    cap_kwh_per_day = float(parameters["cap_kwh_per_day"])
    u_eligible_der_group = parameters["u_eligible_der_group"]
    s_segment = parameters["s_segment"]

    baseline = baseline_profiles_df.select(
        F.col("fc_run_year").cast("int").alias("fc_run_year"),
        F.col("version").cast("string").alias("version"),
        F.col("fc_object_id").cast("int").alias("fc_object_id"),
        F.col("segment").cast("string").alias("segment"),
        F.col("fcy").cast("int").alias("fcy"),
        F.col("forecast_scenario").cast("string").alias("forecast_scenario"),
        F.col("poe").cast("string").alias("poe"),
        F.col("representative_day").cast("string").alias("representative_day"),
        F.col("season").cast("string").alias("season"),
        F.col("day_type").cast("string").alias("day_type"),
        F.col("interval").cast("int").alias("interval"),
        F.col("underlying_demand_mw").cast("double").alias("underlying_demand_mw"),
    )

    segment_metrics = (
        segment_metrics_df.select(
            F.col("segment").cast("string").alias("segment"),
            F.col("n_total").cast("int").alias("n_total"),
            F.col("n_eligible").cast("int").alias("n_eligible"),
            F.col("eligibility_rate").cast("double").alias("eligibility_rate"),
            F.col("n_eligible_no_der").cast("int").alias("n_eligible_no_der"),
            F.col("n_eligible_solar").cast("int").alias("n_eligible_solar"),
            F.col("n_eligible_solar_battery").cast("int").alias("n_eligible_solar_battery"),
            F.col("eligibility_rate_no_der").cast("double").alias("eligibility_rate_no_der"),
            F.col("eligibility_rate_solar").cast("double").alias("eligibility_rate_solar"),
            F.col("eligibility_rate_solar_battery").cast("double").alias("eligibility_rate_solar_battery"),
        )
        .dropDuplicates(["segment"])
    )

    eligible_uptake_rate_expr = F.lit(0.0)
    for group_name, rate_column in DER_GROUP_RATE_COLUMNS.items():
        eligible_uptake_rate_expr = eligible_uptake_rate_expr + (
            F.col(rate_column) * F.lit(float(u_eligible_der_group[group_name]))
        )

    enriched = (
        baseline.join(segment_metrics, on="segment", how="left")
        .fillna(
            {
                "n_total": 0,
                "n_eligible": 0,
                "eligibility_rate": 0.0,
                "n_eligible_no_der": 0,
                "n_eligible_solar": 0,
                "n_eligible_solar_battery": 0,
                "eligibility_rate_no_der": 0.0,
                "eligibility_rate_solar": 0.0,
                "eligibility_rate_solar_battery": 0.0,
            }
        )
        .withColumn(
            "s_value",
            segment_parameter_expr(F.col("segment"), s_segment, float(s_segment["default"])).cast("double"),
        )
        .withColumn(
            "ramp_rate",
            _linear_ramp_expr(
                F.col("fcy"),
                int(parameters["ramp_start_fcy"]),
                int(parameters["ramp_full_fcy"]),
            ),
        )
        .withColumn(
            "eligible_uptake_rate",
            eligible_uptake_rate_expr.cast("double"),
        )
        .withColumn(
            "adoption_rate",
            (F.col("eligible_uptake_rate") * F.col("ramp_rate")).cast("double"),
        )
    )

    group_metrics = (
        enriched.groupBy(*GROUP_COLUMNS)
        .agg(
            (F.sum(F.coalesce(F.col("underlying_demand_mw"), F.lit(0.0))) * F.lit(interval_hours))
            .cast("double")
            .alias("daily_energy_mwh"),
            F.max(F.col("n_total")).cast("int").alias("n_total"),
            F.max(F.col("adoption_rate")).cast("double").alias("adoption_rate"),
            F.max(F.col("s_value")).cast("double").alias("s_value"),
            F.sum(F.when(F.col("interval").isin(window_intervals), F.lit(1)).otherwise(F.lit(0)))
            .cast("int")
            .alias("window_row_count"),
            F.sum(F.when(F.col("interval").isin(donor_intervals), F.lit(1)).otherwise(F.lit(0)))
            .cast("int")
            .alias("donor_row_count"),
        )
        .withColumn(
            "e_shift_mwh",
            (F.col("daily_energy_mwh") * F.col("s_value") * F.lit(k_response) * F.col("adoption_rate")).cast("double"),
        )
        .withColumn("participants", (F.col("n_total") * F.col("adoption_rate")).cast("double"))
        .withColumn("e_cap_mwh", (F.col("participants") * F.lit(cap_kwh_per_day) / F.lit(1000.0)).cast("double"))
        .withColumn(
            "e_shift_capped_mwh",
            F.least(F.col("e_shift_mwh"), F.col("e_cap_mwh")).cast("double"),
        )
        .withColumn(
            "allocatable_shift_mwh",
            F.when(
                (F.col("window_row_count") > F.lit(0)) & (F.col("donor_row_count") > F.lit(0)),
                F.col("e_shift_capped_mwh"),
            )
            .otherwise(F.lit(0.0))
            .cast("double"),
        )
    )

    deltas = (
        enriched.join(
            group_metrics.select(
                *GROUP_COLUMNS,
                "allocatable_shift_mwh",
                "window_row_count",
                "donor_row_count",
            ),
            on=GROUP_COLUMNS,
            how="left",
        )
        .withColumn(
            "delta_mwh",
            F.when(
                F.col("interval").isin(window_intervals) & (F.col("window_row_count") > F.lit(0)),
                F.col("allocatable_shift_mwh") / F.col("window_row_count"),
            )
            .when(
                F.col("interval").isin(donor_intervals) & (F.col("donor_row_count") > F.lit(0)),
                -F.col("allocatable_shift_mwh") / F.col("donor_row_count"),
            )
            .otherwise(F.lit(0.0))
            .cast("double"),
        )
        .withColumn("pma_sso_mw", (F.col("delta_mwh") / F.lit(interval_hours)).cast("double"))
        .select(
            F.col("fc_run_year").cast("int").alias("fc_run_year"),
            F.col("version").cast("string").alias("version"),
            F.col("fc_object_id").cast("int").alias("fc_object_id"),
            F.col("segment").cast("string").alias("segment"),
            F.col("fcy").cast("int").alias("fcy"),
            F.col("forecast_scenario").cast("string").alias("forecast_scenario"),
            F.col("poe").cast("string").alias("poe"),
            F.col("representative_day").cast("string").alias("representative_day"),
            F.col("season").cast("string").alias("season"),
            F.col("day_type").cast("string").alias("day_type"),
            F.col("interval").cast("int").alias("interval"),
            F.col("pma_sso_mw").cast("double").alias("pma_sso_mw"),
        )
    )

    return deltas.select(*OUTPUT_COLUMNS)


def _linear_ramp_expr(fcy_column: Column, ramp_start_fcy: int, ramp_full_fcy: int) -> Column:
    if ramp_full_fcy == ramp_start_fcy:
        return F.when(fcy_column < F.lit(ramp_start_fcy), F.lit(0.0)).otherwise(F.lit(1.0))

    return (
        F.when(fcy_column < F.lit(ramp_start_fcy), F.lit(0.0))
        .when(fcy_column >= F.lit(ramp_full_fcy), F.lit(1.0))
        .otherwise(
            (
                (fcy_column.cast("double") - F.lit(float(ramp_start_fcy)))
                / F.lit(float(ramp_full_fcy - ramp_start_fcy))
            ).cast("double")
        )
    )
