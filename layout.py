from __future__ import annotations

from typing import Dict, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


PERIOD_OPTIONS = {
    "1m": "1 mês",
    "6m": "6 meses",
    "1y": "1 ano",
    "5y": "5 anos",
}


def apply_custom_style() -> None:
    st.markdown(
        """
        <style>
            .main { background: #f7f9fc; }
            .block-container { padding-top: 1.3rem; }
            [data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e5e7eb; }
            .title { font-size: 2rem; font-weight: 700; margin-bottom: 0.2rem; }
            .subtitle { color: #475569; margin-bottom: 1rem; }
            .kpi-row [data-testid="stMetric"] {
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 0.7rem;
                background: #ffffff;
                box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown('<div class="title">📊 Panorama Investidor</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Acompanhe performance e risco de ativos com dados oficiais da Alpha Vantage.</div>',
        unsafe_allow_html=True,
    )


def render_sidebar() -> tuple[str, str]:
    st.sidebar.header("Configurações")
    ticker = st.sidebar.text_input("Ticker", value="PETR4.SA").strip().upper()
    period = st.sidebar.selectbox("Período", options=list(PERIOD_OPTIONS.keys()), format_func=lambda p: PERIOD_OPTIONS[p], index=2)
    st.sidebar.caption("Exemplos: PETR4.SA, VALE3.SA, AAPL, MSFT")
    return ticker, period


def _format_pct(value: Optional[float]) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:.2f}%"


def render_kpis(metrics: Dict[str, Optional[float]]) -> None:
    st.markdown('<div class="kpi-row">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Retorno", _format_pct(metrics.get("return_accumulated")))
    with c2:
        st.metric("Volatilidade", _format_pct(metrics.get("volatility_annualized")))
    with c3:
        sharpe = metrics.get("sharpe")
        st.metric("Sharpe", f"{sharpe:.2f}" if sharpe is not None else "N/A")
    with c4:
        st.metric("Drawdown", _format_pct(metrics.get("max_drawdown")))
    st.markdown("</div>", unsafe_allow_html=True)


def render_friendly_error(message: str) -> None:
    st.warning(
        "⚠️ Não conseguimos carregar os dados agora. "
        f"Detalhe: {message} "
        "Verifique o ticker, aguarde alguns segundos e tente novamente."
    )


def build_price_chart(history: pd.DataFrame, symbol: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=history.index,
            y=history["Close"],
            mode="lines",
            name=symbol,
            line=dict(color="#2563eb", width=2.5),
        )
    )
    fig.update_layout(
        title=f"Preço de fechamento - {symbol}",
        template="plotly_white",
        height=450,
        margin=dict(l=8, r=8, t=42, b=8),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#e2e8f0")
    fig.update_yaxes(showgrid=True, gridcolor="#e2e8f0")
    return fig


def build_volume_chart(history: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        data=[
            go.Bar(
                x=history.index,
                y=history["Volume"],
                marker_color="#93c5fd",
                name="Volume",
            )
        ]
    )
    fig.update_layout(
        title="Volume diário",
        template="plotly_white",
        height=260,
        margin=dict(l=8, r=8, t=42, b=8),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#e2e8f0")
    fig.update_yaxes(showgrid=True, gridcolor="#e2e8f0")
    return fig
