"""Shared fixtures for the ml_services tests."""

import sys
from pathlib import Path

import numpy as np
import pytest

# ml_services is imported as a top-level package, so the directory that
# contains it (code/) must be importable no matter where pytest is started.
CODE_DIR = Path(__file__).resolve().parents[2]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))


@pytest.fixture
def rate_series() -> np.ndarray:
    """300 days of a random-walk 10Y yield around 4.5 percent (decimal form)."""
    rng = np.random.default_rng(1)
    return 0.045 + np.cumsum(rng.normal(0, 0.0005, 300))


@pytest.fixture
def curve_panel() -> np.ndarray:
    """A 300 x 10 panel of synthetic yield curves."""
    from ml_services.pca_factor_model import generate_synthetic_curve_panel

    return generate_synthetic_curve_panel(n_obs=300, seed=42)
