"""
QuantYield ML Services
======================
Self-contained AI and machine learning models for fixed income analytics.

All models are framework-agnostic at the interface level.
PyTorch and XGBoost are optional; scikit-learn and numpy/scipy are required.
"""

from ml_services.credit_spread_model import predict_credit_spread
from ml_services.forecaster import (
    available_backend,
    clear_model_cache,
    forecast_rates,
    train_forecaster,
)
from ml_services.pca_factor_model import (
    decompose_curve,
    factor_sensitivity,
    generate_synthetic_curve_panel,
    reconstruct_curve,
    rolling_pca_factors,
)
from ml_services.regime_classifier import classify_regime
from ml_services.schemas import (
    CreditSpreadResult,
    ForecastResult,
    PCAResult,
    RegimeResult,
    VolatilityResult,
)
from ml_services.volatility_model import forecast_volatility, volatility_term_structure

__all__ = [
    "ForecastResult",
    "RegimeResult",
    "CreditSpreadResult",
    "VolatilityResult",
    "PCAResult",
    "train_forecaster",
    "forecast_rates",
    "clear_model_cache",
    "available_backend",
    "classify_regime",
    "forecast_volatility",
    "volatility_term_structure",
    "predict_credit_spread",
    "decompose_curve",
    "reconstruct_curve",
    "factor_sensitivity",
    "rolling_pca_factors",
    "generate_synthetic_curve_panel",
]
