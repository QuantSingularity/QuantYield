"""
QuantYield — Data Feed
Live US Treasury par yields from FRED API with Django cache backend.
Graceful fallback to representative synthetic curve and history.
"""

import logging
from datetime import date, timedelta
from typing import Optional

import httpx
import numpy as np
import pandas as pd
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger("quantyield")

FRED_SERIES: dict[str, float] = {
    "DGS1MO": 0.0833,
    "DGS3MO": 0.25,
    "DGS6MO": 0.5,
    "DGS1": 1.0,
    "DGS2": 2.0,
    "DGS3": 3.0,
    "DGS5": 5.0,
    "DGS7": 7.0,
    "DGS10": 10.0,
    "DGS20": 20.0,
    "DGS30": 30.0,
}

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
TREASURY_CURVE_CACHE_KEY = "quantyield:treasury_curve"


async def fetch_treasury_curve(as_of_date: Optional[date] = None) -> list[dict]:
    """
    Fetch US Treasury par yields. Uses Django cache (Redis in prod).
    Falls back to hardcoded representative curve if FRED key absent.
    """
    if as_of_date is None:
        cached = cache.get(TREASURY_CURVE_CACHE_KEY)
        if cached is not None:
            return cached

    fred_key = getattr(settings, "FRED_API_KEY", "")
    if not fred_key:
        result = _fallback_treasury_curve(as_of_date)
        if as_of_date is None:
            ttl = getattr(settings, "CURVE_CACHE_TTL", 300)
            cache.set(TREASURY_CURVE_CACHE_KEY, result, ttl)
        return result

    obs_date = as_of_date or date.today()
    start_date = obs_date - timedelta(days=7)
    points: list[dict] = []

    async with httpx.AsyncClient(timeout=10.0) as client:
        for series_id, tenor in FRED_SERIES.items():
            try:
                resp = await client.get(
                    FRED_BASE_URL,
                    params={
                        "series_id": series_id,
                        "api_key": fred_key,
                        "file_type": "json",
                        "observation_start": start_date.isoformat(),
                        "observation_end": obs_date.isoformat(),
                        "sort_order": "desc",
                        "limit": "1",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                obs = data.get("observations", [])
                if obs and obs[0]["value"] != ".":
                    rate = float(obs[0]["value"]) / 100.0
                    points.append(
                        {"tenor": tenor, "rate": rate, "instrument": series_id}
                    )
            except Exception as exc:
                logger.debug("FRED fetch error for %s: %s", series_id, exc)
                continue

    if not points:
        points = _fallback_treasury_curve(as_of_date)

    points = sorted(points, key=lambda x: x["tenor"])

    if as_of_date is None:
        ttl = getattr(settings, "CURVE_CACHE_TTL", 300)
        cache.set(TREASURY_CURVE_CACHE_KEY, points, ttl)

    return points


def _fallback_treasury_curve(as_of_date: Optional[date] = None) -> list[dict]:
    """Representative US Treasury par yield curve (used when FRED key absent)."""
    fallback = {
        0.0833: 0.0526,
        0.25: 0.0532,
        0.5: 0.0530,
        1.0: 0.0515,
        2.0: 0.0489,
        3.0: 0.0472,
        5.0: 0.0456,
        7.0: 0.0452,
        10.0: 0.0445,
        20.0: 0.0471,
        30.0: 0.0459,
    }
    return [
        {"tenor": t, "rate": r, "instrument": "fallback"} for t, r in fallback.items()
    ]


async def fetch_yield_history(
    series_id: str = "DGS10",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    lookback_days: int = 252,
) -> pd.DataFrame:
    """
    Fetch daily yield history from FRED.  Falls back to synthetic data.
    """
    fred_key = getattr(settings, "FRED_API_KEY", "")
    end = end_date or date.today()
    start = start_date or (end - timedelta(days=lookback_days))

    if not fred_key:
        return _synthetic_yield_history(start, end)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                FRED_BASE_URL,
                params={
                    "series_id": series_id,
                    "api_key": fred_key,
                    "file_type": "json",
                    "observation_start": start.isoformat(),
                    "observation_end": end.isoformat(),
                    "sort_order": "asc",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        records = [
            {"date": o["date"], "rate": float(o["value"]) / 100.0}
            for o in data.get("observations", [])
            if o["value"] != "."
        ]

        if records:
            df = pd.DataFrame(records)
            df["date"] = pd.to_datetime(df["date"])
            return df.set_index("date").sort_index()

    except Exception as exc:
        logger.warning("FRED history fetch failed: %s", exc)

    return _synthetic_yield_history(start, end)


def _synthetic_yield_history(start: date, end: date) -> pd.DataFrame:
    dates = pd.date_range(start=start, end=end, freq="B")
    n = len(dates)
    rng = np.random.default_rng(42)
    rates = 0.045 + np.cumsum(rng.normal(0, 0.0005, n))
    rates = np.clip(rates, 0.001, 0.15)
    return pd.DataFrame({"rate": rates}, index=dates)


def compute_yield_changes(df: pd.DataFrame, column: str = "rate") -> np.ndarray:
    return df[column].diff().dropna().values


def compute_rolling_volatility(
    df: pd.DataFrame, window: int = 21, column: str = "rate"
) -> pd.Series:
    """Annualised rolling yield volatility."""
    daily_changes = df[column].diff()
    return daily_changes.rolling(window).std() * np.sqrt(252)


async def fetch_bond_price_history(
    ticker: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> pd.DataFrame:
    try:
        import yfinance as yf

        end = end_date or date.today()
        start = start_date or (end - timedelta(days=365))
        data = yf.download(
            ticker, start=start.isoformat(), end=end.isoformat(), progress=False
        )
        if not data.empty:
            return data[["Close"]].rename(columns={"Close": "price"})
    except Exception:
        pass

    end = end_date or date.today()
    start = start_date or (end - timedelta(days=365))
    dates = pd.date_range(start=start, end=end, freq="B")
    n = len(dates)
    rng = np.random.default_rng(99)
    prices = 100 + np.cumsum(rng.normal(0, 0.1, n))
    return pd.DataFrame({"price": prices}, index=dates)
