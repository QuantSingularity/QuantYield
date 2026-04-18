# QuantYield

Institutional-grade fixed income analytics platform. Provides bond pricing,
yield curve modelling, portfolio risk management, scenario analysis, and
AI-powered rate forecasting through a clean versioned REST API.

---

## Repository Structure

```
QuantYield/
 +-- code/
 |    +-- backend/          Django REST API with full persistence
 |    +-- ml_services/      AI and ML models (framework-agnostic)
 +-- docs/                  Complete documentation suite
 +-- docker-compose.yml     Production Docker stack
 +-- nginx.conf             Reverse proxy configuration
 +-- .env.example           Environment variable template
```

---

## Core Capabilities

| Domain            | Features                                                                   |
| ----------------- | -------------------------------------------------------------------------- |
| Bond Pricing      | Dirty/clean price, YTM solver (Brent), accrued interest, cash flows        |
| Duration          | Macaulay, Modified, DV01, Key Rate Duration across 10 tenors               |
| Spread Analytics  | Z-spread, Monte Carlo OAS for callable bonds                               |
| Yield Curves      | Nelson-Siegel, Svensson, Bootstrap, Cubic Spline                           |
| Portfolio Risk    | Market value, duration, convexity, DV01, sector/rating/maturity allocation |
| Scenario Analysis | 10 standard scenarios + custom parallel/twist/credit shifts                |
| VaR               | Historical (overlapping windows) and parametric VaR/CVaR                   |
| AI Forecasting    | Transformer, LSTM, AR(1) with Monte Carlo confidence bands                 |
| Regime Detection  | ML ensemble classification (normal, inverted, flat, steep, humped)         |
| Volatility        | GARCH(1,1), EGARCH, historical vol term structure                          |
| Credit Spreads    | XGBoost OAS prediction by rating, sector, and macro environment            |
| Curve Factors     | PCA decomposition (Level, Slope, Curvature) with factor sensitivity        |

---

## Quick Start

```bash
# Install dependencies
cd code/backend
pip install -r requirements.txt

# Configure environment
cp ../../.env.example .env

# Set up database and sample data
python manage.py migrate
python manage.py seed_data

# Start the server
python manage.py runserver
```

API docs at http://localhost:8000/docs/
Admin at http://localhost:8000/admin/

### Docker (Full Stack)

```bash
cp .env.example .env
docker-compose up --build
```

---

## Documentation

| Document                 | Description                                               |
| ------------------------ | --------------------------------------------------------- |
| docs/01_overview.md      | Architecture, capabilities, technology stack              |
| docs/02_api_reference.md | Complete endpoint reference with request/response schemas |
| docs/03_quant_models.md  | Mathematical models: pricing, duration, curves, VaR       |
| docs/04_ml_ai_models.md  | AI models: Transformer, LSTM, GARCH, XGBoost, PCA         |
| docs/05_deployment.md    | Production deployment, Docker, environment setup          |
| docs/06_configuration.md | Full configuration reference for all settings             |
| docs/07_data_models.md   | Database schema: all tables, fields, constraints, indexes |
| docs/08_testing.md       | Test suite, running tests, adding tests, CI configuration |

---

## Technology Stack

| Layer          | Technology                                      |
| -------------- | ----------------------------------------------- |
| Web Framework  | Django 5 + Django REST Framework                |
| Database       | SQLite (development) / PostgreSQL (production)  |
| Cache          | Local memory (development) / Redis (production) |
| Deep Learning  | PyTorch - Transformer and LSTM (optional)       |
| ML Ensemble    | scikit-learn, XGBoost                           |
| Volatility     | arch library (GARCH, EGARCH)                    |
| Numerical Core | numpy, scipy, pandas                            |
| API Docs       | drf-spectacular (OpenAPI 3.0)                   |
| Deployment     | Docker Compose, uvicorn, nginx                  |

---

## Test Results

```
64 tests, 0 failures

Service layer (no database):
  test_pricing.py        19 passed
  test_curve_builder.py  17 passed

API integration:
  test_bonds_api.py      16 passed
  test_portfolios_api.py 12 passed
```

Run tests:

```bash
cd code/backend
pytest
```

---

## License

MIT License. See LICENSE for full text.
