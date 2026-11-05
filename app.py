"""Dashboard de anúncios de veículos (vehicles_us.csv) com Streamlit + Plotly Express."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Caminho relativo ao arquivo, não ao diretório de execução: o Render e o
# `streamlit run` local podem partir de diretórios de trabalho diferentes.
DATA_PATH = Path(__file__).resolve().parent / "vehicles_us.csv"

# Preços abaixo disso são majoritariamente placeholders (ex.: US$ 1) e distorcem os gráficos.
MIN_REALISTIC_PRICE = 500

NUMERIC_COLUMNS: dict[str, str] = {
    "price": "Preço (US$)",
    "odometer": "Quilometragem (milhas)",
    "model_year": "Ano do modelo",
    "days_listed": "Dias anunciado",
    "cylinders": "Cilindros",
}

CATEGORICAL_COLUMNS: dict[str, str] = {
    "condition": "Condição",
    "type": "Tipo",
    "fuel": "Combustível",
    "transmission": "Transmissão",
    "manufacturer": "Fabricante",
}

CONDITION_ORDER = ["new", "like new", "excellent", "good", "fair", "salvage"]


def clean_data(raw: pd.DataFrame) -> pd.DataFrame:
    """Trata ausentes com base em grupos semelhantes, em vez de descartar linhas."""
    df = raw.copy()

    df["date_posted"] = pd.to_datetime(df["date_posted"], errors="coerce")
    df["manufacturer"] = df["model"].str.split().str[0]

    # Ausência em is_4wd significa "não é 4x4": a coluna só registra o valor 1.
    df["is_4wd"] = df["is_4wd"].fillna(0).astype(bool)
    df["paint_color"] = df["paint_color"].fillna("unknown")

    # Ano e cilindros são atributos do modelo; a mediana do próprio modelo é a melhor estimativa.
    for col in ("model_year", "cylinders"):
        df[col] = df[col].fillna(df.groupby("model")[col].transform("median"))

    # Quilometragem depende sobretudo da idade do carro.
    df["odometer"] = df["odometer"].fillna(df.groupby("model_year")["odometer"].transform("median"))

    # A mediana de um número par de anúncios pode ser fracionária (ex.: 2011.5).
    df["model_year"] = df["model_year"].round().astype("Int64")
    df["cylinders"] = df["cylinders"].round().astype("Int64")
    return df


def remove_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Remove preços irreais e a cauda superior (p99) de preço e quilometragem."""
    price_cap = df["price"].quantile(0.99)
    odometer_cap = df["odometer"].quantile(0.99)
    mask = (
        df["price"].between(MIN_REALISTIC_PRICE, price_cap)
        & (df["odometer"].isna() | (df["odometer"] <= odometer_cap))
    )
    return df.loc[mask]


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de dados não encontrado: {path}")
    return clean_data(pd.read_csv(path))


def render_sidebar(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filtros")

    drop_outliers = st.sidebar.checkbox("Remover outliers de preço e quilometragem", value=True)
    filtered = remove_outliers(df) if drop_outliers else df

    manufacturers = sorted(filtered["manufacturer"].dropna().unique())
    selected = st.sidebar.multiselect("Fabricantes", manufacturers, placeholder="Todos")
    if selected:
        filtered = filtered[filtered["manufacturer"].isin(selected)]

    year_min = int(df["model_year"].min())
    year_max = int(df["model_year"].max())
    years = st.sidebar.slider("Ano do modelo", year_min, year_max, (max(year_min, 1990), year_max))
    filtered = filtered[filtered["model_year"].between(*years)]

    return filtered


def render_metrics(df: pd.DataFrame) -> None:
    c1, c2, c3 = st.columns(3)
    c1.metric("Anúncios", f"{len(df):,}".replace(",", "."))
    c2.metric("Preço mediano", f"US$ {df['price'].median():,.0f}".replace(",", "."))
    c3.metric("Dias anunciado (mediana)", f"{df['days_listed'].median():.0f}")


def render_histogram(df: pd.DataFrame) -> None:
    st.subheader("Histograma")
    col = st.selectbox(
        "Coluna", list(NUMERIC_COLUMNS), format_func=NUMERIC_COLUMNS.get, key="hist_col"
    )
    color = st.selectbox(
        "Separar por (opcional)",
        [None, *CATEGORICAL_COLUMNS],
        format_func=lambda c: "—" if c is None else CATEGORICAL_COLUMNS[c],
        key="hist_color",
    )

    if st.button("Criar histograma"):
        st.write(f"Criando um histograma para a coluna **{NUMERIC_COLUMNS[col]}**")
        fig = px.histogram(
            df,
            x=col,
            color=color,
            nbins=50,
            labels={**NUMERIC_COLUMNS, **CATEGORICAL_COLUMNS},
            category_orders={"condition": CONDITION_ORDER},
        )
        fig.update_layout(bargap=0.05, yaxis_title="Quantidade de anúncios")
        st.plotly_chart(fig, use_container_width=True)


def render_scatter(df: pd.DataFrame) -> None:
    st.subheader("Gráfico de dispersão")
    numeric_keys = list(NUMERIC_COLUMNS)
    x_col = st.selectbox(
        "Eixo X", numeric_keys, index=numeric_keys.index("odometer"),
        format_func=NUMERIC_COLUMNS.get, key="scatter_x",
    )
    y_col = st.selectbox(
        "Eixo Y", numeric_keys, index=numeric_keys.index("price"),
        format_func=NUMERIC_COLUMNS.get, key="scatter_y",
    )
    color = st.selectbox(
        "Cor por", list(CATEGORICAL_COLUMNS), format_func=CATEGORICAL_COLUMNS.get, key="scatter_color"
    )

    if st.button("Criar gráfico de dispersão"):
        st.write(
            f"Criando um gráfico de dispersão: **{NUMERIC_COLUMNS[x_col]}** × **{NUMERIC_COLUMNS[y_col]}**"
        )
        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            color=color,
            opacity=0.5,
            hover_data=["model", "model_year", "condition"],
            labels={**NUMERIC_COLUMNS, **CATEGORICAL_COLUMNS},
            category_orders={"condition": CONDITION_ORDER},
        )
        st.plotly_chart(fig, use_container_width=True)


def render_price_by_category(df: pd.DataFrame) -> None:
    st.subheader("Preço mediano por categoria")
    if st.checkbox("Mostrar gráfico de barras de preço mediano"):
        cat = st.radio(
            "Agrupar por", list(CATEGORICAL_COLUMNS),
            format_func=CATEGORICAL_COLUMNS.get, horizontal=True,
        )
        summary = (
            df.groupby(cat, observed=True)["price"]
            .median()
            .sort_values(ascending=False)
            .head(20)
            .reset_index()
        )
        fig = px.bar(summary, x=cat, y="price", labels={**NUMERIC_COLUMNS, **CATEGORICAL_COLUMNS})
        st.plotly_chart(fig, use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="Painel de anúncios de veículos", layout="wide")
    st.header("Painel de anúncios de veículos usados (EUA)")
    st.write(
        "Explore cerca de 51 mil anúncios de carros publicados entre 2018 e 2019: "
        "distribuição de preços, quilometragem e como as características do veículo afetam o valor."
    )

    try:
        df = load_data(DATA_PATH)
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    filtered = render_sidebar(df)
    if filtered.empty:
        st.warning("Nenhum anúncio corresponde aos filtros selecionados.")
        st.stop()

    render_metrics(filtered)
    st.divider()
    render_histogram(filtered)
    st.divider()
    render_scatter(filtered)
    st.divider()
    render_price_by_category(filtered)

    if st.checkbox("Mostrar dados"):
        st.dataframe(filtered.head(500), use_container_width=True)


if __name__ == "__main__":
    main()
