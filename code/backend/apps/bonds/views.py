"""
QuantYield — Bonds API Views
Full bond CRUD (ModelViewSet) plus pricing, YTM, spread, KRD,
cash flows, comparison, OAS, and total return analytics.
"""

import asyncio
import logging
import math
from datetime import date

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from services import pricing as ps
from services.curve_builder import _interpolate_spot, bootstrap_spot_rates
from services.data_feed import fetch_treasury_curve
from services.schemas import CurvePointSchema

from .filters import BondFilter
from .models import Bond
from .serializers import (
    BondAnalyticsSerializer,
    BondCompareRequestSerializer,
    BondSerializer,
    BondUpdateSerializer,
    PriceRequestSerializer,
    SpreadRequestSerializer,
    TotalReturnRequestSerializer,
    YieldRequestSerializer,
    _bond_to_schema,
)

logger = logging.getLogger("quantyield")


class BondViewSet(viewsets.ModelViewSet):
    """
    CRUD + analytics for fixed-income instruments.

    list:        GET  /api/v1/bonds/
    create:      POST /api/v1/bonds/
    retrieve:    GET  /api/v1/bonds/{id}/
    partial_update: PATCH /api/v1/bonds/{id}/
    destroy:     DELETE /api/v1/bonds/{id}/
    """

    queryset = Bond.objects.prefetch_related("call_schedule").all()
    serializer_class = BondAnalyticsSerializer
    filterset_class = BondFilter
    search_fields = ["name", "issuer", "isin", "sector", "credit_rating"]
    ordering_fields = ["name", "issuer", "maturity_date", "coupon_rate", "created_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return BondSerializer
        if self.action in ("update", "partial_update"):
            return BondUpdateSerializer
        return BondAnalyticsSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        settlement_str = self.request.query_params.get("settlement")
        if settlement_str:
            try:
                ctx["settlement"] = date.fromisoformat(settlement_str)
            except ValueError:
                pass
        return ctx

    # ── CRUD overrides ─────────────────────────────────────────────────────────

    def create(self, request, *args, **kwargs):
        ser = BondSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        bond = ser.save()
        out = BondAnalyticsSerializer(bond, context=self.get_serializer_context())
        return Response(out.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        ser = BondUpdateSerializer(instance, data=request.data, partial=partial)
        ser.is_valid(raise_exception=True)
        bond = ser.save()
        out = BondAnalyticsSerializer(bond, context=self.get_serializer_context())
        return Response(out.data)

    # ── Price ──────────────────────────────────────────────────────────────────

    @action(detail=True, methods=["post"], url_path="price")
    def price(self, request, pk=None):
        """Price a bond from either a yield or a market price."""
        bond = self.get_object()
        ser = PriceRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        bond_schema = _bond_to_schema(bond)
        settle = data.get("settlement_date") or date.today()

        if data.get("yield_rate") is not None:
            ytm = data["yield_rate"]
            dirty = ps.dirty_price_from_yield(bond_schema, ytm, settle)
            clean = ps.clean_price_from_yield(bond_schema, ytm, settle)
        else:
            clean = data["market_price"]
            ai = ps.accrued_interest(bond_schema, settle)
            dirty = clean + ai
            ytm = ps.ytm_from_clean_price(bond_schema, clean, settle)
            if math.isnan(ytm):
                raise ValidationError("Could not solve YTM for the given price")

        return Response(
            {
                "bond_id": str(bond.id),
                "clean_price": round(clean, 6),
                "dirty_price": round(dirty, 6),
                "ytm": round(ytm, 8),
                "accrued_interest": round(ps.accrued_interest(bond_schema, settle), 6),
                "modified_duration": round(
                    ps.modified_duration(bond_schema, ytm, settle), 6
                ),
                "convexity": round(ps.convexity(bond_schema, ytm, settle), 6),
                "dv01": round(ps.dv01(bond_schema, ytm, settle), 6),
                "settlement_date": settle.isoformat(),
            }
        )

    # ── YTM ───────────────────────────────────────────────────────────────────

    @action(detail=True, methods=["post"], url_path="ytm")
    def calc_ytm(self, request, pk=None):
        """Solve YTM from a clean price."""
        bond = self.get_object()
        ser = YieldRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        bond_schema = _bond_to_schema(bond)
        settle = data.get("settlement_date") or date.today()
        ytm = ps.ytm_from_clean_price(bond_schema, data["clean_price"], settle)
        if math.isnan(ytm):
            raise ValidationError("Could not solve YTM for the given inputs")

        return Response(
            {
                "bond_id": str(bond.id),
                "clean_price": data["clean_price"],
                "ytm": round(ytm, 8),
                "ytm_pct": round(ytm * 100, 6),
                "macaulay_duration": round(
                    ps.macaulay_duration(bond_schema, ytm, settle), 6
                ),
                "modified_duration": round(
                    ps.modified_duration(bond_schema, ytm, settle), 6
                ),
                "convexity": round(ps.convexity(bond_schema, ytm, settle), 6),
                "dv01": round(ps.dv01(bond_schema, ytm, settle), 6),
                "settlement_date": settle.isoformat(),
            }
        )

    # ── Spread ────────────────────────────────────────────────────────────────

    @action(detail=True, methods=["post"], url_path="spread")
    def spread(self, request, pk=None):
        """Compute Z-spread and OAS vs the live Treasury curve."""
        bond = self.get_object()
        ser = SpreadRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        bond_schema = _bond_to_schema(bond)
        settle = data.get("settlement_date") or date.today()

        raw_pts = asyncio.run(fetch_treasury_curve())
        curve_pts = [CurvePointSchema(**p) for p in raw_pts]
        spot_rates = bootstrap_spot_rates(curve_pts)

        zs = ps.z_spread(bond_schema, data["clean_price"], spot_rates, settle)
        ytm = ps.ytm_from_clean_price(bond_schema, data["clean_price"], settle)

        t_mat = (bond.maturity_date - settle).days / 365.0
        tsy_rate = _interpolate_spot(spot_rates, t_mat) if spot_rates else None
        oas_bps = (
            (ytm - tsy_rate) * 10_000
            if (tsy_rate is not None and not math.isnan(ytm))
            else None
        )

        return Response(
            {
                "bond_id": str(bond.id),
                "clean_price": data["clean_price"],
                "z_spread_bps": round(zs * 10_000, 4) if not math.isnan(zs) else None,
                "oas_bps": round(oas_bps, 4) if oas_bps is not None else None,
                "ytm": round(ytm, 8) if not math.isnan(ytm) else None,
                "spread_type": data["spread_type"],
                "settlement_date": settle.isoformat(),
            }
        )

    # ── Key Rate Durations ────────────────────────────────────────────────────

    @action(detail=True, methods=["get"], url_path="key-rate-durations")
    def key_rate_durations(self, request, pk=None):
        """KRD profile across the standard tenor grid."""
        bond = self.get_object()
        settlement_str = request.query_params.get("settlement")
        settle = date.fromisoformat(settlement_str) if settlement_str else date.today()

        bond_schema = _bond_to_schema(bond)
        ytm = ps.ytm_from_clean_price(bond_schema, float(bond.face_value), settle)
        if math.isnan(ytm):
            ytm = float(bond.coupon_rate)

        krd = ps.key_rate_durations(bond_schema, ytm, settle)
        return Response(
            {
                "bond_id": str(bond.id),
                "key_rate_durations": {str(k): round(v, 6) for k, v in krd.items()},
                "total_duration": round(sum(krd.values()), 6),
                "ytm": round(ytm, 8),
                "settlement_date": settle.isoformat(),
            }
        )

    # ── Cash Flows ────────────────────────────────────────────────────────────

    @action(detail=True, methods=["get"], url_path="cash-flows")
    def cash_flows(self, request, pk=None):
        """Full discounted cash flow schedule."""
        bond = self.get_object()
        settlement_str = request.query_params.get("settlement")
        ytm_param = request.query_params.get("ytm")
        settle = date.fromisoformat(settlement_str) if settlement_str else date.today()

        bond_schema = _bond_to_schema(bond)
        if ytm_param is not None:
            ytm = float(ytm_param)
        else:
            ytm = ps.ytm_from_clean_price(bond_schema, float(bond.face_value), settle)
            if math.isnan(ytm):
                ytm = float(bond.coupon_rate)

        flows = ps.cash_flows(bond_schema, settle, ytm)
        return Response(
            {
                "bond_id": str(bond.id),
                "settlement_date": settle.isoformat(),
                "ytm": round(ytm, 8),
                "cash_flows": flows,
                "total_undiscounted": round(sum(f["total"] for f in flows), 4),
                "total_pv": round(sum(f["pv"] for f in flows), 4),
                "num_payments": len(flows),
            }
        )

    # ── Total Return ──────────────────────────────────────────────────────────

    @action(detail=True, methods=["post"], url_path="total-return")
    def total_return(self, request, pk=None):
        """Horizon total return including reinvested coupons."""
        bond = self.get_object()
        ser = TotalReturnRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        bond_schema = _bond_to_schema(bond)
        settle = data.get("settlement_date") or date.today()

        result = ps.total_return(
            bond_schema,
            data["purchase_clean_price"],
            data["horizon_years"],
            data["reinvestment_rate"],
            settle,
        )
        return Response({"bond_id": str(bond.id), **result})

    # ── OAS (Monte Carlo) ─────────────────────────────────────────────────────

    @action(detail=True, methods=["post"], url_path="oas")
    def oas(self, request, pk=None):
        """Monte Carlo OAS for callable bonds; falls back to Z-spread for bullets."""
        bond = self.get_object()
        market_price = request.data.get("market_clean_price")
        settlement_str = request.data.get("settlement")
        n_paths = int(request.data.get("n_paths", 500))

        if market_price is None:
            raise ValidationError("market_clean_price is required")
        market_price = float(market_price)
        settle = date.fromisoformat(settlement_str) if settlement_str else date.today()

        bond_schema = _bond_to_schema(bond)
        raw_pts = asyncio.run(fetch_treasury_curve())
        curve_pts = [CurvePointSchema(**p) for p in raw_pts]
        spot_rates = bootstrap_spot_rates(curve_pts)

        result = ps.callable_oas(
            bond_schema, market_price, spot_rates, settle, n_paths=n_paths
        )
        return Response(
            {"bond_id": str(bond.id), "settlement_date": settle.isoformat(), **result}
        )

    # ── Compare ───────────────────────────────────────────────────────────────

    @action(detail=False, methods=["post"], url_path="compare")
    def compare(self, request):
        """Side-by-side analytics comparison for up to 10 bonds."""
        ser = BondCompareRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        settle = data.get("settlement_date") or date.today()
        results = []

        for bond_id in data["bond_ids"]:
            try:
                bond = Bond.objects.prefetch_related("call_schedule").get(pk=bond_id)
            except Bond.DoesNotExist:
                results.append({"bond_id": str(bond_id), "error": "Bond not found"})
                continue

            bond_schema = _bond_to_schema(bond)
            ytm = ps.ytm_from_clean_price(bond_schema, float(bond.face_value), settle)
            if math.isnan(ytm):
                ytm = float(bond.coupon_rate)

            dp = ps.dirty_price_from_yield(bond_schema, ytm, settle)
            ai = ps.accrued_interest(bond_schema, settle)
            cp = dp - ai

            results.append(
                {
                    "bond_id": str(bond.id),
                    "name": bond.name,
                    "issuer": bond.issuer,
                    "isin": bond.isin,
                    "coupon_rate_pct": round(float(bond.coupon_rate) * 100, 4),
                    "maturity_date": bond.maturity_date.isoformat(),
                    "years_to_maturity": round(
                        (bond.maturity_date - settle).days / 365, 2
                    ),
                    "ytm_pct": round(ytm * 100, 4),
                    "clean_price": round(cp, 4),
                    "dirty_price": round(dp, 4),
                    "accrued_interest": round(ai, 4),
                    "macaulay_duration": round(
                        ps.macaulay_duration(bond_schema, ytm, settle), 4
                    ),
                    "modified_duration": round(
                        ps.modified_duration(bond_schema, ytm, settle), 4
                    ),
                    "convexity": round(ps.convexity(bond_schema, ytm, settle), 4),
                    "dv01": round(ps.dv01(bond_schema, ytm, settle), 4),
                    "credit_rating": bond.credit_rating,
                    "sector": bond.sector,
                    "currency": bond.currency,
                }
            )

        return Response(
            {
                "settlement_date": settle.isoformat(),
                "bonds_compared": len(data["bond_ids"]),
                "results": results,
            }
        )
