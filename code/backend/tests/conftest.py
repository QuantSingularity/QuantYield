"""
pytest-django configuration and shared fixtures.

Django must be configured before any DRF or app imports.
This file handles that setup regardless of where pytest is invoked from.
"""

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Ensure the backend directory is on sys.path so all app/service imports work.
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent  # code/backend/
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# ---------------------------------------------------------------------------
# 2. Configure Django settings before anything else is imported.
#    pytest.ini sets DJANGO_SETTINGS_MODULE when pytest is run from
#    code/backend/, but running from the project root bypasses pytest.ini,
#    so we set the env var explicitly here as a guaranteed fallback.
# ---------------------------------------------------------------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quantyield.settings")

import django

django.setup()

from datetime import date

# ---------------------------------------------------------------------------
# 3. Only now is it safe to import DRF and app code.
# ---------------------------------------------------------------------------
import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def sample_bond_data():
    return {
        "name": "Test Treasury 5%",
        "issuer": "US Treasury",
        "face_value": 1000.0,
        "coupon_rate": 0.05,
        "maturity_date": "2030-06-15",
        "issue_date": "2020-06-15",
        "coupon_frequency": "semiannual",
        "bond_type": "fixed",
        "day_count": "actual/actual",
        "currency": "USD",
        "credit_rating": "AAA",
        "sector": "Government",
        "call_schedule": [],
    }


@pytest.fixture
def sample_bond(db, sample_bond_data):
    from apps.bonds.models import Bond

    return Bond.objects.create(
        name=sample_bond_data["name"],
        issuer=sample_bond_data["issuer"],
        face_value=sample_bond_data["face_value"],
        coupon_rate=sample_bond_data["coupon_rate"],
        maturity_date=date(2030, 6, 15),
        issue_date=date(2020, 6, 15),
        coupon_frequency=sample_bond_data["coupon_frequency"],
        bond_type=sample_bond_data["bond_type"],
        day_count=sample_bond_data["day_count"],
        currency=sample_bond_data["currency"],
        credit_rating=sample_bond_data["credit_rating"],
        sector=sample_bond_data["sector"],
    )


@pytest.fixture
def sample_portfolio(db, sample_bond):
    from apps.portfolios.models import Portfolio, Position

    port = Portfolio.objects.create(
        name="Test Portfolio",
        description="Test",
        currency="USD",
    )
    Position.objects.create(
        portfolio=port,
        bond=sample_bond,
        face_amount=100000,
        purchase_price=1000.0,
        purchase_date=date(2023, 1, 1),
    )
    return port
