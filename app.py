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
            .main {
                background: linear-gradient(180deg, #0b1020 0%, #121a31 100%);
            }

            [data-testid="stHeader"] {
                background: rgba(0,0,0,0);
            }

            [data-testid="stSidebar"] {
                background: #0d1528;
                border-right: 1px solid rgba(255, 255, 255, 0.08);
            }

            .block-container {
                padding-top: 1.5rem;
                padding-bottom: 2rem;
            }

            .app-title {
                font-size: 2rem;
                font-weight: 700;
                color: #f8fafc;
                margin-bottom: 0.3rem;
            }

            .app-subtitle {
                font-size: 1rem;
                color: #cbd5e1;
                margin-bottom: 1.2rem;
            }

            .section-title {
                font-size: 1.2rem;
                font-weight: 600;
                color: #f8fafc;
                margin: 0.4rem 0 0.8rem 0;
            }

            .stMetric {
                background: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(148, 163, 184, 0.2);
                border-radius: 14px;
                padding: 0.8rem;
            }

            .summary-card {
                background: rgba(15, 23, 42, 0.65);
                border: 1px solid rgba(148, 163, 184, 0.15);
                border-radius: 14px;
                padding: 1rem 1.1rem;
                color: #e2e8f0;
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


def calcular_metricas(df: pd.DataFrame, benchmark_df: Optional[pd.DataFrame] = None) -> Dict[str, Optional[float]]:
    if df.empty or "Close" not in df.columns:
        return {
            "retorno_acumulado": None,
            "cagr": None,
            "volatilidade_anualizada": None,
            "sharpe_ratio": None,
            "max_drawdown": None,
            "beta_vs_ibov": None,
        }

    close = df["Close"].dropna()
    returns = close.pct_change().dropna()

    if len(close) < 2:
        return {
            "retorno_acumulado": None,
            "cagr": None,
            "volatilidade_anualizada": None,
            "sharpe_ratio": None,
            "max_drawdown": None,
            "beta_vs_ibov": None,
        }

    retorno_acumulado = ((close.iloc[-1] / close.iloc[0]) - 1) * 100

    anos = len(returns) / 252 if len(returns) > 0 else None
    cagr = ((close.iloc[-1] / close.iloc[0]) ** (1 / anos) - 1) * 100 if anos and anos > 0 else None

    volatilidade_anualizada = returns.std() * (252**0.5) * 100 if not returns.empty else None

    sharpe_ratio = None
    if not returns.empty and returns.std() != 0:
        sharpe_ratio = (returns.mean() / returns.std()) * (252**0.5)

    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = cumulative / running_max - 1
    max_drawdown = drawdown.min() * 100 if not drawdown.empty else None

    beta_vs_ibov = None
    if benchmark_df is not None and not benchmark_df.empty and "Close" in benchmark_df.columns:
        benchmark_returns = benchmark_df["Close"].dropna().pct_change().dropna()
        aligned = pd.concat([returns, benchmark_returns], axis=1, join="inner").dropna()
        if not aligned.empty and aligned.shape[0] > 1:
            aligned.columns = ["asset", "benchmark"]
            benchmark_var = aligned["benchmark"].var()
            if benchmark_var != 0 and not pd.isna(benchmark_var):
                beta_vs_ibov = aligned["asset"].cov(aligned["benchmark"]) / benchmark_var

    return {
        "retorno_acumulado": retorno_acumulado,
        "cagr": cagr,
        "volatilidade_anualizada": volatilidade_anualizada,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_drawdown,
        "beta_vs_ibov": beta_vs_ibov,
    }


def calculate_indicators(history: pd.DataFrame, benchmark_history: Optional[pd.DataFrame] = None) -> Dict[str, Optional[float]]:
    if history.empty or "Close" not in history.columns:
        return {
            "last_price": None,
            "price_change_pct": None,
            "period_return": None,
            "volatility": None,
            "max_drawdown": None,
            "avg_volume": None,
            "ma20": None,
            "ma50": None,
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
    metricas = calcular_metricas(history, benchmark_history)

    avg_volume = history["Volume"].mean() if "Volume" in history.columns else None
    ma20 = close.tail(20).mean() if len(close) >= 20 else None
    ma50 = close.tail(50).mean() if len(close) >= 50 else None

    return {
        "last_price": last_price,
        "price_change_pct": price_change_pct,
        "period_return": period_return,
        "volatility": metricas["volatilidade_anualizada"],
        "max_drawdown": metricas["max_drawdown"],
        "retorno_acumulado": metricas["retorno_acumulado"],
        "cagr": metricas["cagr"],
        "sharpe_ratio": metricas["sharpe_ratio"],
        "beta_vs_ibov": metricas["beta_vs_ibov"],
        "avg_volume": avg_volume,
        "ma20": ma20,
        "ma50": ma50,
    }


def build_price_chart(history: pd.DataFrame, ticker: str) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=history.index,
            y=history["Close"],
            mode="lines",
            name="Fechamento",
            line=dict(width=2.2, color="#38bdf8"),
        )
    )

    if len(history) >= 20:
        ma20 = history["Close"].rolling(20).mean()
        fig.add_trace(
            go.Scatter(
                x=history.index,
                y=ma20,
                mode="lines",
                name="MM20",
                line=dict(width=1.5, color="#f59e0b", dash="dot"),
            )
        )

    fig.update_layout(
        title=f"{ticker} · Histórico de Preços",
        template="plotly_dark",
        height=460,
        margin=dict(l=12, r=12, t=50, b=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis_title="Data",
        yaxis_title="Preço",
        hovermode="x unified",
    )
    return fig


def build_volume_chart(history: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        data=[
            go.Bar(
                x=history.index,
                y=history["Volume"],
                marker_color="#818cf8",
                name="Volume",
            )
        ]
    )
    fig.update_layout(
        title="Volume Diário",
        template="plotly_dark",
        height=260,
        margin=dict(l=12, r=12, t=45, b=12),
        xaxis_title="Data",
        yaxis_title="Volume",
    )
    return fig


def render_header() -> None:
    st.markdown('<div class="app-title">📊 Panorama Investidor</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">Análise rápida de ativos com foco em performance, risco e visual profissional.</div>',
        unsafe_allow_html=True,
    )


def render_sidebar() -> Tuple[str, str]:
    st.sidebar.markdown("## ⚙️ Configurações")
    st.sidebar.caption("Dados via Yahoo Finance com cache inteligente e fallback automático.")

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

    st.sidebar.markdown("---")
    st.sidebar.info("💡 Dica: use sufixo `.SA` para ações brasileiras.")

    return selected_ticker, period_labels[selected_period_label]


def render_overview(indicators: Dict[str, Optional[float]]) -> None:
    st.markdown('<div class="section-title">🧭 Visão Geral</div>', unsafe_allow_html=True)

    cols = st.columns(3)
    with cols[0]:
        st.metric(
            "Preço Atual",
            format_currency(indicators.get("last_price")),
            format_percentage(indicators.get("price_change_pct")),
        )
    with cols[1]:
        st.metric("Retorno no Período", format_percentage(indicators.get("period_return")))
    with cols[2]:
        st.metric("Volume Médio", format_number(indicators.get("avg_volume")))


def render_indicators(indicators: Dict[str, Optional[float]]) -> None:
    st.markdown('<div class="section-title">📐 Indicadores</div>', unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown(
            f"""
            <div class="summary-card">
                <b>Volatilidade Anualizada</b><br>
                {f"{indicators['volatility']:.2f}%" if indicators['volatility'] is not None else 'N/A'}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_b:
        st.markdown(
            f"""
            <div class="summary-card">
                <b>Máx. Drawdown</b><br>
                {f"{indicators['max_drawdown']:.2f}%" if indicators['max_drawdown'] is not None else 'N/A'}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_c:
        st.markdown(
            f"""
            <div class="summary-card">
                <b>Volume Médio</b><br>
                {format_number(indicators['avg_volume'])}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")
    risk_col1, risk_col2, risk_col3 = st.columns(3)
    with risk_col1:
        st.markdown(
            f"""
            <div class="summary-card">
                <b>CAGR</b><br>
                {f"{indicators['cagr']:.2f}%" if indicators['cagr'] is not None else 'N/A'}
            </div>
            """,
            unsafe_allow_html=True,
        )
    with risk_col2:
        st.markdown(
            f"""
            <div class="summary-card">
                <b>Sharpe Ratio</b><br>
                {f"{indicators['sharpe_ratio']:.2f}" if indicators['sharpe_ratio'] is not None else 'N/A'}
            </div>
            """,
            unsafe_allow_html=True,
        )
    with risk_col3:
        st.markdown(
            f"""
            <div class="summary-card">
                <b>Beta vs IBOV</b><br>
                {f"{indicators['beta_vs_ibov']:.2f}" if indicators['beta_vs_ibov'] is not None else 'N/A'}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")
    ma_col1, ma_col2 = st.columns(2)
    with ma_col1:
        st.metric("Média Móvel 20", format_currency(indicators["ma20"]))
    with ma_col2:
        st.metric("Média Móvel 50", format_currency(indicators["ma50"]))


def main() -> None:
    apply_custom_style()
    render_header()

    ticker, period = render_sidebar()

    with st.spinner("Carregando dados do mercado..."):
        history = get_data_with_fallback(ticker, period)
        benchmark_history = get_data_with_fallback("^BVSP", period)

    if history is None or history.empty:
        st.warning("⚠️ Não foi possível carregar os dados agora (possível erro 429/rate limit do Yahoo). Tente novamente em instantes.")
        st.info("Você pode tentar novamente em alguns minutos ou selecionar outro ativo/período.")
        st.markdown('<div class="section-title">📈 Histórico</div>', unsafe_allow_html=True)
        st.empty()
        st.markdown('<div class="section-title">📐 Indicadores</div>', unsafe_allow_html=True)
        st.empty()
        return

    indicators = calculate_indicators(history, benchmark_history)

    with st.container():
        render_overview(indicators)

    st.write("")

    with st.container():
        st.markdown('<div class="section-title">📈 Histórico</div>', unsafe_allow_html=True)
        st.plotly_chart(build_price_chart(history, ticker), use_container_width=True)

        if "Volume" in history.columns:
            st.plotly_chart(build_volume_chart(history), use_container_width=True)

    st.write("")

    with st.container():
        render_indicators(indicators)


if __name__ == "__main__":
    main()
