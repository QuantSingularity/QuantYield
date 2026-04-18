# QuantYield - AI and ML Models Reference

The `ml_services` package provides five independent AI and machine learning
models that enhance the platform with predictive and analytical capabilities.

---

## Overview of ML Models

| Model               | File                   | Primary Use             | Fallback               |
| ------------------- | ---------------------- | ----------------------- | ---------------------- |
| Rate Forecaster     | forecaster.py          | Yield rate prediction   | AR(1) autoregressive   |
| Regime Classifier   | regime_classifier.py   | Curve regime detection  | Rule-based thresholds  |
| Volatility Model    | volatility_model.py    | Vol forecasting (GARCH) | Historical rolling vol |
| Credit Spread Model | credit_spread_model.py | OAS prediction          | Rating-based table     |
| PCA Factor Model    | pca_factor_model.py    | Curve decomposition     | N/A (pure math)        |

---

## 1. Rate Forecaster (`forecaster.py`)

Predicts future interest rate levels with Monte Carlo uncertainty bands.

### Backend Hierarchy

| Priority | Backend     | Requirements | Strengths                                     |
| -------- | ----------- | ------------ | --------------------------------------------- |
| 1        | Transformer | PyTorch      | Multi-head attention, long-range dependencies |
| 2        | LSTM        | PyTorch      | Recurrent memory, proven for time series      |
| 3        | AR(1)       | numpy only   | Always available, interpretable               |

### Transformer Architecture

| Layer               | Configuration                    |
| ------------------- | -------------------------------- |
| Input projection    | Linear(1, d_model)               |
| Positional encoding | Sinusoidal, max length 512       |
| Encoder layers      | 2 TransformerEncoderLayer blocks |
| Attention heads     | 4                                |
| Feedforward dim     | d_model \* 4                     |
| Output              | Linear(d_model, 1)               |
| Loss function       | HuberLoss (robust to outliers)   |
| Optimizer           | AdamW with cosine LR schedule    |

### LSTM Architecture

| Layer         | Configuration      |
| ------------- | ------------------ |
| LSTM layers   | 2 with 0.1 dropout |
| Hidden size   | 64 (configurable)  |
| Output        | Linear(hidden, 1)  |
| Loss function | MSELoss            |
| Optimizer     | Adam               |

### Training Parameters

| Parameter     | Default | Description                            |
| ------------- | ------- | -------------------------------------- |
| seq_len       | 20      | Lookback window in trading days        |
| hidden_size   | 64      | Hidden state dimension                 |
| epochs        | 60      | Training epochs                        |
| learning_rate | 0.001   | Initial Adam learning rate             |
| n_simulations | 500     | Monte Carlo paths for confidence bands |

### Uncertainty Quantification

Monte Carlo simulation injects Gaussian noise proportional to the
historical residual standard deviation at each forecast step.
Default confidence level is 90% (5th and 95th percentiles).

### Usage

```python
from ml_services import train_forecaster, forecast_rates
import numpy as np

# Historical rate series (decimal form)
rates = np.array([0.044, 0.045, 0.046, ...])

# Train (or retrieve cached) model
model_state = train_forecaster(rates, prefer_transformer=True)

# Produce forecast
result = forecast_rates(model_state, rates, horizon_days=30)

print(result.backend)          # "transformer", "lstm", or "arima"
print(result.point[:5])        # First 5 point forecast values
print(result.lower[:5])        # Lower confidence band
print(result.upper[:5])        # Upper confidence band
```

---

## 2. Regime Classifier (`regime_classifier.py`)

Classifies the current yield curve regime using a supervised ML ensemble
trained on macro and curve shape features.

### Regime Labels

| Label    | Description            | Typical 2s10s Spread       |
| -------- | ---------------------- | -------------------------- |
| normal   | Moderate upward slope  | 30 to 120 bps              |
| inverted | Short rates above long | Below -10 bps              |
| flat     | Near-zero slope        | -15 to +20 bps             |
| steep    | Extreme positive slope | Above 120 bps              |
| humped   | Peak in 5-7Y sector    | 2s5s10s butterfly > 25 bps |

### Feature Set

| Feature                | Description                   |
| ---------------------- | ----------------------------- |
| level_10y_pct          | 10Y rate in percentage points |
| slope_2s10s_bps        | 10Y minus 2Y spread in bps    |
| slope_3m2y_bps         | 2Y minus 3M spread in bps     |
| slope_10s30s_bps       | 30Y minus 10Y spread in bps   |
| butterfly_bps          | 2s5s10s butterfly in bps      |
| r2y_pct                | 2Y rate in percentage points  |
| r10y_pct               | 10Y rate in percentage points |
| vol_21d_annualised_pct | Rolling 21-day annualised vol |
| momentum_5d_bps        | 5-day rate change in bps      |

### Ensemble Models

| Model             | Library            | Notes                             |
| ----------------- | ------------------ | --------------------------------- |
| Random Forest     | scikit-learn       | 200 trees, balanced class weights |
| Gradient Boosting | scikit-learn       | 150 trees, LR 0.05                |
| XGBoost           | xgboost (optional) | 200 trees, column subsampling     |

Final probability is the unweighted average across all ensemble members.

### Usage

```python
from ml_services import classify_regime
import numpy as np

spot_rates = {0.25: 0.053, 2.0: 0.049, 5.0: 0.046, 10.0: 0.045, 30.0: 0.046}
rate_history = np.array([0.044, 0.045, 0.046, ...])  # recent 10Y rates

result = classify_regime(spot_rates, rate_history)

print(result.regime)              # "normal"
print(result.probability)         # 0.82
print(result.all_probabilities)   # {"normal": 0.82, "inverted": 0.05, ...}
print(result.features)            # Engineered features used for classification
```

---

## 3. Volatility Model (`volatility_model.py`)

Forecasts yield volatility using GARCH-family models.

### Model Types

| Model       | Key        | Description                            |
| ----------- | ---------- | -------------------------------------- |
| GARCH(1,1)  | garch      | Symmetric variance clustering model    |
| EGARCH(1,1) | egarch     | Asymmetric: captures leverage effect   |
| Historical  | historical | Mean-reverting rolling window fallback |

### GARCH(1,1) Specification

```
sigma_t^2 = omega + alpha * epsilon_{t-1}^2 + beta * sigma_{t-1}^2
```

Estimated via maximum likelihood with Student's t innovations
(heavy-tailed distribution, better for financial data).

### EGARCH(1,1) Specification

```
ln(sigma_t^2) = omega + alpha * (|z_{t-1}| - E|z|) + gamma * z_{t-1} + beta * ln(sigma_{t-1}^2)
```

The gamma parameter captures the leverage effect: negative rate shocks
tend to increase volatility more than positive shocks of equal magnitude.

### Output

All volatility figures are annualised (sqrt(252) scaling) and expressed
as percentage points for interpretability.

### Volatility Term Structure

```python
from ml_services import volatility_term_structure
import numpy as np

rates = np.array([...])
result = volatility_term_structure(rates, windows=[5, 10, 21, 63, 126, 252])
# {"5d": 0.42, "21d": 0.58, "63d": 0.61, "252d": 0.67}
```

---

## 4. Credit Spread Model (`credit_spread_model.py`)

Predicts bond OAS in basis points using bond characteristics and
macro factors.

### Features

| Feature           | Type  | Description                            |
| ----------------- | ----- | -------------------------------------- |
| level_10y_pct     | Macro | 10Y Treasury rate                      |
| slope_2s10s_bps   | Macro | Yield curve slope                      |
| butterfly_bps     | Macro | Curvature                              |
| yield_vol_21d_pct | Macro | Implied volatility proxy               |
| rating_score      | Bond  | Ordinal credit quality (1=AAA, 13=CCC) |
| years_to_maturity | Bond  | Remaining life                         |
| coupon_rate_pct   | Bond  | Annual coupon percentage               |
| sector\_\*        | Bond  | One-hot encoded sector (13 categories) |

### Rating Score Mapping

| Rating | Score |
| ------ | ----- |
| AAA    | 1.0   |
| AA+    | 1.5   |
| AA     | 2.0   |
| AA-    | 2.5   |
| A+     | 3.0   |
| A      | 3.5   |
| A-     | 4.0   |
| BBB+   | 5.0   |
| BBB    | 5.5   |
| BBB-   | 6.0   |
| BB+    | 7.0   |
| BB     | 7.5   |
| BB-    | 8.0   |
| B+     | 9.0   |
| B      | 9.5   |
| B-     | 10.0  |
| CCC+   | 11.0  |
| CCC    | 12.0  |
| NR     | 6.0   |

### Ensemble Prediction

The ensemble averages predictions from Random Forest, Gradient Boosting,
and XGBoost (if available). The 80% confidence interval is derived from
the spread across ensemble members.

### Usage

```python
from ml_services import predict_credit_spread

result = predict_credit_spread(
    rating="A+",
    years_to_maturity=7.5,
    coupon_rate=0.045,
    level_10y=0.045,
    slope_2s10s_bps=55.0,
    butterfly_bps=12.0,
    yield_vol_21d_pct=0.62,
    sector="Technology",
)

print(result.predicted_spread_bps)          # 78.4
print(result.confidence_interval_lower_bps) # 61.2
print(result.confidence_interval_upper_bps) # 95.6
print(result.feature_importances)           # top features by importance
```

---

## 5. PCA Factor Model (`pca_factor_model.py`)

Decomposes yield curve movements into orthogonal risk factors following
the Litterman-Scheinkman (1991) framework.

### The Three Classic Factors

| Factor    | PC  | Explained Variance | Economic Meaning               |
| --------- | --- | ------------------ | ------------------------------ |
| Level     | PC1 | ~88%               | Parallel shift of entire curve |
| Slope     | PC2 | ~9%                | Short vs long end divergence   |
| Curvature | PC3 | ~2%                | Belly vs wings (butterfly)     |

Together these three factors typically explain more than 99% of
yield curve variation.

### Factor Loadings Interpretation

| Factor    | Short End (<2Y) | Medium (5Y) | Long End (>10Y) |
| --------- | --------------- | ----------- | --------------- |
| Level     | Positive        | Positive    | Positive        |
| Slope     | Negative        | Neutral     | Positive        |
| Curvature | Positive        | Negative    | Positive        |

### Applications

**Hedging:** Construct factor-neutral portfolios by matching
Factor 1, 2, and 3 exposures to zero.

**Stress testing:** Apply a 2-standard-deviation shock to a single
factor and observe the resulting curve shift using `factor_sensitivity()`.

**Regime detection:** Monitor rolling PCA factor scores for structural
breaks using `rolling_pca_factors()`.

### Usage

```python
from ml_services import decompose_curve, factor_sensitivity
import numpy as np

# curve_matrix: shape (n_observations, n_tenors)
curve_matrix = np.random.normal(0.045, 0.005, (500, 10))

result = decompose_curve(curve_matrix, n_components=3)

print(result.factor_names)            # ["Level", "Slope", "Curvature"]
print(result.explained_variance_ratio) # [0.88, 0.09, 0.02]

# Sensitivity to a 1-std-dev Level shift
sens = factor_sensitivity(result, "Level", shift_std=1.0)
# {0.25: 0.003, 0.5: 0.003, 1.0: 0.004, ...}
```

---

## Model Caching

All models that require training are cached in-process to avoid
redundant computation:

| Model               | Cache Scope      | Cache Key                               |
| ------------------- | ---------------- | --------------------------------------- |
| Rate Forecaster     | Process lifetime | (backend, seq_len, hidden_size, epochs) |
| Regime Classifier   | Process lifetime | Module-level singleton                  |
| Credit Spread Model | Process lifetime | Module-level singleton                  |
| GARCH               | Not cached       | Fitted per request                      |
| PCA                 | Not cached       | Computed per request                    |

To force retraining:

```python
from ml_services import clear_model_cache, train_forecaster
clear_model_cache()
model = train_forecaster(rates, force_retrain=True)
```
