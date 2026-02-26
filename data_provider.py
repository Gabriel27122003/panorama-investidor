from __future__ import annotations

import os
import time
from functools import lru_cache
from typing import Optional

import pandas as pd
import requests
import streamlit as st
import yfinance as yf

ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"
API_KEY = os.getenv("API_KEY", "").strip()


@lru_cache(maxsize=128)
def _get_ticker(symbol: str) -> yf.Ticker:
    """Reuse Ticker objects to avoid repetitive instantiation."""
    return yf.Ticker(symbol)


def _is_rate_limit_error(error: Exception) -> bool:
    error_message = str(error).lower()
    return "429" in error_message or "rate limit" in error_message


def _period_to_days(period: str) -> Optional[int]:
    mapping = {
        "1mo": 31,
        "3mo": 93,
        "6mo": 186,
        "1y": 366,
        "2y": 731,
        "5y": 1827,
    }
    return mapping.get(period)


def _normalize_history(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    if df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    keep_cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
    cleaned_df = df[keep_cols].dropna(how="all").sort_index()
    return cleaned_df if not cleaned_df.empty else None


def _fetch_alpha_vantage_history(ticker: str, period: str) -> Optional[pd.DataFrame]:
    if not API_KEY:
        return None

    outputsize = "full" if period in {"max", "5y", "2y", "1y"} else "compact"
    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": ticker,
        "outputsize": outputsize,
        "apikey": API_KEY,
    }

    response = requests.get(ALPHA_VANTAGE_URL, params=params, timeout=15)
    response.raise_for_status()

    payload = response.json()
    series = payload.get("Time Series (Daily)")
    if not isinstance(series, dict) or not series:
        return None

    rows = []
    for date_str, values in series.items():
        rows.append(
            {
                "Date": pd.to_datetime(date_str),
                "Open": pd.to_numeric(values.get("1. open"), errors="coerce"),
                "High": pd.to_numeric(values.get("2. high"), errors="coerce"),
                "Low": pd.to_numeric(values.get("3. low"), errors="coerce"),
                "Close": pd.to_numeric(values.get("4. close"), errors="coerce"),
                "Volume": pd.to_numeric(values.get("6. volume"), errors="coerce"),
            }
        )

    df = pd.DataFrame(rows).set_index("Date").sort_index()

    if period != "max":
        days = _period_to_days(period)
        if days:
            cutoff = pd.Timestamp.utcnow().tz_localize(None) - pd.Timedelta(days=days)
            df = df[df.index >= cutoff]

    return _normalize_history(df)


def _fetch_yfinance_history(ticker: str, period: str) -> Optional[pd.DataFrame]:
    for attempt in range(1, 4):
        try:
            ticker_obj = _get_ticker(ticker)
            df = ticker_obj.history(period=period)
            normalized = _normalize_history(df)
            if normalized is not None:
                return normalized
            return None

        except Exception as error:  # nosec: ensure app keeps running on provider failures
            if _is_rate_limit_error(error):
                return None

            if attempt == 3:
                return None

            time.sleep(0.8 * attempt)

    return None


@st.cache_data(ttl=600)
def get_market_data(ticker: str, period: str) -> Optional[pd.DataFrame]:
    """Fetch market data with provider fallback.

    Provider order:
    1) Alpha Vantage (if API_KEY is available)
    2) yfinance
    """
    normalized_ticker = ticker.strip().upper()
    if not normalized_ticker:
        return None

    try:
        alpha_data = _fetch_alpha_vantage_history(normalized_ticker, period)
        if alpha_data is not None and not alpha_data.empty:
            return alpha_data
    except Exception:
        # Fail silently to allow fallback provider.
        pass

    return _fetch_yfinance_history(normalized_ticker, period)
