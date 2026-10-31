import numpy as np
import pytest
from ml_services import credit_spread_model, predict_credit_spread
from ml_services.credit_spread_model import (
    FEATURE_NAMES,
    RATING_SCORES,
    SECTORS,
    _build_feature_vector,
    _generate_credit_training_data,
    _get_credit_model,
)

BOND = {
    "years_to_maturity": 7.0,
    "coupon_rate": 0.05,
    "level_10y": 0.045,
    "slope_2s10s_bps": 50.0,
    "butterfly_bps": 0.0,
    "yield_vol_21d_pct": 0.8,
    "sector": "Industrials",
}


def spread(rating="BBB", **overrides):
    return predict_credit_spread(rating, **{**BOND, **overrides}).predicted_spread_bps


class TestRatingScores:
    def test_worse_ratings_have_higher_scores(self):
        ladder = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]
        scores = [RATING_SCORES[rating] for rating in ladder]

        assert scores == sorted(scores)
        assert len(set(scores)) == len(scores)

    def test_unrated_bonds_are_treated_as_bbb_minus(self):
        assert RATING_SCORES["NR"] == RATING_SCORES["BBB-"]


class TestFeatureVector:
    def build(self, rating="A", sector="Technology"):
        return _build_feature_vector(rating, 5.0, 0.04, 0.045, 40.0, 5.0, 0.9, sector)

    def test_has_one_column_per_feature_name(self):
        assert self.build().shape == (1, len(FEATURE_NAMES))
        assert len(FEATURE_NAMES) == 7 + len(SECTORS)

    def test_converts_rates_to_percent_and_keeps_basis_points(self):
        vector = self.build()[0]

        assert vector[0] == pytest.approx(4.5)  # 10Y level, percent
        assert vector[1] == pytest.approx(40.0)  # slope, bps
        assert vector[5] == pytest.approx(5.0)  # years to maturity
        assert vector[6] == pytest.approx(4.0)  # coupon, percent

    def test_encodes_the_rating_as_its_ordinal_score(self):
        assert self.build(rating="A")[0][4] == RATING_SCORES["A"]

    def test_normalises_rating_case_and_whitespace(self):
        assert np.array_equal(self.build(rating=" bbb "), self.build(rating="BBB"))

    def test_scores_an_unknown_rating_like_bbb_minus(self):
        assert self.build(rating="ZZZ")[0][4] == RATING_SCORES["BBB-"]

    def test_one_hot_encodes_the_sector(self):
        sector_columns = self.build(sector="Technology")[0][7:]

        assert sector_columns.sum() == 1.0
        assert sector_columns[SECTORS.index("Technology")] == 1.0

    def test_maps_an_unknown_sector_to_other(self):
        unknown = self.build(sector="Nonexistent")

        assert np.array_equal(unknown, self.build(sector="Other"))
        assert unknown[0][7:][SECTORS.index("Other")] == 1.0


class TestTrainingData:
    def test_has_the_same_columns_as_the_feature_vector(self):
        features, targets = _generate_credit_training_data(n_samples=100)

        assert features.shape == (100, len(FEATURE_NAMES))
        assert targets.shape == (100,)

    def test_spreads_never_fall_below_5_basis_points(self):
        _, targets = _generate_credit_training_data(n_samples=500)

        assert targets.min() >= 5

    def test_is_reproducible_for_a_given_seed(self):
        first, _ = _generate_credit_training_data(50, seed=1)
        second, _ = _generate_credit_training_data(50, seed=1)

        assert np.array_equal(first, second)


class TestPredictCreditSpread:
    def test_returns_a_positive_spread_with_an_ordered_interval(self):
        result = predict_credit_spread("BBB", **BOND)

        assert result.predicted_spread_bps > 0
        assert (
            result.confidence_interval_lower_bps
            <= result.predicted_spread_bps
            <= result.confidence_interval_upper_bps
        )
        assert result.confidence_interval_lower_bps >= 1.0

    def test_names_the_ensemble_that_produced_the_answer(self):
        result = predict_credit_spread("BBB", **BOND)

        assert result.model in {"xgb_ensemble", "sklearn_ensemble"}

    def test_riskier_ratings_pay_wider_spreads(self):
        spreads = [spread(r) for r in ["AAA", "A", "BBB", "BB", "B", "CCC"]]

        assert spreads == sorted(spreads)
        assert spreads[-1] > 2 * spreads[0]

    def test_longer_maturities_pay_wider_spreads(self):
        assert spread(years_to_maturity=25.0) > spread(years_to_maturity=2.0)

    def test_more_volatile_markets_pay_wider_spreads(self):
        assert spread(yield_vol_21d_pct=1.8) > spread(yield_vol_21d_pct=0.3)

    def test_financials_pay_more_than_technology(self):
        assert spread(sector="Financials") > spread(sector="Technology")

    def test_is_reproducible(self):
        assert spread() == spread()

    def test_treats_unrated_bonds_like_bbb_minus(self):
        assert spread("NR") == spread("BBB-")

    def test_reports_feature_importances_that_sum_to_one(self):
        result = predict_credit_spread("BBB", **BOND)

        assert list(result.feature_importances) == FEATURE_NAMES
        assert sum(result.feature_importances.values()) == pytest.approx(1.0, abs=1e-2)

    def test_rating_is_the_most_important_feature(self):
        importances = predict_credit_spread("BBB", **BOND).feature_importances

        assert max(importances, key=importances.get) == "rating_score"

    def test_the_trained_model_is_cached(self):
        assert _get_credit_model() is _get_credit_model()

    def test_falls_back_to_a_rating_based_estimate_when_the_model_fails(
        self, monkeypatch
    ):
        def broken():
            raise RuntimeError("model unavailable")

        monkeypatch.setattr(credit_spread_model, "_get_credit_model", broken)

        result = predict_credit_spread("BBB", **BOND)

        base = RATING_SCORES["BBB"] * 18
        assert result.model == "rule_based_fallback"
        assert result.predicted_spread_bps == pytest.approx(base)
        assert result.confidence_interval_lower_bps == pytest.approx(base * 0.75)
        assert result.confidence_interval_upper_bps == pytest.approx(base * 1.35)
        assert result.feature_importances == {}

    def test_supports_xgboost_models_stored_as_named_tuples(self, monkeypatch):
        class FixedModel:
            def predict(self, features):
                return np.array([100.0])

        state = {
            "models": [("xgb", FixedModel())],
            "backend": "xgb_ensemble",
            "importances": {},
        }
        monkeypatch.setattr(credit_spread_model, "_get_credit_model", lambda: state)

        result = predict_credit_spread("BBB", **BOND)

        # One model has no spread across models, so the interval is +/- 15 percent
        # scaled by the 80 percent z-score of 1.28.
        assert result.predicted_spread_bps == pytest.approx(100.0)
        assert result.confidence_interval_lower_bps == pytest.approx(
            100 * (1 - 1.28 * 0.15)
        )
        assert result.confidence_interval_upper_bps == pytest.approx(
            100 * (1 + 1.28 * 0.15)
        )
