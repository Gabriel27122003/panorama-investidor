from __future__ import annotations

from typing import Dict, Optional

import pandas as pd

TRADING_DAYS_PER_YEAR = 252


def _empty_metrics() -> Dict[str, Optional[float]]:
    return {
        "retorno_acumulado": None,
        "cagr": None,
        "volatilidade_anualizada": None,
        "sharpe_ratio": None,
        "maximo_drawdown": None,
    }


def calcular_metricas(df: pd.DataFrame) -> Dict[str, Optional[float]]:
    """Calcula métricas de performance a partir da série de preços de fechamento.

    Espera-se um DataFrame com coluna ``Close`` ordenada cronologicamente.
    """
    if df.empty or "Close" not in df.columns:
        return _empty_metrics()

    close = df["Close"].dropna()
    if close.empty:
        return _empty_metrics()

    retornos_diarios = close.pct_change().dropna()

    retorno_acumulado = 0.0
    cagr = 0.0
    if len(close) > 1 and close.iloc[0] > 0:
        retorno_acumulado = (close.iloc[-1] / close.iloc[0]) - 1
        if isinstance(close.index, pd.DatetimeIndex) and len(close.index) > 1:
            dias = (close.index[-1] - close.index[0]).days
            anos = dias / 365.25
        else:
            anos = len(retornos_diarios) / TRADING_DAYS_PER_YEAR

        if anos > 0:
            cagr = (close.iloc[-1] / close.iloc[0]) ** (1 / anos) - 1

    volatilidade_anualizada = None
    sharpe_ratio = None
    if not retornos_diarios.empty:
        desvio = retornos_diarios.std(ddof=1)
        if pd.notna(desvio):
            volatilidade_anualizada = desvio * (TRADING_DAYS_PER_YEAR**0.5)
            if desvio > 0:
                sharpe_ratio = (retornos_diarios.mean() / desvio) * (TRADING_DAYS_PER_YEAR**0.5)

    crescimento = (1 + retornos_diarios).cumprod()
    pico = crescimento.cummax()
    drawdown = (crescimento / pico) - 1
    maximo_drawdown = drawdown.min() if not drawdown.empty else None

    return {
        "retorno_acumulado": retorno_acumulado,
        "cagr": cagr,
        "volatilidade_anualizada": volatilidade_anualizada,
        "sharpe_ratio": sharpe_ratio,
        "maximo_drawdown": maximo_drawdown,
    }


def calculate_metrics(history: pd.DataFrame) -> Dict[str, Optional[float]]:
    """Wrapper de compatibilidade para o restante da aplicação."""
    metricas = calcular_metricas(history)
    return {
        "return_accumulated": None if metricas["retorno_acumulado"] is None else metricas["retorno_acumulado"] * 100,
        "cagr": None if metricas["cagr"] is None else metricas["cagr"] * 100,
        "volatility_annualized": None
        if metricas["volatilidade_anualizada"] is None
        else metricas["volatilidade_anualizada"] * 100,
        "sharpe": metricas["sharpe_ratio"],
        "max_drawdown": None if metricas["maximo_drawdown"] is None else metricas["maximo_drawdown"] * 100,
        "last_close": history["Close"].dropna().iloc[-1] if not history.empty and "Close" in history.columns and not history["Close"].dropna().empty else None,
    }
