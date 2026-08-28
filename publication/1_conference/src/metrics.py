"""Evaluation metrics: flexible-energy recovery ratio and backbone error."""

from __future__ import annotations

import numpy as np


def recovery_ratio(f_hat: np.ndarray, f_true: np.ndarray, dt_hours: float) -> float:
    """R_F = estimated flexible energy / true flexible energy.

    Returns NaN when E_F_true is zero (no event occurred in this scenario),
    since the ratio is undefined rather than misleadingly large/small.
    """
    e_true = float(np.sum(f_true) * dt_hours)
    e_hat = float(np.sum(f_hat) * dt_hours)
    if e_true == 0.0:
        return float("nan")
    return e_hat / e_true


def backbone_abs_error(backbone_hat: float, backbone_true: float) -> float:
    """Absolute error of a single scenario's backbone estimate."""
    return abs(backbone_hat - backbone_true)
