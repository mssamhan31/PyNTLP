"""Single source of truth for the AQF recoverability experiment.

Every grid value, seed, and threshold used anywhere in the pipeline (data
generation, estimation, scoring, figures, and the experiment-factors table
quoted in the paper) is defined here so the paper can never drift from the
code that produced it.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

# --- Paths -------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
BRONZE_DIR = DATA_DIR / "1_bronze"
SILVER_DIR = DATA_DIR / "2_silver"
GOLD_DIR = DATA_DIR / "3_gold"
GOLD_TABLES_DIR = GOLD_DIR / "tables"
GOLD_FIGURES_DIR = GOLD_DIR / "figures"

# --- Fixed-timestamp mixture model L = B + Z*A + eps --------------------
SIGMA = 1.0  # ordinary noise std dev at the fixed timestamp
BACKBONE_B = 10.0  # true backbone level (arbitrary units, e.g. kW)
DAYS = 365  # sample size D at the fixed timestamp
DT_HOURS = 0.5  # interval length, for energy accounting consistency with PyNTLP

# --- Recoverability grid -------------------------------------------------
P_GRID = np.round(np.linspace(0.05, 0.95, 10), 3)  # persistence
KAPPA_GRID = np.round(np.linspace(0.5, 5.0, 10), 3)  # signal-to-variability ratio A/sigma

N_REPLICATES = 20
BASE_SEED = 42

# --- Estimators -----------------------------------------------------------
FIXED_QS = [0.1, 0.2, 0.3]
Q_DEFAULT = 0.2  # fallback quantile when the mixture is not identifiable
D_THRESH = 2.0  # Ashman's D identifiability threshold (rule-of-thumb separation)

ESTIMATOR_VARIANTS = [f"fixed_q_{q}" for q in FIXED_QS] + ["oracle_aqf", "estimated_aqf"]

# Smallest kappa at which the mixture clears the Ashman's D identifiability bar.
# Derived from D_THRESH so the "trustworthy region" quoted in the paper can never
# drift from the fallback rule that actually gates the estimator (D = kappa/sqrt(2)).
KAPPA_IDENTIFIABLE = float(np.sqrt(2.0) * D_THRESH)  # 2.828
P_ROBUST = 0.3  # secondary restriction: events frequent enough to be estimable

# Expected value of max(eps, 0) for eps ~ N(0, sigma^2), in units of sigma.
# This is the per-non-event-day truncation "noise floor" that F_hat = max(L-B_hat, 0)
# counts as flexibility even when the backbone is perfect.
NOISE_FLOOR_PER_DAY = float(1.0 / np.sqrt(2.0 * np.pi))  # 0.3989 sigma

# --- Figure geometry (IEEE two-column) ------------------------------------
# Figures are authored at their FINAL printed width so Word never rescales them
# and in-figure type keeps the point size set here. build_docx derives its
# Inches() widths from these values.
FIG_COL_W_IN = 3.30  # one IEEE column
FIG_FULL_W_IN = 7.00  # both columns (a "figure*" island)
FIG_DPI = 600


def ensure_dirs() -> None:
    """Create the bronze/silver/gold folders if they do not exist yet."""
    for d in (BRONZE_DIR, SILVER_DIR, GOLD_TABLES_DIR, GOLD_FIGURES_DIR):
        d.mkdir(parents=True, exist_ok=True)
