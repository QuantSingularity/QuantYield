"""
QuantYield ML Services - Shared Schemas and Base Classes
Defines the contracts that all ML models in this package must satisfy.
"""

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Forecast output contract
# ---------------------------------------------------------------------------


@dataclass
class ForecastResult:
    """Standard output from any rate forecasting model."""

    point: list[float]
    lower: list[float]
    upper: list[float]
    backend: str
    confidence_level: float = 0.90
    horizon_days: int = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class RegimeResult:
    """Output from the regime classification model."""

    regime: str
    probability: float
    all_probabilities: dict[str, float]
    features: dict[str, float]
    model: str


@dataclass
class CreditSpreadResult:
    """Output from the credit spread prediction model."""

    predicted_spread_bps: float
    confidence_interval_lower_bps: float
    confidence_interval_upper_bps: float
    feature_importances: dict[str, float]
    model: str


@dataclass
class VolatilityResult:
    """Output from the volatility forecasting model."""

    forecast_annualised_pct: list[float]
    current_vol_annualised_pct: float
    model: str
    horizon_days: int
    garch_params: Optional[dict] = None


@dataclass
class PCAResult:
    """Output from the yield curve PCA decomposition."""

    components: list[list[float]]  # shape: [n_components, n_tenors]
    explained_variance_ratio: list[float]
    factor_scores: list[list[float]]  # shape: [n_observations, n_components]
    factor_names: list[str]
    tenors: list[float]
    reconstruction_error: float
