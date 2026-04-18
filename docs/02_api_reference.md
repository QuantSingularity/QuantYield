# QuantYield - API Reference

All endpoints are versioned under `/api/v1/`. Responses are JSON.
Pagination uses `page` and `page_size` query parameters.

---

## Bonds

### List and Create

| Method | Endpoint       | Description                        |
| ------ | -------------- | ---------------------------------- |
| GET    | /api/v1/bonds/ | List all bonds with live analytics |
| POST   | /api/v1/bonds/ | Create a new bond                  |

#### Filter Parameters (GET /api/v1/bonds/)

| Parameter        | Type    | Example          | Description                                                      |
| ---------------- | ------- | ---------------- | ---------------------------------------------------------------- |
| issuer           | string  | "Apple"          | Case-insensitive partial match                                   |
| sector           | string  | "Technology"     | Case-insensitive partial match                                   |
| currency         | string  | "USD"            | Exact match                                                      |
| credit_rating    | string  | "AA+"            | Exact match                                                      |
| bond_type        | string  | "callable"       | One of: fixed, floating, zero_coupon, inflation_linked, callable |
| coupon_frequency | string  | "semiannual"     | One of: annual, semiannual, quarterly, monthly, zero             |
| maturity_from    | date    | "2025-01-01"     | Maturity date on or after                                        |
| maturity_to      | date    | "2035-12-31"     | Maturity date on or before                                       |
| coupon_min       | decimal | "0.03"           | Minimum coupon rate                                              |
| coupon_max       | decimal | "0.08"           | Maximum coupon rate                                              |
| search           | string  | "Treasury"       | Searches name, issuer, ISIN, sector, rating                      |
| ordering         | string  | "-maturity_date" | Prefix with - for descending                                     |
| page             | integer | 2                | Page number                                                      |
| page_size        | integer | 25               | Results per page (max 500)                                       |

#### Bond Create/Response Fields

| Field            | Type    | Required | Description                             |
| ---------------- | ------- | -------- | --------------------------------------- |
| name             | string  | Yes      | Bond name                               |
| issuer           | string  | Yes      | Issuing entity                          |
| isin             | string  | No       | 12-character ISO 6166 ISIN              |
| face_value       | decimal | No       | Par value (default 1000.00)             |
| coupon_rate      | decimal | Yes      | Annual coupon as decimal (0.05 = 5%)    |
| maturity_date    | date    | Yes      | ISO 8601 date                           |
| issue_date       | date    | Yes      | ISO 8601 date                           |
| coupon_frequency | string  | No       | Default: semiannual                     |
| bond_type        | string  | No       | Default: fixed                          |
| day_count        | string  | No       | Default: actual/actual                  |
| currency         | string  | No       | ISO 4217 code, default USD              |
| credit_rating    | string  | No       | S&P / Moody's rating                    |
| sector           | string  | No       | Industry sector                         |
| call_schedule    | array   | No       | List of {call_date, call_price} objects |

#### Analytics Fields (Response Only)

| Field             | Type    | Description                           |
| ----------------- | ------- | ------------------------------------- |
| dirty_price       | decimal | Full price including accrued interest |
| clean_price       | decimal | Flat price (dirty minus accrued)      |
| ytm               | decimal | Yield to maturity (decimal)           |
| duration          | decimal | Macaulay duration in years            |
| modified_duration | decimal | Modified duration                     |
| convexity         | decimal | Price convexity                       |
| dv01              | decimal | Dollar value of 1 basis point         |
| accrued_interest  | decimal | Accrued coupon since last payment     |
| years_to_maturity | decimal | Remaining life in years               |

---

### Single Bond Operations

| Method | Endpoint                               | Description                          |
| ------ | -------------------------------------- | ------------------------------------ |
| GET    | /api/v1/bonds/{id}/                    | Retrieve bond with analytics         |
| PATCH  | /api/v1/bonds/{id}/                    | Update name, issuer, rating, sector  |
| DELETE | /api/v1/bonds/{id}/                    | Delete bond                          |
| POST   | /api/v1/bonds/{id}/price/              | Price from yield or market price     |
| POST   | /api/v1/bonds/{id}/ytm/                | Solve YTM from clean price           |
| POST   | /api/v1/bonds/{id}/spread/             | Z-spread and OAS vs Treasury         |
| GET    | /api/v1/bonds/{id}/cash-flows/         | Full discounted cash flow schedule   |
| GET    | /api/v1/bonds/{id}/key-rate-durations/ | KRD across 10 key tenors             |
| POST   | /api/v1/bonds/{id}/total-return/       | Horizon total return analysis        |
| POST   | /api/v1/bonds/{id}/oas/                | Monte Carlo OAS for callable bonds   |
| POST   | /api/v1/bonds/compare/                 | Side-by-side comparison (2-10 bonds) |

#### POST /price/ - Request Body

| Field           | Type    | Description                      |
| --------------- | ------- | -------------------------------- |
| yield_rate      | decimal | YTM as decimal; price from yield |
| market_price    | decimal | Clean price; solves for YTM      |
| settlement_date | date    | Optional, defaults to today      |

#### POST /ytm/ - Request Body

| Field           | Type    | Description                 |
| --------------- | ------- | --------------------------- |
| clean_price     | decimal | Market clean price          |
| settlement_date | date    | Optional, defaults to today |

#### POST /total-return/ - Request Body

| Field                | Type    | Description                             |
| -------------------- | ------- | --------------------------------------- |
| purchase_clean_price | decimal | Entry clean price                       |
| horizon_years        | decimal | Investment horizon (max 30)             |
| reinvestment_rate    | decimal | Coupon reinvestment rate (default 0.04) |
| settlement_date      | date    | Optional, defaults to today             |

---

## Portfolios

| Method | Endpoint                                     | Description                        |
| ------ | -------------------------------------------- | ---------------------------------- |
| GET    | /api/v1/portfolios/                          | List all portfolios                |
| POST   | /api/v1/portfolios/                          | Create a portfolio                 |
| GET    | /api/v1/portfolios/{id}/                     | Retrieve with positions            |
| PATCH  | /api/v1/portfolios/{id}/                     | Update name, description, currency |
| DELETE | /api/v1/portfolios/{id}/                     | Delete portfolio and positions     |
| POST   | /api/v1/portfolios/{id}/positions/           | Add or update a position           |
| DELETE | /api/v1/portfolios/{id}/positions/{bond_id}/ | Remove a position                  |
| GET    | /api/v1/portfolios/{id}/analytics/           | Full risk metrics and allocations  |
| GET    | /api/v1/portfolios/{id}/pnl/                 | Unrealised P&L vs cost basis       |
| GET    | /api/v1/portfolios/{id}/duration-buckets/    | Duration by maturity bucket        |
| POST   | /api/v1/portfolios/{id}/scenarios/           | Run 10 standard rate scenarios     |
| POST   | /api/v1/portfolios/{id}/custom-scenario/     | User-defined scenario              |
| POST   | /api/v1/portfolios/{id}/var/                 | Historical and parametric VaR      |
| GET    | /api/v1/portfolios/{id}/cs01/                | Credit spread sensitivity          |

#### Analytics Response Fields

| Field                       | Type    | Description                             |
| --------------------------- | ------- | --------------------------------------- |
| total_market_value          | decimal | Sum of all position market values       |
| total_face_value            | decimal | Sum of all position face amounts        |
| portfolio_duration          | decimal | Market-value-weighted Macaulay duration |
| portfolio_modified_duration | decimal | Market-value-weighted modified duration |
| portfolio_convexity         | decimal | Market-value-weighted convexity         |
| portfolio_ytm               | decimal | Market-value-weighted YTM               |
| portfolio_dv01              | decimal | Total DV01 across all positions         |
| key_rate_durations          | object  | KRD aggregated by tenor                 |
| sector_allocation           | object  | Weight by sector                        |
| rating_allocation           | object  | Weight by credit rating                 |
| maturity_distribution       | object  | Weight by maturity bucket               |

#### VaR Request Body

| Field               | Type    | Default      | Description                     |
| ------------------- | ------- | ------------ | ------------------------------- |
| confidence_level    | decimal | 0.99         | VaR confidence (0.90 to 0.9999) |
| holding_period_days | integer | 1            | Holding period (1 to 252)       |
| method              | string  | "historical" | "historical" or "parametric"    |
| lookback_days       | integer | 252          | Historical window (21 to 2520)  |

#### Scenario Shift Fields (custom-scenario)

| Field                   | Type    | Description                            |
| ----------------------- | ------- | -------------------------------------- |
| parallel_shift_bps      | decimal | Uniform rate shift in basis points     |
| twist_short_bps         | decimal | Short-end (0-2Y) shift in basis points |
| twist_long_bps          | decimal | Long-end (10Y+) shift in basis points  |
| credit_spread_shift_bps | decimal | Credit spread widening/tightening      |

---

## Yield Curves

| Method | Endpoint                          | Description                             |
| ------ | --------------------------------- | --------------------------------------- |
| GET    | /api/v1/curves/treasury/          | Live US Treasury curve (5-minute cache) |
| GET    | /api/v1/curves/treasury/regime/   | Curve regime classification             |
| GET    | /api/v1/curves/                   | List custom curves                      |
| POST   | /api/v1/curves/                   | Create and fit a custom curve           |
| GET    | /api/v1/curves/{id}/              | Retrieve curve with fitted parameters   |
| DELETE | /api/v1/curves/{id}/              | Delete curve                            |
| POST   | /api/v1/curves/{id}/interpolate/  | Interpolate rates at arbitrary tenors   |
| POST   | /api/v1/curves/{id}/forward-rate/ | Implied forward rate between two tenors |
| POST   | /api/v1/curves/{id}/forecast/     | LSTM/AR(1) rate forecast                |

#### Treasury Curve Response Fields

| Field                | Type    | Description                                            |
| -------------------- | ------- | ------------------------------------------------------ |
| market_points        | array   | Raw par yield observations from FRED                   |
| nelson_siegel_params | object  | Fitted NS parameters (beta0, beta1, beta2, lambda1)    |
| fit_r_squared        | decimal | R-squared of Nelson-Siegel fit                         |
| fit_rmse             | decimal | Root mean square error of fit                          |
| interpolated_rates   | object  | NS rates at standard tenors                            |
| spline_rates         | object  | Cubic spline rates at standard tenors                  |
| par_yields           | object  | Par yields derived from bootstrapped spots             |
| spot_rates           | object  | Bootstrapped zero-coupon spot rates                    |
| forward_rates        | object  | Implied forward rates (1x2, 2x5, 5x10, 10x30)          |
| regime               | object  | Regime classification with slope and butterfly metrics |

#### Supported Curve Models

| Model         | Key           | Min Points | Description                              |
| ------------- | ------------- | ---------- | ---------------------------------------- |
| Nelson-Siegel | nelson_siegel | 4          | 4-parameter exponential model            |
| Svensson      | svensson      | 6          | 6-parameter extended NS with second hump |
| Bootstrap     | bootstrap     | 2          | Zero-coupon spots from par yields        |
| Cubic Spline  | cubic_spline  | 3          | Not-a-knot boundary conditions           |

---

## Analytics

| Method | Endpoint                                  | Description                           |
| ------ | ----------------------------------------- | ------------------------------------- |
| POST   | /api/v1/analytics/quick-price/            | Price a bond without storing it       |
| POST   | /api/v1/analytics/duration-approximation/ | Taylor P&L approximation              |
| GET    | /api/v1/analytics/benchmark-spreads/      | IG and HY implied yields by rating    |
| POST   | /api/v1/analytics/rolling-volatility/     | Rolling yield vol for any FRED series |
| GET    | /api/v1/analytics/yield-history/          | Rate history time series              |

#### Quick Price Request Body

| Field             | Type    | Default      | Description                  |
| ----------------- | ------- | ------------ | ---------------------------- |
| face_value        | decimal | 1000.0       | Par value                    |
| coupon_rate       | decimal | Required     | Annual coupon as decimal     |
| ytm               | decimal | Required     | Yield to maturity as decimal |
| years_to_maturity | decimal | Required     | Time to maturity in years    |
| coupon_frequency  | string  | "semiannual" | Coupon payment frequency     |
| settlement_date   | date    | Today        | Pricing date                 |

#### Duration Approximation Request Body

| Field             | Type    | Description                 |
| ----------------- | ------- | --------------------------- |
| dirty_price       | decimal | Current full price          |
| modified_duration | decimal | Bond modified duration      |
| convexity         | decimal | Bond convexity              |
| yield_change_bps  | decimal | Yield shift in basis points |

---

## Response Envelope

Errors always return a consistent JSON envelope:

```json
{
  "error": "ValidationError",
  "detail": "maturity_date must be strictly after issue_date",
  "status_code": 400
}
```

Paginated list responses:

```json
{
  "count": 42,
  "next": "http://localhost:8000/api/v1/bonds/?page=2",
  "previous": null,
  "total_pages": 2,
  "results": [...]
}
```

---

## Authentication

| Mode        | Setting                   | Description                        |
| ----------- | ------------------------- | ---------------------------------- |
| Development | AllowAny                  | All endpoints open (default)       |
| Production  | IsAuthenticatedOrReadOnly | Write operations require JWT token |

To obtain a JWT token (when auth is enabled):

```http
POST /api/token/
Content-Type: application/json

{"username": "admin", "password": "..."}
```

Response includes `access` and `refresh` tokens. Pass the access token as:

```
Authorization: Bearer <access_token>
```
