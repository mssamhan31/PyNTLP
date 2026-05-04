"""Time-window utilities for mapping policy windows onto intervals.

Window boundaries use start-inclusive and end-exclusive HH:MM clock times. The
helpers convert those clock windows into one-based interval numbers used by the
Spark model and validation code.
"""

from __future__ import annotations

import re

TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def get_window_intervals(params: dict) -> tuple[list[int], list[int], float]:
    """Return policy-window intervals, donor intervals, and interval hours.

    If no explicit donor window is configured, every interval outside the policy
    window becomes a donor interval. Explicit donor windows may wrap overnight
    but must not overlap the policy window.
    """

    constants = params["constants"]
    parameters = params["parameters"]

    interval_minutes = int(constants["interval_minutes"])
    intervals_per_day = int(constants["intervals_per_day"])
    interval_hours = interval_minutes / 60.0

    all_intervals = list(range(1, intervals_per_day + 1))

    window_set = _build_interval_set(
        interval_minutes=interval_minutes,
        all_intervals=all_intervals,
        window_start=parameters["window_start"],
        window_end=parameters["window_end"],
        window_label="window",
        start_key="window_start",
        end_key="window_end",
    )
    window_intervals = [interval_index for interval_index in all_intervals if interval_index in window_set]

    donor_window_start = parameters.get("donor_window_start")
    donor_window_end = parameters.get("donor_window_end")
    if donor_window_start is None and donor_window_end is None:
        donor_intervals = [interval_index for interval_index in all_intervals if interval_index not in window_set]
    else:
        donor_set = _build_interval_set(
            interval_minutes=interval_minutes,
            all_intervals=all_intervals,
            window_start=donor_window_start,
            window_end=donor_window_end,
            window_label="donor window",
            start_key="donor_window_start",
            end_key="donor_window_end",
        )
        overlap = sorted(window_set & donor_set)
        if overlap:
            raise ValueError(f"Configured donor window overlaps the free window on intervals: {overlap}")
        donor_intervals = [interval_index for interval_index in all_intervals if interval_index in donor_set]

    if not window_intervals:
        raise ValueError("Configured window produced no in-window intervals.")
    if not donor_intervals:
        raise ValueError("Configured window produced no donor intervals.")

    return window_intervals, donor_intervals, interval_hours


def _parse_clock_time(clock_time: str) -> int:
    """Convert an HH:MM clock value into minutes after midnight."""

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
    """Return whether an interval start falls inside a clock window."""

    interval_start_minutes = (interval_index - 1) * interval_minutes

    if window_start_minutes < window_end_minutes:
        return window_start_minutes <= interval_start_minutes < window_end_minutes

    return interval_start_minutes >= window_start_minutes or interval_start_minutes < window_end_minutes


def _build_interval_set(
    interval_minutes: int,
    all_intervals: list[int],
    window_start: str,
    window_end: str,
    window_label: str,
    start_key: str | None = None,
    end_key: str | None = None,
) -> set[int]:
    """Build a set of one-based interval indexes covered by a clock window."""

    window_start_minutes = _parse_clock_time(window_start)
    window_end_minutes = _parse_clock_time(window_end)
    start_key = start_key or f"{window_label}_start"
    end_key = end_key or f"{window_label}_end"

    if window_start_minutes % interval_minutes != 0:
        raise ValueError(f"`{start_key}` must align to `interval_minutes`.")
    if window_end_minutes % interval_minutes != 0:
        raise ValueError(f"`{end_key}` must align to `interval_minutes`.")
    if window_start_minutes == window_end_minutes:
        raise ValueError(f"{window_label.capitalize()} cannot be empty or cover the entire day.")

    return {
        interval_index
        for interval_index in all_intervals
        if _interval_start_in_window(
            interval_index=interval_index,
            interval_minutes=interval_minutes,
            window_start_minutes=window_start_minutes,
            window_end_minutes=window_end_minutes,
        )
    }
