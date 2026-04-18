"""
QuantYield ML Services - Yield Curve Regime Classifier

Classifies the current yield curve regime using an ensemble of:
  - Random Forest (probabilistic, always available via scikit-learn)
  - XGBoost (if installed)

Features engineered from the spot rate curve:
  - Level (10Y rate)
  - Slope (10Y minus 2Y)
  - Curvature (2s5s10s butterfly)
  - Short-end slope (2Y minus 3M)
  - Long-end slope (30Y minus 10Y)
  - Rolling volatility of 10Y (21-day)
  - Rate of change of 10Y (5-day momentum)

Regimes:
  normal    - Upward sloping, moderate slope
  inverted  - Short rates above long rates
  flat      - Near-zero slope
  steep     - Extreme positive slope
  humped    - Peak in the 5-7Y sector
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
from ml_services.schemas import RegimeResult

logger = logging.getLogger("quantyield.ml")

# Regime labels
REGIMES = ["normal", "inverted", "flat", "steep", "humped"]

# Cached model instance
_REGIME_MODEL: Optional[dict] = None


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------


def _engineer_features(
    spot_rates: dict[float, float], rate_history: Optional[np.ndarray] = None
) -> dict[str, float]:
    """
    Build feature vector from a spot rate dictionary.
    All rates are in decimal form (0.045 = 4.5 pct).
    """

    def get(t: float) -> float:
        tenors = sorted(spot_rates.keys())
        if not tenors:
            return 0.0
        if t <= tenors[0]:
            return spot_rates[tenors[0]]
        if t >= tenors[-1]:
            return spot_rates[tenors[-1]]
        for i in range(len(tenors) - 1):
            if tenors[i] <= t <= tenors[i + 1]:
                w = (t - tenors[i]) / (tenors[i + 1] - tenors[i])
                return spot_rates[tenors[i]] * (1 - w) + spot_rates[tenors[i + 1]] * w
        return spot_rates[tenors[-1]]

    r3m = get(0.25)
    r2y = get(2.0)
    r5y = get(5.0)
    r10y = get(10.0)
    r30y = get(30.0)

    slope_2s10s = (r10y - r2y) * 10_000  # bps
    slope_3m2y = (r2y - r3m) * 10_000
    slope_10s30s = (r30y - r10y) * 10_000
    butterfly = (r2y + r10y - 2 * r5y) * 10_000
    level = r10y * 100  # pct

    features = {
        "level_10y_pct": level,
        "slope_2s10s_bps": slope_2s10s,
        "slope_3m2y_bps": slope_3m2y,
        "slope_10s30s_bps": slope_10s30s,
        "butterfly_bps": butterfly,
        "r2y_pct": r2y * 100,
        "r10y_pct": r10y * 100,
    }

    if rate_history is not None and len(rate_history) >= 21:
        daily_changes = np.diff(rate_history)
        vol_21d = float(np.std(daily_changes[-20:])) * np.sqrt(252) * 100
        features["vol_21d_annualised_pct"] = vol_21d
        if len(rate_history) >= 6:
            mom_5d = float(rate_history[-1] - rate_history[-6]) * 10_000
            features["momentum_5d_bps"] = mom_5d
        else:
            features["momentum_5d_bps"] = 0.0
    else:
        features["vol_21d_annualised_pct"] = 0.5
        features["momentum_5d_bps"] = 0.0

    return features


def _rule_based_regime(features: dict[str, float]) -> tuple[str, dict[str, float]]:
    """
    Deterministic rule-based regime classification.
    Used as a baseline and fallback.
    Returns (regime, probability_dict).
    """
    slope = features["slope_2s10s_bps"]
    butterfly = features["butterfly_bps"]
    features["level_10y_pct"]

    # Hard boundaries first
    if slope < -10:
        regime = "inverted"
    elif abs(slope) < 20:
        regime = "flat"
    elif slope > 120:
        regime = "steep"
    elif abs(butterfly) > 25:
        regime = "humped"
    else:
        regime = "normal"

    # Soft probabilities via logistic-style scoring
    probs = {r: 0.05 for r in REGIMES}
    probs[regime] = 0.70
    remaining = 0.30
    others = [r for r in REGIMES if r != regime]
    for r in others:
        probs[r] += remaining / len(others)

    return regime, probs


# ---------------------------------------------------------------------------
# ML model training
# ---------------------------------------------------------------------------


def _generate_synthetic_training_data(
    n_samples: int = 2000, seed: int = 42
) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic labelled regime data for initial model training.
    In production this would be replaced with historically labelled curve data.
    """
    rng = np.random.default_rng(seed)
    X, y = [], []

    regime_configs = {
        "normal": {"slope": (30, 120), "level": (2, 6), "butterfly": (-20, 20)},
        "inverted": {"slope": (-120, -10), "level": (3, 7), "butterfly": (-30, 30)},
        "flat": {"slope": (-20, 20), "level": (2, 6), "butterfly": (-15, 15)},
        "steep": {"slope": (120, 250), "level": (1, 5), "butterfly": (-30, 30)},
        "humped": {"slope": (20, 80), "level": (2, 6), "butterfly": (25, 80)},
    }

    per_regime = n_samples // len(REGIMES)
    for regime_idx, (regime, cfg) in enumerate(regime_configs.items()):
        for _ in range(per_regime):
            slope = rng.uniform(*cfg["slope"])
            level = rng.uniform(*cfg["level"])
            butterfly = rng.uniform(*cfg["butterfly"])
            vol = rng.uniform(0.2, 1.5)
            mom = rng.uniform(-20, 20)
            r2y = level - slope / 20000
            r10y = level / 100
            slope_short = rng.uniform(-30, 60)
            slope_long = rng.uniform(-20, 80)
            X.append(
                [level, slope, slope_short, slope_long, butterfly, r2y, r10y, vol, mom]
            )
            y.append(regime_idx)

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32)


def _train_regime_model() -> dict:
    """Train the regime classifier ensemble."""
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    X, y = _generate_synthetic_training_data()

    rf = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=200,
                    max_depth=8,
                    min_samples_leaf=5,
                    class_weight="balanced",
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
                "clf",
                GradientBoostingClassifier(
                    n_estimators=150,
                    max_depth=4,
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

        xgb_clf = Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "clf",
                    xgb.XGBClassifier(
                        n_estimators=200,
                        max_depth=5,
                        learning_rate=0.05,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        use_label_encoder=False,
                        eval_metric="mlogloss",
                        random_state=42,
                        verbosity=0,
                    ),
                ),
            ]
        )
        xgb_clf.fit(X, y)
        models = [rf, gb, xgb_clf]
        backend = "xgb_ensemble"
    except ImportError:
        models = [rf, gb]
        backend = "sklearn_ensemble"

    logger.info("Regime classifier trained (%s)", backend)
    return {"models": models, "backend": backend, "labels": REGIMES}


def get_regime_model() -> dict:
    """Return cached or freshly trained regime model."""
    global _REGIME_MODEL
    if _REGIME_MODEL is None:
        _REGIME_MODEL = _train_regime_model()
    return _REGIME_MODEL


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def classify_regime(
    spot_rates: dict[float, float],
    rate_history: Optional[np.ndarray] = None,
) -> RegimeResult:
    """
    Classify the current yield curve regime.

    Parameters
    ----------
    spot_rates:
        Dict mapping tenor (years) to spot rate (decimal).
    rate_history:
        Optional 1-D array of recent 10Y rates (decimal) for volatility
        and momentum features.

    Returns
    -------
    RegimeResult with predicted regime, probability, and feature values.
    """
    features = _engineer_features(spot_rates, rate_history)
    feature_array = np.array(
        [
            [
                features["level_10y_pct"],
                features["slope_2s10s_bps"],
                features["slope_3m2y_bps"],
                features["slope_10s30s_bps"],
                features["butterfly_bps"],
                features["r2y_pct"],
                features["r10y_pct"],
                features["vol_21d_annualised_pct"],
                features["momentum_5d_bps"],
            ]
        ],
        dtype=np.float32,
    )

    try:
        model_state = get_regime_model()
        models = model_state["models"]
        labels = model_state["labels"]

        all_probs = np.zeros(len(labels))
        for model in models:
            all_probs += model.predict_proba(feature_array)[0]
        all_probs /= len(models)

        predicted_idx = int(np.argmax(all_probs))
        predicted_regime = labels[predicted_idx]
        prob_dict = {label: round(float(p), 4) for label, p in zip(labels, all_probs)}

        return RegimeResult(
            regime=predicted_regime,
            probability=round(float(all_probs[predicted_idx]), 4),
            all_probabilities=prob_dict,
            features=features,
            model=model_state["backend"],
        )

    except Exception as exc:
        logger.warning(
            "ML regime classifier failed (%s), using rule-based fallback", exc
        )
        regime, probs = _rule_based_regime(features)
        return RegimeResult(
            regime=regime,
            probability=round(probs[regime], 4),
            all_probabilities={k: round(v, 4) for k, v in probs.items()},
            features=features,
            model="rule_based",
        )
