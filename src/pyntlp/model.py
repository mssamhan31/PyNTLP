"""Core PMA SSO model that converts policy parameters into interval deltas.

The public entrypoint accepts normalised baseline profiles, precomputed
lga_segment eligibility metrics, and validated parameters. It returns additive
MW deltas at the same interval grain as the baseline input.
"""

from __future__ import annotations

from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as F

from .schema import (
    BASELINE_REQUIRED_COLUMNS,
    GROUP_COLUMNS,
    LGA_SEGMENT_METRICS_REQUIRED_COLUMNS,
    MODEL_INTERVAL_KEY_COLUMNS,
    OUTPUT_COLUMNS,
)
from .utils import ensure_no_duplicate_keys, ensure_required_columns, lga_segment_parameter_expr
from .windows import get_window_intervals

DER_GROUP_RATE_COLUMNS = {
    "No_DER": "eligibility_rate_no_der",
    "Solar": "eligibility_rate_solar",
    "Solar_Battery": "eligibility_rate_solar_battery",
}

CAP_GROUP_COLUMNS = [column_name for column_name in GROUP_COLUMNS if column_name != "fc_object_id"]


def compute_pma_sso(
    baseline_profiles_df: DataFrame,
    lga_segment_metrics_df: DataFrame,
    params: dict,
) -> DataFrame:
    """Compute additive PMA SSO interval deltas from baseline and lga_segment metrics.

    The calculation is energy neutral within each model group: intervals inside
    the configured window receive positive deltas, while donor intervals receive
    matching negative deltas. Any missing or ineligible lga_segment metrics are
    treated as zero eligible uptake rather than dropping baseline rows.
    """

    ensure_required_columns(baseline_profiles_df, BASELINE_REQUIRED_COLUMNS, "baseline_profiles_df")
    ensure_required_columns(
        lga_segment_metrics_df,
        LGA_SEGMENT_METRICS_REQUIRED_COLUMNS,
        "lga_segment_metrics_df",
    )

    window_intervals, donor_intervals, interval_hours = get_window_intervals(params)
    parameters = params["parameters"]

    k_response = float(parameters["k_response"])
    cap_kwh_per_day = float(parameters["cap_kwh_per_day"])
    u_eligible_der_group = parameters["u_eligible_der_group"]
    s_lga_segment = parameters["s_lga_segment"]

    # Cast the public baseline contract up front so downstream expressions work
    # with predictable Spark types and key duplicate checks use canonical names.
    baseline = baseline_profiles_df.select(
        F.col("fc_object_id").cast("int").alias("fc_object_id"),
        F.col("lga_segment").cast("string").alias("lga_segment"),
        F.col("customer_type").cast("string").alias("customer_type"),
        F.col("fcy").cast("int").alias("fcy"),
        F.col("forecast_scenario").cast("string").alias("forecast_scenario"),
        F.col("season").cast("string").alias("season"),
        F.col("day_type").cast("string").alias("day_type"),
        F.col("representative_day").cast("string").alias("representative_day"),
        F.col("coincident_type").cast("string").alias("coincident_type"),
        F.col("poe").cast("string").alias("poe"),
        F.col("interval").cast("int").alias("interval"),
        F.col("baseline_demand_mw").cast("double").alias("baseline_demand_mw"),
    )
    ensure_no_duplicate_keys(baseline, MODEL_INTERVAL_KEY_COLUMNS, "baseline_profiles_df")

    # Collapse metrics to one row per lga_segment before the join. Missing
    # metrics are filled to zero after the left join below.
    lga_segment_metrics = (
        lga_segment_metrics_df.select(
            F.col("lga_segment").cast("string").alias("lga_segment"),
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
        .dropDuplicates(["lga_segment"])
    )

    # The eligible uptake rate is a weighted sum across DER-group-specific
    # eligibility rates and the configured uptake assumptions.
    eligible_uptake_rate_expr = F.lit(0.0)
    for group_name, rate_column in DER_GROUP_RATE_COLUMNS.items():
        eligible_uptake_rate_expr = eligible_uptake_rate_expr + (
            F.col(rate_column) * F.lit(float(u_eligible_der_group[group_name]))
        )

    # Enrich every baseline interval with eligibility, segment shiftability, and
    # the forecast-year ramp needed for group-level shift allocation.
    enriched = (
        baseline.join(lga_segment_metrics, on="lga_segment", how="left")
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
            lga_segment_parameter_expr(
                F.col("lga_segment"),
                s_lga_segment,
                float(s_lga_segment["default"]),
            ).cast("double"),
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

    # Group-level metrics first calculate each fc_object_id slice's uncapped
    # shift. The participant cap is applied later at lga_segment population
    # grain, then allocated back to these object-level groups.
    group_metrics = (
        enriched.groupBy(*GROUP_COLUMNS)
        .agg(
            (F.sum(F.coalesce(F.col("baseline_demand_mw"), F.lit(0.0))) * F.lit(interval_hours))
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
        .withColumn(
            "allocatable_uncapped_shift_mwh",
            F.when(
                (F.col("window_row_count") > F.lit(0))
                & (F.col("donor_row_count") > F.lit(0))
                & (F.col("e_shift_mwh") > F.lit(0.0)),
                F.col("e_shift_mwh"),
            )
            .otherwise(F.lit(0.0))
            .cast("double"),
        )
    )

    # Apply participant caps once per lga_segment model population. This avoids
    # multiplying the same segment-level NMI count across multiple fc_object_id
    # slices, while preserving the existing output grain.
    capped_population_metrics = (
        group_metrics.groupBy(*CAP_GROUP_COLUMNS)
        .agg(
            F.sum("allocatable_uncapped_shift_mwh").cast("double").alias("population_uncapped_shift_mwh"),
            F.max(F.col("n_total")).cast("int").alias("population_n_total"),
            F.max(F.col("adoption_rate")).cast("double").alias("population_adoption_rate"),
        )
        .withColumn(
            "population_participants",
            (F.col("population_n_total") * F.col("population_adoption_rate")).cast("double"),
        )
        .withColumn(
            "population_cap_mwh",
            (F.col("population_participants") * F.lit(cap_kwh_per_day) / F.lit(1000.0)).cast("double"),
        )
        .withColumn(
            "population_capped_shift_mwh",
            F.least(F.col("population_uncapped_shift_mwh"), F.col("population_cap_mwh")).cast("double"),
        )
    )

    group_metrics = (
        group_metrics.join(
            capped_population_metrics.select(
                *CAP_GROUP_COLUMNS,
                "population_uncapped_shift_mwh",
                "population_capped_shift_mwh",
            ),
            on=CAP_GROUP_COLUMNS,
            how="left",
        )
        .withColumn(
            "allocatable_shift_mwh",
            F.when(
                F.col("population_uncapped_shift_mwh") > F.lit(0.0),
                F.col("population_capped_shift_mwh")
                * F.col("allocatable_uncapped_shift_mwh")
                / F.col("population_uncapped_shift_mwh"),
            )
            .otherwise(F.lit(0.0))
            .cast("double"),
        )
    )

    # Allocate shifted energy flatly across window intervals and remove the same
    # energy from donor intervals, then convert interval MWh back to MW.
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
        .withColumn("delta_mw", (F.col("delta_mwh") / F.lit(interval_hours)).cast("double"))
        .select(
            F.col("fc_object_id").cast("int").alias("fc_object_id"),
            F.col("lga_segment").cast("string").alias("lga_segment"),
            F.col("customer_type").cast("string").alias("customer_type"),
            F.col("fcy").cast("int").alias("fcy"),
            F.col("forecast_scenario").cast("string").alias("forecast_scenario"),
            F.col("season").cast("string").alias("season"),
            F.col("day_type").cast("string").alias("day_type"),
            F.col("representative_day").cast("string").alias("representative_day"),
            F.col("coincident_type").cast("string").alias("coincident_type"),
            F.col("poe").cast("string").alias("poe"),
            F.col("interval").cast("int").alias("interval"),
            F.col("delta_mw").cast("double").alias("delta_mw"),
        )
    )

    return deltas.select(*OUTPUT_COLUMNS)


def _linear_ramp_expr(fcy_column: Column, ramp_start_fcy: int, ramp_full_fcy: int) -> Column:
    """Build a forecast-year adoption ramp expression bounded between zero and one."""

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
