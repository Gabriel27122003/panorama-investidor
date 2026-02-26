from __future__ import annotations

import time
from functools import lru_cache
from typing import Optional

import pandas as pd
import streamlit as st
import yfinance as yf


@lru_cache(maxsize=128)
def _get_ticker(symbol: str) -> yf.Ticker:
    """Reuse Ticker objects to avoid repetitive instantiation."""
    return yf.Ticker(symbol)


def _is_rate_limit_error(error: Exception) -> bool:
    error_message = str(error).lower()
    return "429" in error_message or "rate limit" in error_message


@st.cache_data(ttl=600)
def get_market_data(ticker: str, period: str) -> Optional[pd.DataFrame]:
    """Fetch market data with caching and retry.

    Returns None when Yahoo Finance is unavailable or when no data is found.
    """
    normalized_ticker = ticker.strip().upper()
    if not normalized_ticker:
        return None

    for attempt in range(1, 4):
        try:
            ticker_obj = _get_ticker(normalized_ticker)
            df = ticker_obj.history(period=period)

            if df.empty:
                return None

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            keep_cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
            cleaned_df = df[keep_cols].dropna(how="all")
            return cleaned_df if not cleaned_df.empty else None

        except Exception as error:  # nosec: ensure app keeps running on provider failures
            if _is_rate_limit_error(error):
                return None

            if attempt == 3:
                return None

            time.sleep(0.8 * attempt)

    return None
