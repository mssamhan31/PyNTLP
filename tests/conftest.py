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
            "segment_column": "segment",
            "output_value_column": "pma_sso_mw",
            "schema_version": "v0.1",
        },
        "parameters": {
            "eligible_resi_patterns": ["resi"],
            "smart_meter_code": "SM",
            "eligible_der_type": "EV",
            "window_start": "01:00",
            "window_end": "03:00",
            "cap_kwh_per_day": 5000.0,
            "u_segment": {
                "default": 1.0,
                "Residential": 1.0,
            },
            "ramp_start_fcy": 2025,
            "ramp_full_fcy": 2026,
            "s_segment": {
                "default": 0.25,
                "Residential": 0.25,
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
