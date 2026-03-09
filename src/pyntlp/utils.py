"""Shared helpers for validation and segment parameter resolution."""

from __future__ import annotations

from typing import Any

from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as F


def ensure_required_columns(df: DataFrame, required_columns: list[str], df_name: str) -> None:
    """Raise a clear error if a DataFrame misses required columns."""

    missing_columns = sorted(set(required_columns) - set(df.columns))
    if missing_columns:
        raise ValueError(f"{df_name} is missing required columns: {missing_columns}")


def normalise_token(value: Any) -> str:
    """Normalise scalar tokens for case-insensitive exact matches."""

    if value is None:
        return ""
    return str(value).strip().upper()


def normalise_string_column(column: Column) -> Column:
    """Normalise a Spark string column for case-insensitive comparisons."""

    return F.upper(F.trim(F.coalesce(column.cast("string"), F.lit(""))))


def resolve_segment_parameter(segment: str | None, mapping: dict[str, float], default_value: float) -> float:
    """Resolve an exact-match segment override with fallback to default."""

    if segment is None:
        return float(mapping.get("default", default_value))
    if segment in mapping:
        return float(mapping[segment])
    return float(mapping.get("default", default_value))


def segment_parameter_expr(segment_column: Column, mapping: dict[str, float], default_value: float) -> Column:
    """Build a Spark expression for exact-match segment overrides."""

    expr = F.lit(float(mapping.get("default", default_value)))
    for segment_name, value in mapping.items():
        if segment_name == "default":
            continue
        expr = F.when(segment_column == F.lit(segment_name), F.lit(float(value))).otherwise(expr)
    return expr
