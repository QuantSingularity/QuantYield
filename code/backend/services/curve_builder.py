"""
QuantYield — Yield Curve Builder
Nelson-Siegel, Svensson, Bootstrap, Cubic Spline.
Forward rates, par yields, regime detection.
"""

from typing import Optional

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.optimize import curve_fit
from services.schemas import CurvePointSchema, NelsonSiegelParams, SvenssonParams

# ── Nelson-Siegel ─────────────────────────────────────────────────────────────


def nelson_siegel_rate(
    t: float, beta0: float, beta1: float, beta2: float, lambda1: float
) -> float:
    if t <= 0:
        return beta0 + beta1
    x = t / lambda1
    exp_term = np.exp(-x)
    loading2 = (1 - exp_term) / x
    loading3 = loading2 - exp_term
    return beta0 + beta1 * loading2 + beta2 * loading3


def _nelson_siegel_vector(
    tenors: np.ndarray, beta0: float, beta1: float, beta2: float, lambda1: float
) -> np.ndarray:
    return np.array(
        [nelson_siegel_rate(t, beta0, beta1, beta2, lambda1) for t in tenors]
    )


def fit_nelson_siegel(
    points: list[CurvePointSchema],
) -> tuple[NelsonSiegelParams, float, float]:
    tenors = np.array([p.tenor for p in points])
    rates = np.array([p.rate for p in points])

    p0 = [rates[-1], rates[0] - rates[-1], 0.0, 1.5]
    bounds = ([-0.1, -0.5, -0.5, 0.01], [0.5, 0.5, 0.5, 30.0])

    try:
        popt, _ = curve_fit(
            _nelson_siegel_vector, tenors, rates, p0=p0, bounds=bounds, maxfev=10_000
        )
        fitted = _nelson_siegel_vector(tenors, *popt)
        residuals = rates - fitted
        ss_res = float(np.sum(residuals**2))
        ss_tot = float(np.sum((rates - np.mean(rates)) ** 2))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        rmse = float(np.sqrt(np.mean(residuals**2)))
        params = NelsonSiegelParams(
            beta0=float(popt[0]),
            beta1=float(popt[1]),
            beta2=float(popt[2]),
            lambda1=float(popt[3]),
        )
        return params, float(r2), rmse
    except RuntimeError:
        params = NelsonSiegelParams(
            beta0=float(rates[-1]), beta1=0.0, beta2=0.0, lambda1=1.5
        )
        return params, 0.0, float(np.std(rates))


# ── Svensson ──────────────────────────────────────────────────────────────────


def svensson_rate(t: float, beta0, beta1, beta2, beta3, lambda1, lambda2) -> float:
    if t <= 0:
        return beta0 + beta1
    x1, x2 = t / lambda1, t / lambda2
    exp1, exp2 = np.exp(-x1), np.exp(-x2)
    l2 = (1 - exp1) / x1
    l3 = l2 - exp1
    l4 = (1 - exp2) / x2 - exp2
    return beta0 + beta1 * l2 + beta2 * l3 + beta3 * l4


def _svensson_vector(tenors, beta0, beta1, beta2, beta3, lambda1, lambda2):
    return np.array(
        [svensson_rate(t, beta0, beta1, beta2, beta3, lambda1, lambda2) for t in tenors]
    )


def fit_svensson(points: list[CurvePointSchema]) -> tuple[SvenssonParams, float, float]:
    tenors = np.array([p.tenor for p in points])
    rates = np.array([p.rate for p in points])
    p0 = [rates[-1], rates[0] - rates[-1], 0.0, 0.0, 1.5, 5.0]
    bounds = ([-0.1, -0.5, -0.5, -0.5, 0.01, 0.01], [0.5, 0.5, 0.5, 0.5, 30.0, 30.0])
    try:
        popt, _ = curve_fit(
            _svensson_vector, tenors, rates, p0=p0, bounds=bounds, maxfev=10_000
        )
        fitted = _svensson_vector(tenors, *popt)
        residuals = rates - fitted
        ss_res = float(np.sum(residuals**2))
        ss_tot = float(np.sum((rates - np.mean(rates)) ** 2))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        rmse = float(np.sqrt(np.mean(residuals**2)))
        params = SvenssonParams(
            beta0=float(popt[0]),
            beta1=float(popt[1]),
            beta2=float(popt[2]),
            beta3=float(popt[3]),
            lambda1=float(popt[4]),
            lambda2=float(popt[5]),
        )
        return params, float(r2), rmse
    except RuntimeError:
        params = SvenssonParams(
            beta0=float(rates[-1]),
            beta1=0.0,
            beta2=0.0,
            beta3=0.0,
            lambda1=1.5,
            lambda2=5.0,
        )
        return params, 0.0, float(np.std(rates))


# ── Cubic Spline ──────────────────────────────────────────────────────────────


def fit_cubic_spline(points: list[CurvePointSchema]) -> CubicSpline:
    tenors = np.array([p.tenor for p in points])
    rates = np.array([p.rate for p in points])
    idx = np.argsort(tenors)
    return CubicSpline(tenors[idx], rates[idx], bc_type="not-a-knot")


# ── Bootstrap ────────────────────────────────────────────────────────────────


def bootstrap_spot_rates(points: list[CurvePointSchema]) -> dict[float, float]:
    """
    Bootstrap zero-coupon spot rates from semi-annual par yields (FRED convention).
    """
    sorted_pts = sorted(points, key=lambda p: p.tenor)
    spot_rates: dict[float, float] = {}

    for p in sorted_pts:
        t, par = p.tenor, p.rate
        if t <= 0:
            continue
        if t <= 0.5:
            spot_rates[t] = par
            continue

        freq = 2
        coupon = par / freq
        periods = int(round(t * freq))
        if periods == 0:
            spot_rates[t] = par
            continue

        pv_coupons = 0.0
        for k in range(1, periods):
            tk = k / freq
            rk = _interpolate_spot(spot_rates, tk)
            pv_coupons += coupon * np.exp(-rk * tk)

        df_T = (1.0 - pv_coupons) / (1.0 + coupon)
        spot_rates[t] = -np.log(df_T) / t if df_T > 0 else par

    return spot_rates


def _interpolate_spot(spot_rates: dict[float, float], t: float) -> float:
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


# ── Generic Interpolation ─────────────────────────────────────────────────────


def interpolate_rate(
    model: str,
    parameters: dict,
    tenor: float,
    spline: Optional[CubicSpline] = None,
    spot_rates: Optional[dict[float, float]] = None,
) -> float:
    if model == "nelson_siegel":
        return nelson_siegel_rate(
            tenor,
            parameters["beta0"],
            parameters["beta1"],
            parameters["beta2"],
            parameters["lambda1"],
        )
    if model == "svensson":
        return svensson_rate(
            tenor,
            parameters["beta0"],
            parameters["beta1"],
            parameters["beta2"],
            parameters["beta3"],
            parameters["lambda1"],
            parameters["lambda2"],
        )
    if model == "cubic_spline" and spline is not None:
        return float(spline(tenor))
    if model == "bootstrap":
        sr = spot_rates or parameters.get("spot_rates", {})
        if sr and isinstance(next(iter(sr)), str):
            sr = {float(k): v for k, v in sr.items()}
        return _interpolate_spot(sr, tenor)
    return 0.0


# ── Forward Rates ─────────────────────────────────────────────────────────────


def forward_rate(
    spot_rate_t1: float, spot_rate_t2: float, t1: float, t2: float
) -> float:
    if t2 <= t1 or t1 < 0:
        raise ValueError("t2 must be greater than t1 >= 0")
    return (spot_rate_t2 * t2 - spot_rate_t1 * t1) / (t2 - t1)


# ── Par Yield ─────────────────────────────────────────────────────────────────


def par_yield(spot_rates: dict[float, float], maturity: float, freq: int = 2) -> float:
    periods = int(maturity * freq)
    if periods == 0:
        return _interpolate_spot(spot_rates, maturity)

    discount_sum = 0.0
    for i in range(1, periods + 1):
        t = i / freq
        r = _interpolate_spot(spot_rates, t)
        discount_sum += np.exp(-r * t)

    r_mat = _interpolate_spot(spot_rates, maturity)
    terminal_df = np.exp(-r_mat * maturity)

    if discount_sum == 0:
        return 0.0
    return freq * (1 - terminal_df) / discount_sum


# ── Regime Detection ──────────────────────────────────────────────────────────


def detect_regime(spot_rates: dict[float, float]) -> dict:
    r2 = _interpolate_spot(spot_rates, 2.0)
    r5 = _interpolate_spot(spot_rates, 5.0)
    r10 = _interpolate_spot(spot_rates, 10.0)
    r30 = _interpolate_spot(spot_rates, 30.0)

    slope_2s10s_bps = (r10 - r2) * 10_000
    slope_2s30s_bps = (r30 - r2) * 10_000
    butterfly_bps = (r2 + r10 - 2 * r5) * 10_000

    if abs(slope_2s10s_bps) < 15:
        regime = "flat"
        desc = "Curve is flat — 2s10s spread within ±15bps"
    elif slope_2s10s_bps > 100:
        regime = "steep"
        desc = f"Curve is steeply upward sloping — 2s10s at {slope_2s10s_bps:.0f}bps"
    elif slope_2s10s_bps < 0:
        regime = "inverted"
        desc = f"Curve is inverted — 2s10s at {slope_2s10s_bps:.0f}bps"
    elif abs(butterfly_bps) > 20:
        regime = "humped"
        desc = f"Curve is humped — 2s5s10s butterfly at {butterfly_bps:.0f}bps"
    else:
        regime = "normal"
        desc = f"Curve is normally upward sloping — 2s10s at {slope_2s10s_bps:.0f}bps"

    return {
        "regime": regime,
        "slope_2s10s_bps": round(slope_2s10s_bps, 2),
        "slope_2s30s_bps": round(slope_2s30s_bps, 2),
        "curvature_butterfly_bps": round(butterfly_bps, 2),
        "ten_year_rate_pct": round(r10 * 100, 4),
        "two_year_rate_pct": round(r2 * 100, 4),
        "description": desc,
    }
