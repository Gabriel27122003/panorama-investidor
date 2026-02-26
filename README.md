# Panorama Investidor

Aplicação Streamlit para análise de ações com dados da **Alpha Vantage**.


## Fonte de dados

- Provedor único: **Alpha Vantage**
- Sem uso de **Yahoo Finance**
- Sem dependência de **yfinance**

## Pré-requisitos

1. Python 3.10+
2. Chave da Alpha Vantage

## Instalação

```bash
pip install -r requirements.txt
```

## Configuração da chave de API

Defina a variável de ambiente usada pelo app:

```bash
export ALPHA_VANTAGE_KEY="sua_chave"
```

No Streamlit Cloud, configure `ALPHA_VANTAGE_KEY` em **Secrets** ou variáveis do app.

## Executar localmente

```bash
streamlit run app.py
```

## Estrutura do projeto

- `app.py`: ponto de entrada e fluxo principal da interface
- `data_provider.py`: integração com Alpha Vantage e cache (`@st.cache_data(ttl=900)`)
- `metrics.py`: cálculos de retorno, volatilidade, sharpe e drawdown
- `layout.py`: componentes visuais, sidebar, KPIs e gráficos Plotly
