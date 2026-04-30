"""Shared helpers for validation and lga_segment parameter resolution."""

from __future__ import annotations

from typing import Any

from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as F


def ensure_required_columns(df: DataFrame, required_columns: list[str], df_name: str) -> None:
    """Raise a clear error if a DataFrame misses required columns."""

    missing_columns = sorted(set(required_columns) - set(df.columns))
    if missing_columns:
        raise ValueError(f"{df_name} is missing required columns: {missing_columns}")


def ensure_no_duplicate_keys(df: DataFrame, key_columns: list[str], df_name: str) -> None:
    """Raise a clear error if a DataFrame has duplicate key rows."""

    duplicate_count = df.groupBy(*key_columns).count().filter(F.col("count") > 1).limit(1).count()
    if duplicate_count:
        raise ValueError(f"{df_name} contains duplicate rows on key: {key_columns}")


def normalise_token(value: Any) -> str:
    """Normalise scalar tokens for case-insensitive exact matches."""

    if value is None:
        return ""
    return str(value).strip().upper()


def normalise_string_column(column: Column) -> Column:
    """Normalise a Spark string column for case-insensitive comparisons."""

    return F.upper(F.trim(F.coalesce(column.cast("string"), F.lit(""))))


def resolve_lga_segment_parameter(lga_segment: str | None, mapping: dict[str, float], default_value: float) -> float:
    """Resolve an exact-match lga_segment override with fallback to default."""

    if lga_segment is None:
        return float(mapping.get("default", default_value))
    if lga_segment in mapping:
        return float(mapping[lga_segment])
    return float(mapping.get("default", default_value))


def lga_segment_parameter_expr(lga_segment_column: Column, mapping: dict[str, float], default_value: float) -> Column:
    """Build a Spark expression for exact-match lga_segment overrides."""

    expr = F.lit(float(mapping.get("default", default_value)))
    for lga_segment, value in mapping.items():
        if lga_segment == "default":
            continue
        expr = F.when(lga_segment_column == F.lit(lga_segment), F.lit(float(value))).otherwise(expr)
    return expr
