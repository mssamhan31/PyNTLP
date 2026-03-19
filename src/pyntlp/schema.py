"""Shared schema definitions for public package contracts."""

from pyspark.sql.types import DoubleType, IntegerType, StringType, StructField, StructType

BASELINE_REQUIRED_COLUMNS = [
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
]

SEGMENT_ATTRIBUTES_REQUIRED_COLUMNS = [
    "nmi",
    "segment",
    "der_type",
]

SMART_METER_REQUIRED_COLUMNS = [
    "nmi",
    "meter_type_code",
]

SEGMENT_METRICS_REQUIRED_COLUMNS = [
    "segment",
    "n_total",
    "n_eligible",
    "eligibility_rate",
    "n_eligible_no_der",
    "n_eligible_solar",
    "n_eligible_solar_battery",
    "eligibility_rate_no_der",
    "eligibility_rate_solar",
    "eligibility_rate_solar_battery",
]

OUTPUT_METRIC_COLUMNS = [
    "pma_sso_mw",
    "pma_sso_pct_of_underlying",
]

OUTPUT_COLUMNS = [
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
    *OUTPUT_METRIC_COLUMNS,
]

OUTPUT_KEY_COLUMNS = [
    column_name for column_name in OUTPUT_COLUMNS if column_name not in OUTPUT_METRIC_COLUMNS
]

OUTPUT_NON_NULL_COLUMNS = [
    column_name for column_name in OUTPUT_COLUMNS if column_name != "pma_sso_pct_of_underlying"
]

GROUP_COLUMNS = [
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
]

OUTPUT_SCHEMA = StructType(
    [
        StructField("fc_run_year", IntegerType(), False),
        StructField("version", StringType(), False),
        StructField("fc_object_id", IntegerType(), False),
        StructField("segment", StringType(), True),
        StructField("fcy", IntegerType(), False),
        StructField("forecast_scenario", StringType(), False),
        StructField("poe", StringType(), False),
        StructField("representative_day", StringType(), False),
        StructField("season", StringType(), False),
        StructField("day_type", StringType(), False),
        StructField("interval", IntegerType(), False),
        StructField("pma_sso_mw", DoubleType(), False),
        StructField("pma_sso_pct_of_underlying", DoubleType(), True),
    ]
)

OUTPUT_SCHEMA_SIGNATURE = [
    (field.name, field.dataType.simpleString()) for field in OUTPUT_SCHEMA.fields
]

VALIDATION_REPORT_SCHEMA = StructType(
    [
        StructField("check_name", StringType(), False),
        StructField("status", StringType(), False),
        StructField("detail", StringType(), False),
    ]
)
