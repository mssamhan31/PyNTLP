"""Shared schema definitions for public package contracts."""

from pyspark.sql.types import DoubleType, IntegerType, StringType, StructField, StructType

BASELINE_REQUIRED_COLUMNS = [
    "fc_object_id",
    "lga_segment",
    "customer_type",
    "fcy",
    "forecast_scenario",
    "season",
    "day_type",
    "representative_day",
    "coincident_type",
    "poe",
    "interval",
    "baseline_demand_mw",
]

LGA_SEGMENT_ATTRIBUTES_REQUIRED_COLUMNS = [
    "nmi",
    "lga_segment",
]

SMART_METER_REQUIRED_COLUMNS = [
    "nmi",
    "meter_type_code",
]

LGA_SEGMENT_METRICS_REQUIRED_COLUMNS = [
    "lga_segment",
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
    "delta_mw",
]

OUTPUT_ATTRIBUTE_COLUMNS = [
    "customer_type",
]

OUTPUT_COLUMNS = [
    "fc_object_id",
    "lga_segment",
    "customer_type",
    "fcy",
    "forecast_scenario",
    "season",
    "day_type",
    "representative_day",
    "coincident_type",
    "poe",
    "interval",
    *OUTPUT_METRIC_COLUMNS,
]

OUTPUT_KEY_COLUMNS = [
    column_name for column_name in OUTPUT_COLUMNS if column_name not in OUTPUT_METRIC_COLUMNS
]

MODEL_INTERVAL_KEY_COLUMNS = [
    column_name for column_name in OUTPUT_KEY_COLUMNS if column_name not in OUTPUT_ATTRIBUTE_COLUMNS
]

OUTPUT_NON_NULL_COLUMNS = [
    column_name for column_name in OUTPUT_COLUMNS if column_name not in OUTPUT_ATTRIBUTE_COLUMNS
]

GROUP_COLUMNS = [
    column_name for column_name in MODEL_INTERVAL_KEY_COLUMNS if column_name != "interval"
]

OUTPUT_SCHEMA = StructType(
    [
        StructField("fc_object_id", IntegerType(), False),
        StructField("lga_segment", StringType(), False),
        StructField("customer_type", StringType(), True),
        StructField("fcy", IntegerType(), False),
        StructField("forecast_scenario", StringType(), False),
        StructField("season", StringType(), False),
        StructField("day_type", StringType(), False),
        StructField("representative_day", StringType(), False),
        StructField("coincident_type", StringType(), False),
        StructField("poe", StringType(), False),
        StructField("interval", IntegerType(), False),
        StructField("delta_mw", DoubleType(), False),
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
