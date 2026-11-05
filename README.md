# Painel de anúncios de veículos usados

Aplicativo web em **Streamlit** para explorar cerca de 51 mil anúncios de carros usados nos EUA (`vehicles_us.csv`, maio/2018 a abril/2019). Ele ajuda a entender como preço, quilometragem, idade, condição e tipo do veículo se relacionam.

**App online:** https://vehicles-dashboard-wjhj.onrender.com/

## Funcionalidades

- **Filtros na barra lateral:** remoção de outliers de preço/quilometragem, seleção de fabricantes e intervalo de ano do modelo.
- **Indicadores:** total de anúncios, preço mediano e mediana de dias anunciado.
- **Botão "Criar histograma":** histograma de qualquer coluna numérica, opcionalmente separado por uma categoria.
- **Botão "Criar gráfico de dispersão":** dispersão entre duas colunas numéricas, colorida por categoria (padrão: preço × quilometragem por condição).
- **Caixa de seleção:** gráfico de barras com o preço mediano por condição, tipo, combustível, transmissão ou fabricante.
- **Caixa de seleção "Mostrar dados":** tabela com os dados filtrados.

## Tratamento dos dados

- `is_4wd` ausente → `False` (a coluna só registra `1`).
- `paint_color` ausente → `unknown`.
- `model_year` e `cylinders` ausentes → mediana do mesmo modelo.
- `odometer` ausente → mediana do mesmo ano do modelo.
- Coluna `manufacturer` derivada da primeira palavra de `model`.

A análise exploratória completa está em [`notebooks/EDA.ipynb`](notebooks/EDA.ipynb).

## Estrutura

```
├── .streamlit/config.toml   # porta/endereço exigidos pelo Render
├── notebooks/EDA.ipynb      # análise exploratória
├── app.py                   # aplicativo Streamlit
├── requirements.txt
└── vehicles_us.csv
```

## Como executar localmente

```bash
python -m venv vehicles_env
# Windows: vehicles_env\Scripts\activate | macOS/Linux: source vehicles_env/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Acesse http://localhost:10000 (porta definida em `.streamlit/config.toml`).

## Tecnologias

Python 3.11 · pandas · plotly-express · Streamlit · Render
