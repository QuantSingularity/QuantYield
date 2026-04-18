"""
QuantYield — Pricing Engine
Full cash-flow discounting for fixed-rate, zero-coupon, and callable bonds.
Supports four day-count conventions and four coupon frequencies.
YTM solved via Brent's method (scipy) with 1e-10 convergence tolerance.
"""

import math
from datetime import date
from typing import Optional

import numpy as np
from dateutil.relativedelta import relativedelta
from scipy.optimize import brentq
from services.schemas import BondSchema

FREQUENCY_MAP: dict[str, int] = {
    "annual": 1,
    "semiannual": 2,
    "quarterly": 4,
    "monthly": 12,
    "zero": 0,
}


# ── Day Count ─────────────────────────────────────────────────────────────────


def day_count_fraction(start: date, end: date, convention: str) -> float:
    if start >= end:
        return 0.0

    if convention == "actual/actual":
        delta = (end - start).days
        year_days = 366 if _is_leap_year(start.year) else 365
        return delta / year_days

    if convention == "actual/360":
        return (end - start).days / 360.0

    if convention == "actual/365":
        return (end - start).days / 365.0

    if convention == "30/360":
        d1, m1, y1 = start.day, start.month, start.year
        d2, m2, y2 = end.day, end.month, end.year
        d1 = min(d1, 30)
        if d1 == 30:
            d2 = min(d2, 30)
        return (360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)) / 360.0

    return (end - start).days / 365.0


def _is_leap_year(year: int) -> bool:
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


# ── Coupon Schedule ───────────────────────────────────────────────────────────


def generate_coupon_dates(bond: BondSchema, settlement: date) -> list[date]:
    """Generate all future coupon dates from settlement to maturity (inclusive)."""
    freq = FREQUENCY_MAP.get(bond.coupon_frequency, 2)
    if freq == 0:
        return [bond.maturity_date]

    months_per_period = 12 // freq
    dates: list[date] = []
    current = bond.maturity_date

    while current > settlement:
        dates.append(current)
        current = current - relativedelta(months=months_per_period)

    return sorted(dates)


def cash_flows(bond: BondSchema, settlement: date, ytm: float) -> list[dict]:
    """Discounted cash flow schedule — coupon + principal with PV."""
    freq = FREQUENCY_MAP.get(bond.coupon_frequency, 2)
    coupon_dates = generate_coupon_dates(bond, settlement)

    if not coupon_dates:
        return []

    results = []
    coupon_per_period = (bond.coupon_rate * bond.face_value / freq) if freq > 0 else 0.0

    for cd in coupon_dates:
        t = day_count_fraction(settlement, cd, bond.day_count)
        is_maturity = cd == bond.maturity_date
        principal = bond.face_value if is_maturity else 0.0
        coupon = coupon_per_period if freq > 0 else 0.0
        total = coupon + principal

        if freq == 0:
            pv = bond.face_value / ((1 + ytm) ** t)
        else:
            discount = (1 + ytm / freq) ** (t * freq)
            pv = total / discount if discount != 0 else 0.0

        results.append(
            {
                "date": cd.isoformat(),
                "coupon": round(coupon, 6),
                "principal": round(principal, 6),
                "total": round(total, 6),
                "pv": round(pv, 6),
                "tenor_years": round(t, 6),
            }
        )

    return results


# ── Accrued Interest ──────────────────────────────────────────────────────────


def accrued_interest(bond: BondSchema, settlement: date) -> float:
    freq = FREQUENCY_MAP.get(bond.coupon_frequency, 2)
    if freq == 0:
        return 0.0

    all_dates = generate_coupon_dates(bond, bond.issue_date)
    if not all_dates:
        return 0.0

    prev_coupon = bond.issue_date
    for cd in all_dates:
        if cd <= settlement:
            prev_coupon = cd
        else:
            break

    next_coupon: Optional[date] = None
    for cd in all_dates:
        if cd > settlement:
            next_coupon = cd
            break

    if next_coupon is None:
        return 0.0

    period_fraction = day_count_fraction(prev_coupon, next_coupon, bond.day_count)
    elapsed_fraction = day_count_fraction(prev_coupon, settlement, bond.day_count)

    if period_fraction == 0:
        return 0.0

    coupon_per_period = bond.coupon_rate * bond.face_value / freq
    return coupon_per_period * (elapsed_fraction / period_fraction)


# ── Dirty / Clean Price ───────────────────────────────────────────────────────


def dirty_price_from_yield(bond: BondSchema, ytm: float, settlement: date) -> float:
    freq = FREQUENCY_MAP.get(bond.coupon_frequency, 2)
    coupon_dates = generate_coupon_dates(bond, settlement)

    if not coupon_dates:
        return bond.face_value

    if freq == 0:
        t = day_count_fraction(settlement, bond.maturity_date, bond.day_count)
        return bond.face_value / ((1 + ytm) ** t)

    coupon_per_period = bond.coupon_rate * bond.face_value / freq
    pv = 0.0

    for cd in coupon_dates:
        t = day_count_fraction(settlement, cd, bond.day_count)
        discount = (1 + ytm / freq) ** (t * freq)
        pv += coupon_per_period / discount

    t_mat = day_count_fraction(settlement, bond.maturity_date, bond.day_count)
    pv += bond.face_value / ((1 + ytm / freq) ** (t_mat * freq))

    return pv


def clean_price_from_yield(bond: BondSchema, ytm: float, settlement: date) -> float:
    return dirty_price_from_yield(bond, ytm, settlement) - accrued_interest(
        bond, settlement
    )


# ── YTM Solver ────────────────────────────────────────────────────────────────


def ytm_from_clean_price(
    bond: BondSchema, clean_price: float, settlement: date
) -> float:
    ai = accrued_interest(bond, settlement)
    dirty = clean_price + ai

    def objective(y: float) -> float:
        return dirty_price_from_yield(bond, y, settlement) - dirty

    try:
        return brentq(objective, -0.5, 5.0, xtol=1e-10, maxiter=500)
    except ValueError:
        return math.nan


# ── Duration & Convexity ──────────────────────────────────────────────────────


def macaulay_duration(bond: BondSchema, ytm: float, settlement: date) -> float:
    freq = FREQUENCY_MAP.get(bond.coupon_frequency, 2)
    coupon_dates = generate_coupon_dates(bond, settlement)
    dp = dirty_price_from_yield(bond, ytm, settlement)

    if dp == 0 or not coupon_dates:
        return 0.0

    if freq == 0:
        return day_count_fraction(settlement, bond.maturity_date, bond.day_count)

    coupon_per_period = bond.coupon_rate * bond.face_value / freq
    weighted_sum = 0.0

    for cd in coupon_dates:
        t = day_count_fraction(settlement, cd, bond.day_count)
        discount = (1 + ytm / freq) ** (t * freq)
        weighted_sum += t * (coupon_per_period / discount)

    t_mat = day_count_fraction(settlement, bond.maturity_date, bond.day_count)
    weighted_sum += t_mat * bond.face_value / ((1 + ytm / freq) ** (t_mat * freq))

    return weighted_sum / dp


def modified_duration(bond: BondSchema, ytm: float, settlement: date) -> float:
    freq = FREQUENCY_MAP.get(bond.coupon_frequency, 2)
    mac_dur = macaulay_duration(bond, ytm, settlement)
    divisor = 1 + ytm / max(freq, 1)
    return mac_dur / divisor


def convexity(bond: BondSchema, ytm: float, settlement: date) -> float:
    freq = FREQUENCY_MAP.get(bond.coupon_frequency, 2)
    coupon_dates = generate_coupon_dates(bond, settlement)
    dp = dirty_price_from_yield(bond, ytm, settlement)

    if dp == 0 or not coupon_dates or freq == 0:
        return 0.0

    coupon_per_period = bond.coupon_rate * bond.face_value / freq
    conv_sum = 0.0

    for cd in coupon_dates:
        t = day_count_fraction(settlement, cd, bond.day_count)
        discount = (1 + ytm / freq) ** (t * freq + 2)
        conv_sum += t * (t + 1 / freq) * (coupon_per_period / discount)

    t_mat = day_count_fraction(settlement, bond.maturity_date, bond.day_count)
    conv_sum += (
        t_mat
        * (t_mat + 1 / freq)
        * bond.face_value
        / ((1 + ytm / freq) ** (t_mat * freq + 2))
    )

    return conv_sum / dp


def dv01(bond: BondSchema, ytm: float, settlement: date) -> float:
    """Dollar Value of 1 basis point (always positive)."""
    dp_up = dirty_price_from_yield(bond, ytm + 0.0001, settlement)
    dp_dn = dirty_price_from_yield(bond, ytm - 0.0001, settlement)
    return (dp_dn - dp_up) / 2.0


# ── Price Change Approximation ────────────────────────────────────────────────


def price_change_approximation(
    dirty_price: float, mod_dur: float, convex: float, yield_change: float
) -> float:
    """Second-order Taylor approximation of price change."""
    return dirty_price * (-mod_dur * yield_change + 0.5 * convex * yield_change**2)


# ── Z-Spread ──────────────────────────────────────────────────────────────────


def z_spread(
    bond: BondSchema,
    clean_price: float,
    spot_rates: dict[float, float],
    settlement: date,
) -> float:
    """Compute Z-spread: constant spread to all spot rates that prices the bond."""
    ai = accrued_interest(bond, settlement)
    dirty = clean_price + ai
    freq = FREQUENCY_MAP.get(bond.coupon_frequency, 2)
    coupon_dates = generate_coupon_dates(bond, settlement)

    if not coupon_dates or freq == 0:
        return 0.0

    tenors = sorted(spot_rates.keys())
    rates = [spot_rates[t] for t in tenors]

    def interp(t: float) -> float:
        if not tenors:
            return 0.0
        if t <= tenors[0]:
            return rates[0]
        if t >= tenors[-1]:
            return rates[-1]
        for i in range(len(tenors) - 1):
            if tenors[i] <= t <= tenors[i + 1]:
                w = (t - tenors[i]) / (tenors[i + 1] - tenors[i])
                return rates[i] * (1 - w) + rates[i + 1] * w
        return rates[-1]

    coupon_per_period = bond.coupon_rate * bond.face_value / freq

    def objective(spread: float) -> float:
        pv = 0.0
        for cd in coupon_dates:
            t = day_count_fraction(settlement, cd, bond.day_count)
            r = interp(t) + spread
            pv += coupon_per_period / ((1 + r) ** t)
        t_mat = day_count_fraction(settlement, bond.maturity_date, bond.day_count)
        r_mat = interp(t_mat) + spread
        pv += bond.face_value / ((1 + r_mat) ** t_mat)
        return pv - dirty

    try:
        return brentq(objective, -0.5, 5.0, xtol=1e-10, maxiter=500)
    except ValueError:
        return math.nan


# ── Key Rate Duration ─────────────────────────────────────────────────────────


def key_rate_durations(
    bond: BondSchema,
    ytm: float,
    settlement: date,
    key_tenors: Optional[list[float]] = None,
) -> dict[float, float]:
    """KRD via triangular bump at each key tenor."""
    if key_tenors is None:
        key_tenors = [0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]

    dp = dirty_price_from_yield(bond, ytm, settlement)
    if dp == 0:
        return {kt: 0.0 for kt in key_tenors}

    bump = 0.0001  # 1 bp
    krd = {}
    for kt in key_tenors:
        dp_up = _bumped_price(bond, ytm, settlement, kt, bump)
        dp_dn = _bumped_price(bond, ytm, settlement, kt, -bump)
        krd[kt] = -(dp_up - dp_dn) / (2 * bump * dp)

    return krd


def _bumped_price(
    bond: BondSchema, ytm: float, settlement: date, key_tenor: float, bump: float
) -> float:
    """Price bond with a triangular yield bump centred at key_tenor."""
    freq = FREQUENCY_MAP.get(bond.coupon_frequency, 2)
    coupon_dates = generate_coupon_dates(bond, settlement)

    if not coupon_dates or freq == 0:
        return dirty_price_from_yield(bond, ytm, settlement)

    coupon_per_period = bond.coupon_rate * bond.face_value / freq
    pv = 0.0

    for cd in coupon_dates:
        t = day_count_fraction(settlement, cd, bond.day_count)
        weight = max(0.0, 1.0 - abs(t - key_tenor))
        bumped_ytm = ytm + bump * weight
        discount = (1 + bumped_ytm / freq) ** (t * freq)
        pv += coupon_per_period / discount

    t_mat = day_count_fraction(settlement, bond.maturity_date, bond.day_count)
    weight = max(0.0, 1.0 - abs(t_mat - key_tenor))
    bumped_ytm = ytm + bump * weight
    pv += bond.face_value / ((1 + bumped_ytm / freq) ** (t_mat * freq))

    return pv


# ── Total Return ──────────────────────────────────────────────────────────────


def total_return(
    bond: BondSchema,
    purchase_clean_price: float,
    horizon_years: float,
    reinvestment_rate: float,
    settlement: date,
) -> dict:
    """
    Horizon total return including reinvested coupons, price change, and accrued interest.
    """
    freq = FREQUENCY_MAP.get(bond.coupon_frequency, 2)
    coupon_dates = generate_coupon_dates(bond, settlement)

    horizon_date = date(
        settlement.year + int(horizon_years),
        settlement.month,
        settlement.day,
    )
    if horizon_date > bond.maturity_date:
        horizon_date = bond.maturity_date

    purchase_ai = accrued_interest(bond, settlement)
    purchase_dirty = purchase_clean_price + purchase_ai

    reinvested_value = 0.0
    coupon_per_period = (bond.coupon_rate * bond.face_value / freq) if freq > 0 else 0.0

    for cd in coupon_dates:
        if cd <= horizon_date:
            time_to_reinvest = (horizon_date - cd).days / 365.0
            reinvested_value += (
                coupon_per_period * (1 + reinvestment_rate) ** time_to_reinvest
            )

    if horizon_date >= bond.maturity_date:
        horizon_dirty = bond.face_value
        horizon_ai = 0.0
    else:
        ytm = ytm_from_clean_price(bond, purchase_clean_price, settlement)
        if math.isnan(ytm):
            ytm = bond.coupon_rate
        horizon_dirty = dirty_price_from_yield(bond, ytm, horizon_date)
        horizon_ai = accrued_interest(bond, horizon_date)

    terminal_value = horizon_dirty + reinvested_value
    pnl = terminal_value - purchase_dirty
    total_return_pct = (terminal_value / purchase_dirty) ** (
        1 / max(horizon_years, 1 / 365)
    ) - 1

    return {
        "purchase_dirty_price": round(purchase_dirty, 6),
        "terminal_value": round(terminal_value, 6),
        "reinvested_coupons": round(reinvested_value, 6),
        "horizon_dirty_price": round(horizon_dirty, 6),
        "horizon_accrued_interest": round(horizon_ai, 6),
        "pnl": round(pnl, 6),
        "total_return_annualized_pct": round(total_return_pct * 100, 4),
        "horizon_date": horizon_date.isoformat(),
        "horizon_years": round(horizon_years, 4),
    }


# ── Callable Bond OAS (Monte Carlo) ──────────────────────────────────────────


def callable_oas(
    bond: BondSchema,
    market_clean_price: float,
    spot_rates: dict[float, float],
    settlement: date,
    n_paths: int = 500,
    rate_vol: float = 0.01,
) -> dict:
    """
    Monte Carlo OAS for callable bonds.
    Falls back to Z-spread for bullets.
    """
    if not bond.call_schedule:
        zs = z_spread(bond, market_clean_price, spot_rates, settlement)
        return {
            "oas_bps": round(zs * 10000, 4) if not math.isnan(zs) else None,
            "z_spread_bps": round(zs * 10000, 4) if not math.isnan(zs) else None,
            "option_value_bps": 0.0,
            "method": "z_spread_fallback",
            "note": "Bond has no call schedule; OAS equals Z-spread",
        }

    tenors = sorted(spot_rates.keys())
    rates_arr = np.array([spot_rates[t] for t in tenors])

    def interp_rate(t: float) -> float:
        if not tenors:
            return 0.0
        if t <= tenors[0]:
            return float(rates_arr[0])
        if t >= tenors[-1]:
            return float(rates_arr[-1])
        for i in range(len(tenors) - 1):
            if tenors[i] <= t <= tenors[i + 1]:
                w = (t - tenors[i]) / (tenors[i + 1] - tenors[i])
                return float(rates_arr[i] * (1 - w) + rates_arr[i + 1] * w)
        return float(rates_arr[-1])

    freq = FREQUENCY_MAP.get(bond.coupon_frequency, 2)
    coupon_dates = generate_coupon_dates(bond, settlement)
    coupon_per_period = (bond.coupon_rate * bond.face_value / freq) if freq > 0 else 0.0

    call_map = {
        cs.call_date: cs.call_price / 100.0 * bond.face_value
        for cs in bond.call_schedule
    }

    rng = np.random.default_rng(42)
    dt = 1 / 12
    r0 = interp_rate(0.25)

    def price_path(spread: float) -> float:
        total_pv = 0.0
        for _ in range(n_paths):
            n_steps = int((bond.maturity_date - settlement).days / 30) + 1
            rates_path = np.zeros(n_steps)
            rates_path[0] = r0
            eps = rng.standard_normal(n_steps - 1)
            for i in range(1, n_steps):
                rates_path[i] = max(
                    rates_path[i - 1]
                    * np.exp(
                        -0.1 * rates_path[i - 1] * dt
                        + rate_vol * math.sqrt(dt) * eps[i - 1]
                    ),
                    0.0001,
                )
            pv = 0.0
            called = False
            for cd in coupon_dates:
                t_days = (cd - settlement).days
                step = min(int(t_days / 30), n_steps - 1)
                r_path = rates_path[step]
                df = math.exp(
                    -(r_path + spread)
                    * day_count_fraction(settlement, cd, bond.day_count)
                )
                if cd in call_map and not called:
                    call_px = call_map[cd]
                    continuation = dirty_price_from_yield(bond, r_path + spread, cd)
                    if call_px <= continuation:
                        pv += df * (coupon_per_period + call_px)
                        called = True
                        break
                pv += df * coupon_per_period
            if not called:
                t_mat = day_count_fraction(
                    settlement, bond.maturity_date, bond.day_count
                )
                r_step = rates_path[
                    min(int((bond.maturity_date - settlement).days / 30), n_steps - 1)
                ]
                df_mat = math.exp(-(r_step + spread) * t_mat)
                pv += df_mat * bond.face_value
            total_pv += pv
        return total_pv / n_paths

    ai = accrued_interest(bond, settlement)
    market_dirty = market_clean_price + ai

    try:
        oas = brentq(
            lambda s: price_path(s) - market_dirty, -0.02, 0.30, xtol=1e-6, maxiter=100
        )
    except ValueError:
        oas = math.nan

    zs = z_spread(bond, market_clean_price, spot_rates, settlement)
    option_value_bps = (
        (zs - oas) * 10000 if not (math.isnan(oas) or math.isnan(zs)) else None
    )

    return {
        "oas_bps": round(oas * 10000, 4) if not math.isnan(oas) else None,
        "z_spread_bps": round(zs * 10000, 4) if not math.isnan(zs) else None,
        "option_value_bps": (
            round(option_value_bps, 4) if option_value_bps is not None else None
        ),
        "method": "monte_carlo",
        "n_paths": n_paths,
        "rate_vol_pct": round(rate_vol * 100, 2),
    }
