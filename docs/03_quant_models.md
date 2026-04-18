# QuantYield - Quantitative Models Reference

This document describes the mathematical models and conventions used
in the pricing engine, curve builder, and risk analytics.

---

## Day Count Conventions

| Convention    | Key           | Description                                  | Formula                                    |
| ------------- | ------------- | -------------------------------------------- | ------------------------------------------ |
| Actual/Actual | actual/actual | Actual calendar days over actual year length | days / (366 if leap else 365)              |
| Actual/360    | actual/360    | Actual days over fixed 360-day year          | days / 360                                 |
| Actual/365    | actual/365    | Actual days over fixed 365-day year          | days / 365                                 |
| 30/360        | 30/360        | Each month counts as 30 days                 | (360*(y2-y1) + 30*(m2-m1) + (d2-d1)) / 360 |

---

## Coupon Frequencies

| Label      | Periods Per Year | Months Between Payments |
| ---------- | ---------------- | ----------------------- |
| annual     | 1                | 12                      |
| semiannual | 2                | 6                       |
| quarterly  | 4                | 3                       |
| monthly    | 12               | 1                       |
| zero       | 0                | N/A (discount bond)     |

---

## Bond Pricing

### Dirty Price

The dirty (full) price is the present value of all future cash flows discounted at YTM:

```
P_dirty = sum( C/m / (1 + y/m)^(t_i * m) ) + F / (1 + y/m)^(T * m)
```

Where:

- C = annual coupon
- m = coupon frequency (periods per year)
- y = yield to maturity (annual, compounded at frequency m)
- t_i = time in years to the i-th coupon from settlement
- F = face value
- T = time in years to maturity from settlement

### Clean Price

```
P_clean = P_dirty - AI
```

Where AI is the accrued interest.

### Accrued Interest

```
AI = (C/m) * (t_elapsed / t_period)
```

Where t_elapsed is the day-count fraction since the last coupon date and
t_period is the full coupon period fraction.

### Zero Coupon Bond

```
P_dirty = F / (1 + y)^T
```

No accrued interest applies to zero coupon bonds.

---

## YTM Solver

YTM is solved numerically using Brent's method on the objective:

```
f(y) = P_dirty(y) - P_dirty_target = 0
```

Parameters:

- Bracket: y in [-0.5, 5.0]
- Convergence tolerance: 1e-10
- Maximum iterations: 500

Brent's method guarantees convergence when a root exists within the bracket
and does not require derivatives.

---

## Duration Measures

### Macaulay Duration

```
D_mac = (1 / P_dirty) * sum( t_i * PV_i )
```

Where PV_i is the present value of the cash flow at time t_i.

### Modified Duration

```
D_mod = D_mac / (1 + y/m)
```

This is the approximate percentage price change per unit change in yield:

```
dP/P ~ -D_mod * dy
```

### Convexity

```
C = (1 / P_dirty) * sum( t_i * (t_i + 1/m) * PV_i / (1 + y/m)^2 )
```

### Second-Order Price Approximation

```
dP ~ P * (-D_mod * dy + 0.5 * C * dy^2)
```

### DV01

Dollar value of a 1 basis point change in yield:

```
DV01 = (P(y - 0.0001) - P(y + 0.0001)) / 2
```

DV01 is always reported as a positive number.

---

## Key Rate Duration

KRD measures sensitivity to a shift at a single point on the yield curve,
holding all other rates constant. QuantYield uses triangular bumps:

```
bump_weight(t_i) = max(0, 1 - |t_i - kt|)
```

Where kt is the key tenor. This means the bump fades linearly to zero
at tenors more than 1 year away from the key tenor.

Standard key tenors: 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30 (years)

---

## Z-Spread

The Z-spread is the constant spread added to the entire spot rate curve
such that the resulting discount rates reprice the bond exactly:

```
P_dirty = sum( C/m / (1 + r(t_i) + Z)^t_i ) + F / (1 + r(T) + Z)^T
```

Solved using Brent's method on Z in [-0.5, 5.0].

---

## OAS (Option-Adjusted Spread)

For callable bonds, OAS is computed via Monte Carlo simulation:

1. Generate N short-rate paths using a lognormal model:
   `r_{t+1} = r_t * exp(-kappa * r_t * dt + sigma * sqrt(dt) * epsilon)`

2. For each path, exercise the call option at each call date if:
   `call_price <= continuation_value(r_path, spread)`

3. Price all paths at the given spread. OAS is the spread that makes
   the average simulated price equal to the market dirty price.

For non-callable bonds, OAS equals Z-spread.

| Parameter            | Default | Description                     |
| -------------------- | ------- | ------------------------------- |
| n_paths              | 500     | Monte Carlo simulation paths    |
| rate_vol             | 1%      | Short rate lognormal volatility |
| mean reversion kappa | 0.10    | Speed of mean reversion         |

---

## Total Return Analysis

Horizon total return accounts for:

1. Reinvested coupons compounded at the reinvestment rate
2. Price appreciation or depreciation to the horizon date
3. Accrued interest at the horizon

```
TV = P_horizon + sum( C_i * (1 + r_reinv)^((H - t_i)/365) )

TR_annualised = (TV / P_purchase)^(1/H) - 1
```

Where:

- TV = terminal value
- H = horizon in years
- P_purchase = purchase dirty price
- r_reinv = reinvestment rate

---

## Yield Curve Models

### Nelson-Siegel

```
y(t) = beta0 + beta1 * ((1 - e^(-t/lambda)) / (t/lambda))
             + beta2 * ((1 - e^(-t/lambda)) / (t/lambda) - e^(-t/lambda))
```

| Parameter | Economic Interpretation                      |
| --------- | -------------------------------------------- |
| beta0     | Long-run yield level (t -> infinity)         |
| beta1     | Short-run slope (negative if upward sloping) |
| beta2     | Curvature / hump magnitude                   |
| lambda1   | Decay factor (location of hump)              |

### Svensson

Extends Nelson-Siegel with a second curvature term to capture multiple humps:

```
y(t) = beta0 + beta1 * L(t, lambda1) + beta2 * C(t, lambda1) + beta3 * C(t, lambda2)
```

Where L and C are the standard NS loading functions applied at two decay rates.

### Bootstrap

Extracts zero-coupon spot rates from par yields using no-arbitrage:

```
DF(T) = (1 - coupon * sum(DF(t_k), k=1..T-1)) / (1 + coupon)
s(T) = -ln(DF(T)) / T
```

Assumes semi-annual coupon frequency (FRED convention).
Intermediate discount factors are linearly interpolated.

### Cubic Spline

Fits a natural cubic spline through all market data points with
not-a-knot boundary conditions. Exact at knot points, smooth
(C2 continuous) everywhere.

---

## Regime Detection

| Regime   | Condition                  | Description                  |
| -------- | -------------------------- | ---------------------------- |
| flat     | 2s10s in [-15, +15] bps    | Near-zero slope              |
| inverted | 2s10s < -10 bps            | Short rates above long rates |
| steep    | 2s10s > 120 bps            | Very steep upward slope      |
| humped   | 2s5s10s butterfly > 20 bps | Peak in medium tenors        |
| normal   | All other cases            | Moderate upward slope        |

The ML regime classifier uses these thresholds as labels for training
and augments them with momentum, volatility, and level features.

---

## VaR Methodologies

### Historical VaR

1. Collect DV01 for the portfolio.
2. Compute daily yield changes over the lookback window.
3. Scale: P&L*i = -DV01 * yield*change_i * 10,000.
4. For multi-day VaR, use overlapping n-day changes (not sqrt-n scaling).
5. VaR = abs(percentile(P&L, 1 - confidence_level)).
6. CVaR (Expected Shortfall) = mean of observations below VaR.

### Parametric VaR

Assumes normally distributed P&L:

```
VaR = DV01 * z * sigma * sqrt(H) * 10000
```

Where:

- z = normal quantile at the confidence level
- sigma = daily yield volatility (annualised / sqrt(252))
- H = holding period in days

---

## Scenario Analysis - Standard Set

| Scenario         | Parallel | Twist Short | Twist Long | Credit |
| ---------------- | -------- | ----------- | ---------- | ------ |
| +100bps parallel | +100     | 0           | 0          | 0      |
| -100bps parallel | -100     | 0           | 0          | 0      |
| +200bps parallel | +200     | 0           | 0          | 0      |
| -200bps parallel | -200     | 0           | 0          | 0      |
| Bear flattener   | 0        | +50         | -50        | 0      |
| Bull steepener   | 0        | -50         | +50        | 0      |
| Bear twist +50   | +50      | +25         | 0          | 0      |
| Bull twist -50   | -50      | -25         | 0          | 0      |
| +300bps shock    | +300     | 0           | 0          | 0      |
| Credit widening  | 0        | 0           | 0          | +100   |

All shifts are in basis points.
