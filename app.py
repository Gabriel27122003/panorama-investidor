import streamlit as st

from data_provider import get_data_with_fallback
from layout import (
    apply_custom_style,
    build_price_chart,
    build_volume_chart,
    render_header,
    render_indicators,
    render_overview,
    render_sidebar,
)
from metrics import calculate_indicators


st.set_page_config(
    page_title="Panorama Investidor",
    page_icon="📈",
    layout="wide",
)


def main() -> None:
    apply_custom_style()
    render_header()

    ticker, period = render_sidebar()

    with st.spinner("Carregando dados do mercado..."):
        history = get_data_with_fallback(ticker, period)

    if history is None or history.empty:
        st.warning("⚠️ Não foi possível carregar os dados agora. O Yahoo pode estar limitando requisições. Tente novamente em instantes.")
        st.info("Você pode tentar novamente em alguns minutos ou selecionar outro ativo/período.")
        st.markdown('<div class="section-title">📈 Histórico</div>', unsafe_allow_html=True)
        st.empty()
        st.markdown('<div class="section-title">📐 Indicadores</div>', unsafe_allow_html=True)
        st.empty()
        return

    indicators = calculate_indicators(history)

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
