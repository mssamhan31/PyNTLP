"""Segment-level eligibility metrics derived from normalised inputs."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from .schema import SMART_METER_REQUIRED_COLUMNS
from .utils import ensure_required_columns, normalise_string_column, normalise_token


def build_segment_metrics(
    segment_attributes_df: DataFrame,
    smart_meter_df: DataFrame,
    params: dict,
    segment_col: str = "segment",
) -> DataFrame:
    """Compute segment-level eligibility rates from normalised inputs."""

    ensure_required_columns(
        segment_attributes_df,
        ["nmi", segment_col, "der_type"],
        "segment_attributes_df",
    )
    ensure_required_columns(smart_meter_df, SMART_METER_REQUIRED_COLUMNS, "smart_meter_df")

    eligible_resi_patterns = params["parameters"]["eligible_resi_patterns"]
    smart_meter_code = normalise_token(params["parameters"]["smart_meter_code"])
    eligible_der_type = normalise_token(params["parameters"]["eligible_der_type"])

    attrs = (
        segment_attributes_df.select(
            F.trim(F.col("nmi").cast("string")).alias("nmi"),
            F.col(segment_col).cast("string").alias("segment"),
            F.col("der_type").cast("string").alias("der_type"),
        )
        .where(F.col("nmi").isNotNull())
        .dropDuplicates()
    )

    attr_flags = attrs.groupBy("segment", "nmi").agg(
        F.max(
            F.when(normalise_string_column(F.col("der_type")) == F.lit(eligible_der_type), F.lit(1)).otherwise(F.lit(0))
        ).alias("has_eligible_der")
    )

    meter_flags = (
        smart_meter_df.select(
            F.trim(F.col("nmi").cast("string")).alias("nmi"),
            F.col("meter_type_code").cast("string").alias("meter_type_code"),
        )
        .where(F.col("nmi").isNotNull())
        .groupBy("nmi")
        .agg(
            F.max(
                F.when(
                    normalise_string_column(F.col("meter_type_code")) == F.lit(smart_meter_code),
                    F.lit(1),
                ).otherwise(F.lit(0))
            ).alias("has_smart_meter")
        )
    )

    residential_pattern = "|".join(f"(?:{pattern.lower()})" for pattern in eligible_resi_patterns)
    residential_flag = F.lower(F.coalesce(F.col("segment"), F.lit(""))).rlike(residential_pattern)

    metrics = (
        attr_flags.join(meter_flags, on="nmi", how="left")
        .fillna({"has_smart_meter": 0})
        .groupBy("segment")
        .agg(
            F.count("*").cast("int").alias("n_total"),
            F.sum(
                F.when(
                    residential_flag
                    & (F.col("has_smart_meter") == F.lit(1))
                    & (F.col("has_eligible_der") == F.lit(1)),
                    F.lit(1),
                ).otherwise(F.lit(0))
            )
            .cast("int")
            .alias("n_eligible"),
        )
        .withColumn(
            "eligibility_rate",
            F.when(F.col("n_total") > F.lit(0), F.col("n_eligible") / F.col("n_total")).otherwise(F.lit(0.0)),
        )
        .select(
            F.col("segment"),
            F.col("n_total").cast("int"),
            F.col("n_eligible").cast("int"),
            F.col("eligibility_rate").cast("double"),
        )
    )

    return metrics

