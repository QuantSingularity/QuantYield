"""
QuantYield ML Services - Credit Spread Predictor

Predicts corporate bond credit spreads using an XGBoost / Random Forest
ensemble trained on macro and market features.

Features:
  - Treasury level (10Y rate)
  - Yield curve slope (10Y minus 2Y)
  - Yield curve curvature (butterfly)
  - Implied volatility proxy (rolling 21d vol of 10Y)
  - Credit rating (ordinal encoded)
  - Time to maturity
  - Coupon rate
  - Sector (one-hot encoded)

Output:
  - Predicted OAS in basis points
  - 80 pct prediction interval
  - Feature importance ranking
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
from ml_services.schemas import CreditSpreadResult

logger = logging.getLogger("quantyield.ml")

# Rating -> ordinal score (lower = higher quality)
RATING_SCORES: dict[str, float] = {
    "AAA": 1.0,
    "AA+": 1.5,
    "AA": 2.0,
    "AA-": 2.5,
    "A+": 3.0,
    "A": 3.5,
    "A-": 4.0,
    "BBB+": 5.0,
    "BBB": 5.5,
    "BBB-": 6.0,
    "BB+": 7.0,
    "BB": 7.5,
    "BB-": 8.0,
    "B+": 9.0,
    "B": 9.5,
    "B-": 10.0,
    "CCC+": 11.0,
    "CCC": 12.0,
    "CCC-": 13.0,
    "NR": 6.0,  # treat unrated as BBB- equivalent
}

SECTORS = [
    "Government",
    "Financials",
    "Technology",
    "Energy",
    "Healthcare",
    "Consumer Discretionary",
    "Consumer Staples",
    "Industrials",
    "Telecommunications",
    "Utilities",
    "Materials",
    "Real Estate",
    "Other",
]

FEATURE_NAMES = [
    "level_10y_pct",
    "slope_2s10s_bps",
    "butterfly_bps",
    "yield_vol_21d_pct",
    "rating_score",
    "years_to_maturity",
    "coupon_rate_pct",
] + [f"sector_{s.replace(' ', '_').lower()}" for s in SECTORS]

_CREDIT_MODEL: Optional[dict] = None


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------


def _build_feature_vector(
    rating: str,
    years_to_maturity: float,
    coupon_rate: float,
    level_10y: float,
    slope_2s10s_bps: float,
    butterfly_bps: float,
    yield_vol_21d_pct: float,
    sector: str,
) -> np.ndarray:
    rating_score = RATING_SCORES.get(rating.strip().upper(), 6.0)
    sector_ohe = [1.0 if s == sector else 0.0 for s in SECTORS]
    if sum(sector_ohe) == 0:
        # Unknown sector -> "Other"
        sector_ohe[-1] = 1.0

    features = [
        level_10y * 100,
        slope_2s10s_bps,
        butterfly_bps,
        yield_vol_21d_pct,
        rating_score,
        years_to_maturity,
        coupon_rate * 100,
    ] + sector_ohe

    return np.array(features, dtype=np.float32).reshape(1, -1)


# ---------------------------------------------------------------------------
# Synthetic training data
# ---------------------------------------------------------------------------


def _generate_credit_training_data(
    n_samples: int = 5000, seed: int = 42
) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate realistic-looking synthetic credit spread training data.
    Spreads increase with rating risk, maturity (up to ~15Y), and vol.
    """
    rng = np.random.default_rng(seed)

    X, y = [], []
    rating_items = list(RATING_SCORES.items())

    for _ in range(n_samples):
        rating_name, rating_score = rating_items[rng.integers(len(rating_items))]
        ytm_years = rng.uniform(1, 30)
        coupon = rng.uniform(0.01, 0.08)
        level_10y = rng.uniform(2.0, 8.0)
        slope = rng.uniform(-80, 180)
        butterfly = rng.uniform(-40, 60)
        vol = rng.uniform(0.2, 2.0)
        sector_idx = rng.integers(len(SECTORS))
        sector_ohe = [0.0] * len(SECTORS)
        sector_ohe[sector_idx] = 1.0

        # Spread model: base from rating + maturity premium + macro sensitivity
        base_spread = 15 * rating_score + rng.normal(0, 5)
        maturity_premium = max(0, (ytm_years - 5) * 1.5)
        macro_factor = -slope * 0.3 + vol * 30
        sector_factor = [0, 40, -10, 30, 15, 25, 10, 20, 35, 5, 25, 45, 0][sector_idx]
        spread_bps = max(
            5,
            base_spread
            + maturity_premium
            + macro_factor
            + sector_factor
            + rng.normal(0, 10),
        )

        features = [
            level_10y,
            slope,
            butterfly,
            vol,
            rating_score,
            ytm_years,
            coupon * 100,
        ] + sector_ohe
        X.append(features)
        y.append(spread_bps)

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


# ---------------------------------------------------------------------------
# Model training
# ---------------------------------------------------------------------------


def _train_credit_model() -> dict:
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    X, y = _generate_credit_training_data()

    rf = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "reg",
                RandomForestRegressor(
                    n_estimators=300,
                    max_depth=10,
                    min_samples_leaf=5,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    rf.fit(X, y)

    gb = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "reg",
                GradientBoostingRegressor(
                    n_estimators=200,
                    max_depth=5,
                    learning_rate=0.05,
                    subsample=0.8,
                    random_state=42,
                ),
            ),
        ]
    )
    gb.fit(X, y)

    try:
        import xgboost as xgb

        xgb_reg = xgb.XGBRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbosity=0,
        )
        xgb_reg.fit(X, y)
        models = [rf, gb, ("xgb", xgb_reg)]
        backend = "xgb_ensemble"
    except ImportError:
        models = [rf, gb]
        backend = "sklearn_ensemble"

    # Extract RF feature importances
    rf_inner = rf.named_steps["reg"]
    importances = {
        name: round(float(imp), 4)
        for name, imp in zip(FEATURE_NAMES, rf_inner.feature_importances_)
    }

    logger.info("Credit spread model trained (%s)", backend)
    return {"models": models, "backend": backend, "importances": importances}


def _get_credit_model() -> dict:
    global _CREDIT_MODEL
    if _CREDIT_MODEL is None:
        _CREDIT_MODEL = _train_credit_model()
    return _CREDIT_MODEL


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def predict_credit_spread(
    rating: str,
    years_to_maturity: float,
    coupon_rate: float,
    level_10y: float,
    slope_2s10s_bps: float,
    butterfly_bps: float,
    yield_vol_21d_pct: float,
    sector: str = "Other",
) -> CreditSpreadResult:
    """
    Predict the OAS / credit spread for a bond.

    Parameters
    ----------
    rating:
        Credit rating string (e.g. "A+", "BBB", "BB-").
    years_to_maturity:
        Remaining life of the bond in years.
    coupon_rate:
        Annual coupon as decimal (0.05 = 5 pct).
    level_10y:
        Current 10Y Treasury rate as decimal.
    slope_2s10s_bps:
        10Y minus 2Y Treasury spread in basis points.
    butterfly_bps:
        2s5s10s butterfly in basis points.
    yield_vol_21d_pct:
        Annualised 21-day rolling volatility of 10Y rate in percentage points.
    sector:
        Bond sector (e.g. "Technology", "Financials").

    Returns
    -------
    CreditSpreadResult with predicted spread and confidence interval.
    """
    X = _build_feature_vector(
        rating,
        years_to_maturity,
        coupon_rate,
        level_10y,
        slope_2s10s_bps,
        butterfly_bps,
        yield_vol_21d_pct,
        sector,
    )

    try:
        model_state = _get_credit_model()
        models = model_state["models"]

        predictions = []
        for m in models:
            if isinstance(m, tuple):
                # XGBoost not in pipeline
                predictions.append(float(m[1].predict(X)[0]))
            else:
                predictions.append(float(m.predict(X)[0]))

        mean_pred = float(np.mean(predictions))
        std_pred = (
            float(np.std(predictions)) if len(predictions) > 1 else mean_pred * 0.15
        )

        lower = max(1.0, mean_pred - 1.28 * std_pred)  # 80 pct interval
        upper = mean_pred + 1.28 * std_pred

        importances = model_state.get("importances", {})

        return CreditSpreadResult(
            predicted_spread_bps=round(mean_pred, 2),
            confidence_interval_lower_bps=round(lower, 2),
            confidence_interval_upper_bps=round(upper, 2),
            feature_importances=importances,
            model=model_state["backend"],
        )

    except Exception as exc:
        logger.warning("Credit spread prediction failed (%s), using rule-based", exc)
        # Simple rating-based fallback
        base = RATING_SCORES.get(rating.strip().upper(), 6.0) * 18
        return CreditSpreadResult(
            predicted_spread_bps=round(base, 2),
            confidence_interval_lower_bps=round(base * 0.75, 2),
            confidence_interval_upper_bps=round(base * 1.35, 2),
            feature_importances={},
            model="rule_based_fallback",
        )
