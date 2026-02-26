from __future__ import annotations

from pathlib import Path
import importlib.util

import streamlit as st


BASE_DIR = Path(__file__).resolve().parent


def _load_local_module(module_name: str):
    """Carrega um módulo local de forma resiliente em ambientes com hot-reload."""
    module_path = BASE_DIR / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(f"local_{module_name}", module_path)
    if spec is None or spec.loader is None:
        raise ModuleNotFoundError(f"Não foi possível localizar o módulo '{module_name}'.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


try:
    from data_provider import get_data
except (KeyError, ModuleNotFoundError):
    get_data = _load_local_module("data_provider").get_data

try:
    from layout import (
        apply_custom_style,
        build_price_chart,
        build_volume_chart,
        render_friendly_error,
        render_header,
        render_kpis,
        render_sidebar,
    )
except (KeyError, ModuleNotFoundError):
    layout_module = _load_local_module("layout")
    apply_custom_style = layout_module.apply_custom_style
    build_price_chart = layout_module.build_price_chart
    build_volume_chart = layout_module.build_volume_chart
    render_friendly_error = layout_module.render_friendly_error
    render_header = layout_module.render_header
    render_kpis = layout_module.render_kpis
    render_sidebar = layout_module.render_sidebar

try:
    from metrics import calculate_metrics
except (KeyError, ModuleNotFoundError):
    calculate_metrics = _load_local_module("metrics").calculate_metrics


st.set_page_config(layout="wide", page_title="Panorama Investidor", page_icon="📈")


def main() -> None:
    apply_custom_style()
    render_header()

    ticker, period = render_sidebar()

    if not ticker:
        st.info("Informe um ticker para começar a análise.")
        return

    with st.spinner("Buscando dados na Alpha Vantage..."):
        history = get_data(ticker, period)

    if history is None or history.empty:
        st.info("😕 Não encontramos dados para esse ativo no período selecionado. Tente outro ticker ou período.")
        render_friendly_error("Não foi possível carregar os dados desse ativo agora.")
        return

    metrics = calculate_metrics(history)
    render_kpis(metrics)

    st.plotly_chart(build_price_chart(history, ticker), use_container_width=True)

    if "Volume" in history.columns and history["Volume"].notna().any():
        st.plotly_chart(build_volume_chart(history), use_container_width=True)


if __name__ == "__main__":
    main()
