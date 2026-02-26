import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📊 Panorama do Investidor")

tickers = st.text_input(
    "Digite os tickers separados por vírgula (ex: PETR4.SA, VALE3.SA)",
    "PETR4.SA,VALE3.SA"
)

lista = [t.strip() for t in tickers.split(",") if t.strip()]

if lista:
    dados = []

    for ticker in lista:
        try:
            acao = yf.Ticker(ticker)
            info = acao.info
            hist = acao.history(period="1y")

            preco = info.get("currentPrice", 0)
            dy = info.get("dividendYield", 0)
            pl = info.get("trailingPE", 0)

            dados.append({
                "Ticker": ticker,
                "Preço Atual": preco,
                "Dividend Yield (%)": round(dy * 100, 2) if dy else 0,
                "P/L": pl
            })

            fig = px.line(hist, x=hist.index, y="Close",
                          title=f"{ticker} - Últimos 12 meses")
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Erro ao carregar {ticker}: {e}")

    df = pd.DataFrame(dados)
    st.subheader("📋 Tabela Consolidada")
    st.dataframe(df, use_container_width=True)
