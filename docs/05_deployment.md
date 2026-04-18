# QuantYield - Deployment Guide

---

## Development Setup

### Prerequisites

| Tool   | Minimum Version |
| ------ | --------------- |
| Python | 3.12            |
| pip    | 23.0            |
| Git    | Any recent      |

### Steps

```bash
# Clone the repository
git clone <repository_url>
cd QuantYield

# Create virtual environment
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\activate           # Windows

# Install backend dependencies
pip install -r code/backend/requirements.txt

# Install ML services dependencies (optional but recommended)
pip install -r code/ml_services/requirements.txt

# Configure environment
cp .env.example code/backend/.env
# Edit code/backend/.env with your settings

# Run migrations
cd code/backend
python manage.py migrate

# Seed sample data
python manage.py seed_data

# Create admin user
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

---

## Environment Variables

| Variable             | Required | Default              | Description                                  |
| -------------------- | -------- | -------------------- | -------------------------------------------- |
| SECRET_KEY           | Yes      | (insecure)           | Django secret key, must change in production |
| DEBUG                | No       | True                 | Enable debug mode                            |
| DATABASE_URL         | No       | sqlite:///db.sqlite3 | Database connection string                   |
| CACHE_URL            | No       | locmemcache://       | Cache backend URL                            |
| ALLOWED_HOSTS        | No       | \*                   | Comma-separated allowed hostnames            |
| CORS_ALLOWED_ORIGINS | No       | localhost:3000,5173  | Allowed CORS origins                         |
| FRED_API_KEY         | No       | (empty)              | FRED API key for live Treasury data          |
| CURVE_CACHE_TTL      | No       | 300                  | Treasury curve cache TTL in seconds          |
| MAX_PORTFOLIO_SIZE   | No       | 500                  | Maximum bonds per portfolio                  |
| DEFAULT_CURRENCY     | No       | USD                  | Default currency code                        |

### Database URL Formats

| Database       | URL Format                                                |
| -------------- | --------------------------------------------------------- |
| SQLite         | sqlite:///db.sqlite3                                      |
| PostgreSQL     | postgres://user:password@host:5432/dbname                 |
| PostgreSQL SSL | postgres://user:password@host:5432/dbname?sslmode=require |

### Cache URL Formats

| Cache           | URL Format                         |
| --------------- | ---------------------------------- |
| Local memory    | locmemcache://                     |
| Redis           | redis://localhost:6379/1           |
| Redis with auth | redis://:password@localhost:6379/1 |

---

## Docker Compose (Production-like)

The included `docker-compose.yml` starts a full production stack:

| Service | Image                   | Port | Role                         |
| ------- | ----------------------- | ---- | ---------------------------- |
| db      | postgres:16-alpine      | 5432 | Primary database             |
| redis   | redis:7-alpine          | 6379 | Cache and sessions           |
| api     | (built from Dockerfile) | 8000 | Django / uvicorn             |
| nginx   | nginx:1.25-alpine       | 80   | Reverse proxy + static files |

### Starting the Stack

```bash
# From the project root
cp .env.example .env
# Edit .env with your configuration

docker-compose up --build

# In another terminal, to run management commands:
docker-compose exec api python manage.py createsuperuser
docker-compose exec api python manage.py sync_treasury
```

### Stopping the Stack

```bash
docker-compose down            # Stops containers, keeps volumes
docker-compose down -v         # Stops containers, deletes volumes
```

---

## Production Checklist

| Item          | Action                                                                                                                    |
| ------------- | ------------------------------------------------------------------------------------------------------------------------- |
| SECRET_KEY    | Generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" |
| DEBUG         | Set to False                                                                                                              |
| ALLOWED_HOSTS | Set to your domain name(s)                                                                                                |
| DATABASE_URL  | Point to PostgreSQL                                                                                                       |
| CACHE_URL     | Point to Redis                                                                                                            |
| HTTPS         | Configure SSL in nginx, set SECURE_SSL_REDIRECT=True                                                                      |
| FRED_API_KEY  | Register at fred.stlouisfed.org for live data                                                                             |
| Static files  | Run python manage.py collectstatic                                                                                        |
| Superuser     | Create admin account after first deploy                                                                                   |
| Seed data     | Run python manage.py seed_data if desired                                                                                 |

---

## Django Settings Modules

| Environment | Module                          | Activated By                   |
| ----------- | ------------------------------- | ------------------------------ |
| Development | quantyield.settings.development | DJANGO_SETTINGS_MODULE env var |
| Production  | quantyield.settings.production  | DJANGO_SETTINGS_MODULE env var |
| Default     | quantyield.settings             | Fallback to base settings      |

Switch settings:

```bash
export DJANGO_SETTINGS_MODULE=quantyield.settings.production
python manage.py runserver
```

---

## Management Commands

| Command                                        | Description                                    |
| ---------------------------------------------- | ---------------------------------------------- |
| python manage.py migrate                       | Apply database migrations                      |
| python manage.py seed_data                     | Populate with sample bonds, portfolios, curves |
| python manage.py seed_data --clear             | Clear all data and re-seed                     |
| python manage.py sync_treasury                 | Refresh Treasury curve cache from FRED         |
| python manage.py sync_treasury --save-snapshot | Save today's curve snapshot to DB              |
| python manage.py createsuperuser               | Create admin user                              |
| python manage.py collectstatic                 | Collect static files to STATIC_ROOT            |

### Scheduling sync_treasury

Add to cron for automated cache refresh (every 5 minutes during market hours):

```
*/5 9-17 * * 1-5 /path/to/.venv/bin/python /path/to/code/backend/manage.py sync_treasury
```

---

## Running Tests

```bash
cd code/backend

# Install test dependencies
pip install pytest pytest-django

# Run all 64 tests
pytest

# Service-layer tests only (no database required)
pytest tests/test_pricing.py tests/test_curve_builder.py -v

# API tests
pytest tests/test_bonds_api.py tests/test_portfolios_api.py -v

# With coverage report
pip install pytest-cov
pytest --cov=services --cov=apps --cov-report=html
# Open htmlcov/index.html in a browser
```

---

## Performance Tuning

| Setting                | Recommendation                            |
| ---------------------- | ----------------------------------------- |
| uvicorn workers        | 2 \* CPU_count + 1                        |
| PostgreSQL connections | max 100 per uvicorn instance              |
| Redis max memory       | 256MB with allkeys-lru eviction           |
| CURVE_CACHE_TTL        | 300s during market hours, 3600s overnight |
| Pagination page_size   | Default 50; avoid more than 200 per page  |

---

## Monitoring and Health

The `/api/v1/health/` endpoint returns:

| Field        | Description                       |
| ------------ | --------------------------------- |
| status       | "ok" or error message             |
| version      | Application version               |
| python       | Python version string             |
| django       | Django version                    |
| numpy        | numpy version                     |
| database     | "ok" or "error"                   |
| fred_api_key | True if FRED key is configured    |
| forecaster   | "transformer", "lstm", or "arima" |
