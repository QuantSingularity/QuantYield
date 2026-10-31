import numpy as np
import pytest
from ml_services import classify_regime, regime_classifier
from ml_services.regime_classifier import (
    REGIMES,
    _engineer_features,
    _generate_synthetic_training_data,
    _rule_based_regime,
    get_regime_model,
)

# Spot curves in decimal form, keyed by tenor in years.
INVERTED = {0.25: 0.052, 2.0: 0.050, 5.0: 0.047, 10.0: 0.044, 30.0: 0.045}
NORMAL = {0.25: 0.040, 2.0: 0.042, 5.0: 0.045, 10.0: 0.0495, 30.0: 0.052}
FLAT = {0.25: 0.045, 2.0: 0.0450, 5.0: 0.0452, 10.0: 0.0453, 30.0: 0.046}
STEEP = {0.25: 0.010, 2.0: 0.015, 5.0: 0.030, 10.0: 0.0450, 30.0: 0.050}


class TestFeatureEngineering:
    def test_measures_slopes_and_level_in_their_reporting_units(self):
        features = _engineer_features(NORMAL)

        assert features["level_10y_pct"] == pytest.approx(4.95)
        assert features["slope_2s10s_bps"] == pytest.approx(75.0)
        assert features["slope_3m2y_bps"] == pytest.approx(20.0)
        assert features["slope_10s30s_bps"] == pytest.approx(25.0)
        assert features["butterfly_bps"] == pytest.approx(15.0)

    def test_interpolates_between_quoted_tenors(self):
        features = _engineer_features({1.0: 0.03, 5.0: 0.05})

        assert features["r2y_pct"] == pytest.approx(3.5)

    def test_holds_the_end_rates_flat_outside_the_quoted_range(self):
        features = _engineer_features({1.0: 0.03, 5.0: 0.05})

        assert features["r10y_pct"] == pytest.approx(5.0)

    def test_an_empty_curve_gives_zero_rates_instead_of_failing(self):
        features = _engineer_features({})

        assert features["r10y_pct"] == 0.0
        assert features["slope_2s10s_bps"] == 0.0

    def test_uses_neutral_defaults_without_history(self):
        features = _engineer_features(NORMAL)

        assert features["vol_21d_annualised_pct"] == 0.5
        assert features["momentum_5d_bps"] == 0.0

    def test_ignores_histories_shorter_than_21_observations(self):
        features = _engineer_features(NORMAL, rate_history=np.linspace(0.04, 0.05, 20))

        assert features["vol_21d_annualised_pct"] == 0.5
        assert features["momentum_5d_bps"] == 0.0

    def test_derives_momentum_and_volatility_from_the_history(self):
        steady_climb = 0.04 + 0.0001 * np.arange(30)

        features = _engineer_features(NORMAL, rate_history=steady_climb)

        # Five days of +1bp is +5bp, and constant daily changes have no volatility.
        assert features["momentum_5d_bps"] == pytest.approx(5.0)
        assert features["vol_21d_annualised_pct"] == pytest.approx(0.0, abs=1e-9)


class TestRuleBasedRegime:
    @pytest.mark.parametrize(
        ("slope", "butterfly", "expected"),
        [
            (-50, 0, "inverted"),
            (-10.1, 0, "inverted"),
            (-10, 0, "flat"),
            (0, 0, "flat"),
            (19.9, 0, "flat"),
            (20, 0, "normal"),
            (60, 0, "normal"),
            (60, 25, "normal"),
            (60, 30, "humped"),
            (60, -30, "humped"),
            (121, 0, "steep"),
            (121, 50, "steep"),
        ],
    )
    def test_classifies_by_slope_then_butterfly(self, slope, butterfly, expected):
        features = {
            "slope_2s10s_bps": slope,
            "butterfly_bps": butterfly,
            "level_10y_pct": 4.0,
        }

        regime, _ = _rule_based_regime(features)

        assert regime == expected

    def test_gives_the_chosen_regime_70_percent_and_the_others_equal_shares(self):
        regime, probabilities = _rule_based_regime(
            {"slope_2s10s_bps": 60, "butterfly_bps": 0, "level_10y_pct": 4.0}
        )

        others = [p for r, p in probabilities.items() if r != regime]
        assert probabilities[regime] == pytest.approx(0.70)
        assert len(others) == len(REGIMES) - 1
        assert others == [pytest.approx(others[0])] * len(others)

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Known defect: every regime starts at 0.05 and the remaining 0.30 is "
            "then spread over the other four as well, so the fallback "
            "probabilities sum to 1.2. Remove this marker once they sum to 1."
        ),
    )
    def test_probabilities_sum_to_one(self):
        _, probabilities = _rule_based_regime(
            {"slope_2s10s_bps": 60, "butterfly_bps": 0, "level_10y_pct": 4.0}
        )

        assert sum(probabilities.values()) == pytest.approx(1.0)


class TestTrainingData:
    def test_has_one_row_of_nine_features_per_sample(self):
        features, labels = _generate_synthetic_training_data(n_samples=1000)

        assert features.shape == (1000, 9)
        assert labels.shape == (1000,)

    def test_classes_are_perfectly_balanced(self):
        _, labels = _generate_synthetic_training_data(n_samples=1000)

        assert np.bincount(labels).tolist() == [200] * len(REGIMES)

    def test_is_reproducible_for_a_given_seed(self):
        first, _ = _generate_synthetic_training_data(100, seed=3)
        second, _ = _generate_synthetic_training_data(100, seed=3)

        assert np.array_equal(first, second)


class TestClassifyRegime:
    @pytest.mark.parametrize(
        ("curve", "expected"),
        [
            (INVERTED, "inverted"),
            (NORMAL, "normal"),
            (FLAT, "flat"),
            (STEEP, "steep"),
        ],
    )
    def test_recognises_clear_curve_shapes(self, curve, expected):
        result = classify_regime(curve)

        assert result.regime == expected
        assert result.probability > 0.5

    def test_probabilities_are_a_distribution_over_all_regimes(self):
        result = classify_regime(NORMAL)

        assert list(result.all_probabilities) == REGIMES
        assert sum(result.all_probabilities.values()) == pytest.approx(1.0, abs=1e-3)

    def test_reports_the_most_probable_regime(self):
        result = classify_regime(STEEP)

        best = max(result.all_probabilities, key=result.all_probabilities.get)
        assert result.regime == best
        assert result.probability == result.all_probabilities[best]

    def test_reports_the_features_it_used(self):
        result = classify_regime(NORMAL)

        assert result.features["slope_2s10s_bps"] == pytest.approx(75.0)
        assert set(result.features) == set(_engineer_features(NORMAL))

    def test_names_the_ensemble_that_produced_the_answer(self):
        assert classify_regime(NORMAL).model in {"xgb_ensemble", "sklearn_ensemble"}

    def test_accepts_a_rate_history(self):
        history = 0.045 + np.cumsum(np.random.default_rng(2).normal(0, 0.0004, 60))

        result = classify_regime(NORMAL, rate_history=history)

        assert result.features["momentum_5d_bps"] == pytest.approx(
            (history[-1] - history[-6]) * 10_000
        )

    def test_the_trained_model_is_cached(self):
        assert get_regime_model() is get_regime_model()

    def test_falls_back_to_the_rules_when_the_model_fails(self, monkeypatch):
        def broken():
            raise RuntimeError("model unavailable")

        monkeypatch.setattr(regime_classifier, "get_regime_model", broken)

        result = classify_regime(INVERTED)

        assert result.model == "rule_based"
        assert result.regime == "inverted"
        assert result.probability == pytest.approx(0.70)
