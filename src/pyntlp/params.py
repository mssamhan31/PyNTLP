"""Parameter loading and validation for the public YAML contract."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

SUPPORTED_WINDOW_SHAPES = {"flat"}
SUPPORTED_DONOR_SHAPES = {"flat"}
SUPPORTED_ENERGY_ACCOUNTING = {"energy_neutral"}

REQUIRED_CONSTANT_KEYS = {
    "model_name",
    "model_tier",
    "interval_minutes",
    "intervals_per_day",
    "timezone",
    "segment_column",
    "output_value_column",
}

REQUIRED_PARAMETER_KEYS = {
    "eligible_resi_patterns",
    "smart_meter_code",
    "eligible_der_type",
    "window_start",
    "window_end",
    "cap_kwh_per_day",
    "u_segment",
    "ramp_start_fcy",
    "ramp_full_fcy",
    "s_segment",
    "k_response",
    "window_shape",
    "donor_shape",
    "energy_accounting",
}

TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def load_params(path_or_dict: str | Path | dict[str, Any]) -> dict[str, Any]:
    """Load params from YAML or a dictionary and return a validated structure."""

    raw_params = _load_raw_params(path_or_dict)
    if not isinstance(raw_params, dict):
        raise ValueError("Params must deserialize to a dictionary.")

    missing_sections = sorted({"constants", "parameters"} - set(raw_params))
    if missing_sections:
        raise ValueError(f"Params missing top-level sections: {missing_sections}")

    constants = _validate_constants(raw_params["constants"])
    parameters = _validate_parameters(raw_params["parameters"])

    return {
        "constants": constants,
        "parameters": parameters,
    }


def _load_raw_params(path_or_dict: str | Path | dict[str, Any]) -> dict[str, Any]:
    if isinstance(path_or_dict, (str, Path)):
        path = Path(path_or_dict)
        with path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle)
        return loaded or {}

    if isinstance(path_or_dict, dict):
        return path_or_dict

    raise TypeError("path_or_dict must be a file path or a dictionary.")


def _validate_constants(raw_constants: Any) -> dict[str, Any]:
    if not isinstance(raw_constants, dict):
        raise ValueError("`constants` must be a dictionary.")

    missing_keys = sorted(REQUIRED_CONSTANT_KEYS - set(raw_constants))
    if missing_keys:
        raise ValueError(f"`constants` missing required keys: {missing_keys}")

    interval_minutes = _require_int(raw_constants, "interval_minutes", minimum=1)
    intervals_per_day = _require_int(raw_constants, "intervals_per_day", minimum=1)
    if 1440 % interval_minutes != 0:
        raise ValueError("`interval_minutes` must divide evenly into 1440 minutes.")
    expected_intervals = 1440 // interval_minutes
    if intervals_per_day != expected_intervals:
        raise ValueError(
            "`intervals_per_day` must equal 1440 / interval_minutes "
            f"({expected_intervals} for the supplied constants)."
        )

    return {
        "model_name": _require_str(raw_constants, "model_name"),
        "model_tier": _require_str(raw_constants, "model_tier"),
        "interval_minutes": interval_minutes,
        "intervals_per_day": intervals_per_day,
        "timezone": _require_str(raw_constants, "timezone"),
        "segment_column": _require_str(raw_constants, "segment_column"),
        "output_value_column": _require_str(raw_constants, "output_value_column"),
        "schema_version": _optional_str(raw_constants.get("schema_version")),
    }


def _validate_parameters(raw_parameters: Any) -> dict[str, Any]:
    if not isinstance(raw_parameters, dict):
        raise ValueError("`parameters` must be a dictionary.")

    missing_keys = sorted(REQUIRED_PARAMETER_KEYS - set(raw_parameters))
    if missing_keys:
        raise ValueError(f"`parameters` missing required keys: {missing_keys}")

    ramp_start_fcy = _require_int(raw_parameters, "ramp_start_fcy")
    ramp_full_fcy = _require_int(raw_parameters, "ramp_full_fcy")
    if ramp_full_fcy < ramp_start_fcy:
        raise ValueError("`ramp_full_fcy` must be greater than or equal to `ramp_start_fcy`.")

    return {
        "eligible_resi_patterns": _require_str_list(raw_parameters, "eligible_resi_patterns"),
        "smart_meter_code": _require_str(raw_parameters, "smart_meter_code"),
        "eligible_der_type": _require_str(raw_parameters, "eligible_der_type"),
        "window_start": _require_time(raw_parameters, "window_start"),
        "window_end": _require_time(raw_parameters, "window_end"),
        "cap_kwh_per_day": _require_float(raw_parameters, "cap_kwh_per_day", minimum=0.0),
        "u_segment": _require_float_mapping(raw_parameters, "u_segment", require_default=True, minimum=0.0, maximum=1.0),
        "ramp_start_fcy": ramp_start_fcy,
        "ramp_full_fcy": ramp_full_fcy,
        "s_segment": _require_float_mapping(raw_parameters, "s_segment", require_default=True, minimum=0.0, maximum=1.0),
        "k_response": _require_float(raw_parameters, "k_response", minimum=0.0),
        "window_shape": _require_choice(raw_parameters, "window_shape", SUPPORTED_WINDOW_SHAPES),
        "donor_shape": _require_choice(raw_parameters, "donor_shape", SUPPORTED_DONOR_SHAPES),
        "energy_accounting": _require_choice(raw_parameters, "energy_accounting", SUPPORTED_ENERGY_ACCOUNTING),
        "season_modifiers": _optional_float_mapping(raw_parameters.get("season_modifiers")),
        "daytype_modifiers": _optional_float_mapping(raw_parameters.get("daytype_modifiers")),
        "rebound_share": _optional_float(raw_parameters.get("rebound_share"), minimum=0.0, maximum=1.0),
        "rebound_shape": _optional_str(raw_parameters.get("rebound_shape")),
    }


def _require_str(container: dict[str, Any], key: str) -> str:
    value = container.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"`{key}` must be a non-empty string.")
    return value.strip()


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Optional string values must be strings when supplied.")
    stripped = value.strip()
    return stripped or None


def _require_int(container: dict[str, Any], key: str, minimum: int | None = None) -> int:
    value = container.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"`{key}` must be an integer.")
    if minimum is not None and value < minimum:
        raise ValueError(f"`{key}` must be >= {minimum}.")
    return value


def _require_float(container: dict[str, Any], key: str, minimum: float | None = None, maximum: float | None = None) -> float:
    return _optional_float(container.get(key), minimum=minimum, maximum=maximum, key=key)


def _optional_float(
    value: Any,
    minimum: float | None = None,
    maximum: float | None = None,
    key: str = "value",
) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"`{key}` must be numeric.")
    numeric_value = float(value)
    if minimum is not None and numeric_value < minimum:
        raise ValueError(f"`{key}` must be >= {minimum}.")
    if maximum is not None and numeric_value > maximum:
        raise ValueError(f"`{key}` must be <= {maximum}.")
    return numeric_value


def _require_str_list(container: dict[str, Any], key: str) -> list[str]:
    value = container.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"`{key}` must be a non-empty list of strings.")

    cleaned_values: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"`{key}` must contain only non-empty strings.")
        cleaned_values.append(item.strip())

    return cleaned_values


def _require_time(container: dict[str, Any], key: str) -> str:
    value = _require_str(container, key)
    if not TIME_PATTERN.match(value):
        raise ValueError(f"`{key}` must use HH:MM 24-hour format.")
    return value


def _require_choice(container: dict[str, Any], key: str, supported_values: set[str]) -> str:
    value = _require_str(container, key).lower()
    if value not in supported_values:
        raise ValueError(f"`{key}` must be one of {sorted(supported_values)}.")
    return value


def _require_float_mapping(
    container: dict[str, Any],
    key: str,
    require_default: bool,
    minimum: float | None = None,
    maximum: float | None = None,
) -> dict[str, float]:
    mapping = container.get(key)
    if not isinstance(mapping, dict) or not mapping:
        raise ValueError(f"`{key}` must be a non-empty mapping.")
    if require_default and "default" not in mapping:
        raise ValueError(f"`{key}` must contain a `default` entry.")

    normalised_mapping: dict[str, float] = {}
    for item_key, item_value in mapping.items():
        if not isinstance(item_key, str) or not item_key.strip():
            raise ValueError(f"`{key}` mapping keys must be non-empty strings.")
        numeric_value = _optional_float(
            item_value,
            minimum=minimum,
            maximum=maximum,
            key=f"{key}.{item_key}",
        )
        normalised_mapping[item_key.strip()] = float(numeric_value)

    return normalised_mapping


def _optional_float_mapping(value: Any) -> dict[str, float]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("Optional modifier mappings must be dictionaries when supplied.")

    normalised_mapping: dict[str, float] = {}
    for item_key, item_value in value.items():
        if not isinstance(item_key, str) or not item_key.strip():
            raise ValueError("Optional modifier mapping keys must be non-empty strings.")
        numeric_value = _optional_float(
            item_value,
            key=f"modifier.{item_key}",
        )
        normalised_mapping[item_key.strip()] = float(numeric_value)
    return normalised_mapping

