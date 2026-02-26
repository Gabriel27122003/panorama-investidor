from __future__ import annotations

from typing import Dict, Optional

import pandas as pd


def calculate_metrics(history: pd.DataFrame) -> Dict[str, Optional[float]]:
    if history.empty or "Close" not in history.columns:
        return {
            "return_accumulated": None,
            "volatility_annualized": None,
            "sharpe": None,
            "max_drawdown": None,
            "last_close": None,
        }

    close = history["Close"].dropna()
    if close.empty:
        return {
            "return_accumulated": None,
            "volatility_annualized": None,
            "sharpe": None,
            "max_drawdown": None,
            "last_close": None,
        }

    returns = close.pct_change().dropna()

    return_accumulated = ((close.iloc[-1] / close.iloc[0]) - 1) * 100 if len(close) > 1 else 0.0
    volatility_annualized = returns.std() * (252**0.5) * 100 if not returns.empty else None

    sharpe = None
    if not returns.empty and returns.std() and returns.std() > 0:
        sharpe = (returns.mean() / returns.std()) * (252**0.5)

    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative / running_max - 1) * 100
    max_drawdown = drawdown.min() if not drawdown.empty else None

    return {
        "return_accumulated": return_accumulated,
        "volatility_annualized": volatility_annualized,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "last_close": close.iloc[-1],
    }
