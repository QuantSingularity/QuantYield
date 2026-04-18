"""
QuantYield — Analytics API Views
Quick pricer, duration/convexity P&L approximation, benchmark spreads,
rolling yield volatility.
"""

import asyncio
import calendar
import logging
from datetime import date

from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from services import pricing as ps
from services.curve_builder import _interpolate_spot, bootstrap_spot_rates
from services.data_feed import (
    compute_rolling_volatility,
    fetch_treasury_curve,
    fetch_yield_history,
)
from services.risk import price_change_approximation
from services.schemas import BondSchema, CurvePointSchema

logger = logging.getLogger("quantyield")


# ── Request Serializers ───────────────────────────────────────────────────────


class QuickPriceSerializer(serializers.Serializer):
    face_value = serializers.FloatField(default=1000.0, min_value=0.000001)
    coupon_rate = serializers.FloatField(min_value=0, max_value=1)
    ytm = serializers.FloatField()
    years_to_maturity = serializers.FloatField(min_value=0.001)
    coupon_frequency = serializers.ChoiceField(
        choices=["annual", "semiannual", "quarterly", "monthly", "zero"],
        default="semiannual",
    )
    settlement_date = serializers.DateField(required=False, allow_null=True)


class DurationApproxSerializer(serializers.Serializer):
    dirty_price = serializers.FloatField(min_value=0.000001)
    modified_duration = serializers.FloatField(min_value=0)
    convexity = serializers.FloatField(min_value=0)
    yield_change_bps = serializers.FloatField()


class RollingVolSerializer(serializers.Serializer):
    window_days = serializers.IntegerField(default=21, min_value=5, max_value=252)
    lookback_days = serializers.IntegerField(default=252, min_value=21, max_value=2520)
    series_id = serializers.CharField(default="DGS10")


# ── Helpers ───────────────────────────────────────────────────────────────────


def _build_quick_bond(
    face_value: float,
    coupon_rate: float,
    years_to_maturity: float,
    coupon_frequency: str,
    settlement: date,
) -> BondSchema:
    total_months = int(round(years_to_maturity * 12))
    if total_months <= 0:
        raise ValidationError("years_to_maturity too small")

    y = settlement.year + (settlement.month - 1 + total_months) // 12
    m = (settlement.month - 1 + total_months) % 12 + 1
    d = min(settlement.day, calendar.monthrange(y, m)[1])
    maturity = date(y, m, d)

    return BondSchema(
        name="QuickPrice",
        issuer="Generic",
        face_value=face_value,
        coupon_rate=coupon_rate,
        maturity_date=maturity,
        issue_date=settlement,
        coupon_frequency=coupon_frequency,
        bond_type="fixed",
        day_count="actual/actual",
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────


@api_view(["POST"])
def quick_price(request):
    """
    Price a bond from scratch without creating a stored record.
    Useful for what-if analysis and rapid valuation.
    """
    ser = QuickPriceSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data
    settle = data.get("settlement_date") or date.today()

    try:
        bond = _build_quick_bond(
            data["face_value"],
            data["coupon_rate"],
            data["years_to_maturity"],
            data["coupon_frequency"],
            settle,
        )
    except Exception as exc:
        raise ValidationError(str(exc))

    ytm = data["ytm"]
    dirty = ps.dirty_price_from_yield(bond, ytm, settle)
    clean = ps.clean_price_from_yield(bond, ytm, settle)
    ai = ps.accrued_interest(bond, settle)
    mac = ps.macaulay_duration(bond, ytm, settle)
    mod = ps.modified_duration(bond, ytm, settle)
    cv = ps.convexity(bond, ytm, settle)
    d1 = ps.dv01(bond, ytm, settle)

    return Response(
        {
            "dirty_price": round(dirty, 6),
            "clean_price": round(clean, 6),
            "accrued_interest": round(ai, 6),
            "macaulay_duration": round(mac, 6),
            "modified_duration": round(mod, 6),
            "convexity": round(cv, 6),
            "dv01": round(d1, 6),
            "price_per_100": round(clean / data["face_value"] * 100, 6),
            "maturity_date": bond.maturity_date.isoformat(),
            "settlement_date": settle.isoformat(),
        }
    )


@api_view(["POST"])
def duration_approximation(request):
    """
    Second-order Taylor (duration + convexity) P&L approximation
    for a given yield shift in basis points.
    """
    ser = DurationApproxSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    dy = data["yield_change_bps"] / 10_000
    pnl = price_change_approximation(
        data["dirty_price"], data["modified_duration"], data["convexity"], dy
    )
    new_price = data["dirty_price"] + pnl
    dur_only = -data["modified_duration"] * dy * data["dirty_price"]
    conv_only = 0.5 * data["convexity"] * dy**2 * data["dirty_price"]
    higher_order = pnl - dur_only - conv_only

    return Response(
        {
            "yield_change_bps": data["yield_change_bps"],
            "estimated_pnl": round(pnl, 6),
            "new_dirty_price": round(new_price, 6),
            "pnl_pct": round(pnl / data["dirty_price"] * 100, 4),
            "duration_contribution": round(dur_only, 6),
            "convexity_contribution": round(conv_only, 6),
            "higher_order_residual": round(higher_order, 8),
        }
    )


@api_view(["GET"])
def benchmark_spreads(request):
    """
    Live Treasury rates with representative IG and HY credit spreads,
    producing implied all-in yields for each rating / tenor combination.
    """
    raw_pts = asyncio.run(fetch_treasury_curve())
    curve_pts = [CurvePointSchema(**p) for p in raw_pts]
    spot_rates = bootstrap_spot_rates(curve_pts)

    tenors = [0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]
    treasury_rates = {
        str(t): round(_interpolate_spot(spot_rates, t), 6) for t in tenors
    }

    ig_spreads = {"AAA": 20, "AA": 45, "A": 75, "BBB": 130}
    hy_spreads = {"BB": 280, "B": 450, "CCC": 750}

    implied_yields: dict = {}
    for rating, spread_bps in {**ig_spreads, **hy_spreads}.items():
        implied_yields[rating] = {
            str(t): round(treasury_rates[str(t)] + spread_bps / 10_000, 6)
            for t in tenors
        }

    return Response(
        {
            "treasury_rates": treasury_rates,
            "ig_spreads_bps": ig_spreads,
            "hy_spreads_bps": hy_spreads,
            "implied_yields_by_rating": implied_yields,
            "as_of_date": date.today().isoformat(),
        }
    )


@api_view(["POST"])
def rolling_volatility(request):
    """
    Annualised rolling yield volatility for any FRED series.
    Returns time series of vol alongside summary statistics.
    """
    ser = RollingVolSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    hist_df = asyncio.run(
        fetch_yield_history(
            series_id=data["series_id"],
            lookback_days=data["lookback_days"],
        )
    )
    vol_series = compute_rolling_volatility(hist_df, window=data["window_days"])
    vol_clean = vol_series.dropna()

    return Response(
        {
            "series_id": data["series_id"],
            "window_days": data["window_days"],
            "lookback_days": data["lookback_days"],
            "current_vol_annualised_pct": (
                round(float(vol_clean.iloc[-1]) * 100, 4)
                if not vol_clean.empty
                else None
            ),
            "max_vol_annualised_pct": (
                round(float(vol_clean.max()) * 100, 4) if not vol_clean.empty else None
            ),
            "min_vol_annualised_pct": (
                round(float(vol_clean.min()) * 100, 4) if not vol_clean.empty else None
            ),
            "mean_vol_annualised_pct": (
                round(float(vol_clean.mean()) * 100, 4) if not vol_clean.empty else None
            ),
            "observations": len(vol_clean),
            "dates": [str(d.date()) for d in vol_clean.index],
            "values": [round(float(v) * 100, 4) for v in vol_clean.values],
        }
    )


@api_view(["GET"])
def yield_history(request):
    """
    Raw yield history for a given FRED series, suitable for charting.
    """
    series_id = request.query_params.get("series_id", "DGS10")
    lookback_days = int(request.query_params.get("lookback_days", 252))

    hist_df = asyncio.run(
        fetch_yield_history(series_id=series_id, lookback_days=lookback_days)
    )

    return Response(
        {
            "series_id": series_id,
            "lookback_days": lookback_days,
            "observations": len(hist_df),
            "dates": [str(d.date()) for d in hist_df.index],
            "rates_pct": [round(float(r) * 100, 4) for r in hist_df["rate"].values],
            "latest_rate_pct": (
                round(float(hist_df["rate"].iloc[-1]) * 100, 4)
                if not hist_df.empty
                else None
            ),
        }
    )
