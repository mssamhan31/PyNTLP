"""Backbone estimators: fixed-quantile baseline and Adaptive Quantile
Flexibility (AQF), with identifiability check and soft-blend fallback.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import norm
from sklearn.mixture import GaussianMixture


def fixed_quantile_backbone(load: np.ndarray, q: float) -> float:
    """Backbone estimate B_hat = Q_q(L) for a fixed, pre-chosen quantile."""
    return float(np.quantile(load, q))


@dataclass
class MixtureFit:
    p_hat: float
    kappa_hat: float
    sigma_hat: float
    backbone_hat: float  # mean of the lower ("non-event") component


def fit_mixture(load: np.ndarray, seed: int) -> MixtureFit:
    """Fit a 2-component Gaussian mixture with shared (tied) variance.

    The lower-mean component is treated as the non-event/backbone state and
    the higher-mean component as the event state, matching L = B + Z*A + eps.
    """
    gmm = GaussianMixture(n_components=2, covariance_type="tied", random_state=seed, n_init=5)
    gmm.fit(load.reshape(-1, 1))

    means = gmm.means_.ravel()
    weights = gmm.weights_.ravel()
    sigma_hat = float(np.sqrt(gmm.covariances_.ravel()[0]))

    low_idx = int(np.argmin(means))
    high_idx = 1 - low_idx

    backbone_hat = float(means[low_idx])
    p_hat = float(weights[high_idx])
    kappa_hat = float(max(means[high_idx] - means[low_idx], 0.0) / sigma_hat) if sigma_hat > 0 else 0.0

    return MixtureFit(p_hat=p_hat, kappa_hat=kappa_hat, sigma_hat=sigma_hat, backbone_hat=backbone_hat)


def aqf_quantile(p_hat: float, kappa_hat: float) -> float:
    """Bias-minimising quantile q_t*, the b=0 corollary of the central relation.

    q_t* = (1 - p_hat) / 2 + p_hat * Phi(-kappa_hat)
    """
    return (1.0 - p_hat) / 2.0 + p_hat * norm.cdf(-kappa_hat)


def identifiability_diagnostic(kappa_hat: float) -> float:
    """Ashman's D separation statistic: D = kappa / sqrt(2)."""
    return kappa_hat / np.sqrt(2.0)


def fallback_blend(q_star: float, q_default: float, d_hat: float, d_thresh: float) -> tuple[float, float]:
    """Soft-blend q_star toward q_default in proportion to identifiability confidence.

    Returns (q_final, weight) where weight=1 means "fully trust q_star" and
    weight=0 means "not identifiable, use the default".
    """
    weight = float(np.clip(d_hat / d_thresh, 0.0, 1.0))
    q_final = weight * q_star + (1.0 - weight) * q_default
    return q_final, weight


def residual_estimator(load: np.ndarray, backbone_hat: float) -> np.ndarray:
    """Shape-identifiable candidate flexibility: F_hat = max(L - B_hat, 0)."""
    return np.maximum(load - backbone_hat, 0.0)
