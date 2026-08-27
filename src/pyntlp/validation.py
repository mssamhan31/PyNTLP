"""Validation helpers for PMA output schema and neutrality checks.

The validation report is intentionally Spark-native so notebooks and pipelines
can display or persist it beside model outputs. Each row is a named check with a
PASS/FAIL status and human-readable diagnostic detail.
"""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from .schema import (
    GROUP_COLUMNS,
    OUTPUT_COLUMNS,
    OUTPUT_NON_NULL_COLUMNS,
    OUTPUT_SCHEMA_SIGNATURE,
    VALIDATION_REPORT_SCHEMA,
)
from .windows import get_window_intervals


def validate_pma(pma_delta_df: DataFrame, params: dict) -> DataFrame:
    """Validate output schema, required values, and group-level energy neutrality.

    The function never mutates the PMA DataFrame. It returns a small validation
    DataFrame that callers can display, persist, or convert into a hard failure.
    """

    spark = pma_delta_df.sparkSession
    report_rows: list[tuple[str, str, str]] = []

    # Schema checks are exact so column order and Spark types stay aligned with
    # the package contract.
    actual_schema_signature = [
        (field.name, field.dataType.simpleString()) for field in pma_delta_df.schema.fields
    ]
    schema_status = "PASS" if actual_schema_signature == OUTPUT_SCHEMA_SIGNATURE else "FAIL"
    report_rows.append(
        (
            "output_schema_exact",
            schema_status,
            f"expected={OUTPUT_SCHEMA_SIGNATURE}; actual={actual_schema_signature}",
        )
    )

    missing_columns = sorted(set(OUTPUT_COLUMNS) - set(pma_delta_df.columns))
    extra_columns = sorted(set(pma_delta_df.columns) - set(OUTPUT_COLUMNS))
    column_status = "PASS" if not missing_columns and not extra_columns else "FAIL"
    report_rows.append(
        (
            "output_columns",
            column_status,
            f"missing={missing_columns}; extra={extra_columns}",
        )
    )

    # Only customer_type may be nullable in the public output contract.
    missing_non_null_columns = sorted(set(OUTPUT_NON_NULL_COLUMNS) - set(pma_delta_df.columns))
    if missing_non_null_columns:
        report_rows.append(
            (
                "required_columns_non_null",
                "FAIL",
                "Cannot evaluate null checks because required non-null output columns are missing: "
                f"{missing_non_null_columns}",
            )
        )
    else:
        null_aggregations = [
            F.sum(F.when(F.col(column_name).isNull(), F.lit(1)).otherwise(F.lit(0))).alias(column_name)
            for column_name in OUTPUT_NON_NULL_COLUMNS
        ]
        raw_null_counts = pma_delta_df.select(*null_aggregations).first().asDict()
        null_counts = {key: int(value or 0) for key, value in raw_null_counts.items()}
        total_nulls = int(sum(null_counts.values()))
        report_rows.append(
            (
                "required_columns_non_null",
                "PASS" if total_nulls == 0 else "FAIL",
                f"total_nulls={total_nulls}; per_column={null_counts}",
            )
        )

    missing_energy_columns = sorted(set(GROUP_COLUMNS + ["delta_mw"]) - set(pma_delta_df.columns))
    if missing_energy_columns:
        report_rows.append(
            (
                "group_energy_neutrality",
                "FAIL",
                "Cannot evaluate neutrality because required columns are missing: "
                f"{missing_energy_columns}",
            )
        )
        return spark.createDataFrame(report_rows, schema=VALIDATION_REPORT_SCHEMA)

    # Convert interval MW deltas to MWh before checking neutrality at the same
    # model grouping grain used by compute_pma_sso.
    interval_hours = get_window_intervals(params)[2]
    energy_error_df = pma_delta_df.groupBy(*GROUP_COLUMNS).agg(
        F.abs(F.sum(F.col("delta_mw") * F.lit(interval_hours))).alias("abs_energy_error_mwh")
    )
    max_error = energy_error_df.agg(F.max(F.col("abs_energy_error_mwh"))).first()[0]
    max_error = float(max_error or 0.0)
    tolerance = 1e-9
    report_rows.append(
        (
            "group_energy_neutrality",
            "PASS" if max_error <= tolerance else "FAIL",
            f"max_abs_energy_error_mwh={max_error:.12g}; tolerance={tolerance}",
        )
    )

    return spark.createDataFrame(report_rows, schema=VALIDATION_REPORT_SCHEMA)
