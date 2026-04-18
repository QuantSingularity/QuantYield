"""
QuantYield ML Services - Yield Curve PCA Factor Decomposition

Decomposes the yield curve into its principal components:
  - PC1: Level (parallel shift, explains ~90 pct of variance)
  - PC2: Slope (short vs long end)
  - PC3: Curvature (butterfly / hump)

This is the standard Litterman-Scheinkman (1991) approach used by
fixed income desks for risk factor decomposition and hedging.

Additional capabilities:
  - Factor score time series extraction
  - Curve reconstruction from k factors
  - Stress-testing via factor perturbation
  - Rolling PCA for regime change detection
"""

from __future__ import annotations

import logging

import numpy as np
from ml_services.schemas import PCAResult

logger = logging.getLogger("quantyield.ml")

STANDARD_TENORS = [0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0]
FACTOR_NAMES = ["Level", "Slope", "Curvature"]


# ---------------------------------------------------------------------------
# Core PCA
# ---------------------------------------------------------------------------


def decompose_curve(
    curve_matrix: np.ndarray,
    tenors: list[float] | None = None,
    n_components: int = 3,
) -> PCAResult:
    """
    Perform PCA on a panel of yield curve observations.

    Parameters
    ----------
    curve_matrix:
        Array of shape (n_observations, n_tenors) where each row is a
        yield curve observation (rates in decimal form).
    tenors:
        Tenor labels corresponding to columns of curve_matrix.
        Defaults to STANDARD_TENORS.
    n_components:
        Number of principal components to retain.

    Returns
    -------
    PCAResult with loadings, explained variance, and factor scores.
    """
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    if tenors is None:
        tenors = STANDARD_TENORS[: curve_matrix.shape[1]]

    # Standardise each tenor (remove mean, scale to unit variance)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(curve_matrix)

    n_comp = min(n_components, X_scaled.shape[1], X_scaled.shape[0])
    pca = PCA(n_components=n_comp, random_state=42)
    factor_scores = pca.fit_transform(X_scaled)

    # Sign convention: PC1 positive => parallel upward shift
    for i in range(n_comp):
        if pca.components_[i].mean() < 0:
            pca.components_[i] *= -1
            factor_scores[:, i] *= -1

    # Reconstruction error (in-sample)
    X_reconstructed = pca.inverse_transform(factor_scores)
    reconstruction_error = float(np.sqrt(np.mean((X_scaled - X_reconstructed) ** 2)))

    factor_labels = FACTOR_NAMES[:n_comp] + [
        f"PC{i+1}" for i in range(len(FACTOR_NAMES), n_comp)
    ]

    return PCAResult(
        components=pca.components_.tolist(),
        explained_variance_ratio=pca.explained_variance_ratio_.tolist(),
        factor_scores=factor_scores.tolist(),
        factor_names=factor_labels,
        tenors=tenors,
        reconstruction_error=round(reconstruction_error, 6),
    )


def reconstruct_curve(
    result: PCAResult, factor_overrides: dict[str, float] | None = None
) -> dict[float, float]:
    """
    Reconstruct a yield curve from PCA factors, optionally overriding factor scores.
    Useful for stress-testing specific factor movements.

    Parameters
    ----------
    result:
        PCAResult from ``decompose_curve()``.
    factor_overrides:
        Dict mapping factor name (e.g. "Level") to new score value.
        If None, uses the last observed factor scores.

    Returns
    -------
    Dict mapping tenor to reconstructed rate.
    """
    components = np.array(result.components)
    last_scores = (
        np.array(result.factor_scores[-1])
        if result.factor_scores
        else np.zeros(len(result.factor_names))
    )

    scores = last_scores.copy()
    if factor_overrides:
        for i, name in enumerate(result.factor_names):
            if name in factor_overrides:
                scores[i] = factor_overrides[name]

    # Approximate reconstruction (assumes zero mean, unit variance scaler)
    reconstructed = components.T @ scores
    return {tenor: round(float(r), 6) for tenor, r in zip(result.tenors, reconstructed)}


def factor_sensitivity(
    result: PCAResult,
    factor_name: str,
    shift_std: float = 1.0,
) -> dict[float, float]:
    """
    Compute the change in each tenor rate for a 1-std-dev shift in a factor.

    Parameters
    ----------
    result:
        PCAResult from ``decompose_curve()``.
    factor_name:
        Name of the factor to shift (e.g. "Level", "Slope").
    shift_std:
        Number of standard deviations to shift.

    Returns
    -------
    Dict mapping tenor to rate change in decimal.
    """
    if factor_name not in result.factor_names:
        raise ValueError(
            f"Factor '{factor_name}' not found. Available: {result.factor_names}"
        )

    idx = result.factor_names.index(factor_name)
    loading = np.array(result.components[idx])
    rate_change = loading * shift_std

    return {tenor: round(float(dr), 6) for tenor, dr in zip(result.tenors, rate_change)}


def rolling_pca_factors(
    curve_matrix: np.ndarray,
    window: int = 63,
    tenors: list[float] | None = None,
) -> dict[str, list[float]]:
    """
    Compute rolling PCA factor scores to detect regime changes over time.

    Parameters
    ----------
    curve_matrix:
        Array of shape (n_observations, n_tenors).
    window:
        Rolling window size in trading days.
    tenors:
        Tenor labels.

    Returns
    -------
    Dict mapping factor name to list of rolling factor score values.
    """
    n_obs = curve_matrix.shape[0]
    if n_obs < window:
        return {}

    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    factor_history: dict[str, list[float]] = {name: [] for name in FACTOR_NAMES[:3]}

    for i in range(window, n_obs + 1):
        window_data = curve_matrix[i - window : i]
        scaler = StandardScaler()
        X = scaler.fit_transform(window_data)
        pca = PCA(n_components=3, random_state=42)
        pca.fit(X)
        scores = pca.transform(X[-1:].reshape(1, -1))[0]

        for j, name in enumerate(FACTOR_NAMES[:3]):
            factor_history[name].append(round(float(scores[j]), 6))

    return factor_history


# ---------------------------------------------------------------------------
# Synthetic curve generator (for testing and demos)
# ---------------------------------------------------------------------------


def generate_synthetic_curve_panel(
    n_obs: int = 500,
    tenors: list[float] | None = None,
    seed: int = 42,
) -> np.ndarray:
    """
    Generate a realistic panel of yield curves driven by 3 latent factors.
    Used for testing and documentation examples.
    """
    if tenors is None:
        tenors = STANDARD_TENORS

    rng = np.random.default_rng(seed)
    len(tenors)

    # Latent factor paths (random walk)
    level_path = 0.045 + np.cumsum(rng.normal(0, 0.0005, n_obs))
    slope_path = 0.005 + np.cumsum(rng.normal(0, 0.0003, n_obs))
    curve_path = 0.002 + np.cumsum(rng.normal(0, 0.0002, n_obs))

    curves = []
    for t in range(n_obs):
        lv, sl, cu = level_path[t], slope_path[t], curve_path[t]
        row = []
        for tenor in tenors:
            # Nelson-Siegel style: level + slope * exp(-t) + curvature * t*exp(-t)
            x = tenor / 2.0
            rate = lv + sl * np.exp(-x) + cu * x * np.exp(-x) + rng.normal(0, 0.0002)
            row.append(max(0.001, rate))
        curves.append(row)

    return np.array(curves)
