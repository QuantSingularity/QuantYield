# QuantYield — Django Edition

**Institutional-grade fixed income analytics platform**, converted from FastAPI to Django REST Framework with a full persistence layer, admin interface, JWT authentication, caching, and comprehensive test suite.

---

## What's New vs the Original FastAPI Version

| Feature         | FastAPI (original)                   | Django (this version)                  |
| --------------- | ------------------------------------ | -------------------------------------- |
| Database        | ❌ In-memory dicts (lost on restart) | ✅ SQLite (dev) / PostgreSQL (prod)    |
| Admin UI        | ❌ None                              | ✅ Full Django Admin                   |
| Authentication  | ❌ Open                              | ✅ JWT + Session (optional)            |
| Caching         | ⚠️ Custom TTL dict                   | ✅ Django cache (Redis in prod)        |
| Pagination      | ❌ None                              | ✅ Page-number pagination              |
| Filtering       | ❌ None                              | ✅ django-filter on all list endpoints |
| Search          | ❌ None                              | ✅ Full-text search                    |
| Rate limiting   | ❌ None                              | ✅ DRF throttling                      |
| API versioning  | ❌ None                              | ✅ `/api/v1/` prefix                   |
| OpenAPI docs    | ✅ Auto (FastAPI)                    | ✅ drf-spectacular (Swagger + ReDoc)   |
| Management cmds | ❌ None                              | ✅ `seed_data`, `sync_treasury`        |
| Tests           | ⚠️ Partial                           | ✅ 64 tests, all passing               |
| Migrations      | ❌ None                              | ✅ Full Django migrations              |

---

## Architecture

```
quantyield_django/
├── manage.py
├── quantyield/                    # Django project package
│   ├── settings/
│   │   ├── base.py                # Shared settings
│   │   ├── development.py         # Dev overrides
│   │   └── production.py          # Production hardening
│   ├── urls.py                    # Root URL config
│   ├── asgi.py                    # ASGI entry point (uvicorn)
│   └── wsgi.py                    # WSGI entry point (gunicorn)
│
├── apps/
│   ├── core/                      # Health check, middleware, exceptions
│   │   └── management/commands/
│   │       ├── seed_data.py       # Populate DB with sample bonds/portfolios
│   │       └── sync_treasury.py   # Refresh Treasury curve from FRED
│   ├── bonds/                     # Bond CRUD + analytics (ORM + ViewSets)
│   ├── portfolios/                # Portfolio CRUD + risk analytics
│   ├── curves/                    # Yield curve CRUD + forecasting
│   └── analytics/                 # Standalone analytics (quick-price, vol, spreads)
│
├── services/                      # Pure-Python quant service layer (no Django deps)
│   ├── schemas.py                 # Dataclasses (BondSchema, CurvePointSchema, etc.)
│   ├── pricing.py                 # Full pricing engine
│   ├── curve_builder.py           # NS, Svensson, Bootstrap, Cubic Spline
│   ├── risk.py                    # Portfolio risk, VaR, scenarios, P&L
│   ├── data_feed.py               # FRED API + synthetic fallbacks
│   └── ml_forecaster.py           # LSTM / AR(1) rate forecasting
│
└── tests/
    ├── conftest.py                 # Shared fixtures
    ├── test_pricing.py             # 19 service-layer pricing tests
    ├── test_curve_builder.py       # 17 curve builder tests
    ├── test_bonds_api.py           # Bond API integration tests
    └── test_portfolios_api.py      # Portfolio API integration tests
```

---

## Quick Start

### 1. Clone & Install

```bash
git clone <repo>
cd quantyield_django
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY
# Optionally add FRED_API_KEY for live Treasury data
```

### 3. Run Migrations & Seed Data

```bash
python manage.py migrate
python manage.py seed_data         # loads 8 bonds, 2 portfolios, 3 curves
python manage.py createsuperuser   # for admin access
```

### 4. Start the Development Server

```bash
python manage.py runserver
# or with uvicorn for async support:
uvicorn quantyield.asgi:application --reload
```

### 5. Explore

| URL                                    | Description               |
| -------------------------------------- | ------------------------- |
| `http://localhost:8000/docs/`          | Swagger UI (full OpenAPI) |
| `http://localhost:8000/redoc/`         | ReDoc                     |
| `http://localhost:8000/admin/`         | Django Admin              |
| `http://localhost:8000/api/v1/`        | API root                  |
| `http://localhost:8000/api/v1/health/` | Health check              |

---

## Docker Compose (Production-like)

```bash
# Copy and configure environment
cp .env.example .env
# Set SECRET_KEY, FRED_API_KEY (optional), etc.

docker-compose up --build
# API:   http://localhost:8000
# Admin: http://localhost:8000/admin/
```

The compose stack runs PostgreSQL + Redis + Django (uvicorn, 4 workers) + Nginx.

---

## API Reference

### Bonds — `/api/v1/bonds/`

| Method   | Endpoint                                 | Description                            |
| -------- | ---------------------------------------- | -------------------------------------- |
| `GET`    | `/api/v1/bonds/`                         | List all bonds (paginated, filterable) |
| `POST`   | `/api/v1/bonds/`                         | Create a bond                          |
| `GET`    | `/api/v1/bonds/{id}/`                    | Get bond with live analytics           |
| `PATCH`  | `/api/v1/bonds/{id}/`                    | Update metadata (name, rating, sector) |
| `DELETE` | `/api/v1/bonds/{id}/`                    | Delete bond                            |
| `POST`   | `/api/v1/bonds/{id}/price/`              | Price from yield or market price       |
| `POST`   | `/api/v1/bonds/{id}/ytm/`                | Solve YTM from clean price             |
| `POST`   | `/api/v1/bonds/{id}/spread/`             | Z-spread + OAS vs live Treasury        |
| `GET`    | `/api/v1/bonds/{id}/cash-flows/`         | Discounted cash flow schedule          |
| `GET`    | `/api/v1/bonds/{id}/key-rate-durations/` | KRD profile                            |
| `POST`   | `/api/v1/bonds/{id}/total-return/`       | Horizon total return                   |
| `POST`   | `/api/v1/bonds/{id}/oas/`                | Monte Carlo OAS (callable bonds)       |
| `POST`   | `/api/v1/bonds/compare/`                 | Side-by-side analytics (up to 10)      |

**Filter parameters** (on `GET /api/v1/bonds/`):

- `issuer`, `sector`, `currency`, `credit_rating`, `bond_type`, `coupon_frequency`
- `maturity_from`, `maturity_to` (date range)
- `coupon_min`, `coupon_max`
- `search` (name, issuer, ISIN, sector, rating)
- `ordering` (name, maturity_date, coupon_rate, created_at)

### Portfolios — `/api/v1/portfolios/`

| Method             | Endpoint                                       | Description                         |
| ------------------ | ---------------------------------------------- | ----------------------------------- |
| `GET/POST`         | `/api/v1/portfolios/`                          | List / create                       |
| `GET/PATCH/DELETE` | `/api/v1/portfolios/{id}/`                     | Retrieve / update / delete          |
| `POST`             | `/api/v1/portfolios/{id}/positions/`           | Add / update a position             |
| `DELETE`           | `/api/v1/portfolios/{id}/positions/{bond_id}/` | Remove position                     |
| `GET`              | `/api/v1/portfolios/{id}/analytics/`           | Full risk metrics, KRD, allocations |
| `GET`              | `/api/v1/portfolios/{id}/pnl/`                 | Unrealised P&L vs purchase price    |
| `GET`              | `/api/v1/portfolios/{id}/duration-buckets/`    | Duration contribution by bucket     |
| `POST`             | `/api/v1/portfolios/{id}/scenarios/`           | Run 10 standard rate scenarios      |
| `POST`             | `/api/v1/portfolios/{id}/custom-scenario/`     | Custom rate shift                   |
| `POST`             | `/api/v1/portfolios/{id}/var/`                 | Historical + parametric VaR/CVaR    |
| `GET`              | `/api/v1/portfolios/{id}/cs01/`                | Credit spread sensitivity           |

### Curves — `/api/v1/curves/`

| Method       | Endpoint                            | Description                           |
| ------------ | ----------------------------------- | ------------------------------------- |
| `GET`        | `/api/v1/curves/treasury/`          | Live US Treasury curve (cached 5 min) |
| `GET`        | `/api/v1/curves/treasury/regime/`   | Curve regime detection                |
| `GET/POST`   | `/api/v1/curves/`                   | List / create custom curves           |
| `GET/DELETE` | `/api/v1/curves/{id}/`              | Retrieve / delete                     |
| `POST`       | `/api/v1/curves/{id}/interpolate/`  | Interpolate rates at arbitrary tenors |
| `POST`       | `/api/v1/curves/{id}/forward-rate/` | Implied forward rate                  |
| `POST`       | `/api/v1/curves/{id}/forecast/`     | LSTM / AR(1) rate forecast            |

**Supported curve models**: `nelson_siegel`, `svensson`, `bootstrap`, `cubic_spline`

### Analytics — `/api/v1/analytics/`

| Method | Endpoint                                    | Description                           |
| ------ | ------------------------------------------- | ------------------------------------- |
| `POST` | `/api/v1/analytics/quick-price/`            | Price a bond without storing it       |
| `POST` | `/api/v1/analytics/duration-approximation/` | Taylor P&L approximation              |
| `GET`  | `/api/v1/analytics/benchmark-spreads/`      | IG/HY implied yields by rating        |
| `POST` | `/api/v1/analytics/rolling-volatility/`     | Rolling yield vol for any FRED series |
| `GET`  | `/api/v1/analytics/yield-history/`          | Raw rate history for charting         |

---

## Quant Capabilities

### Pricing Engine (`services/pricing.py`)

- **Day count conventions**: Actual/Actual, Actual/360, Actual/365, 30/360
- **Coupon frequencies**: Annual, Semi-annual, Quarterly, Monthly, Zero
- **YTM solver**: Brent's method with 1e-10 convergence tolerance
- **Accrued interest**: Full period arithmetic with relativedelta month handling
- **Duration**: Macaulay, Modified, DV01
- **Convexity**: Second-order price sensitivity
- **Key Rate Durations**: Triangular bump at 10 standard tenors
- **Z-spread**: Constant OAS spread to full spot curve
- **Total Return**: Reinvested coupon horizon analysis
- **Callable OAS**: Monte Carlo simulation with lognormal short-rate model

### Curve Builder (`services/curve_builder.py`)

- **Nelson-Siegel**: 4-parameter fit with R² / RMSE diagnostics
- **Svensson**: 6-parameter extension for humped curves
- **Bootstrap**: Zero-coupon spot rates from semi-annual par yields (FRED convention)
- **Cubic Spline**: `not-a-knot` boundary conditions, exact at market points
- **Forward rates**: Implied forward from any two spot tenors
- **Par yields**: Derived from bootstrapped spot rates
- **Regime detection**: Normal / Inverted / Flat / Humped / Steep with butterfly spread

### Risk Analytics (`services/risk.py`)

- **Portfolio metrics**: Market-value-weighted duration, convexity, DV01, YTM
- **10 standard scenarios**: ±100/200/300bps parallel, bear/bull flattener/steepener, credit widening
- **Custom scenarios**: Arbitrary parallel, twist (short/long), and credit spread shifts
- **Historical VaR**: DV01-scaled, overlapping n-day windows, CVaR/ES
- **Parametric VaR**: Normal distribution, sqrt(t) scaling
- **Duration bucket report**: 6-bucket maturity decomposition
- **CS01**: Credit spread sensitivity per position
- **Portfolio P&L**: Unrealised P&L vs cost basis with per-position detail

### ML Forecaster (`services/ml_forecaster.py`)

- **LSTM** (requires PyTorch): 2-layer LSTM with dropout, Monte Carlo confidence bands
- **AR(1) fallback**: Autoregressive model when PyTorch is absent
- **In-process caching**: Model trained once per process lifetime

---

## Running Tests

```bash
# All 64 tests
pytest

# Service layer only (no DB required)
pytest tests/test_pricing.py tests/test_curve_builder.py -v

# API tests
pytest tests/test_bonds_api.py tests/test_portfolios_api.py -v

# With coverage
pip install pytest-cov
pytest --cov=services --cov=apps --cov-report=html
```

---

## Management Commands

```bash
# Populate DB with representative bond data
python manage.py seed_data

# Clear and re-seed
python manage.py seed_data --clear

# Refresh Treasury curve cache from FRED
python manage.py sync_treasury

# Save today's Treasury snapshot to DB
python manage.py sync_treasury --save-snapshot
```

---

## Environment Variables

| Variable               | Default                     | Description                                  |
| ---------------------- | --------------------------- | -------------------------------------------- |
| `SECRET_KEY`           | (insecure dev key)          | Django secret key — **change in production** |
| `DEBUG`                | `True`                      | Debug mode                                   |
| `DATABASE_URL`         | `sqlite:///db.sqlite3`      | Database connection string                   |
| `CACHE_URL`            | `locmemcache://`            | Cache backend URL                            |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000,...` | Allowed CORS origins                         |
| `FRED_API_KEY`         | `""`                        | FRED API key for live Treasury data          |
| `CURVE_CACHE_TTL`      | `300`                       | Treasury curve cache TTL (seconds)           |
| `MAX_PORTFOLIO_SIZE`   | `500`                       | Max bonds per portfolio                      |
| `DEFAULT_CURRENCY`     | `USD`                       | Default currency                             |

---

## License

MIT — see `LICENSE` for details.
