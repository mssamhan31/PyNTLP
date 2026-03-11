from __future__ import annotations

import copy

import pytest
import yaml

from pyntlp import load_params


def test_load_params_from_dict(base_params):
    params = load_params(copy.deepcopy(base_params))

    assert params["constants"]["interval_minutes"] == 60
    assert params["parameters"]["u_eligible_der_group"]["No_DER"] == 1.0
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


def test_load_params_rejects_partial_donor_window(base_params):
    invalid_params = copy.deepcopy(base_params)
    invalid_params["parameters"]["donor_window_start"] = "04:00"

    with pytest.raises(ValueError, match="donor_window_start"):
        load_params(invalid_params)


def test_load_params_rejects_duplicate_der_group_mapping(base_params):
    invalid_params = copy.deepcopy(base_params)
    invalid_params["parameters"]["eligible_der_groups"]["Solar"] = ["No_DER"]

    with pytest.raises(ValueError, match="eligible_der_groups"):
        load_params(invalid_params)
