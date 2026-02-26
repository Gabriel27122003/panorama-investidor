from __future__ import annotations

import os
from typing import Optional

import pandas as pd
import requests
import streamlit as st

ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"
API_KEY = os.getenv("ALPHA_VANTAGE_KEY")

_PERIOD_TO_DAYS = {
    "1m": 31,
    "6m": 186,
    "1y": 366,
    "5y": 365 * 5,
}


class DataProviderError(Exception):
    """Mantida por compatibilidade, mas get_data não propaga exceções."""


def _parse_alpha_vantage_series(payload: dict) -> Optional[pd.DataFrame]:
    if "Note" in payload:
        st.warning(
            "Limite de requisições da Alpha Vantage atingido. Tente novamente em alguns minutos."
        )
        return None

    if "Error Message" in payload:
        st.warning("Ticker inválido ou não suportado pela Alpha Vantage.")
        return None

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
                "Close": pd.to_numeric(values.get("5. adjusted close"), errors="coerce"),
                "Volume": pd.to_numeric(values.get("6. volume"), errors="coerce"),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return None

    return df.set_index("Date").sort_index().dropna(subset=["Close"])


def _filter_period(df: pd.DataFrame, period: str) -> pd.DataFrame:
    days = _PERIOD_TO_DAYS.get(period, _PERIOD_TO_DAYS["6m"])
    if days is None:
        return df

    cutoff = pd.Timestamp.utcnow().tz_localize(None) - pd.Timedelta(days=days)
    return df[df.index >= cutoff]


@st.cache_data(ttl=900)
def get_data(symbol: str, period: str) -> Optional[pd.DataFrame]:
    """Busca dados históricos da Alpha Vantage sem quebrar o app em caso de erro."""
    try:
        if not API_KEY:
            st.warning("Variável ALPHA_VANTAGE_KEY não configurada.")
            return None

        clean_symbol = symbol.strip().upper()
        if not clean_symbol:
            return None

        normalized_period = period.strip().lower()
        if normalized_period not in _PERIOD_TO_DAYS:
            normalized_period = "6m"

        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": clean_symbol,
            "outputsize": "full" if normalized_period in {"1y", "5y"} else "compact",
            "apikey": API_KEY,
        }

        response = requests.get(ALPHA_VANTAGE_URL, params=params, timeout=20)
        response.raise_for_status()
        payload = response.json()

        df = _parse_alpha_vantage_series(payload)
        if df is None:
            return None

        filtered = _filter_period(df, normalized_period)
        if filtered.empty:
            return None

        return filtered
    except Exception:
        return None
