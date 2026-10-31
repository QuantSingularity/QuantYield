import numpy as np
import pytest
from ml_services.pca_factor_model import (
    STANDARD_TENORS,
    decompose_curve,
    factor_sensitivity,
    generate_synthetic_curve_panel,
    reconstruct_curve,
    rolling_pca_factors,
)


class TestSyntheticCurvePanel:
    def test_defaults_to_500_observations_of_the_standard_tenors(self):
        panel = generate_synthetic_curve_panel()

        assert panel.shape == (500, len(STANDARD_TENORS))

    def test_honours_a_custom_size_and_tenor_grid(self):
        panel = generate_synthetic_curve_panel(n_obs=40, tenors=[1.0, 5.0, 10.0])

        assert panel.shape == (40, 3)

    def test_rates_never_fall_below_the_floor(self):
        panel = generate_synthetic_curve_panel(n_obs=200)

        assert panel.min() >= 0.001

    def test_is_reproducible_for_a_given_seed(self):
        first = generate_synthetic_curve_panel(n_obs=50, seed=7)
        second = generate_synthetic_curve_panel(n_obs=50, seed=7)
        other = generate_synthetic_curve_panel(n_obs=50, seed=8)

        assert np.array_equal(first, second)
        assert not np.array_equal(first, other)


class TestDecomposeCurve:
    def test_returns_three_named_factors_by_default(self, curve_panel):
        result = decompose_curve(curve_panel)

        assert result.factor_names == ["Level", "Slope", "Curvature"]
        assert np.array(result.components).shape == (3, curve_panel.shape[1])
        assert np.array(result.factor_scores).shape == (curve_panel.shape[0], 3)

    def test_uses_the_standard_tenors_unless_told_otherwise(self, curve_panel):
        assert decompose_curve(curve_panel).tenors == STANDARD_TENORS

        custom = [0.5 * (i + 1) for i in range(curve_panel.shape[1])]
        assert decompose_curve(curve_panel, tenors=custom).tenors == custom

    def test_variance_ratios_are_descending_and_level_dominates(self, curve_panel):
        ratios = decompose_curve(curve_panel).explained_variance_ratio

        assert ratios == sorted(ratios, reverse=True)
        assert sum(ratios) <= 1.0 + 1e-9
        assert ratios[0] > 0.9

    def test_components_are_orthonormal(self, curve_panel):
        components = np.array(decompose_curve(curve_panel).components)

        assert np.allclose(components @ components.T, np.eye(3), atol=1e-8)

    def test_components_follow_the_positive_sign_convention(self, curve_panel):
        components = np.array(decompose_curve(curve_panel).components)

        assert (components.mean(axis=1) >= 0).all()

    def test_names_extra_components_by_position(self, curve_panel):
        result = decompose_curve(curve_panel, n_components=5)

        assert result.factor_names == ["Level", "Slope", "Curvature", "PC4", "PC5"]

    def test_never_returns_more_components_than_tenors(self, curve_panel):
        result = decompose_curve(curve_panel[:, :2])

        assert len(result.components) == 2
        assert result.factor_names == ["Level", "Slope"]

    def test_reconstruction_error_is_small_for_three_factor_data(self, curve_panel):
        error = decompose_curve(curve_panel).reconstruction_error

        assert 0 < error < 0.2


class TestReconstructCurve:
    def test_uses_the_last_observed_factor_scores_by_default(self, curve_panel):
        result = decompose_curve(curve_panel)
        expected = np.array(result.components).T @ np.array(result.factor_scores[-1])

        rebuilt = reconstruct_curve(result)

        assert list(rebuilt) == result.tenors
        assert np.allclose(list(rebuilt.values()), expected, atol=1e-5)

    def test_zeroing_every_factor_gives_a_zero_curve(self, curve_panel):
        result = decompose_curve(curve_panel)

        rebuilt = reconstruct_curve(
            result, {"Level": 0.0, "Slope": 0.0, "Curvature": 0.0}
        )

        assert all(value == 0.0 for value in rebuilt.values())

    def test_overriding_one_factor_leaves_the_others_untouched(self, curve_panel):
        result = decompose_curve(curve_panel)
        base = np.array(list(reconstruct_curve(result).values()))
        shifted = np.array(list(reconstruct_curve(result, {"Level": 3.0}).values()))

        level_loading = np.array(result.components[0])
        level_score = result.factor_scores[-1][0]
        expected_change = level_loading * (3.0 - level_score)

        assert np.allclose(shifted - base, expected_change, atol=1e-5)

    def test_ignores_overrides_for_unknown_factors(self, curve_panel):
        result = decompose_curve(curve_panel)

        assert reconstruct_curve(result, {"Nonsense": 9.0}) == reconstruct_curve(result)


class TestFactorSensitivity:
    def test_is_the_loading_times_the_shift(self, curve_panel):
        result = decompose_curve(curve_panel)

        change = factor_sensitivity(result, "Slope", shift_std=2.0)

        expected = np.array(result.components[1]) * 2.0
        assert np.allclose(list(change.values()), expected, atol=1e-5)
        assert list(change) == result.tenors

    def test_scales_linearly_with_the_shift(self, curve_panel):
        result = decompose_curve(curve_panel)

        one = np.array(list(factor_sensitivity(result, "Level", 1.0).values()))
        three = np.array(list(factor_sensitivity(result, "Level", 3.0).values()))

        assert np.allclose(three, 3 * one, atol=1e-5)

    def test_a_level_shift_moves_every_tenor_the_same_way(self, curve_panel):
        change = factor_sensitivity(decompose_curve(curve_panel), "Level")

        assert all(value > 0 for value in change.values())

    def test_rejects_an_unknown_factor(self, curve_panel):
        result = decompose_curve(curve_panel)

        with pytest.raises(ValueError, match="Nonsense.*Level"):
            factor_sensitivity(result, "Nonsense")


class TestRollingPcaFactors:
    def test_returns_nothing_when_history_is_shorter_than_the_window(self, curve_panel):
        assert rolling_pca_factors(curve_panel[:10], window=63) == {}

    def test_produces_one_score_per_window_position(self, curve_panel):
        history = rolling_pca_factors(curve_panel[:100], window=63)

        assert set(history) == {"Level", "Slope", "Curvature"}
        assert all(len(scores) == 100 - 63 + 1 for scores in history.values())
