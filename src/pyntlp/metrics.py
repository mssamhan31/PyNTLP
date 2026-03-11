"""Segment-level eligibility metrics derived from normalised inputs."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from .schema import SMART_METER_REQUIRED_COLUMNS
from .utils import ensure_required_columns, normalise_string_column, normalise_token

DER_GROUP_SUFFIXES = {
    "No_DER": "no_der",
    "Solar": "solar",
    "Solar_Battery": "solar_battery",
}


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
    eligible_der_groups = {
        group_name: [normalise_token(raw_value) for raw_value in raw_values]
        for group_name, raw_values in params["parameters"]["eligible_der_groups"].items()
    }

    attrs = (
        segment_attributes_df.select(
            F.trim(F.col("nmi").cast("string")).alias("nmi"),
            F.col(segment_col).cast("string").alias("segment"),
            F.col("der_type").cast("string").alias("der_type"),
        )
        .where(F.col("nmi").isNotNull())
        .dropDuplicates()
    )

    der_type_normalised = normalise_string_column(F.col("der_type"))
    attrs_with_group_flags = attrs.select(
        "segment",
        "nmi",
        *[
            F.when(der_type_normalised.isin(group_values), F.lit(1)).otherwise(F.lit(0)).alias(
                f"is_{DER_GROUP_SUFFIXES[group_name]}"
            )
            for group_name, group_values in eligible_der_groups.items()
        ],
    )

    _raise_if_nmi_maps_to_multiple_der_groups(attrs_with_group_flags)

    attr_flags = attrs_with_group_flags.groupBy("segment", "nmi").agg(
        *[
            F.max(F.col(f"is_{suffix}")).cast("int").alias(f"has_eligible_{suffix}")
            for suffix in DER_GROUP_SUFFIXES.values()
        ]
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
            *[
                F.sum(
                    F.when(
                        residential_flag
                        & (F.col("has_smart_meter") == F.lit(1))
                        & (F.col(f"has_eligible_{suffix}") == F.lit(1)),
                        F.lit(1),
                    ).otherwise(F.lit(0))
                )
                .cast("int")
                .alias(f"n_eligible_{suffix}")
                for suffix in DER_GROUP_SUFFIXES.values()
            ],
        )
        .withColumn(
            "n_eligible",
            (
                F.col("n_eligible_no_der") + F.col("n_eligible_solar") + F.col("n_eligible_solar_battery")
            ).cast("int"),
        )
        .withColumn(
            "eligibility_rate_no_der",
            F.when(F.col("n_total") > F.lit(0), F.col("n_eligible_no_der") / F.col("n_total")).otherwise(F.lit(0.0)),
        )
        .withColumn(
            "eligibility_rate_solar",
            F.when(F.col("n_total") > F.lit(0), F.col("n_eligible_solar") / F.col("n_total")).otherwise(F.lit(0.0)),
        )
        .withColumn(
            "eligibility_rate_solar_battery",
            F.when(
                F.col("n_total") > F.lit(0),
                F.col("n_eligible_solar_battery") / F.col("n_total"),
            ).otherwise(F.lit(0.0)),
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
            F.col("n_eligible_no_der").cast("int"),
            F.col("n_eligible_solar").cast("int"),
            F.col("n_eligible_solar_battery").cast("int"),
            F.col("eligibility_rate_no_der").cast("double"),
            F.col("eligibility_rate_solar").cast("double"),
            F.col("eligibility_rate_solar_battery").cast("double"),
        )
    )

    return metrics


def _raise_if_nmi_maps_to_multiple_der_groups(attrs_with_group_flags: DataFrame) -> None:
    group_columns = [f"is_{suffix}" for suffix in DER_GROUP_SUFFIXES.values()]
    matched_group_count_expr = F.lit(0)
    for column_name in group_columns:
        matched_group_count_expr = matched_group_count_expr + F.col(column_name)

    conflicting_rows = (
        attrs_with_group_flags.groupBy("nmi")
        .agg(*[F.max(F.col(column_name)).cast("int").alias(column_name) for column_name in group_columns])
        .withColumn("matched_group_count", matched_group_count_expr.cast("int"))
        .filter(F.col("matched_group_count") > F.lit(1))
    )

    if conflicting_rows.limit(1).count():
        sample_nmis = [row["nmi"] for row in conflicting_rows.select("nmi").orderBy("nmi").limit(10).collect()]
        raise ValueError(
            "One or more NMIs map to multiple DER eligibility groups. "
            f"sample_nmis={sample_nmis}"
        )
