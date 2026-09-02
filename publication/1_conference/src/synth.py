"""Synthetic data generator for the fixed-timestamp mixture model.

L = B + Z*A + eps,  Z ~ Bernoulli(p),  eps ~ N(0, sigma^2),  A = kappa * sigma
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate_days(
    p: float,
    kappa: float,
    sigma: float,
    backbone_b: float,
    days: int,
    seed: int,
) -> pd.DataFrame:
    """Generate D synthetic days for one (p, kappa) scenario.

    Returns a DataFrame with one row per day: day index, event indicator Z,
    noise eps, observed load L, and the ground-truth backbone/flexible split
    (B_true is constant by construction; F_true = Z * A).
    """
    rng = np.random.default_rng(seed)
    a = kappa * sigma

    z = rng.binomial(1, p, size=days)
    eps = rng.normal(0.0, sigma, size=days)
    f_true = z * a
    load = backbone_b + f_true + eps

    return pd.DataFrame(
        {
            "day": np.arange(days),
            "z": z,
            "eps": eps,
            "l": load,
            "b_true": backbone_b,
            "f_true": f_true,
        }
    )
