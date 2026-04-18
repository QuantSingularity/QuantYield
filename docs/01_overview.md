# QuantYield - Platform Overview

QuantYield is an institutional-grade fixed income analytics platform providing
bond pricing, yield curve modelling, portfolio risk management, and AI-powered
forecasting through a clean REST API built on Django.

---

## Platform Capabilities

| Domain             | Capabilities                                                     |
| ------------------ | ---------------------------------------------------------------- |
| Bond Pricing       | Dirty/clean price, YTM solving, accrued interest, cash flows     |
| Duration Analytics | Macaulay, Modified, DV01, Key Rate Duration (10 tenors)          |
| Spread Analytics   | Z-spread, OAS (Monte Carlo), benchmark spread matrix             |
| Yield Curves       | Nelson-Siegel, Svensson, Bootstrap, Cubic Spline                 |
| Portfolio Risk     | Duration, convexity, VaR, CVaR, scenario analysis                |
| AI Forecasting     | Transformer, LSTM, AR(1) rate forecasting with uncertainty bands |
| Regime Detection   | ML ensemble (Random Forest + XGBoost) regime classification      |
| Volatility         | GARCH(1,1), EGARCH, historical volatility term structure         |
| Credit Risk        | XGBoost credit spread prediction with feature importances        |
| Curve Factors      | PCA factor decomposition (Level, Slope, Curvature)               |

---

## System Architecture

```
QuantYield/
 +-- code/
 |    +-- backend/          Django REST API (persistence, admin, CRUD)
 |    +-- ml_services/      AI and ML models (framework-agnostic)
 +-- docs/                  Full documentation suite
 +-- docker-compose.yml     Production stack (Postgres + Redis + Nginx)
 +-- nginx.conf             Reverse proxy configuration
```

The backend and ML services are deliberately decoupled. The ML services
directory is a standalone Python package that can be used independently
of Django. The Django backend imports from it but does not depend on
any ML-specific framework at the web layer.

---

## Technology Stack

| Layer              | Technology                                      |
| ------------------ | ----------------------------------------------- |
| Web Framework      | Django 5 + Django REST Framework                |
| Database           | SQLite (development) / PostgreSQL (production)  |
| Cache              | Local memory (development) / Redis (production) |
| Task Scheduling    | Management commands (cron-friendly)             |
| API Documentation  | drf-spectacular (OpenAPI 3.0, Swagger, ReDoc)   |
| ML - Deep Learning | PyTorch (Transformer, LSTM) - optional          |
| ML - Ensemble      | scikit-learn, XGBoost                           |
| ML - Volatility    | arch (GARCH, EGARCH)                            |
| ML - Statistics    | scipy, statsmodels                              |
| Numerical Core     | numpy, scipy, pandas                            |
| Deployment         | Docker Compose, uvicorn (ASGI), nginx           |

---

## Key Design Decisions

### Service Layer Separation

The `services/` package in the backend and the `ml_services/` package contain
pure Python with no Django dependencies. This means:

- Services can be tested without a running Django instance.
- ML models can be replaced, updated, or extended without touching API code.
- The same pricing engine can be embedded in notebooks or scripts.

### Graceful Degradation

Every ML feature has a fallback:

| Primary                | Fallback                      |
| ---------------------- | ----------------------------- |
| Transformer forecaster | LSTM                          |
| LSTM forecaster        | AR(1) autoregressive          |
| GARCH volatility       | Historical rolling vol        |
| XGBoost credit model   | Random Forest                 |
| ML regime classifier   | Rule-based detection          |
| FRED live data         | Representative fallback curve |

### Caching Strategy

| Resource         | TTL              | Backend              |
| ---------------- | ---------------- | -------------------- |
| Treasury curve   | 300 seconds      | Redis / local memory |
| ML model weights | Process lifetime | In-process dict      |
| Yield history    | Not cached       | Fetched on demand    |

---

## Quick Start

```bash
# 1. Install dependencies
cd code/backend
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env: set SECRET_KEY, optionally FRED_API_KEY

# 3. Run migrations and seed data
python manage.py migrate
python manage.py seed_data

# 4. Start the server
python manage.py runserver

# API docs: http://localhost:8000/docs/
# Admin UI: http://localhost:8000/admin/
```

### Docker (Full Stack)

```bash
cp .env.example .env
docker-compose up --build
# API:   http://localhost:8000
# Admin: http://localhost:8000/admin/
```

---

## API Base URLs

| Resource     | URL                 |
| ------------ | ------------------- |
| API Root     | /api/v1/            |
| Bonds        | /api/v1/bonds/      |
| Portfolios   | /api/v1/portfolios/ |
| Yield Curves | /api/v1/curves/     |
| Analytics    | /api/v1/analytics/  |
| Swagger UI   | /docs/              |
| ReDoc        | /redoc/             |
| Admin        | /admin/             |
| Health Check | /api/v1/health/     |
