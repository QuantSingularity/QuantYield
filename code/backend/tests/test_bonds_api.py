"""
Tests for the Bonds REST API endpoints.
"""

import pytest


@pytest.mark.django_db
class TestBondCRUD:
    def test_create_bond(self, api_client, sample_bond_data):
        url = "/api/v1/bonds/"
        resp = api_client.post(url, sample_bond_data, format="json")
        assert resp.status_code == 201, resp.data
        data = resp.json()
        assert data["name"] == sample_bond_data["name"]
        assert data["issuer"] == sample_bond_data["issuer"]
        assert "id" in data
        assert "ytm" in data
        assert "modified_duration" in data

    def test_list_bonds(self, api_client, sample_bond):
        resp = api_client.get("/api/v1/bonds/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1

    def test_get_bond(self, api_client, sample_bond):
        resp = api_client.get(f"/api/v1/bonds/{sample_bond.id}/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(sample_bond.id)
        assert data["dirty_price"] is not None
        assert data["ytm"] is not None

    def test_patch_bond(self, api_client, sample_bond):
        resp = api_client.patch(
            f"/api/v1/bonds/{sample_bond.id}/",
            {"credit_rating": "AA+"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["credit_rating"] == "AA+"

    def test_delete_bond(self, api_client, sample_bond):
        resp = api_client.delete(f"/api/v1/bonds/{sample_bond.id}/")
        assert resp.status_code == 204

    def test_filter_by_sector(self, api_client, sample_bond):
        resp = api_client.get("/api/v1/bonds/?sector=Government")
        assert resp.status_code == 200
        results = resp.json()["results"]
        assert all("Government" in r["sector"] for r in results)

    def test_search_by_name(self, api_client, sample_bond):
        resp = api_client.get(f"/api/v1/bonds/?search={sample_bond.name[:10]}")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1

    def test_invalid_isin(self, api_client, sample_bond_data):
        sample_bond_data["isin"] = "INVALID"
        resp = api_client.post("/api/v1/bonds/", sample_bond_data, format="json")
        assert resp.status_code == 400

    def test_maturity_before_issue_rejected(self, api_client, sample_bond_data):
        sample_bond_data["maturity_date"] = "2019-01-01"
        resp = api_client.post("/api/v1/bonds/", sample_bond_data, format="json")
        assert resp.status_code == 400


@pytest.mark.django_db
class TestBondAnalytics:
    def test_price_from_yield(self, api_client, sample_bond):
        resp = api_client.post(
            f"/api/v1/bonds/{sample_bond.id}/price/",
            {"yield_rate": 0.05},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "clean_price" in data
        assert "dirty_price" in data
        assert "dv01" in data

    def test_price_from_market_price(self, api_client, sample_bond):
        resp = api_client.post(
            f"/api/v1/bonds/{sample_bond.id}/price/",
            {"market_price": 980.0},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["ytm"] > 0

    def test_ytm_endpoint(self, api_client, sample_bond):
        resp = api_client.post(
            f"/api/v1/bonds/{sample_bond.id}/ytm/",
            {"clean_price": 1000.0},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "ytm" in data
        assert abs(data["ytm"] - 0.05) < 0.01

    def test_cash_flows(self, api_client, sample_bond):
        resp = api_client.get(f"/api/v1/bonds/{sample_bond.id}/cash-flows/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["num_payments"] > 0
        assert data["cash_flows"][-1]["principal"] == 1000.0

    def test_key_rate_durations(self, api_client, sample_bond):
        resp = api_client.get(f"/api/v1/bonds/{sample_bond.id}/key-rate-durations/")
        assert resp.status_code == 200
        data = resp.json()
        assert "key_rate_durations" in data
        assert data["total_duration"] > 0

    def test_total_return(self, api_client, sample_bond):
        resp = api_client.post(
            f"/api/v1/bonds/{sample_bond.id}/total-return/",
            {
                "purchase_clean_price": 1000.0,
                "horizon_years": 3.0,
                "reinvestment_rate": 0.04,
            },
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_return_annualized_pct" in data
        assert data["reinvested_coupons"] > 0

    def test_compare_bonds(self, api_client, sample_bond, sample_bond_data):
        # Create a second bond
        sample_bond_data["name"] = "Bond B"
        sample_bond_data.pop("isin", None)
        resp2 = api_client.post("/api/v1/bonds/", sample_bond_data, format="json")
        assert resp2.status_code == 201
        bond2_id = resp2.json()["id"]

        resp = api_client.post(
            "/api/v1/bonds/compare/",
            {"bond_ids": [str(sample_bond.id), bond2_id]},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["bonds_compared"] == 2
        assert len(data["results"]) == 2
