"""
QuantYield Backend - ML Forecaster Bridge
Delegates to code/ml_services for all forecasting logic.
The backend imports this thin wrapper so Django views remain unchanged.
"""

import os
import sys

# Add ml_services to path so backend can import it
_ml_path = os.path.join(os.path.dirname(__file__), "..", "..", "ml_services")
_ml_abs = os.path.abspath(_ml_path)
if _ml_abs not in sys.path:
    sys.path.insert(0, _ml_abs)

try:
    from ml_services.forecaster import (
        available_backend,
        clear_model_cache,
        forecast_rates,
    )
    from ml_services.forecaster import train_forecaster as train_lstm_forecaster
except ImportError:
    # Fallback: use the original self-contained implementation
    import numpy as np

    _MODEL_CACHE: dict = {}

    def train_lstm_forecaster(
        rate_series,
        seq_len=20,
        hidden_size=64,
        epochs=50,
        lr=0.001,
        force_retrain=False,
    ):
        cache_key = (seq_len, hidden_size, epochs)
        if not force_retrain and cache_key in _MODEL_CACHE:
            return _MODEL_CACHE[cache_key]
        diffs = np.diff(rate_series)
        phi = float(np.corrcoef(diffs[:-1], diffs[1:])[0, 1]) if len(diffs) > 1 else 0.0
        phi = float(np.clip(phi, -0.99, 0.99))
        sigma = float(np.std(diffs)) if len(diffs) > 0 else 0.001
        state = {
            "model": None,
            "mean": float(np.mean(rate_series)),
            "std": float(np.std(rate_series)) or 1.0,
            "seq_len": seq_len,
            "backend": "arima",
            "last_value": float(rate_series[-1]),
            "phi": phi,
            "sigma": sigma,
        }
        _MODEL_CACHE[cache_key] = state
        return state

    def forecast_rates(model_state, rate_series, horizon_days=30, n_simulations=300):
        phi = model_state.get("phi", 0.0)
        sigma = model_state.get("sigma", 0.001)
        last = model_state.get("last_value", float(rate_series[-1]))
        diffs = np.diff(rate_series)
        last_diff = float(diffs[-1]) if len(diffs) > 0 else 0.0
        point, cur_val, cur_diff = [], last, last_diff
        for _ in range(horizon_days):
            nxt_diff = phi * cur_diff
            cur_val = max(cur_val + nxt_diff, 0.0001)
            point.append(cur_val)
            cur_diff = nxt_diff
        rng = np.random.default_rng(42)
        sims = []
        for _ in range(n_simulations):
            sv, sd = last, last_diff
            path = []
            for _ in range(horizon_days):
                nd = phi * sd + rng.normal(0, sigma)
                sv = max(sv + nd, 0.0001)
                path.append(sv)
                sd = nd
            sims.append(path)
        sims_arr = np.array(sims)
        lower = np.percentile(sims_arr, 5, axis=0).tolist()
        upper = np.percentile(sims_arr, 95, axis=0).tolist()
        return {"point": point, "lower": lower, "upper": upper, "backend": "arima"}

    def clear_model_cache():
        _MODEL_CACHE.clear()

    def available_backend():
        return "arima"
