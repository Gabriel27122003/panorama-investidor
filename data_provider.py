from __future__ import annotations

import os
from typing import Optional

import pandas as pd
import requests
import streamlit as st

ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"

_PERIOD_TO_DAYS = {
    "1m": 31,
    "6m": 186,
    "1y": 366,
    "max": None,
}


class DataProviderError(Exception):
    """Error raised when market data cannot be loaded from Alpha Vantage."""


def _validate_period(period: str) -> str:
    normalized = period.strip().lower()
    if normalized not in _PERIOD_TO_DAYS:
        raise DataProviderError(
            f"Período inválido: {period}. Use um destes: {', '.join(_PERIOD_TO_DAYS.keys())}."
        )
    return normalized


def _parse_alpha_vantage_series(payload: dict) -> pd.DataFrame:
    if "Error Message" in payload:
        raise DataProviderError("Ticker inválido ou não suportado pela Alpha Vantage.")

    if "Note" in payload:
        raise DataProviderError(
            "Limite de requisições da Alpha Vantage atingido. Tente novamente em alguns minutos."
        )

    series = payload.get("Time Series (Daily)")
    if not isinstance(series, dict) or not series:
        raise DataProviderError("A API retornou resposta vazia para este ativo.")

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
        raise DataProviderError("Não foi possível normalizar os dados retornados pela API.")

    return df.set_index("Date").sort_index().dropna(subset=["Close"])


def _filter_period(df: pd.DataFrame, period: str) -> pd.DataFrame:
    days = _PERIOD_TO_DAYS[period]
    if days is None:
        return df

    cutoff = pd.Timestamp.utcnow().tz_localize(None) - pd.Timedelta(days=days)
    return df[df.index >= cutoff]


@st.cache_data(ttl=900)
def get_data(symbol: str, period: str) -> pd.DataFrame:
    """Return historical OHLCV data from Alpha Vantage.

    Args:
        symbol: Asset ticker (ex.: AAPL, PETR4.SA)
        period: One of: 1m, 6m, 1y, max
    """
    api_key = os.getenv("ALPHA_VANTAGE_KEY", "").strip()
    if not api_key:
        raise DataProviderError(
            "Variável de ambiente ALPHA_VANTAGE_KEY não configurada no ambiente."
        )

    clean_symbol = symbol.strip().upper()
    if not clean_symbol:
        raise DataProviderError("Informe um ticker válido.")

    normalized_period = _validate_period(period)

    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": clean_symbol,
        "outputsize": "full" if normalized_period in {"1y", "max"} else "compact",
        "apikey": api_key,
    }

    try:
        response = requests.get(ALPHA_VANTAGE_URL, params=params, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DataProviderError("Falha de conexão com a Alpha Vantage.") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise DataProviderError("A resposta da Alpha Vantage não está em formato JSON válido.") from exc

    df = _parse_alpha_vantage_series(payload)
    filtered = _filter_period(df, normalized_period)

    if filtered.empty:
        raise DataProviderError("Não há dados disponíveis para o período selecionado.")

    return filtered
