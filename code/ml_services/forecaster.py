"""
QuantYield ML Services - Rate Forecaster
Three backends in order of preference:
  1. Transformer (PyTorch) - multi-head attention for sequence modelling
  2. LSTM (PyTorch)        - two-layer LSTM with dropout
  3. AR(1) (numpy only)    - autoregressive fallback, always available

All backends share the same ForecastResult output schema and are selected
automatically based on what is installed.

The trained model is cached in-process to avoid repeated training.
"""

from __future__ import annotations

import logging

import numpy as np
from ml_services.schemas import ForecastResult

logger = logging.getLogger("quantyield.ml")

# Module-level model cache: (backend, seq_len, hidden, epochs) -> state dict
_MODEL_CACHE: dict[tuple, dict] = {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def train_forecaster(
    rate_series: np.ndarray,
    seq_len: int = 20,
    hidden_size: int = 64,
    epochs: int = 60,
    lr: float = 0.001,
    force_retrain: bool = False,
    prefer_transformer: bool = True,
) -> dict:
    """
    Train (or return cached) a rate forecasting model.

    Parameters
    ----------
    rate_series:
        Historical yield series as decimal fractions (e.g. 0.045 = 4.5 pct).
    seq_len:
        Lookback window length in trading days.
    hidden_size:
        Hidden state size for LSTM / feedforward dimension for Transformer.
    epochs:
        Training epochs (only used on first call per cache key).
    lr:
        Adam learning rate.
    force_retrain:
        If True, ignore the cache and retrain from scratch.
    prefer_transformer:
        If True and PyTorch is available, try the Transformer backend first.

    Returns
    -------
    A state dict compatible with ``forecast_rates()``.
    """
    backend_tag = "transformer" if prefer_transformer else "lstm"
    cache_key = (backend_tag, seq_len, hidden_size, epochs)

    if not force_retrain and cache_key in _MODEL_CACHE:
        logger.debug("Returning cached %s model (key=%s)", backend_tag, cache_key)
        return _MODEL_CACHE[cache_key]

    state = _train_best_available(
        rate_series, seq_len, hidden_size, epochs, lr, prefer_transformer
    )
    _MODEL_CACHE[cache_key] = state
    return state


def forecast_rates(
    model_state: dict,
    rate_series: np.ndarray,
    horizon_days: int = 30,
    n_simulations: int = 500,
    confidence_level: float = 0.90,
) -> ForecastResult:
    """
    Produce a point forecast and Monte Carlo confidence bands.

    Parameters
    ----------
    model_state:
        Dict returned by ``train_forecaster()``.
    rate_series:
        Full historical series (decimal fractions).
    horizon_days:
        Number of business days to forecast.
    n_simulations:
        Monte Carlo paths for confidence band estimation.
    confidence_level:
        Symmetric confidence level, e.g. 0.90 means 5th/95th percentiles.

    Returns
    -------
    ForecastResult with point, lower, upper lists of length horizon_days.
    """
    backend = model_state.get("backend", "arima")

    if backend == "transformer":
        return _forecast_transformer(
            model_state, rate_series, horizon_days, n_simulations, confidence_level
        )
    if backend == "lstm":
        return _forecast_lstm(
            model_state, rate_series, horizon_days, n_simulations, confidence_level
        )
    return _forecast_arima(
        model_state, rate_series, horizon_days, n_simulations, confidence_level
    )


def clear_model_cache() -> None:
    """Evict all cached models (useful for testing or memory management)."""
    _MODEL_CACHE.clear()
    logger.info("Model cache cleared")


def available_backend() -> str:
    """Return the best available backend without training anything."""
    try:
        import torch  # noqa: F401

        return "transformer"
    except ImportError:
        pass
    return "arima"


# ---------------------------------------------------------------------------
# Sequence utilities
# ---------------------------------------------------------------------------


def _make_sequences(data: np.ndarray, seq_len: int):
    X, y = [], []
    for i in range(len(data) - seq_len):
        X.append(data[i : i + seq_len])
        y.append(data[i + seq_len])
    return np.array(X), np.array(y)


# ---------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------


def _train_best_available(
    rate_series, seq_len, hidden_size, epochs, lr, prefer_transformer
):
    try:
        import torch
        import torch.nn as nn

        if prefer_transformer:
            logger.info("Training Transformer forecaster (PyTorch available)")
            return _train_transformer(
                rate_series, seq_len, hidden_size, epochs, lr, torch, nn
            )
        else:
            logger.info("Training LSTM forecaster (PyTorch available)")
            return _train_lstm(rate_series, seq_len, hidden_size, epochs, lr, torch, nn)
    except ImportError:
        logger.warning("PyTorch not installed - falling back to AR(1) model")
        return _train_arima(rate_series, seq_len)


# ---------------------------------------------------------------------------
# Transformer backend
# ---------------------------------------------------------------------------


def _train_transformer(rate_series, seq_len, hidden_size, epochs, lr, torch, nn):
    mean_r = float(np.mean(rate_series))
    std_r = float(np.std(rate_series)) or 1.0
    normalized = (rate_series - mean_r) / std_r

    X, y = _make_sequences(normalized, seq_len)
    X_t = torch.FloatTensor(X).unsqueeze(-1)  # (N, seq_len, 1)
    y_t = torch.FloatTensor(y)

    class PositionalEncoding(nn.Module):
        def __init__(self, d_model: int, max_len: int = 512, dropout: float = 0.1):
            super().__init__()
            self.dropout = nn.Dropout(p=dropout)
            pe = torch.zeros(max_len, d_model)
            position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
            div_term = torch.exp(
                torch.arange(0, d_model, 2).float() * (-np.log(10000.0) / d_model)
            )
            pe[:, 0::2] = torch.sin(position * div_term)
            if d_model % 2 == 1:
                pe[:, 1::2] = torch.cos(position * div_term[: d_model // 2])
            else:
                pe[:, 1::2] = torch.cos(position * div_term)
            pe = pe.unsqueeze(0)
            self.register_buffer("pe", pe)

        def forward(self, x):
            x = x + self.pe[:, : x.size(1)]
            return self.dropout(x)

    class TransformerForecaster(nn.Module):
        def __init__(self, d_model=hidden_size, nhead=4, num_layers=2, dropout=0.1):
            super().__init__()
            self.input_proj = nn.Linear(1, d_model)
            self.pos_enc = PositionalEncoding(d_model, dropout=dropout)
            encoder_layer = nn.TransformerEncoderLayer(
                d_model=d_model,
                nhead=nhead,
                dim_feedforward=d_model * 4,
                dropout=dropout,
                batch_first=True,
            )
            self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
            self.fc = nn.Linear(d_model, 1)

        def forward(self, x):
            # x: (batch, seq_len, 1)
            x = self.input_proj(x)  # (batch, seq_len, d_model)
            x = self.pos_enc(x)
            x = self.encoder(x)  # (batch, seq_len, d_model)
            x = self.fc(x[:, -1, :])  # (batch, 1)
            return x.squeeze(-1)

    model = TransformerForecaster()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    criterion = nn.HuberLoss()  # robust to outliers vs pure MSE

    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        pred = model(X_t)
        loss = criterion(pred, y_t)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()

    return {
        "model": model,
        "mean": mean_r,
        "std": std_r,
        "seq_len": seq_len,
        "backend": "transformer",
    }


def _forecast_transformer(
    model_state, rate_series, horizon_days, n_simulations, confidence_level
):
    try:
        import torch

        model = model_state["model"]
        mean_r = model_state["mean"]
        std_r = model_state["std"]
        seq_len = model_state["seq_len"]

        model.eval()
        normalized = (rate_series - mean_r) / std_r
        seed_seq = normalized[-seq_len:].copy()

        # Point forecast
        point: list[float] = []
        cur = seed_seq.copy()
        with torch.no_grad():
            for _ in range(horizon_days):
                x = torch.FloatTensor(cur).unsqueeze(0).unsqueeze(-1)
                pred = model(x).item()
                point.append(pred * std_r + mean_r)
                cur = np.roll(cur, -1)
                cur[-1] = pred

        # Monte Carlo bands
        rng = np.random.default_rng(42)
        # Residual std from training set (used for noise injection)
        noise_std = float(np.std(np.diff(normalized))) * 0.5

        sims = []
        for _ in range(n_simulations):
            sim_seq = seed_seq.copy()
            path = []
            with torch.no_grad():
                for _ in range(horizon_days):
                    x = torch.FloatTensor(sim_seq).unsqueeze(0).unsqueeze(-1)
                    pred = model(x).item() + rng.normal(0, noise_std)
                    path.append(pred * std_r + mean_r)
                    sim_seq = np.roll(sim_seq, -1)
                    sim_seq[-1] = pred
            sims.append(path)

        sims_arr = np.array(sims)
        alpha = (1.0 - confidence_level) / 2.0
        lower = np.percentile(sims_arr, alpha * 100, axis=0).tolist()
        upper = np.percentile(sims_arr, (1 - alpha) * 100, axis=0).tolist()

        return ForecastResult(
            point=point,
            lower=lower,
            upper=upper,
            backend="transformer",
            confidence_level=confidence_level,
            horizon_days=horizon_days,
            metadata={"n_simulations": n_simulations},
        )

    except Exception as exc:
        logger.warning("Transformer forecast failed (%s), falling back to AR(1)", exc)
        fallback = _train_arima(rate_series, model_state.get("seq_len", 20))
        return _forecast_arima(
            fallback, rate_series, horizon_days, n_simulations, confidence_level
        )


# ---------------------------------------------------------------------------
# LSTM backend
# ---------------------------------------------------------------------------


def _train_lstm(rate_series, seq_len, hidden_size, epochs, lr, torch, nn):
    mean_r = float(np.mean(rate_series))
    std_r = float(np.std(rate_series)) or 1.0
    normalized = (rate_series - mean_r) / std_r

    X, y = _make_sequences(normalized, seq_len)
    X_t = torch.FloatTensor(X).unsqueeze(-1)
    y_t = torch.FloatTensor(y)

    class LSTMForecaster(nn.Module):
        def __init__(self, input_size=1, hidden=hidden_size, num_layers=2):
            super().__init__()
            self.lstm = nn.LSTM(
                input_size, hidden, num_layers, batch_first=True, dropout=0.1
            )
            self.fc = nn.Linear(hidden, 1)

        def forward(self, x):
            out, _ = self.lstm(x)
            return self.fc(out[:, -1, :]).squeeze(-1)

    model = LSTMForecaster()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    model.train()
    for _ in range(epochs):
        optimizer.zero_grad()
        pred = model(X_t)
        loss = criterion(pred, y_t)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

    return {
        "model": model,
        "mean": mean_r,
        "std": std_r,
        "seq_len": seq_len,
        "backend": "lstm",
    }


def _forecast_lstm(
    model_state, rate_series, horizon_days, n_simulations, confidence_level
):
    try:
        import torch

        model = model_state["model"]
        mean_r = model_state["mean"]
        std_r = model_state["std"]
        seq_len = model_state["seq_len"]

        model.eval()
        normalized = (rate_series - mean_r) / std_r
        seed_seq = normalized[-seq_len:].copy()
        noise_std = float(np.std(np.diff(normalized))) * 0.5

        point: list[float] = []
        cur = seed_seq.copy()
        with torch.no_grad():
            for _ in range(horizon_days):
                x = torch.FloatTensor(cur).unsqueeze(0).unsqueeze(-1)
                pred = model(x).item()
                point.append(pred * std_r + mean_r)
                cur = np.roll(cur, -1)
                cur[-1] = pred

        rng = np.random.default_rng(42)
        sims = []
        for _ in range(n_simulations):
            sim_seq = seed_seq.copy()
            path = []
            with torch.no_grad():
                for _ in range(horizon_days):
                    x = torch.FloatTensor(sim_seq).unsqueeze(0).unsqueeze(-1)
                    pred = model(x).item() + rng.normal(0, noise_std)
                    path.append(pred * std_r + mean_r)
                    sim_seq = np.roll(sim_seq, -1)
                    sim_seq[-1] = pred
            sims.append(path)

        sims_arr = np.array(sims)
        alpha = (1.0 - confidence_level) / 2.0
        lower = np.percentile(sims_arr, alpha * 100, axis=0).tolist()
        upper = np.percentile(sims_arr, (1 - alpha) * 100, axis=0).tolist()

        return ForecastResult(
            point=point,
            lower=lower,
            upper=upper,
            backend="lstm",
            confidence_level=confidence_level,
            horizon_days=horizon_days,
            metadata={"n_simulations": n_simulations},
        )
    except Exception as exc:
        logger.warning("LSTM forecast failed (%s), falling back to AR(1)", exc)
        fallback = _train_arima(rate_series, model_state.get("seq_len", 20))
        return _forecast_arima(
            fallback, rate_series, horizon_days, n_simulations, confidence_level
        )


# ---------------------------------------------------------------------------
# AR(1) fallback - always available
# ---------------------------------------------------------------------------


def _train_arima(rate_series, seq_len):
    mean_r = float(np.mean(rate_series))
    std_r = float(np.std(rate_series)) or 1.0
    diffs = np.diff(rate_series)
    phi = float(np.corrcoef(diffs[:-1], diffs[1:])[0, 1]) if len(diffs) > 1 else 0.0
    phi = float(np.clip(phi, -0.99, 0.99))
    sigma = float(np.std(diffs)) if len(diffs) > 0 else 0.001
    return {
        "model": None,
        "mean": mean_r,
        "std": std_r,
        "seq_len": seq_len,
        "backend": "arima",
        "last_value": float(rate_series[-1]),
        "phi": phi,
        "sigma": sigma,
    }


def _forecast_arima(
    model_state, rate_series, horizon_days, n_simulations, confidence_level
):
    phi = model_state.get("phi", 0.0)
    sigma = model_state.get("sigma", 0.001)
    last = model_state.get("last_value", float(rate_series[-1]))
    diffs = np.diff(rate_series)
    last_diff = float(diffs[-1]) if len(diffs) > 0 else 0.0

    point: list[float] = []
    cur_val, cur_diff = last, last_diff
    for _ in range(horizon_days):
        nxt_diff = phi * cur_diff
        cur_val = max(cur_val + nxt_diff, 0.0001)
        point.append(cur_val)
        cur_diff = nxt_diff

    rng = np.random.default_rng(42)
    sims = []
    for _ in range(n_simulations):
        sv, sd = last, last_diff
        path = []
        for _ in range(horizon_days):
            nd = phi * sd + rng.normal(0, sigma)
            sv = max(sv + nd, 0.0001)
            path.append(sv)
            sd = nd
        sims.append(path)

    sims_arr = np.array(sims)
    alpha = (1.0 - confidence_level) / 2.0
    lower = np.percentile(sims_arr, alpha * 100, axis=0).tolist()
    upper = np.percentile(sims_arr, (1 - alpha) * 100, axis=0).tolist()

    return ForecastResult(
        point=point,
        lower=lower,
        upper=upper,
        backend="arima",
        confidence_level=confidence_level,
        horizon_days=horizon_days,
        metadata={"phi": phi, "sigma": sigma},
    )
