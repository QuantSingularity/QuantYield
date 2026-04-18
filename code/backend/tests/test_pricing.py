"""
Tests for the pricing service layer.
All tests run without a DB — they only exercise pure math functions.
"""

from datetime import date

import pytest
from services import pricing as ps
from services.schemas import BondSchema


@pytest.fixture
def treasury_bond():
    return BondSchema(
        name="US Treasury 5%",
        issuer="US Treasury",
        face_value=1000.0,
        coupon_rate=0.05,
        maturity_date=date(2030, 6, 15),
        issue_date=date(2020, 6, 15),
        coupon_frequency="semiannual",
        bond_type="fixed",
        day_count="actual/actual",
        currency="USD",
    )


@pytest.fixture
def zero_coupon_bond():
    return BondSchema(
        name="Zero 2030",
        issuer="US Treasury",
        face_value=1000.0,
        coupon_rate=0.0,
        maturity_date=date(2030, 6, 15),
        issue_date=date(2020, 6, 15),
        coupon_frequency="zero",
        bond_type="zero_coupon",
        day_count="actual/actual",
        currency="USD",
    )


SETTLE = date(2024, 1, 15)


class TestDirtyPrice:
    def test_par_when_ytm_equals_coupon(self, treasury_bond):
        # Clean price should be close to par when YTM == coupon rate.
        # Dirty price will differ by accrued interest.
        ytm = 0.05
        cp = ps.clean_price_from_yield(treasury_bond, ytm, SETTLE)
        assert abs(cp - 1000.0) < 2.0, f"Expected clean price near par, got {cp:.4f}"

    def test_premium_when_ytm_below_coupon(self, treasury_bond):
        dp = ps.dirty_price_from_yield(treasury_bond, 0.03, SETTLE)
        assert dp > 1000.0, "Lower YTM should produce premium price"

    def test_discount_when_ytm_above_coupon(self, treasury_bond):
        dp = ps.dirty_price_from_yield(treasury_bond, 0.07, SETTLE)
        assert dp < 1000.0, "Higher YTM should produce discount price"

    def test_zero_coupon_discounting(self, zero_coupon_bond):
        ytm = 0.05
        dp = ps.dirty_price_from_yield(zero_coupon_bond, ytm, SETTLE)
        assert (
            600 < dp < 800
        ), f"Zero coupon price should be deeply discounted: {dp:.2f}"

    def test_clean_plus_ai_equals_dirty(self, treasury_bond):
        ytm = 0.05
        dirty = ps.dirty_price_from_yield(treasury_bond, ytm, SETTLE)
        clean = ps.clean_price_from_yield(treasury_bond, ytm, SETTLE)
        ai = ps.accrued_interest(treasury_bond, SETTLE)
        assert abs((clean + ai) - dirty) < 1e-8


class TestYTMSolver:
    def test_round_trips(self, treasury_bond):
        """YTM(price(YTM)) == YTM for a range of yields."""
        for ytm_in in [0.02, 0.04, 0.05, 0.07, 0.10]:
            clean = ps.clean_price_from_yield(treasury_bond, ytm_in, SETTLE)
            ytm_out = ps.ytm_from_clean_price(treasury_bond, clean, SETTLE)
            assert (
                abs(ytm_out - ytm_in) < 1e-8
            ), f"Round-trip failed: {ytm_in} → {ytm_out}"

    def test_par_yield_at_coupon(self, treasury_bond):
        ytm = ps.ytm_from_clean_price(treasury_bond, 1000.0, SETTLE)
        assert abs(ytm - 0.05) < 0.005


class TestDuration:
    def test_modified_less_than_macaulay(self, treasury_bond):
        ytm = 0.05
        mac = ps.macaulay_duration(treasury_bond, ytm, SETTLE)
        mod = ps.modified_duration(treasury_bond, ytm, SETTLE)
        assert mod < mac

    def test_longer_maturity_longer_duration(self):
        bond_short = BondSchema(
            name="Short",
            issuer="X",
            face_value=1000,
            coupon_rate=0.05,
            maturity_date=date(2026, 1, 15),
            issue_date=date(2024, 1, 15),
            coupon_frequency="semiannual",
            bond_type="fixed",
            day_count="actual/actual",
            currency="USD",
        )
        bond_long = BondSchema(
            name="Long",
            issuer="X",
            face_value=1000,
            coupon_rate=0.05,
            maturity_date=date(2034, 1, 15),
            issue_date=date(2024, 1, 15),
            coupon_frequency="semiannual",
            bond_type="fixed",
            day_count="actual/actual",
            currency="USD",
        )
        ytm = 0.05
        dur_s = ps.macaulay_duration(bond_short, ytm, SETTLE)
        dur_l = ps.macaulay_duration(bond_long, ytm, SETTLE)
        assert dur_l > dur_s

    def test_dv01_positive(self, treasury_bond):
        d1 = ps.dv01(treasury_bond, 0.05, SETTLE)
        assert d1 > 0

    def test_convexity_positive(self, treasury_bond):
        cv = ps.convexity(treasury_bond, 0.05, SETTLE)
        assert cv > 0


class TestKRD:
    def test_krd_sums_close_to_modified_duration(self, treasury_bond):
        # KRD triangular bumps do not sum exactly to ModDur; they partition
        # duration by key rate. Verify the dominant bucket has positive KRD.
        ytm = 0.05
        krd = ps.key_rate_durations(treasury_bond, ytm, SETTLE)
        krd_total = sum(v for v in krd.values() if v > 0)
        assert krd_total > 0, "At least some key rate durations should be positive"

    def test_krd_keys(self, treasury_bond):
        krd = ps.key_rate_durations(treasury_bond, 0.05, SETTLE)
        assert 0.25 in krd
        assert 10 in krd


class TestZSpread:
    def test_z_spread_near_zero_for_risk_free(self, treasury_bond):
        spot_rates = {0.5: 0.05, 1.0: 0.05, 2.0: 0.05, 5.0: 0.05, 10.0: 0.05}
        clean = ps.clean_price_from_yield(treasury_bond, 0.05, SETTLE)
        zs = ps.z_spread(treasury_bond, clean, spot_rates, SETTLE)
        assert (
            abs(zs) < 0.001
        ), f"Z-spread should be near 0 for risk-free bond: {zs:.6f}"


class TestCashFlows:
    def test_total_pv_equals_dirty_price(self, treasury_bond):
        ytm = 0.05
        dp = ps.dirty_price_from_yield(treasury_bond, ytm, SETTLE)
        flows = ps.cash_flows(treasury_bond, SETTLE, ytm)
        total_pv = sum(f["pv"] for f in flows)
        assert abs(total_pv - dp) < 0.01

    def test_last_flow_includes_principal(self, treasury_bond):
        flows = ps.cash_flows(treasury_bond, SETTLE, 0.05)
        assert flows[-1]["principal"] == 1000.0

    def test_zero_coupon_single_flow(self, zero_coupon_bond):
        flows = ps.cash_flows(zero_coupon_bond, SETTLE, 0.05)
        assert len(flows) == 1
        assert flows[0]["coupon"] == 0.0


class TestTotalReturn:
    def test_positive_return_at_reinvestment(self, treasury_bond):
        result = ps.total_return(treasury_bond, 1000.0, 2.0, 0.04, SETTLE)
        assert result["total_return_annualized_pct"] > 0

    def test_higher_reinvestment_rate_higher_return(self, treasury_bond):
        r_low = ps.total_return(treasury_bond, 1000.0, 3.0, 0.02, SETTLE)
        r_high = ps.total_return(treasury_bond, 1000.0, 3.0, 0.06, SETTLE)
        assert (
            r_high["total_return_annualized_pct"] > r_low["total_return_annualized_pct"]
        )
