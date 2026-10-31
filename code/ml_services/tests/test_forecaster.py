import sys
import types

import numpy as np
import pytest
from ml_services import (
    available_backend,
    clear_model_cache,
    forecast_rates,
    train_forecaster,
)


@pytest.fixture(autouse=True)
def fresh_cache():
    """Every test starts and ends with an empty in-process model cache."""
    clear_model_cache()
    yield
    clear_model_cache()


@pytest.fixture
def no_torch(monkeypatch):
    """Make `import torch` fail, so the numpy-only AR(1) backend is used."""
    monkeypatch.setitem(sys.modules, "torch", None)


@pytest.fixture
def arima_state(rate_series, no_torch):
    return train_forecaster(rate_series, seq_len=20, epochs=1)


class TestAvailableBackend:
    def test_is_arima_without_pytorch(self, no_torch):
        assert available_backend() == "arima"

    def test_is_transformer_when_pytorch_is_importable(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "torch", types.ModuleType("torch"))

        assert available_backend() == "transformer"


class TestTrainForecaster:
    def test_falls_back_to_the_ar1_model_without_pytorch(self, arima_state):
        assert arima_state["backend"] == "arima"
        assert arima_state["model"] is None

    def test_records_the_series_statistics(self, rate_series, arima_state):
        assert arima_state["last_value"] == pytest.approx(rate_series[-1])
        assert arima_state["mean"] == pytest.approx(rate_series.mean())
        assert arima_state["seq_len"] == 20
        assert arima_state["sigma"] == pytest.approx(np.diff(rate_series).std())

    def test_the_autoregressive_coefficient_is_kept_inside_the_unit_interval(
        self, no_torch
    ):
        # Perfectly alternating changes give a correlation of exactly -1.
        rates = 0.04 + np.cumsum(np.tile([0.001, -0.001], 50))

        state = train_forecaster(rates, epochs=1)

        assert state["phi"] == pytest.approx(-0.99)

    def test_recovers_the_persistence_of_the_daily_changes(self, no_torch):
        rng = np.random.default_rng(11)
        phi, changes = 0.6, [0.0]
        for shock in rng.normal(0, 0.0005, 4000):
            changes.append(phi * changes[-1] + shock)
        rates = 0.05 + np.cumsum(changes)

        state = train_forecaster(rates, epochs=1)

        assert state["phi"] == pytest.approx(0.6, abs=0.08)

    def test_returns_the_cached_model_on_repeat_calls(self, rate_series, no_torch):
        first = train_forecaster(rate_series, seq_len=20, epochs=1)

        assert train_forecaster(rate_series, seq_len=20, epochs=1) is first

    def test_force_retrain_ignores_the_cache(self, rate_series, no_torch):
        first = train_forecaster(rate_series, seq_len=20, epochs=1)

        again = train_forecaster(rate_series, seq_len=20, epochs=1, force_retrain=True)

        assert again is not first

    def test_different_settings_get_separate_cache_entries(self, rate_series, no_torch):
        short = train_forecaster(rate_series, seq_len=10, epochs=1)
        long = train_forecaster(rate_series, seq_len=30, epochs=1)

        assert short is not long
        assert short["seq_len"] == 10
        assert long["seq_len"] == 30

    def test_clearing_the_cache_forces_a_new_model(self, rate_series, no_torch):
        first = train_forecaster(rate_series, seq_len=20, epochs=1)

        clear_model_cache()

        assert train_forecaster(rate_series, seq_len=20, epochs=1) is not first


class TestForecastRates:
    def test_returns_one_value_per_day_in_every_series(self, rate_series, arima_state):
        result = forecast_rates(arima_state, rate_series, horizon_days=7)

        assert result.backend == "arima"
        assert result.horizon_days == 7
        assert len(result.point) == len(result.lower) == len(result.upper) == 7

    def test_the_band_brackets_the_point_forecast(self, rate_series, arima_state):
        result = forecast_rates(arima_state, rate_series, horizon_days=7)

        for low, mid, high in zip(result.lower, result.point, result.upper):
            assert low <= mid <= high

    def test_a_higher_confidence_level_gives_a_wider_band(
        self, rate_series, arima_state
    ):
        wide = forecast_rates(arima_state, rate_series, 7, confidence_level=0.99)
        narrow = forecast_rates(arima_state, rate_series, 7, confidence_level=0.50)

        wide_width = np.array(wide.upper) - np.array(wide.lower)
        narrow_width = np.array(narrow.upper) - np.array(narrow.lower)
        assert wide_width.mean() > narrow_width.mean()

    def test_the_band_widens_further_into_the_future(self, rate_series, arima_state):
        result = forecast_rates(arima_state, rate_series, horizon_days=15)

        widths = np.array(result.upper) - np.array(result.lower)
        assert widths[-1] > widths[0]

    def test_is_reproducible(self, rate_series, arima_state):
        first = forecast_rates(arima_state, rate_series, horizon_days=5)
        second = forecast_rates(arima_state, rate_series, horizon_days=5)

        assert first.point == second.point
        assert first.lower == second.lower
        assert first.upper == second.upper

    def test_echoes_the_request_and_model_parameters(self, rate_series, arima_state):
        result = forecast_rates(
            arima_state, rate_series, horizon_days=4, confidence_level=0.8
        )

        assert result.confidence_level == 0.8
        assert result.metadata == {
            "phi": arima_state["phi"],
            "sigma": arima_state["sigma"],
        }

    def test_rates_never_forecast_below_the_floor(self):
        # A sharp final drop that keeps persisting would push the rate below zero.
        rates = np.array([0.0200, 0.0105, 0.0005])
        state = {"backend": "arima", "phi": 0.9, "sigma": 0.0, "last_value": 0.0005}

        result = forecast_rates(state, rates, horizon_days=5, n_simulations=10)

        assert result.point == [0.0001] * 5
        assert result.lower == [0.0001] * 5
        assert result.upper == [0.0001] * 5

    def test_a_state_without_ar_parameters_forecasts_a_flat_line(self, rate_series):
        result = forecast_rates({"backend": "arima"}, rate_series, horizon_days=3)

        assert result.point == pytest.approx([rate_series[-1]] * 3)

    @pytest.mark.parametrize("backend", ["transformer", "lstm"])
    def test_a_failing_neural_backend_falls_back_to_ar1(
        self, backend, rate_series, no_torch
    ):
        state = {
            "backend": backend,
            "model": None,
            "mean": float(rate_series.mean()),
            "std": float(rate_series.std()),
            "seq_len": 20,
        }

        result = forecast_rates(state, rate_series, horizon_days=5, n_simulations=50)

        assert result.backend == "arima"
        assert len(result.point) == 5

    @pytest.mark.filterwarnings("ignore:invalid value:RuntimeWarning")
    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Known defect: a constant series has zero-variance changes, so the "
            "AR(1) correlation is NaN and every forecast value is NaN. Remove this "
            "marker once the coefficient falls back to 0 for constant series."
        ),
    )
    def test_a_constant_series_forecasts_a_constant(self, no_torch):
        flat = np.full(50, 0.04)
        state = train_forecaster(flat, epochs=1)

        result = forecast_rates(state, flat, horizon_days=3, n_simulations=20)

        assert result.point == pytest.approx([0.04] * 3)
