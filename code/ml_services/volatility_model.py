"""
QuantYield ML Services - Volatility Forecaster

Produces multi-day volatility forecasts using:
  - GARCH(1,1) via the arch library (primary)
  - EGARCH(1,1) for asymmetric volatility (leverage effect)
  - Rolling historical volatility (always-available fallback)

All outputs are annualised (sqrt-252 scaling applied) and reported as
percentages for readability.
"""

from __future__ import annotations

import logging

import numpy as np
from ml_services.schemas import VolatilityResult

logger = logging.getLogger("quantyield.ml")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def forecast_volatility(
    rate_series: np.ndarray,
    horizon_days: int = 21,
    model_type: str = "garch",
) -> VolatilityResult:
    """
    Forecast yield volatility over the specified horizon.

    Parameters
    ----------
    rate_series:
        Daily yield observations in decimal form (e.g. 0.045 = 4.5 pct).
    horizon_days:
        Number of trading days to forecast.
    model_type:
        One of "garch", "egarch", or "historical".

    Returns
    -------
    VolatilityResult with forecasted and current volatility.
    """
    daily_changes = (
        np.diff(rate_series) * 10_000
    )  # convert to bps for numerical stability

    if len(daily_changes) < 30:
        return _historical_vol(rate_series, horizon_days)

    if model_type in ("garch", "egarch"):
        try:
            return _garch_forecast(daily_changes, rate_series, horizon_days, model_type)
        except Exception as exc:
            logger.warning("GARCH model failed (%s), using historical vol", exc)

    return _historical_vol(rate_series, horizon_days)


# ---------------------------------------------------------------------------
# GARCH backend
# ---------------------------------------------------------------------------


def _garch_forecast(
    daily_changes_bps: np.ndarray,
    rate_series: np.ndarray,
    horizon_days: int,
    model_type: str,
) -> VolatilityResult:
    from arch import arch_model

    # Centre the series
    mu = float(np.mean(daily_changes_bps))
    y = daily_changes_bps - mu

    if model_type == "egarch":
        am = arch_model(y, vol="EGARCH", p=1, q=1, dist="skewt")
    else:
        am = arch_model(y, vol="GARCH", p=1, q=1, dist="t")

    res = am.fit(disp="off", show_warning=False)
    forecasts = res.forecast(horizon=horizon_days, reindex=False)
    # variance is in bps^2 - convert to annualised pct
    var_forecast = forecasts.variance.values[-1]  # shape: (horizon,)
    # vol in bps/day -> pct/year: divide by 10000, multiply by sqrt(252)*100
    vol_forecast_pct = (np.sqrt(var_forecast) / 10_000) * np.sqrt(252) * 100

    current_vol = float((np.std(daily_changes_bps[-21:]) / 10_000) * np.sqrt(252) * 100)

    params = res.params.to_dict()
    garch_params = {
        "omega": round(float(params.get("omega", 0)), 8),
        "alpha": round(float(params.get("alpha[1]", params.get("alpha", 0))), 6),
        "beta": round(float(params.get("beta[1]", params.get("beta", 0))), 6),
        "log_likelihood": round(float(res.loglikelihood), 4),
    }

    return VolatilityResult(
        forecast_annualised_pct=[round(float(v), 4) for v in vol_forecast_pct],
        current_vol_annualised_pct=round(current_vol, 4),
        model=model_type,
        horizon_days=horizon_days,
        garch_params=garch_params,
    )


# ---------------------------------------------------------------------------
# Historical volatility fallback
# ---------------------------------------------------------------------------


def _historical_vol(rate_series: np.ndarray, horizon_days: int) -> VolatilityResult:
    """Simple expanding/rolling historical volatility forecast."""
    daily_changes = np.diff(rate_series)
    window = min(21, len(daily_changes))
    current_vol = float(np.std(daily_changes[-window:])) * np.sqrt(252) * 100

    # Flat forecast with slight mean-reversion toward long-run average
    long_run_vol = float(np.std(daily_changes)) * np.sqrt(252) * 100
    half_life = 63  # ~3-month mean reversion
    forecast = []
    v = current_vol
    for _ in range(horizon_days):
        v = v + (long_run_vol - v) / half_life
        forecast.append(round(v, 4))

    return VolatilityResult(
        forecast_annualised_pct=forecast,
        current_vol_annualised_pct=round(current_vol, 4),
        model="historical_mean_reversion",
        horizon_days=horizon_days,
        garch_params=None,
    )


# ---------------------------------------------------------------------------
# Volatility term structure
# ---------------------------------------------------------------------------


def volatility_term_structure(
    rate_series: np.ndarray,
    windows: list[int] | None = None,
) -> dict[str, float]:
    """
    Compute realised volatility at multiple horizons for a term structure view.

    Returns
    -------
    Dict mapping window label to annualised volatility percentage.
    """
    if windows is None:
        windows = [5, 10, 21, 63, 126, 252]

    daily_changes = np.diff(rate_series)
    result: dict[str, float] = {}

    for w in windows:
        if len(daily_changes) >= w:
            vol = float(np.std(daily_changes[-w:])) * np.sqrt(252) * 100
            result[f"{w}d"] = round(vol, 4)

    return result
