"""Shared helpers for validation and lga_segment parameter resolution.

The functions here are intentionally small and dependency-light so model,
metrics, and validation code can share consistent error handling and string
normalisation without duplicating Spark expressions.
"""

from __future__ import annotations

from typing import Any

from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as F


def ensure_required_columns(df: DataFrame, required_columns: list[str], df_name: str) -> None:
    """Raise a clear error if a DataFrame misses required columns.

    This is usually called at public function boundaries before any Spark
    transformation is assembled.
    """

    missing_columns = sorted(set(required_columns) - set(df.columns))
    if missing_columns:
        raise ValueError(f"{df_name} is missing required columns: {missing_columns}")


def ensure_no_duplicate_keys(df: DataFrame, key_columns: list[str], df_name: str) -> None:
    """Raise a clear error if a DataFrame has duplicate key rows.

    The check only needs to find one duplicate group, keeping the action small
    while still failing fast before downstream joins or allocations.
    """

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
    """Resolve an exact-match lga_segment override with fallback to default.

    This scalar version mirrors `lga_segment_parameter_expr` for tests or other
    non-Spark callers that need the same precedence rule.
    """

    if lga_segment is None:
        return float(mapping.get("default", default_value))
    if lga_segment in mapping:
        return float(mapping[lga_segment])
    return float(mapping.get("default", default_value))


def lga_segment_parameter_expr(lga_segment_column: Column, mapping: dict[str, float], default_value: float) -> Column:
    """Build a Spark expression for exact-match lga_segment overrides.

    Specific lga_segment entries win over `default`; missing or unmatched values
    fall back to the supplied default value.
    """

    expr = F.lit(float(mapping.get("default", default_value)))
    for lga_segment, value in mapping.items():
        if lga_segment == "default":
            continue
        expr = F.when(lga_segment_column == F.lit(lga_segment), F.lit(float(value))).otherwise(expr)
    return expr
