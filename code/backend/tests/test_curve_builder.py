"""
Tests for the curve builder service layer.
"""

import pytest
from services import curve_builder as cb
from services.schemas import CurvePointSchema


@pytest.fixture
def treasury_points():
    return [
        CurvePointSchema(tenor=0.25, rate=0.0532),
        CurvePointSchema(tenor=0.5, rate=0.0530),
        CurvePointSchema(tenor=1.0, rate=0.0515),
        CurvePointSchema(tenor=2.0, rate=0.0489),
        CurvePointSchema(tenor=3.0, rate=0.0472),
        CurvePointSchema(tenor=5.0, rate=0.0456),
        CurvePointSchema(tenor=7.0, rate=0.0452),
        CurvePointSchema(tenor=10.0, rate=0.0445),
        CurvePointSchema(tenor=20.0, rate=0.0471),
        CurvePointSchema(tenor=30.0, rate=0.0459),
    ]


class TestNelsonSiegel:
    def test_fit_succeeds(self, treasury_points):
        params, r2, rmse = cb.fit_nelson_siegel(treasury_points)
        assert r2 > 0.8, f"R² too low: {r2}"
        assert rmse < 0.005

    def test_long_run_level(self, treasury_points):
        params, _, _ = cb.fit_nelson_siegel(treasury_points)
        # beta0 should approximate the long-run level (around 4-5%)
        assert 0.03 < params.beta0 < 0.08

    def test_interpolation_within_range(self, treasury_points):
        params, _, _ = cb.fit_nelson_siegel(treasury_points)
        rate = cb.nelson_siegel_rate(
            5.0, params.beta0, params.beta1, params.beta2, params.lambda1
        )
        assert 0.03 < rate < 0.08


class TestSvensson:
    def test_fit_succeeds(self, treasury_points):
        params, r2, rmse = cb.fit_svensson(treasury_points)
        assert r2 > 0.8

    def test_better_fit_than_ns(self, treasury_points):
        _, r2_ns, rmse_ns = cb.fit_nelson_siegel(treasury_points)
        _, r2_sv, rmse_sv = cb.fit_svensson(treasury_points)
        # Svensson should fit at least as well (more parameters)
        assert r2_sv >= r2_ns - 0.05


class TestBootstrap:
    def test_spot_rates_returned(self, treasury_points):
        spot = cb.bootstrap_spot_rates(treasury_points)
        assert len(spot) > 0
        assert 1.0 in spot or any(abs(k - 1.0) < 0.01 for k in spot)

    def test_spot_rates_reasonable(self, treasury_points):
        spot = cb.bootstrap_spot_rates(treasury_points)
        for tenor, rate in spot.items():
            assert 0.0 < rate < 0.2, f"Unreasonable spot rate at {tenor}Y: {rate}"

    def test_interpolation(self, treasury_points):
        spot = cb.bootstrap_spot_rates(treasury_points)
        r = cb._interpolate_spot(spot, 4.0)
        assert 0.03 < r < 0.08


class TestCubicSpline:
    def test_exact_at_knots(self, treasury_points):
        spline = cb.fit_cubic_spline(treasury_points)
        for pt in treasury_points:
            fitted = float(spline(pt.tenor))
            assert abs(fitted - pt.rate) < 1e-8, f"Spline not exact at knot {pt.tenor}Y"

    def test_interpolation_between_knots(self, treasury_points):
        spline = cb.fit_cubic_spline(treasury_points)
        rate = float(spline(4.0))
        assert 0.03 < rate < 0.08


class TestForwardRate:
    def test_forward_rate_formula(self):
        r1, r2, t1, t2 = 0.04, 0.05, 2.0, 5.0
        fwd = cb.forward_rate(r1, r2, t1, t2)
        # (r2*t2 - r1*t1) / (t2-t1)
        expected = (0.05 * 5.0 - 0.04 * 2.0) / 3.0
        assert abs(fwd - expected) < 1e-10

    def test_invalid_tenors_raise(self):
        with pytest.raises(ValueError):
            cb.forward_rate(0.04, 0.05, 5.0, 2.0)  # t2 < t1


class TestParYield:
    def test_par_yield_reasonable(self, treasury_points):
        spot = cb.bootstrap_spot_rates(treasury_points)
        py = cb.par_yield(spot, 10.0)
        assert 0.03 < py < 0.08

    def test_par_yield_at_short_tenor(self, treasury_points):
        spot = cb.bootstrap_spot_rates(treasury_points)
        py = cb.par_yield(spot, 1.0)
        assert 0.03 < py < 0.08


class TestRegimeDetection:
    def test_normal_regime(self):
        spot = {0.5: 0.04, 2.0: 0.045, 5.0: 0.048, 10.0: 0.05, 30.0: 0.052}
        regime = cb.detect_regime(spot)
        assert regime["regime"] == "normal"

    def test_inverted_regime(self):
        spot = {0.5: 0.055, 2.0: 0.053, 5.0: 0.050, 10.0: 0.048, 30.0: 0.045}
        regime = cb.detect_regime(spot)
        assert regime["regime"] == "inverted"

    def test_flat_regime(self):
        spot = {0.5: 0.05, 2.0: 0.05005, 5.0: 0.05005, 10.0: 0.0501, 30.0: 0.0501}
        regime = cb.detect_regime(spot)
        assert regime["regime"] == "flat"
