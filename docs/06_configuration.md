# QuantYield - Configuration Reference

---

## Environment Variables

All configuration is driven by environment variables loaded from the `.env`
file at project root. Copy `.env.example` to `.env` to get started.

### Core Django

| Variable               | Type    | Default             | Required    | Description                                                        |
| ---------------------- | ------- | ------------------- | ----------- | ------------------------------------------------------------------ |
| SECRET_KEY             | string  | insecure dev key    | Yes in prod | Django cryptographic secret. Generate with get_random_secret_key() |
| DEBUG                  | boolean | True                | No          | Enables debug pages and verbose errors                             |
| ALLOWED_HOSTS          | list    | \*                  | Yes in prod | Comma-separated allowed hostnames                                  |
| DJANGO_SETTINGS_MODULE | string  | quantyield.settings | No          | Settings module path                                               |

### Database

| Variable     | Type       | Default              | Description                                         |
| ------------ | ---------- | -------------------- | --------------------------------------------------- |
| DATABASE_URL | URL string | sqlite:///db.sqlite3 | Database connection string (dj-database-url format) |

Supported backends and URL formats:

| Backend           | URL Pattern                                           |
| ----------------- | ----------------------------------------------------- |
| SQLite            | sqlite:///relative/path/db.sqlite3                    |
| SQLite (absolute) | sqlite:////absolute/path/db.sqlite3                   |
| PostgreSQL        | postgres://user:pass@host:5432/dbname                 |
| PostgreSQL SSL    | postgres://user:pass@host:5432/dbname?sslmode=require |

### Cache

| Variable  | Type       | Default        | Description                             |
| --------- | ---------- | -------------- | --------------------------------------- |
| CACHE_URL | URL string | locmemcache:// | Cache backend (django-cache-url format) |

Supported backends:

| Backend         | URL Pattern                    | Notes                                   |
| --------------- | ------------------------------ | --------------------------------------- |
| Local memory    | locmemcache://                 | Per-process, not shared between workers |
| Redis           | redis://host:6379/db           | Recommended for production multi-worker |
| Redis with auth | redis://:password@host:6379/db | Password-protected Redis                |
| Dummy           | dummycache://                  | No caching, useful for testing          |

### CORS

| Variable             | Type | Default                                     | Description                                   |
| -------------------- | ---- | ------------------------------------------- | --------------------------------------------- |
| CORS_ALLOWED_ORIGINS | list | http://localhost:3000,http://localhost:5173 | Origins allowed to make cross-domain requests |

### QuantYield Platform

| Variable           | Type    | Default | Min | Max   | Description                              |
| ------------------ | ------- | ------- | --- | ----- | ---------------------------------------- |
| FRED_API_KEY       | string  | (empty) | -   | -     | FRED API key for live Treasury data      |
| CURVE_CACHE_TTL    | integer | 300     | 10  | 86400 | Treasury curve cache lifetime in seconds |
| MAX_PORTFOLIO_SIZE | integer | 500     | 1   | 5000  | Maximum bonds allowed per portfolio      |
| DEFAULT_CURRENCY   | string  | USD     | -   | -     | Default ISO 4217 currency code           |

---

## Django REST Framework Settings

Configured in `quantyield/settings/base.py`. Key settings:

| Setting                     | Development Value | Production Value          | Description                             |
| --------------------------- | ----------------- | ------------------------- | --------------------------------------- |
| DEFAULT_PERMISSION_CLASSES  | AllowAny          | IsAuthenticatedOrReadOnly | Who can access the API                  |
| DEFAULT_THROTTLE_RATES anon | 200/hour          | 200/hour                  | Rate limit for unauthenticated requests |
| DEFAULT_THROTTLE_RATES user | 2000/hour         | 2000/hour                 | Rate limit for authenticated requests   |
| PAGE_SIZE                   | 50                | 50                        | Default results per page                |
| MAX_PAGE_SIZE               | 500               | 500                       | Maximum results per page                |

---

## Installed Applications

| App               | Label      | Purpose                                                   |
| ----------------- | ---------- | --------------------------------------------------------- |
| apps.core         | core       | Health check, middleware, pagination, management commands |
| apps.bonds        | bonds      | Bond CRUD, pricing analytics, OAS, KRD                    |
| apps.portfolios   | portfolios | Portfolio management, VaR, scenario analysis              |
| apps.curves       | curves     | Yield curve fitting, interpolation, forecasting           |
| apps.analytics    | analytics  | Standalone analytics endpoints                            |
| rest_framework    | -          | Django REST Framework                                     |
| corsheaders       | -          | Cross-Origin Resource Sharing                             |
| django_filters    | -          | Advanced queryset filtering                               |
| drf_spectacular   | -          | OpenAPI 3.0 schema generation                             |
| django_extensions | -          | Development utilities                                     |

---

## Middleware Stack

Middleware is applied in the order listed. Each layer wraps the next.

| Position | Middleware               | Purpose                                             |
| -------- | ------------------------ | --------------------------------------------------- |
| 1        | SecurityMiddleware       | HTTPS redirect, security headers                    |
| 2        | CorsMiddleware           | CORS headers for browser clients                    |
| 3        | SessionMiddleware        | Session cookie support                              |
| 4        | CommonMiddleware         | URL normalisation, Content-Length                   |
| 5        | CsrfViewMiddleware       | CSRF token validation                               |
| 6        | AuthenticationMiddleware | Attach user to request                              |
| 7        | MessageMiddleware        | Django messages framework                           |
| 8        | XFrameOptionsMiddleware  | Clickjacking protection                             |
| 9        | RequestTimingMiddleware  | Log request duration, add X-Response-Time-Ms header |

---

## URL Structure

| Prefix              | Module               | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| /                   | quantyield.urls      | Root URL dispatcher            |
| /admin/             | django.contrib.admin | Admin interface                |
| /api/v1/            | apps.core.urls       | Health check, root info        |
| /api/v1/bonds/      | apps.bonds.urls      | Bond endpoints                 |
| /api/v1/portfolios/ | apps.portfolios.urls | Portfolio endpoints            |
| /api/v1/curves/     | apps.curves.urls     | Yield curve endpoints          |
| /api/v1/analytics/  | apps.analytics.urls  | Analytics endpoints            |
| /api/schema/        | drf_spectacular      | Raw OpenAPI schema (JSON/YAML) |
| /docs/              | drf_spectacular      | Swagger UI                     |
| /redoc/             | drf_spectacular      | ReDoc documentation            |

---

## Security Settings (Production)

| Setting                        | Value    | Description                          |
| ------------------------------ | -------- | ------------------------------------ |
| DEBUG                          | False    | Disables debug pages                 |
| SECURE_BROWSER_XSS_FILTER      | True     | Adds X-XSS-Protection header         |
| SECURE_CONTENT_TYPE_NOSNIFF    | True     | Adds X-Content-Type-Options: nosniff |
| X_FRAME_OPTIONS                | DENY     | Prevents clickjacking                |
| SECURE_HSTS_SECONDS            | 31536000 | 1 year HSTS                          |
| SECURE_HSTS_INCLUDE_SUBDOMAINS | True     | HSTS covers all subdomains           |

---

## Logging Configuration

| Logger        | Level | Handler | Description                           |
| ------------- | ----- | ------- | ------------------------------------- |
| root          | INFO  | console | Default catch-all                     |
| django        | INFO  | console | Django framework logs                 |
| quantyield    | DEBUG | console | Application-level logs                |
| quantyield.ml | INFO  | console | ML model training and prediction logs |

Log format: `[timestamp] LEVEL logger_name message`

To increase verbosity for ML models:

```python
# In settings
LOGGING["loggers"]["quantyield.ml"] = {
    "handlers": ["console"],
    "level": "DEBUG",
    "propagate": False,
}
```

---

## Throttle Configuration

| Throttle Class   | Scope    | Default Rate | Configurable                   |
| ---------------- | -------- | ------------ | ------------------------------ |
| AnonRateThrottle | Per IP   | 200/hour     | Yes via DEFAULT_THROTTLE_RATES |
| UserRateThrottle | Per user | 2000/hour    | Yes via DEFAULT_THROTTLE_RATES |

Rate format: `N/period` where period is second, minute, hour, or day.

Development settings override rates to 10000/hour to avoid friction
during local development and testing.

---

## Pagination

All list endpoints are paginated using `StandardResultsSetPagination`.

| Parameter | Type    | Default | Maximum       |
| --------- | ------- | ------- | ------------- |
| page      | integer | 1       | (total pages) |
| page_size | integer | 50      | 500           |

Response envelope:

| Field       | Description                  |
| ----------- | ---------------------------- |
| count       | Total number of items        |
| next        | URL of next page or null     |
| previous    | URL of previous page or null |
| total_pages | Total number of pages        |
| results     | Array of items for this page |
