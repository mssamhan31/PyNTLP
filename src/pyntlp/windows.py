"""Time-window utilities for mapping policy windows onto intervals."""

from __future__ import annotations

import re

TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def get_window_intervals(params: dict) -> tuple[list[int], list[int], float]:
    """Return window intervals, donor intervals, and interval hours."""

    constants = params["constants"]
    parameters = params["parameters"]

    interval_minutes = int(constants["interval_minutes"])
    intervals_per_day = int(constants["intervals_per_day"])
    interval_hours = interval_minutes / 60.0

    window_start_minutes = _parse_clock_time(parameters["window_start"])
    window_end_minutes = _parse_clock_time(parameters["window_end"])

    if window_start_minutes % interval_minutes != 0:
        raise ValueError("`window_start` must align to `interval_minutes`.")
    if window_end_minutes % interval_minutes != 0:
        raise ValueError("`window_end` must align to `interval_minutes`.")
    if window_start_minutes == window_end_minutes:
        raise ValueError("Window cannot be empty or cover the entire day.")

    all_intervals = list(range(1, intervals_per_day + 1))
    window_set = {
        interval_index
        for interval_index in all_intervals
        if _interval_start_in_window(
            interval_index=interval_index,
            interval_minutes=interval_minutes,
            window_start_minutes=window_start_minutes,
            window_end_minutes=window_end_minutes,
        )
    }
    window_intervals = [interval_index for interval_index in all_intervals if interval_index in window_set]
    donor_intervals = [interval_index for interval_index in all_intervals if interval_index not in window_set]

    if not window_intervals:
        raise ValueError("Configured window produced no in-window intervals.")
    if not donor_intervals:
        raise ValueError("Configured window produced no donor intervals.")

    return window_intervals, donor_intervals, interval_hours


def _parse_clock_time(clock_time: str) -> int:
    match = TIME_PATTERN.match(clock_time)
    if match is None:
        raise ValueError(f"Clock time must use HH:MM 24-hour format: {clock_time}")
    hours = int(match.group(1))
    minutes = int(match.group(2))
    return hours * 60 + minutes


def _interval_start_in_window(
    interval_index: int,
    interval_minutes: int,
    window_start_minutes: int,
    window_end_minutes: int,
) -> bool:
    interval_start_minutes = (interval_index - 1) * interval_minutes

    if window_start_minutes < window_end_minutes:
        return window_start_minutes <= interval_start_minutes < window_end_minutes

    return interval_start_minutes >= window_start_minutes or interval_start_minutes < window_end_minutes

