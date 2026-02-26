from __future__ import annotations

import streamlit as st

from data_provider import DataProviderError, get_data
from layout import (
    apply_custom_style,
    build_price_chart,
    build_volume_chart,
    render_friendly_error,
    render_header,
    render_kpis,
    render_sidebar,
)
from metrics import calculate_metrics


st.set_page_config(page_title="Panorama Investidor", page_icon="📈", layout="wide")


def main() -> None:
    apply_custom_style()
    render_header()

    ticker, period = render_sidebar()

    if not ticker:
        st.info("Informe um ticker para começar a análise.")
        return

    try:
        with st.spinner("Buscando dados na Alpha Vantage..."):
            history = get_data(ticker, period)
    except DataProviderError as exc:
        render_friendly_error(str(exc))
        return
    except Exception:
        render_friendly_error("Erro inesperado ao processar os dados.")
        return

    if history.empty:
        render_friendly_error("A API retornou uma série vazia para esse ativo.")
        return

    metrics = calculate_metrics(history)
    render_kpis(metrics)

    st.plotly_chart(build_price_chart(history, ticker), use_container_width=True)

    if "Volume" in history.columns and history["Volume"].notna().any():
        st.plotly_chart(build_volume_chart(history), use_container_width=True)


if __name__ == "__main__":
    main()
