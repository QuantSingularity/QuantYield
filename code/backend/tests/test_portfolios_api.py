"""
Tests for Portfolio API endpoints.
"""

import pytest


@pytest.mark.django_db
class TestPortfolioCRUD:
    def test_create_portfolio(self, api_client):
        resp = api_client.post(
            "/api/v1/portfolios/",
            {"name": "My Portfolio", "description": "Test", "currency": "USD"},
            format="json",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My Portfolio"
        assert "id" in data

    def test_list_portfolios(self, api_client, sample_portfolio):
        resp = api_client.get("/api/v1/portfolios/")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1

    def test_get_portfolio(self, api_client, sample_portfolio):
        resp = api_client.get(f"/api/v1/portfolios/{sample_portfolio.id}/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_portfolio.id)
        assert data["position_count"] >= 1

    def test_delete_portfolio(self, api_client, sample_portfolio):
        resp = api_client.delete(f"/api/v1/portfolios/{sample_portfolio.id}/")
        assert resp.status_code == 204


@pytest.mark.django_db
class TestPortfolioPositions:
    def test_add_position(self, api_client, sample_portfolio, sample_bond):
        resp = api_client.post(
            f"/api/v1/portfolios/{sample_portfolio.id}/positions/",
            {
                "bond": str(sample_bond.id),
                "face_amount": 50000,
                "purchase_price": 1000.0,
            },
            format="json",
        )
        assert resp.status_code in (200, 201)

    def test_remove_position(self, api_client, sample_portfolio, sample_bond):
        resp = api_client.delete(
            f"/api/v1/portfolios/{sample_portfolio.id}/positions/{sample_bond.id}/"
        )
        assert resp.status_code == 204


@pytest.mark.django_db
class TestPortfolioAnalytics:
    def test_analytics(self, api_client, sample_portfolio):
        resp = api_client.get(f"/api/v1/portfolios/{sample_portfolio.id}/analytics/")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_market_value" in data
        assert "portfolio_duration" in data
        assert "portfolio_dv01" in data
        assert "key_rate_durations" in data
        assert "sector_allocation" in data

    def test_scenarios(self, api_client, sample_portfolio):
        resp = api_client.post(f"/api/v1/portfolios/{sample_portfolio.id}/scenarios/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["scenarios"]) == 10
        # All scenarios should have a pnl value
        for s in data["scenarios"]:
            assert "pnl" in s

    def test_custom_scenario(self, api_client, sample_portfolio):
        resp = api_client.post(
            f"/api/v1/portfolios/{sample_portfolio.id}/custom-scenario/",
            {"parallel_shift_bps": 100},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pnl"] < 0, "Rates up → bond prices down"

    def test_pnl(self, api_client, sample_portfolio):
        resp = api_client.get(f"/api/v1/portfolios/{sample_portfolio.id}/pnl/")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_market_value" in data
        assert "positions" in data

    def test_duration_buckets(self, api_client, sample_portfolio):
        resp = api_client.get(
            f"/api/v1/portfolios/{sample_portfolio.id}/duration-buckets/"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "buckets" in data
        assert "total_modified_duration" in data

    def test_var(self, api_client, sample_portfolio):
        resp = api_client.post(
            f"/api/v1/portfolios/{sample_portfolio.id}/var/",
            {"confidence_level": 0.99, "holding_period_days": 1, "lookback_days": 252},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "historical" in data
        assert "parametric" in data
        assert data["historical"]["var"] > 0
