from typing import Optional

import pandas as pd
import streamlit as st
import yfinance as yf


@st.cache_data(ttl=3600)
def get_data(symbol: str, period: str) -> Optional[pd.DataFrame]:
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)

        if df.empty:
            raise ValueError("DataFrame vazio")

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        keep_cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
        return df[keep_cols].dropna(how="all")

    except Exception:
        return None


def get_data_with_fallback(symbol: str, period: str) -> Optional[pd.DataFrame]:
    data = get_data(symbol, period)
    if data is not None and not data.empty:
        return data

    if period != "6mo":
        fallback_data = get_data(symbol, "6mo")
        if fallback_data is not None and not fallback_data.empty:
            return fallback_data

    return None
