"""Public package exports for pyntlp.

Importing from `pyntlp` exposes the stable functions used by notebooks and
pipeline wrappers: parameter loading, eligibility metrics, PMA computation,
validation, and window utilities.
"""

from .metrics import build_lga_segment_metrics
from .model import compute_pma_sso
from .params import load_params
from .utils import resolve_lga_segment_parameter
from .validation import validate_pma
from .windows import get_window_intervals

__all__ = [
    "build_lga_segment_metrics",
    "compute_pma_sso",
    "get_window_intervals",
    "load_params",
    "resolve_lga_segment_parameter",
    "validate_pma",
]

__version__ = "0.1.0"
