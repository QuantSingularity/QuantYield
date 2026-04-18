# QuantYield - Data Models Reference

This document describes the Django ORM models, their fields, relationships,
and the constraints enforced at the database level.

---

## Entity Relationship Summary

```
Bond (1) ----< (0..*) CallSchedule
Bond (1) ----< (0..*) Position
Portfolio (1) ----< (1..*) Position
YieldCurve (1) ----< (2..*) CurveDataPoint
```

---

## Bond

**Table:** `bonds_bond`

Stores the economic terms of a fixed income instrument. Analytics (price,
duration, yield) are computed on demand from stored terms and are never
persisted.

| Column           | Type          | Nullable | Default       | Description                       |
| ---------------- | ------------- | -------- | ------------- | --------------------------------- |
| id               | UUID          | No       | uuid4()       | Primary key                       |
| isin             | VARCHAR(12)   | Yes      | NULL          | ISO 6166 ISIN, unique             |
| name             | VARCHAR(255)  | No       | -             | Bond display name                 |
| issuer           | VARCHAR(255)  | No       | -             | Issuing entity                    |
| face_value       | DECIMAL(18,6) | No       | 1000.000000   | Par value                         |
| coupon_rate      | DECIMAL(10,8) | No       | -             | Annual rate as decimal            |
| maturity_date    | DATE          | No       | -             | Final maturity                    |
| issue_date       | DATE          | No       | -             | Original issue date               |
| settlement_date  | DATE          | Yes      | NULL          | Optional settlement date override |
| coupon_frequency | VARCHAR(20)   | No       | semiannual    | Payment frequency                 |
| bond_type        | VARCHAR(20)   | No       | fixed         | Instrument type                   |
| day_count        | VARCHAR(20)   | No       | actual/actual | Day count convention              |
| currency         | VARCHAR(3)    | No       | USD           | ISO 4217 currency code            |
| credit_rating    | VARCHAR(10)   | Yes      | NULL          | Credit rating string              |
| sector           | VARCHAR(100)  | Yes      | NULL          | Industry sector                   |
| description      | TEXT          | Yes      | NULL          | Free-text notes                   |
| created_at       | TIMESTAMP     | No       | NOW()         | Record creation time              |
| updated_at       | TIMESTAMP     | No       | NOW()         | Last modification time            |

### Enumerated Values

**coupon_frequency**

| Value      | Label           |
| ---------- | --------------- |
| annual     | Annual          |
| semiannual | Semi-Annual     |
| quarterly  | Quarterly       |
| monthly    | Monthly         |
| zero       | Zero (Discount) |

**bond_type**

| Value            | Label            |
| ---------------- | ---------------- |
| fixed            | Fixed Rate       |
| floating         | Floating Rate    |
| zero_coupon      | Zero Coupon      |
| inflation_linked | Inflation Linked |
| callable         | Callable         |

**day_count**

| Value         | Label         |
| ------------- | ------------- |
| actual/actual | Actual/Actual |
| actual/360    | Actual/360    |
| actual/365    | Actual/365    |
| 30/360        | 30/360        |

### Constraints

| Constraint           | Rule                                            |
| -------------------- | ----------------------------------------------- |
| maturity_after_issue | maturity_date must be strictly after issue_date |
| isin_format          | Must match [A-Z]{2}[A-Z0-9]{9}[0-9]             |
| zero_coupon_rate     | Zero coupon bonds must have coupon_rate = 0     |
| coupon_rate_range    | 0 <= coupon_rate <= 1                           |
| face_value_positive  | face_value > 0                                  |

### Indexes

| Index               | Columns       | Type  |
| ------------------- | ------------- | ----- |
| bonds_bond_issuer   | issuer        | BTree |
| bonds_bond_type     | bond_type     | BTree |
| bonds_bond_sector   | sector        | BTree |
| bonds_bond_rating   | credit_rating | BTree |
| bonds_bond_currency | currency      | BTree |
| bonds_bond_maturity | maturity_date | BTree |

---

## CallSchedule

**Table:** `bonds_callschedule`

Stores individual call dates for callable bonds. A bond with no rows in
this table is treated as a bullet bond by the OAS engine.

| Column     | Type          | Nullable | Default  | Description                                    |
| ---------- | ------------- | -------- | -------- | ---------------------------------------------- |
| id         | UUID          | No       | uuid4()  | Primary key                                    |
| bond_id    | UUID          | No       | FK       | Foreign key to Bond                            |
| call_date  | DATE          | No       | -        | Date on which the call option may be exercised |
| call_price | DECIMAL(10,4) | No       | 100.0000 | Call price as percentage of face value         |

### Constraints

| Constraint          | Rule                                |
| ------------------- | ----------------------------------- |
| unique_bond_date    | (bond_id, call_date) must be unique |
| call_price_positive | call_price > 0                      |

---

## Portfolio

**Table:** `portfolios_portfolio`

Stores metadata for a named collection of bond positions. Market value and
risk metrics are computed dynamically from positions.

| Column      | Type         | Nullable | Default | Description                 |
| ----------- | ------------ | -------- | ------- | --------------------------- |
| id          | UUID         | No       | uuid4() | Primary key                 |
| name        | VARCHAR(255) | No       | -       | Portfolio name              |
| description | TEXT         | Yes      | NULL    | Optional description        |
| currency    | VARCHAR(3)   | No       | USD     | Base currency for reporting |
| created_at  | TIMESTAMP    | No       | NOW()   | Record creation time        |
| updated_at  | TIMESTAMP    | No       | NOW()   | Last modification time      |

### Indexes

| Index                         | Columns  |
| ----------------------------- | -------- |
| portfolios_portfolio_currency | currency |
| portfolios_portfolio_name     | name     |

---

## Position

**Table:** `portfolios_position`

Represents a single bond holding within a portfolio.

| Column         | Type          | Nullable | Default | Description                              |
| -------------- | ------------- | -------- | ------- | ---------------------------------------- |
| id             | UUID          | No       | uuid4() | Primary key                              |
| portfolio_id   | UUID          | No       | FK      | Foreign key to Portfolio                 |
| bond_id        | UUID          | No       | FK      | Foreign key to Bond (PROTECT on delete)  |
| face_amount    | DECIMAL(20,4) | No       | -       | Notional face amount held                |
| purchase_price | DECIMAL(12,6) | Yes      | NULL    | Entry clean price per unit of face value |
| purchase_date  | DATE          | Yes      | NULL    | Date position was established            |
| notes          | TEXT          | Yes      | NULL    | Position-level notes                     |
| created_at     | TIMESTAMP     | No       | NOW()   | Record creation time                     |
| updated_at     | TIMESTAMP     | No       | NOW()   | Last modification time                   |

### Constraints

| Constraint            | Rule                                             |
| --------------------- | ------------------------------------------------ |
| unique_portfolio_bond | (portfolio_id, bond_id) must be unique           |
| face_amount_positive  | face_amount > 0                                  |
| bond_protected        | Bond cannot be deleted while held in a portfolio |

---

## YieldCurve

**Table:** `curves_yieldcurve`

Stores a fitted yield curve with its model parameters. The raw data
points that were used to fit the curve are stored in CurveDataPoint.

| Column     | Type         | Nullable | Default       | Description             |
| ---------- | ------------ | -------- | ------------- | ----------------------- |
| id         | UUID         | No       | uuid4()       | Primary key             |
| name       | VARCHAR(255) | No       | -             | Curve name              |
| curve_type | VARCHAR(20)  | No       | government    | Curve category          |
| currency   | VARCHAR(3)   | No       | USD           | Currency                |
| model      | VARCHAR(20)  | No       | nelson_siegel | Fitting model           |
| as_of_date | DATE         | No       | -             | Observation date        |
| parameters | JSON         | No       | {}            | Fitted model parameters |
| r_squared  | FLOAT        | Yes      | NULL          | Goodness-of-fit metric  |
| rmse       | FLOAT        | Yes      | NULL          | Root mean square error  |
| created_at | TIMESTAMP    | No       | NOW()         | Record creation time    |
| updated_at | TIMESTAMP    | No       | NOW()         | Last modification time  |

### Parameters JSON Structure by Model

| Model         | Parameters                                                                                           |
| ------------- | ---------------------------------------------------------------------------------------------------- |
| nelson_siegel | {"beta0": float, "beta1": float, "beta2": float, "lambda1": float}                                   |
| svensson      | {"beta0": float, "beta1": float, "beta2": float, "beta3": float, "lambda1": float, "lambda2": float} |
| bootstrap     | {"spot_rates": {"tenor_string": float, ...}}                                                         |
| cubic_spline  | {"model": "cubic_spline_fitted"}                                                                     |

### Enumerated Values

**curve_type**

| Value      | Label      |
| ---------- | ---------- |
| government | Government |
| swap       | Swap       |
| corporate  | Corporate  |
| ois        | OIS        |

**model**

| Value         | Label         |
| ------------- | ------------- |
| nelson_siegel | Nelson-Siegel |
| svensson      | Svensson      |
| bootstrap     | Bootstrap     |
| cubic_spline  | Cubic Spline  |

### Indexes

| Index                      | Columns    |
| -------------------------- | ---------- |
| curves_yieldcurve_asof     | as_of_date |
| curves_yieldcurve_type     | curve_type |
| curves_yieldcurve_currency | currency   |

---

## CurveDataPoint

**Table:** `curves_curvedatapoint`

Stores individual tenor/rate observations used to fit a YieldCurve.

| Column     | Type        | Nullable | Default | Description                          |
| ---------- | ----------- | -------- | ------- | ------------------------------------ |
| id         | UUID        | No       | uuid4() | Primary key                          |
| curve_id   | UUID        | No       | FK      | Foreign key to YieldCurve            |
| tenor      | FLOAT       | No       | -       | Tenor in years                       |
| rate       | FLOAT       | No       | -       | Par yield or spot rate as decimal    |
| instrument | VARCHAR(50) | Yes      | NULL    | Source instrument label (e.g. DGS10) |

### Constraints

| Constraint         | Rule                             |
| ------------------ | -------------------------------- |
| unique_curve_tenor | (curve_id, tenor) must be unique |

---

## Service Layer Schemas (Not Persisted)

These are Python dataclasses used only within the service layer.
They mirror the ORM models but have no database representation.

### BondSchema

| Field            | Type                         | Description              |
| ---------------- | ---------------------------- | ------------------------ |
| name             | str                          | Bond name                |
| issuer           | str                          | Issuer                   |
| face_value       | float                        | Par value                |
| coupon_rate      | float                        | Annual coupon as decimal |
| maturity_date    | date                         | Maturity                 |
| issue_date       | date                         | Issue date               |
| coupon_frequency | str                          | Frequency key            |
| bond_type        | str                          | Type key                 |
| day_count        | str                          | Convention key           |
| currency         | str                          | Currency code            |
| credit_rating    | str or None                  | Rating                   |
| sector           | str or None                  | Sector                   |
| settlement_date  | date or None                 | Override                 |
| call_schedule    | list[CallDateSchema] or None | Call dates               |

### ScenarioShiftSchema

| Field                   | Type  | Default | Description         |
| ----------------------- | ----- | ------- | ------------------- |
| parallel_shift_bps      | float | 0.0     | Parallel rate shift |
| twist_short_bps         | float | 0.0     | Short-end shift     |
| twist_long_bps          | float | 0.0     | Long-end shift      |
| credit_spread_shift_bps | float | 0.0     | Credit spread shift |

### ScenarioResultSchema

| Field                  | Type  | Description                        |
| ---------------------- | ----- | ---------------------------------- |
| scenario_name          | str   | Label                              |
| pnl                    | float | Absolute P&L                       |
| pnl_pct                | float | P&L as fraction of portfolio value |
| new_portfolio_value    | float | Post-shift market value            |
| duration_contribution  | float | Duration-driven P&L component      |
| convexity_contribution | float | Convexity-driven P&L component     |
