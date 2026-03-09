from __future__ import annotations

import copy

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

