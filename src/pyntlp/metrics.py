"""LGA-segment eligibility metrics derived from normalised inputs."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from .schema import LGA_SEGMENT_ATTRIBUTES_REQUIRED_COLUMNS, SMART_METER_REQUIRED_COLUMNS
from .utils import ensure_required_columns, normalise_string_column, normalise_token

DER_GROUP_SUFFIXES = {
    "No_DER": "no_der",
    "Solar": "solar",
    "Solar_Battery": "solar_battery",
}


def build_lga_segment_metrics(
    lga_segment_attributes_df: DataFrame,
    smart_meter_df: DataFrame,
    params: dict,
) -> DataFrame:
    """Compute lga_segment-level eligibility rates from normalised inputs."""

    ensure_required_columns(
        lga_segment_attributes_df,
        LGA_SEGMENT_ATTRIBUTES_REQUIRED_COLUMNS,
        "lga_segment_attributes_df",
    )
    ensure_required_columns(smart_meter_df, SMART_METER_REQUIRED_COLUMNS, "smart_meter_df")

    eligible_resi_patterns = params["parameters"]["eligible_resi_patterns"]
    smart_meter_code = normalise_token(params["parameters"]["smart_meter_code"])

    attrs = (
        lga_segment_attributes_df.select(
            F.trim(F.col("nmi").cast("string")).alias("nmi"),
            F.col("lga_segment").cast("string").alias("lga_segment"),
        )
        .where(F.col("nmi").isNotNull())
        .dropDuplicates()
    )

    normalised_lga_segment = normalise_string_column(F.col("lga_segment"))
    attrs_with_group_flags = attrs.select(
        "lga_segment",
        "nmi",
        *[
            F.when(normalised_lga_segment.endswith(group_name.upper()), F.lit(1))
            .otherwise(F.lit(0))
            .alias(f"is_{DER_GROUP_SUFFIXES[group_name]}")
            for group_name in DER_GROUP_SUFFIXES
        ],
    )

    _raise_if_nmi_maps_to_multiple_der_groups(attrs_with_group_flags)

    attr_flags = attrs_with_group_flags.groupBy("lga_segment", "nmi").agg(
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
    residential_flag = F.lower(F.coalesce(F.col("lga_segment"), F.lit(""))).rlike(residential_pattern)

    metrics = (
        attr_flags.join(meter_flags, on="nmi", how="left")
        .fillna({"has_smart_meter": 0})
        .groupBy("lga_segment")
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
            F.col("lga_segment"),
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
            "One or more NMIs map to multiple DER eligibility groups inferred from lga_segment. "
            f"sample_nmis={sample_nmis}"
        )
