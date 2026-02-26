from typing import Dict, Optional

import pandas as pd


def calculate_indicators(history: pd.DataFrame) -> Dict[str, Optional[float]]:
    if history.empty or "Close" not in history.columns:
        return {
            "last_price": None,
            "price_change_pct": None,
            "period_return": None,
            "volatility": None,
            "sharpe_ratio": None,
            "max_drawdown": None,
            "avg_volume": None,
            "ma20": None,
            "ma50": None,
        }

    close = history["Close"].dropna()
    returns = close.pct_change().dropna()

    last_price = close.iloc[-1] if not close.empty else None
    previous_close = close.iloc[-2] if len(close) > 1 else None
    price_change_pct = ((last_price / previous_close) - 1) * 100 if last_price is not None and previous_close not in (None, 0) else None

    period_return = ((close.iloc[-1] / close.iloc[0]) - 1) * 100 if len(close) > 1 else None
    volatility = returns.std() * (252**0.5) * 100 if not returns.empty else None

    sharpe_ratio = None
    if not returns.empty and returns.std() != 0:
        sharpe_ratio = (returns.mean() / returns.std()) * (252**0.5)

    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative / running_max - 1) * 100
    max_drawdown = drawdown.min() if not drawdown.empty else None

    avg_volume = history["Volume"].mean() if "Volume" in history.columns else None
    ma20 = close.tail(20).mean() if len(close) >= 20 else None
    ma50 = close.tail(50).mean() if len(close) >= 50 else None

    return {
        "last_price": last_price,
        "price_change_pct": price_change_pct,
        "period_return": period_return,
        "volatility": volatility,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_drawdown,
        "avg_volume": avg_volume,
        "ma20": ma20,
        "ma50": ma50,
    }
