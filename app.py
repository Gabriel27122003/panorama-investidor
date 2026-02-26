from typing import Dict, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_provider import get_market_data


st.set_page_config(
    page_title="Panorama Investidor",
    page_icon="📈",
    layout="wide",
)


def apply_custom_style() -> None:
    st.markdown(
        """
        <style>
            :root {
                --bg-primary: #f4f7fb;
                --surface: #ffffff;
                --surface-alt: #eef2f8;
                --border: #dde4ef;
                --text-primary: #111827;
                --text-secondary: #526072;
                --accent: #1d4ed8;
                --accent-soft: #dbeafe;
            }

            .main {
                background: var(--bg-primary);
            }

            [data-testid="stHeader"] {
                background: rgba(255,255,255,0.92);
                border-bottom: 1px solid var(--border);
            }

            [data-testid="stSidebar"] {
                background: #ffffff;
                border-right: 1px solid var(--border);
            }

            .block-container {
                padding-top: 1.5rem;
                padding-bottom: 2rem;
            }

            .app-title {
                font-size: 2rem;
                font-weight: 750;
                color: var(--text-primary);
                margin-bottom: 0.3rem;
            }

            .app-subtitle {
                font-size: 1rem;
                color: var(--text-secondary);
                margin-bottom: 1.2rem;
            }

            .section-title {
                font-size: 1.2rem;
                font-weight: 600;
                color: var(--text-primary);
                margin: 0.4rem 0 0.8rem 0;
            }

            .stMetric {
                background: linear-gradient(180deg, var(--surface) 0%, #fbfcff 100%);
                border: 1px solid var(--border);
                border-radius: 14px;
                padding: 0.85rem;
                box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
            }

            [data-testid="stMetricLabel"] {
                color: var(--text-secondary);
                font-weight: 600;
            }

            [data-testid="stMetricValue"] {
                color: var(--text-primary);
            }

            [data-testid="stMetricDelta"] {
                font-weight: 600;
            }

            .panel {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 16px;
                padding: 1rem;
                box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_data_with_fallback(symbol: str, period: str) -> Optional[pd.DataFrame]:
    data = get_market_data(symbol, period)
    if data is not None and not data.empty:
        return data

    # fallback automático para período menor
    if period != "6mo":
        fallback_data = get_market_data(symbol, "6mo")
        if fallback_data is not None and not fallback_data.empty:
            return fallback_data

    return None


def format_currency(value: Optional[float]) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_number(value: Optional[float]) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:,.0f}".replace(",", ".")


def format_percentage(value: Optional[float]) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:.2f}%"


def calculate_indicators(history: pd.DataFrame) -> Dict[str, Optional[float]]:
    if history.empty or "Close" not in history.columns:
        return {
            "last_price": None,
            "price_change_pct": None,
            "period_return": None,
            "volatility": None,
            "sharpe": None,
            "max_drawdown": None,
            "avg_volume": None,
        }

    close = history["Close"].dropna()
    returns = close.pct_change().dropna()

    last_price = close.iloc[-1] if not close.empty else None
    previous_close = close.iloc[-2] if len(close) > 1 else None
    price_change_pct = (
        ((last_price / previous_close) - 1) * 100
        if last_price is not None and previous_close not in (None, 0) and not pd.isna(previous_close)
        else None
    )

    period_return = ((close.iloc[-1] / close.iloc[0]) - 1) * 100 if len(close) > 1 else None
    volatility = returns.std() * (252**0.5) * 100 if not returns.empty else None
    sharpe = (
        (returns.mean() / returns.std()) * (252**0.5)
        if not returns.empty and returns.std() and returns.std() > 0
        else None
    )

    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative / running_max - 1) * 100
    max_drawdown = drawdown.min() if not drawdown.empty else None

    avg_volume = history["Volume"].mean() if "Volume" in history.columns else None

    return {
        "period_return": period_return,
        "volatility": volatility,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "avg_volume": avg_volume,
        "last_price": last_price,
        "price_change_pct": price_change_pct,
    }


def build_price_chart(history: pd.DataFrame, ticker: str, benchmark_label: Optional[str] = None, benchmark_history: Optional[pd.DataFrame] = None) -> go.Figure:
    base_series = (history["Close"] / history["Close"].iloc[0]) * 100
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=history.index,
            y=base_series,
            mode="lines",
            name=f"{ticker} (Base 100)",
            line=dict(width=2.6, color="#1d4ed8"),
        )
    )

    if benchmark_history is not None and not benchmark_history.empty and benchmark_label:
        benchmark_base = (benchmark_history["Close"] / benchmark_history["Close"].iloc[0]) * 100
        fig.add_trace(
            go.Scatter(
                x=benchmark_history.index,
                y=benchmark_base,
                mode="lines",
                name=f"{benchmark_label} (Base 100)",
                line=dict(width=2, color="#0ea5e9", dash="dot"),
            )
        )

    fig.update_layout(
        title=f"Performance Relativa · {ticker}",
        template="plotly_white",
        height=460,
        margin=dict(l=12, r=12, t=50, b=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis_title="Data",
        yaxis_title="Índice Base 100",
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#edf2f7")
    fig.update_yaxes(showgrid=True, gridcolor="#edf2f7")
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
        title="Volume Diário",
        template="plotly_white",
        height=260,
        margin=dict(l=12, r=12, t=45, b=12),
        xaxis_title="Data",
        yaxis_title="Volume",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#edf2f7")
    fig.update_yaxes(showgrid=True, gridcolor="#edf2f7")
    return fig


def render_header() -> None:
    st.markdown('<div class="app-title">📊 Panorama Investidor</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">Análise rápida de ativos com foco em performance, risco e visual profissional.</div>',
        unsafe_allow_html=True,
    )


def render_sidebar() -> Tuple[str, str, Optional[str]]:
    st.sidebar.markdown("## ⚙️ Configurações")
    st.sidebar.caption("Dados via Alpha Vantage com fallback automático para Yahoo Finance.")

    default_tickers = [
        "PETR4.SA",
        "VALE3.SA",
        "ITUB4.SA",
        "BBDC4.SA",
        "BBAS3.SA",
        "AAPL",
        "MSFT",
        "GOOGL",
    ]

    ticker = st.sidebar.selectbox("Ativo", default_tickers, index=0)
    custom_ticker = st.sidebar.text_input("Ou digite um ticker manualmente", "")

    selected_ticker = custom_ticker.strip().upper() if custom_ticker.strip() else ticker

    period_labels = {
        "1 mês": "1mo",
        "6 meses": "6mo",
        "1 ano": "1y",
        "5 anos": "5y",
        "Máximo": "max",
    }
    selected_period_label = st.sidebar.selectbox("Período", list(period_labels.keys()), index=2)

    benchmark_options = {
        "Sem benchmark": None,
        "IBOV (^BVSP)": "^BVSP",
        "S&P 500 (^GSPC)": "^GSPC",
        "Nasdaq 100 (^NDX)": "^NDX",
    }
    selected_benchmark = st.sidebar.selectbox("Benchmark (opcional)", list(benchmark_options.keys()), index=0)

    st.sidebar.markdown("---")
    st.sidebar.info("💡 Dica: use sufixo `.SA` para ações brasileiras.")

    return selected_ticker, period_labels[selected_period_label], benchmark_options[selected_benchmark]


def render_kpis(indicators: Dict[str, Optional[float]]) -> None:
    st.markdown('<div class="section-title">📌 KPIs Principais</div>', unsafe_allow_html=True)

    cols = st.columns(4)
    with cols[0]:
        st.metric(
            "Retorno acumulado",
            format_percentage(indicators.get("period_return")),
        )
    with cols[1]:
        st.metric("Volatilidade anualizada", format_percentage(indicators.get("volatility")))
    with cols[2]:
        sharpe = indicators.get("sharpe")
        st.metric("Sharpe Ratio", f"{sharpe:.2f}" if sharpe is not None else "N/A")
    with cols[3]:
        st.metric("Máximo Drawdown", format_percentage(indicators.get("max_drawdown")))


def render_support_metrics(indicators: Dict[str, Optional[float]]) -> None:
    st.markdown('<div class="section-title">🧾 Detalhes</div>', unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Preço atual", format_currency(indicators.get("last_price")), format_percentage(indicators.get("price_change_pct")))
    with col_b:
        st.metric("Volume médio", format_number(indicators.get("avg_volume")))
    with col_c:
        st.metric("Observação", "Perfil Institucional")


def main() -> None:
    apply_custom_style()
    render_header()

    ticker, period, benchmark = render_sidebar()

    with st.spinner("Carregando dados do mercado..."):
        history = get_data_with_fallback(ticker, period)

    if history is None or history.empty:
        st.error(
            "Não foi possível carregar os dados para este ativo agora. "
            "Verifique o ticker, troque o período ou tente novamente em instantes."
        )
        st.info("Se o problema persistir, os provedores Alpha Vantage e Yahoo Finance podem estar indisponíveis no momento.")
        return

    benchmark_history = None
    if benchmark:
        benchmark_history = get_data_with_fallback(benchmark, period)
        if benchmark_history is None or benchmark_history.empty:
            st.warning(
                f"Não foi possível carregar o benchmark {benchmark} no período selecionado. "
                "O gráfico seguirá apenas com o ativo principal."
            )
            benchmark_history = None

    indicators = calculate_indicators(history)

    with st.container():
        render_kpis(indicators)

    st.write("")

    with st.container():
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📈 Histórico</div>', unsafe_allow_html=True)
        st.plotly_chart(
            build_price_chart(history, ticker, benchmark, benchmark_history),
            use_container_width=True,
        )

        if "Volume" in history.columns:
            st.plotly_chart(build_volume_chart(history), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")

    with st.container():
        render_support_metrics(indicators)


if __name__ == "__main__":
    main()
