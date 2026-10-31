import numpy as np
import pytest
from ml_services import volatility_model
from ml_services.volatility_model import (
    _historical_vol,
    forecast_volatility,
    volatility_term_structure,
)

ANNUALISE_PCT = np.sqrt(252) * 100


@pytest.fixture
def alternating_rates() -> np.ndarray:
    """A series whose daily changes alternate between -10bp and +10bp."""
    return 0.04 + np.cumsum(np.tile([0.001, -0.001], 40))


class TestForecastVolatility:
    def test_garch_returns_one_positive_value_per_day(self, rate_series):
        result = forecast_volatility(rate_series, horizon_days=10, model_type="garch")

        assert result.model == "garch"
        assert result.horizon_days == 10
        assert len(result.forecast_annualised_pct) == 10
        assert all(value > 0 for value in result.forecast_annualised_pct)
        assert result.current_vol_annualised_pct > 0

    def test_garch_reports_its_fitted_parameters(self, rate_series):
        params = forecast_volatility(rate_series, horizon_days=5).garch_params

        assert set(params) == {"omega", "alpha", "beta", "log_likelihood"}
        assert params["alpha"] >= 0
        assert params["beta"] >= 0

    def test_historical_model_can_be_requested_directly(self, rate_series):
        result = forecast_volatility(rate_series, 5, model_type="historical")

        assert result.model == "historical_mean_reversion"
        assert result.garch_params is None

    def test_an_unknown_model_type_uses_historical_volatility(self, rate_series):
        result = forecast_volatility(rate_series, 5, model_type="nonsense")

        assert result.model == "historical_mean_reversion"

    def test_short_histories_skip_the_garch_fit(self, rate_series):
        result = forecast_volatility(rate_series[:20], horizon_days=4)

        assert result.model == "historical_mean_reversion"
        assert len(result.forecast_annualised_pct) == 4

    def test_falls_back_to_historical_when_the_garch_fit_fails(
        self, rate_series, monkeypatch
    ):
        def broken(*args, **kwargs):
            raise RuntimeError("optimiser did not converge")

        monkeypatch.setattr(volatility_model, "_garch_forecast", broken)

        result = forecast_volatility(rate_series, horizon_days=6, model_type="garch")

        assert result.model == "historical_mean_reversion"
        assert len(result.forecast_annualised_pct) == 6

    def test_noisier_rates_have_higher_current_volatility(self):
        rng = np.random.default_rng(3)
        shocks = rng.normal(0, 1, 200)
        calm = 0.045 + np.cumsum(shocks * 0.0002)
        noisy = 0.045 + np.cumsum(shocks * 0.0010)

        calm_vol = forecast_volatility(calm, 3, "historical").current_vol_annualised_pct
        noisy_vol = forecast_volatility(
            noisy, 3, "historical"
        ).current_vol_annualised_pct

        assert noisy_vol == pytest.approx(5 * calm_vol, rel=1e-6)

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Known defect: arch cannot produce analytic EGARCH forecasts beyond one "
            "step, so every multi-day EGARCH request silently becomes historical "
            "volatility. Remove this marker once simulation-based forecasts are used."
        ),
    )
    def test_egarch_is_used_for_multi_day_horizons(self, rate_series):
        result = forecast_volatility(rate_series, horizon_days=10, model_type="egarch")

        assert result.model == "egarch"

    def test_egarch_works_for_a_one_day_horizon(self, rate_series):
        result = forecast_volatility(rate_series, horizon_days=1, model_type="egarch")

        assert result.model == "egarch"
        assert len(result.forecast_annualised_pct) == 1


class TestHistoricalVolatility:
    def test_annualises_daily_changes_with_root_252(self, alternating_rates):
        result = _historical_vol(alternating_rates, horizon_days=3)

        expected = 0.001 * ANNUALISE_PCT
        assert result.current_vol_annualised_pct == pytest.approx(expected, rel=0.02)

    def test_mean_reverts_towards_the_long_run_level(self):
        rng = np.random.default_rng(5)
        turbulent = rng.normal(0, 0.002, 200)
        calm = rng.normal(0, 0.0002, 30)
        rates = 0.045 + np.cumsum(np.concatenate([turbulent, calm]))

        result = _historical_vol(rates, horizon_days=20)
        forecast = result.forecast_annualised_pct
        long_run = float(np.std(np.diff(rates))) * ANNUALISE_PCT

        assert result.current_vol_annualised_pct < long_run
        assert forecast == sorted(forecast)
        assert result.current_vol_annualised_pct < forecast[0]
        assert forecast[-1] < long_run

    def test_reports_the_requested_horizon(self, rate_series):
        result = _historical_vol(rate_series, horizon_days=12)

        assert result.horizon_days == 12
        assert len(result.forecast_annualised_pct) == 12


class TestVolatilityTermStructure:
    def test_reports_the_default_windows_for_long_histories(self, rate_series):
        result = volatility_term_structure(rate_series)

        assert list(result) == ["5d", "10d", "21d", "63d", "126d", "252d"]
        assert all(value > 0 for value in result.values())

    def test_skips_windows_longer_than_the_history(self, rate_series):
        result = volatility_term_structure(rate_series[:30], windows=[5, 100])

        assert list(result) == ["5d"]

    def test_annualises_each_window(self, alternating_rates):
        result = volatility_term_structure(alternating_rates, windows=[4])

        assert result["4d"] == pytest.approx(0.001 * ANNUALISE_PCT, abs=1e-3)
