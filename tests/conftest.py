from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pytest
from pyspark.sql import SparkSession


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def _java_available() -> bool:
    if os.environ.get("JAVA_HOME"):
        return True
    return shutil.which("java") is not None


@pytest.fixture(scope="session")
def spark():
    if not _java_available():
        pytest.skip("Java runtime not available; skipping Spark-based tests.")

    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)
    spark_session = (
        SparkSession.builder.master("local[2]")
        .appName("pyntlp-tests")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    yield spark_session
    spark_session.stop()


@pytest.fixture()
def base_params():
    return {
        "constants": {
            "model_name": "pyntlp",
            "model_tier": "public",
            "interval_minutes": 60,
            "intervals_per_day": 24,
            "timezone": "UTC",
            "schema_version": "v0.1",
        },
        "parameters": {
            "eligible_resi_patterns": ["Large Res", "Med Res", "Small Res", "Apartment"],
            "smart_meter_code": "SM",
            "window_start": "01:00",
            "window_end": "03:00",
            "cap_kwh_per_day": 5000.0,
            "u_eligible_der_group": {
                "No_DER": 1.0,
                "Solar": 0.0,
                "Solar_Battery": 0.0,
            },
            "ramp_start_fcy": 2025,
            "ramp_full_fcy": 2026,
            "s_lga_segment": {
                "default": 0.25,
                "Central Coast (NSW)_Large Res - NoOP - No_DER": 0.25,
            },
            "k_response": 1.0,
            "window_shape": "flat",
            "donor_shape": "flat",
            "energy_accounting": "energy_neutral",
            "season_modifiers": {},
            "daytype_modifiers": {},
            "rebound_share": 0.0,
            "rebound_shape": "flat",
        },
    }
