# QuantYield - Testing Guide

---

## Test Suite Overview

| File                         | Tests | Scope                          | Database |
| ---------------------------- | ----- | ------------------------------ | -------- |
| tests/test_pricing.py        | 19    | Service layer - pricing engine | No       |
| tests/test_curve_builder.py  | 17    | Service layer - curve builder  | No       |
| tests/test_bonds_api.py      | 16    | API integration - bonds        | Yes      |
| tests/test_portfolios_api.py | 12    | API integration - portfolios   | Yes      |
| Total                        | 64    |                                |          |

All 64 tests pass with the current codebase.

---

## Running Tests

### Basic Execution

```bash
cd code/backend

# All tests
pytest

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Show print output
pytest -s
```

### Targeted Execution

```bash
# Service layer only (fast, no DB setup)
pytest tests/test_pricing.py tests/test_curve_builder.py -v

# API layer only
pytest tests/test_bonds_api.py tests/test_portfolios_api.py -v

# Single test class
pytest tests/test_pricing.py::TestYTMSolver -v

# Single test
pytest tests/test_pricing.py::TestYTMSolver::test_round_trips -v
```

### With Coverage

```bash
pip install pytest-cov

# Coverage for services and apps
pytest --cov=services --cov=apps --cov-report=term-missing

# HTML report
pytest --cov=services --cov=apps --cov-report=html
# Open htmlcov/index.html
```

---

## Test Architecture

### Service Layer Tests (No Database)

Tests in `test_pricing.py` and `test_curve_builder.py` operate entirely on
Python dataclasses (BondSchema, CurvePointSchema) with no Django or database
dependency. They run fast and can be used in CI without a database.

```python
# Example: no database marker, uses BondSchema directly
@pytest.fixture
def treasury_bond():
    return BondSchema(
        name="US Treasury 5%",
        coupon_rate=0.05,
        maturity_date=date(2030, 6, 15),
        ...
    )

class TestYTMSolver:
    def test_round_trips(self, treasury_bond):
        for ytm_in in [0.02, 0.04, 0.05, 0.07, 0.10]:
            clean = ps.clean_price_from_yield(treasury_bond, ytm_in, SETTLE)
            ytm_out = ps.ytm_from_clean_price(treasury_bond, clean, SETTLE)
            assert abs(ytm_out - ytm_in) < 1e-8
```

### API Integration Tests (Database)

Tests in `test_bonds_api.py` and `test_portfolios_api.py` use the
`@pytest.mark.django_db` marker and DRF's `APIClient`. The test database
is created and torn down automatically by pytest-django.

```python
@pytest.mark.django_db
class TestBondCRUD:
    def test_create_bond(self, api_client, sample_bond_data):
        resp = api_client.post("/api/v1/bonds/", sample_bond_data, format="json")
        assert resp.status_code == 201
```

---

## Shared Fixtures (conftest.py)

| Fixture          | Scope         | Description                           |
| ---------------- | ------------- | ------------------------------------- |
| api_client       | function      | DRF APIClient instance                |
| sample_bond_data | function      | Dict of valid bond fields             |
| sample_bond      | function (DB) | Persisted Bond ORM instance           |
| sample_portfolio | function (DB) | Persisted Portfolio with one Position |

---

## Test Categories

### Pricing Tests

| Class           | Tests | What is Verified                                               |
| --------------- | ----- | -------------------------------------------------------------- |
| TestDirtyPrice  | 5     | Price direction, zero coupon, dirty = clean + AI               |
| TestYTMSolver   | 2     | Round-trip accuracy, par YTM                                   |
| TestDuration    | 4     | Mac vs Mod, duration ordering, DV01 sign, convexity sign       |
| TestKRD         | 2     | KRD keys present, positive values                              |
| TestZSpread     | 1     | Near-zero spread for risk-free benchmark bond                  |
| TestCashFlows   | 3     | PV sum equals dirty price, principal in last flow, zero coupon |
| TestTotalReturn | 2     | Positive return, reinvestment rate monotonicity                |

### Curve Builder Tests

| Class               | Tests | What is Verified                                           |
| ------------------- | ----- | ---------------------------------------------------------- |
| TestNelsonSiegel    | 3     | R-squared > 0.8, beta0 economic range, interpolation range |
| TestSvensson        | 2     | R-squared > 0.8, better or equal fit vs NS                 |
| TestBootstrap       | 3     | Spot rates returned, rates in valid range, interpolation   |
| TestCubicSpline     | 2     | Exact at knots, smooth interpolation                       |
| TestForwardRate     | 2     | Formula correctness, invalid tenor rejection               |
| TestParYield        | 2     | Reasonable values at 10Y and 1Y                            |
| TestRegimeDetection | 3     | Normal, inverted, and flat regime classification           |

### Bond API Tests

| Class             | Tests | What is Verified                                                                          |
| ----------------- | ----- | ----------------------------------------------------------------------------------------- |
| TestBondCRUD      | 9     | Create, list, get, patch, delete, filtering, search, ISIN validation, maturity validation |
| TestBondAnalytics | 7     | Price from yield, price from market, YTM, cash flows, KRD, total return, compare          |

### Portfolio API Tests

| Class                  | Tests | What is Verified                                                            |
| ---------------------- | ----- | --------------------------------------------------------------------------- |
| TestPortfolioCRUD      | 4     | Create, list, get, delete                                                   |
| TestPortfolioPositions | 2     | Add position, remove position                                               |
| TestPortfolioAnalytics | 6     | Analytics, scenarios, custom scenario direction, P&L, duration buckets, VaR |

---

## Adding New Tests

### Testing a New Service Function

```python
# tests/test_pricing.py

class TestNewFeature:
    def test_something(self, treasury_bond):
        result = ps.new_function(treasury_bond, ...)
        assert result > 0
        assert isinstance(result, float)
```

No database marker required for service-layer tests.

### Testing a New API Endpoint

```python
# tests/test_bonds_api.py

@pytest.mark.django_db
class TestNewEndpoint:
    def test_endpoint(self, api_client, sample_bond):
        resp = api_client.post(
            f"/api/v1/bonds/{sample_bond.id}/new-action/",
            {"param": "value"},
            format="json",
        )
        assert resp.status_code == 200
        assert "expected_field" in resp.json()
```

---

## Continuous Integration

The test suite is designed for CI environments. Key properties:

| Property             | Detail                                             |
| -------------------- | -------------------------------------------------- |
| No external services | FRED API falls back to synthetic data              |
| No network calls     | All HTTP calls are either mocked or use fallbacks  |
| Deterministic        | Random number generators use fixed seeds (seed=42) |
| Fast                 | Service tests run in under 5 seconds               |
| Isolated             | Each test gets a fresh database transaction        |

### Recommended CI Configuration

```yaml
# .github/workflows/test.yml
steps:
  - uses: actions/checkout@v4
  - uses: actions/setup-python@v5
    with:
      python-version: "3.12"
  - run: pip install -r code/backend/requirements.txt pytest pytest-django
  - run: cd code/backend && pytest --tb=short
```

---

## pytest.ini Options

| Option                 | Value               | Description                         |
| ---------------------- | ------------------- | ----------------------------------- |
| DJANGO_SETTINGS_MODULE | quantyield.settings | Settings used for testing           |
| python_files           | tests/test\_\*.py   | Test file discovery pattern         |
| python_classes         | Test\*              | Test class discovery pattern        |
| python_functions       | test\_\*            | Test function discovery pattern     |
| addopts --tb=short     | always on           | Concise traceback format            |
| addopts -v             | always on           | Verbose test names                  |
| addopts --reuse-db     | always on           | Reuse test DB between runs (faster) |
