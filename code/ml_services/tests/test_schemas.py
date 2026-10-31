import ml_services
from ml_services.schemas import (
    CreditSpreadResult,
    ForecastResult,
    PCAResult,
    RegimeResult,
    VolatilityResult,
)


class TestForecastResult:
    def test_defaults(self):
        result = ForecastResult(point=[0.04], lower=[0.03], upper=[0.05], backend="x")

        assert result.confidence_level == 0.90
        assert result.horizon_days == 0
        assert result.metadata == {}

    def test_metadata_is_not_shared_between_instances(self):
        first = ForecastResult(point=[], lower=[], upper=[], backend="x")
        second = ForecastResult(point=[], lower=[], upper=[], backend="x")

        first.metadata["seen"] = True

        assert second.metadata == {}


class TestVolatilityResult:
    def test_garch_params_are_optional(self):
        result = VolatilityResult(
            forecast_annualised_pct=[1.0],
            current_vol_annualised_pct=1.0,
            model="historical",
            horizon_days=1,
        )

        assert result.garch_params is None


class TestResultContainers:
    def test_regime_result_keeps_its_fields(self):
        result = RegimeResult(
            regime="normal",
            probability=0.9,
            all_probabilities={"normal": 0.9},
            features={"slope_2s10s_bps": 75.0},
            model="rule_based",
        )

        assert result.regime == "normal"
        assert result.all_probabilities["normal"] == 0.9

    def test_credit_spread_result_keeps_its_fields(self):
        result = CreditSpreadResult(
            predicted_spread_bps=120.0,
            confidence_interval_lower_bps=100.0,
            confidence_interval_upper_bps=140.0,
            feature_importances={"rating_score": 0.5},
            model="sklearn_ensemble",
        )

        assert result.predicted_spread_bps == 120.0
        assert result.feature_importances == {"rating_score": 0.5}

    def test_pca_result_keeps_its_fields(self):
        result = PCAResult(
            components=[[1.0, 1.0]],
            explained_variance_ratio=[1.0],
            factor_scores=[[0.0]],
            factor_names=["Level"],
            tenors=[2.0, 10.0],
            reconstruction_error=0.0,
        )

        assert result.factor_names == ["Level"]
        assert result.tenors == [2.0, 10.0]


class TestPackageApi:
    def test_every_exported_name_resolves(self):
        for name in ml_services.__all__:
            assert hasattr(ml_services, name), name

    def test_exports_the_five_result_types_and_all_entry_points(self):
        exported = set(ml_services.__all__)

        assert {
            "ForecastResult",
            "RegimeResult",
            "CreditSpreadResult",
            "VolatilityResult",
            "PCAResult",
        } <= exported
        assert {
            "train_forecaster",
            "forecast_rates",
            "classify_regime",
            "forecast_volatility",
            "predict_credit_spread",
            "decompose_curve",
        } <= exported
