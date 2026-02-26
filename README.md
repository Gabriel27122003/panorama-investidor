# panorama-investidor

Aplicação Streamlit para análise rápida de ativos com indicadores de risco e performance.

## Configuração

1. Crie e ative um ambiente virtual.
2. Instale dependências:

```bash
pip install -r requirements.txt
```

3. Configure a chave da Alpha Vantage via variável de ambiente (sem expor chave no código):

```bash
export API_KEY="sua_chave_alpha_vantage"
```

> Se `API_KEY` não estiver definida, o app usa fallback direto para `yfinance`.

## Execução

```bash
streamlit run app.py
```
