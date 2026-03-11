from __future__ import annotations

import copy

import pytest

from pyntlp import get_window_intervals, load_params


def test_get_window_intervals_is_start_inclusive_and_end_exclusive(base_params):
    params = load_params(copy.deepcopy(base_params))

    window_intervals, donor_intervals, interval_hours = get_window_intervals(params)

    assert window_intervals == [2, 3]
    assert donor_intervals[0] == 1
    assert 2 not in donor_intervals
    assert len(window_intervals) == 2
    assert len(donor_intervals) == 22
    assert interval_hours == 1.0


def test_get_window_intervals_supports_overnight_windows(base_params):
    overnight_params = copy.deepcopy(base_params)
    overnight_params["parameters"]["window_start"] = "23:00"
    overnight_params["parameters"]["window_end"] = "02:00"

    params = load_params(overnight_params)
    window_intervals, donor_intervals, _ = get_window_intervals(params)

    assert window_intervals == [1, 2, 24]
    assert len(donor_intervals) == 21


def test_get_window_intervals_supports_explicit_donor_window(base_params):
    explicit_donor_params = copy.deepcopy(base_params)
    explicit_donor_params["parameters"]["donor_window_start"] = "04:00"
    explicit_donor_params["parameters"]["donor_window_end"] = "06:00"

    params = load_params(explicit_donor_params)
    window_intervals, donor_intervals, _ = get_window_intervals(params)

    assert window_intervals == [2, 3]
    assert donor_intervals == [5, 6]


def test_get_window_intervals_supports_explicit_overnight_donor_window(base_params):
    explicit_donor_params = copy.deepcopy(base_params)
    explicit_donor_params["parameters"]["window_start"] = "10:00"
    explicit_donor_params["parameters"]["window_end"] = "12:00"
    explicit_donor_params["parameters"]["donor_window_start"] = "23:00"
    explicit_donor_params["parameters"]["donor_window_end"] = "02:00"

    params = load_params(explicit_donor_params)
    window_intervals, donor_intervals, _ = get_window_intervals(params)

    assert window_intervals == [11, 12]
    assert donor_intervals == [1, 2, 24]


def test_get_window_intervals_rejects_overlapping_explicit_donor_window(base_params):
    overlapping_params = copy.deepcopy(base_params)
    overlapping_params["parameters"]["donor_window_start"] = "02:00"
    overlapping_params["parameters"]["donor_window_end"] = "04:00"

    params = load_params(overlapping_params)

    with pytest.raises(ValueError, match="overlaps"):
        get_window_intervals(params)
