from __future__ import annotations

import copy

import pytest
import yaml

from pyntlp import load_params


def test_load_params_from_dict(base_params):
    params = load_params(copy.deepcopy(base_params))

    assert params["constants"]["interval_minutes"] == 60
    assert params["parameters"]["u_segment"]["Residential"] == 1.0
    assert params["parameters"]["window_shape"] == "flat"


def test_load_params_from_yaml_path(tmp_path, base_params):
    params_path = tmp_path / "params.yaml"
    params_path.write_text(yaml.safe_dump(base_params), encoding="utf-8")

    params = load_params(params_path)

    assert params["parameters"]["window_start"] == "01:00"
    assert params["constants"]["segment_column"] == "segment"


def test_load_params_fails_fast_for_missing_required_key(base_params):
    invalid_params = copy.deepcopy(base_params)
    del invalid_params["parameters"]["cap_kwh_per_day"]

    with pytest.raises(ValueError, match="cap_kwh_per_day"):
        load_params(invalid_params)

