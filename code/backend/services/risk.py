"""
QuantYield — Risk Analytics
Portfolio duration/convexity, scenario analysis, VaR/CVaR, CS01, duration buckets, P&L.
"""

import math
from datetime import date
from typing import Optional

import numpy as np
from services.pricing import accrued_interest
from services.pricing import convexity as bond_convexity
from services.pricing import dirty_price_from_yield, dv01, modified_duration
from services.schemas import BondSchema, ScenarioResultSchema, ScenarioShiftSchema

# ── Portfolio Risk Metrics ────────────────────────────────────────────────────


def portfolio_risk_metrics(
    bonds: list[BondSchema],
    ytms: list[float],
    face_amounts: list[float],
    settlement: date,
) -> dict:
    market_values: list[float] = []
    durations: list[float] = []
    convexities: list[float] = []
    dv01s: list[float] = []
    ytm_contributions: list[float] = []

    for bond, ytm, face in zip(bonds, ytms, face_amounts):
        dp = dirty_price_from_yield(bond, ytm, settlement)
        mv = dp * face / bond.face_value
        market_values.append(mv)

        md = modified_duration(bond, ytm, settlement)
        cv = bond_convexity(bond, ytm, settlement)
        d1 = dv01(bond, ytm, settlement) * face / bond.face_value

        durations.append(md * mv)
        convexities.append(cv * mv)
        dv01s.append(d1)
        ytm_contributions.append(ytm * mv)

    total_mv = sum(market_values)
    if total_mv == 0:
        return {}

    port_duration = sum(durations) / total_mv
    port_convexity = sum(convexities) / total_mv
    port_ytm = sum(ytm_contributions) / total_mv
    port_dv01 = sum(dv01s)

    return {
        "total_market_value": total_mv,
        "portfolio_duration": port_duration,
        "portfolio_modified_duration": port_duration,
        "portfolio_convexity": port_convexity,
        "portfolio_ytm": port_ytm,
        "portfolio_dv01": port_dv01,
        "portfolio_spread_duration": port_duration,
        "market_values": market_values,
    }


# ── Scenario Analysis ─────────────────────────────────────────────────────────


def scenario_pnl(
    bonds: list[BondSchema],
    ytms: list[float],
    face_amounts: list[float],
    settlement: date,
    shift: ScenarioShiftSchema,
    scenario_name: str,
) -> ScenarioResultSchema:
    original_values: list[float] = []
    new_values: list[float] = []
    dur_contributions: list[float] = []
    conv_contributions: list[float] = []

    for bond, ytm, face in zip(bonds, ytms, face_amounts):
        dp_orig = dirty_price_from_yield(bond, ytm, settlement)
        mv_orig = dp_orig * face / bond.face_value
        t_mat = (bond.maturity_date - settlement).days / 365.0

        if t_mat <= 2:
            rate_shift = (shift.parallel_shift_bps + shift.twist_short_bps) / 10000
        elif t_mat <= 10:
            w = (t_mat - 2) / 8
            rate_shift = (
                shift.parallel_shift_bps / 10000
                + (1 - w) * shift.twist_short_bps / 10000
                + w * shift.twist_long_bps / 10000
            )
        else:
            rate_shift = (shift.parallel_shift_bps + shift.twist_long_bps) / 10000

        rate_shift += shift.credit_spread_shift_bps / 10000

        new_ytm = ytm + rate_shift
        dp_new = dirty_price_from_yield(bond, new_ytm, settlement)
        mv_new = dp_new * face / bond.face_value

        md = modified_duration(bond, ytm, settlement)
        cv = bond_convexity(bond, ytm, settlement)
        dur_pnl = -md * rate_shift * mv_orig
        conv_pnl = 0.5 * cv * rate_shift**2 * mv_orig

        original_values.append(mv_orig)
        new_values.append(mv_new)
        dur_contributions.append(dur_pnl)
        conv_contributions.append(conv_pnl)

    total_orig = sum(original_values)
    total_new = sum(new_values)
    pnl = total_new - total_orig
    pnl_pct = pnl / total_orig if total_orig != 0 else 0.0

    return ScenarioResultSchema(
        scenario_name=scenario_name,
        pnl=pnl,
        pnl_pct=pnl_pct,
        new_portfolio_value=total_new,
        duration_contribution=sum(dur_contributions),
        convexity_contribution=sum(conv_contributions),
    )


def run_standard_scenarios(
    bonds: list[BondSchema],
    ytms: list[float],
    face_amounts: list[float],
    settlement: date,
) -> list[ScenarioResultSchema]:
    scenarios = [
        (ScenarioShiftSchema(parallel_shift_bps=100), "+100bps parallel"),
        (ScenarioShiftSchema(parallel_shift_bps=-100), "-100bps parallel"),
        (ScenarioShiftSchema(parallel_shift_bps=200), "+200bps parallel"),
        (ScenarioShiftSchema(parallel_shift_bps=-200), "-200bps parallel"),
        (ScenarioShiftSchema(twist_short_bps=50, twist_long_bps=-50), "bear flattener"),
        (ScenarioShiftSchema(twist_short_bps=-50, twist_long_bps=50), "bull steepener"),
        (
            ScenarioShiftSchema(parallel_shift_bps=50, twist_short_bps=25),
            "bear twist +50bps",
        ),
        (
            ScenarioShiftSchema(parallel_shift_bps=-50, twist_short_bps=-25),
            "bull twist -50bps",
        ),
        (ScenarioShiftSchema(parallel_shift_bps=300), "+300bps shock"),
        (ScenarioShiftSchema(credit_spread_shift_bps=100), "credit widening +100bps"),
    ]
    return [
        scenario_pnl(bonds, ytms, face_amounts, settlement, s, n) for s, n in scenarios
    ]


# ── Historical & Parametric VaR ───────────────────────────────────────────────


def historical_var(
    yield_changes: np.ndarray,
    portfolio_dv01: float,
    confidence_level: float = 0.99,
    holding_period_days: int = 1,
) -> dict:
    if len(yield_changes) < 2:
        return {"error": "Insufficient data for VaR computation"}

    pnl_1d = -portfolio_dv01 * yield_changes * 10_000

    if holding_period_days > 1 and len(yield_changes) > holding_period_days * 5:
        n = holding_period_days
        nd_changes = np.array(
            [yield_changes[i : i + n].sum() for i in range(len(yield_changes) - n + 1)]
        )
        pnl_nd = -portfolio_dv01 * nd_changes * 10_000
        used_scaling = "overlapping_nd"
    else:
        pnl_nd = pnl_1d * math.sqrt(holding_period_days)
        used_scaling = "sqrt_t_approx"

    var = float(np.percentile(pnl_nd, (1 - confidence_level) * 100))
    tail = pnl_nd[pnl_nd <= var]
    es = float(np.mean(tail)) if len(tail) > 0 else var

    return {
        "var": abs(var),
        "expected_shortfall": abs(es),
        "confidence_level": confidence_level,
        "holding_period_days": holding_period_days,
        "method": "historical",
        "scaling": used_scaling,
        "observations": len(yield_changes),
    }


def parametric_var(
    portfolio_dv01: float,
    yield_volatility: float,
    confidence_level: float = 0.99,
    holding_period_days: int = 1,
) -> dict:
    from scipy.stats import norm

    z = norm.ppf(confidence_level)
    daily_vol = yield_volatility * math.sqrt(holding_period_days)
    var = portfolio_dv01 * z * daily_vol * 10_000

    return {
        "var": float(abs(var)),
        "confidence_level": confidence_level,
        "holding_period_days": holding_period_days,
        "method": "parametric",
        "yield_volatility": yield_volatility,
    }


# ── Credit Spread Sensitivity ─────────────────────────────────────────────────


def credit_spread_sensitivity(
    bonds: list[BondSchema],
    ytms: list[float],
    face_amounts: list[float],
    settlement: date,
    spread_bump_bps: float = 1.0,
) -> dict:
    bump = spread_bump_bps / 10000
    total_cs01 = 0.0
    cs01_by_bond: list[float] = []

    for bond, ytm, face in zip(bonds, ytms, face_amounts):
        dp_orig = dirty_price_from_yield(bond, ytm, settlement)
        dp_bumped = dirty_price_from_yield(bond, ytm + bump, settlement)
        mv = dp_orig * face / bond.face_value
        mv_bumped = dp_bumped * face / bond.face_value
        cs01 = mv_bumped - mv
        total_cs01 += cs01
        cs01_by_bond.append(cs01)

    return {
        "total_cs01": total_cs01,
        "cs01_by_bond": cs01_by_bond,
        "spread_bump_bps": spread_bump_bps,
    }


# ── Duration Bucket Report ────────────────────────────────────────────────────

DURATION_BUCKETS = [
    ("0–1Y", 0, 1),
    ("1–3Y", 1, 3),
    ("3–5Y", 3, 5),
    ("5–7Y", 5, 7),
    ("7–10Y", 7, 10),
    ("10Y+", 10, 999),
]


def duration_bucket_report(
    bonds: list[BondSchema],
    ytms: list[float],
    face_amounts: list[float],
    settlement: date,
) -> dict:
    buckets: dict[str, dict] = {
        label: {
            "market_value": 0.0,
            "weight": 0.0,
            "duration_contribution": 0.0,
            "dv01": 0.0,
        }
        for label, *_ in DURATION_BUCKETS
    }

    total_mv = 0.0
    total_dur_mv = 0.0

    for bond, ytm, face in zip(bonds, ytms, face_amounts):
        dp = dirty_price_from_yield(bond, ytm, settlement)
        mv = dp * face / bond.face_value
        md = modified_duration(bond, ytm, settlement)
        d1 = dv01(bond, ytm, settlement) * face / bond.face_value
        t_mat = (bond.maturity_date - settlement).days / 365.0

        for label, lo, hi in DURATION_BUCKETS:
            if lo <= t_mat < hi:
                buckets[label]["market_value"] += mv
                buckets[label]["duration_contribution"] += md * mv
                buckets[label]["dv01"] += d1
                break

        total_mv += mv
        total_dur_mv += md * mv

    if total_mv > 0:
        for label in buckets:
            bkt = buckets[label]
            bkt["weight"] = bkt["market_value"] / total_mv
            bkt["duration_pct"] = (
                bkt["duration_contribution"] / total_dur_mv if total_dur_mv else 0.0
            )

    return {
        "total_market_value": total_mv,
        "total_modified_duration": total_dur_mv / total_mv if total_mv else 0.0,
        "buckets": buckets,
    }


# ── Portfolio P&L ─────────────────────────────────────────────────────────────


def portfolio_pnl(
    bonds: list[BondSchema],
    ytms: list[float],
    face_amounts: list[float],
    purchase_prices: list[Optional[float]],
    purchase_dates: list[Optional[date]],
    settlement: date,
) -> dict:
    positions_out = []
    total_cost = 0.0
    total_mv = 0.0

    for bond, ytm, face, pp, pd in zip(
        bonds, ytms, face_amounts, purchase_prices, purchase_dates
    ):
        dp_now = dirty_price_from_yield(bond, ytm, settlement)
        mv_now = dp_now * face / bond.face_value

        if pp is not None:
            ai_purchase = accrued_interest(bond, pd or settlement)
            cost = (pp + ai_purchase) * face / bond.face_value
        else:
            cost = mv_now

        pnl = mv_now - cost
        pnl_pct = pnl / cost if cost else 0.0

        positions_out.append(
            {
                "bond_name": bond.name,
                "face_amount": face,
                "market_value": round(mv_now, 4),
                "cost_basis": round(cost, 4),
                "unrealized_pnl": round(pnl, 4),
                "pnl_pct": round(pnl_pct * 100, 4),
                "ytm": round(ytm, 6),
            }
        )

        total_mv += mv_now
        total_cost += cost

    total_pnl = total_mv - total_cost
    total_pnl_pct = total_pnl / total_cost if total_cost else 0.0

    return {
        "total_market_value": round(total_mv, 4),
        "total_cost_basis": round(total_cost, 4),
        "unrealized_pnl": round(total_pnl, 4),
        "unrealized_pnl_pct": round(total_pnl_pct * 100, 4),
        "positions": positions_out,
    }
