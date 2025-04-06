import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from web.commons.session import check_login
from web.commons.style_utils import add_logo
from web.pages.commons.database_connectors import get_evaluations


def extract_learning_rate(model_name):
    match = re.search(r"lr_([\d\.]+)", model_name)
    return float(match.group(1)) if match else None


def extract_number_companies(model_name):
    match = re.search(r"ncompanies_(\d+)", model_name)
    return int(match.group(1)) if match else None


# change_theme_toogle()
add_logo(with_name=False, sidebar=True)
check_login()
# add_sidebar_navigation()
# st.set_page_config(page_title="Análisis de Métricas de Modelos", layout="wide")

st.title("📈 Análisis de Métricas de Modelos")
df = get_evaluations()

if not df.empty:
    # Convertir fechas a formato datetime
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"])

    st.write("### Tabla Interactiva de Evaluación de Modelos")

    # Sidebar filters
    # start_date = st.sidebar.date_input("Fecha de inicio", df["start_date"].min().date())
    # end_date = st.sidebar.date_input("Fecha de fin", df["end_date"].max().date())

    min_date = df["start_date"].min().date()
    max_date = df["end_date"].max().date()

    if df.empty:
        st.warning("No hay datos disponibles en el rango seleccionado.")
    else:
        df_pivot = df.pivot_table(
            index=[
                "evaluation_id",
                "model_id",
                "model_name",
                "algorithm",
                "feature_extractor",
                "normalization",
                "start_date",
                "end_date",
                "phase",
                "num_evaluations",
            ],
            columns="metric_name",
            values="value",
        ).reset_index()

        df_pivot["learning_rate"] = df_pivot["model_name"].apply(extract_learning_rate)
        df_pivot["number_of_companies"] = df_pivot["model_name"].apply(
            extract_number_companies
        )

        # AgGrid(df_pivot)
        selection = st.dataframe(df_pivot, hide_index=True, on_select="rerun")

        selected_rows = selection.get("selection", {}).get("rows", [])

        metric_columns = df_pivot.columns.difference(
            [
                "evaluation_id",
                "model_id",
                "model_name",
                "algorithm",
                "feature_extractor",
                "learning _rate",
                "number_of_companies",
                "normalization",
                "start_date",
                "end_date",
                "phase",
                "num_evaluations",
            ]
        )

        st.write("### Selección de Métricas para Análisis")
        col1, col2 = st.columns(2)
        x_axis = col1.selectbox("Seleccionar eje X", metric_columns)
        y_axis = col2.selectbox("Seleccionar eje Y", metric_columns[::-1])

        selected_models = []
        if selected_rows:
            selected_df = df_pivot.iloc[selected_rows]
            for _, row in selected_df.iterrows():
                selected_models.append(row["model_name"])

        comparation_mode = st.radio(
            "Modo de Comparación",
            [
                "Todos",
                "Por Fase",
                "Por Algoritmo",
                "Por Extractor de Características",
                "Por Learning Rate",
                "Por Número de Compañías",
            ],
            horizontal=True,
        )

        if comparation_mode == "Por Fase":
            col_division = "phase"
            values = df_pivot["phase"].unique()
        elif comparation_mode == "Por Algoritmo":
            col_division = "algorithm"
            values = df_pivot["algorithm"].unique()
        elif comparation_mode == "Por Extractor de Características":
            col_division = "feature_extractor"
            values = df_pivot["feature_extractor"].unique()
        elif comparation_mode == "Por Learning Rate":
            col_division = "learning_rate"
            values = df_pivot["learning_rate"].unique()
        elif comparation_mode == "Por Número de Compañías":
            col_division = "number_of_companies"
            values = df_pivot["number_of_companies"].unique()
        else:
            col_division = None
            values = None

        fig = go.FigureWidget()

        color_map = (
            px.colors.qualitative.Plotly
        )  # usa una paleta de colores si hay más de 2 valores

        if col_division:
            color_dict = {
                val: color_map[i % len(color_map)] for i, val in enumerate(values)
            }

            for val in values:
                df_val = df_pivot[df_pivot[col_division] == val]

                hover_text = (
                    "Model: "
                    + df_val["model_name"]
                    + "<br>Algorithm: "
                    + df_val["algorithm"]
                    + "<br>Feature Extractor: "
                    + df_val["feature_extractor"]
                    + "<br>Phase: "
                    + df_val["phase"]
                    + "<br>Learning Rate: "
                    + df_val["learning_rate"].astype(str)
                    + "<br>Number of Companies: "
                    + df_val["number_of_companies"].astype(str)
                )

                fig.add_trace(
                    go.Scatter(
                        x=df_val[x_axis],
                        y=df_val[y_axis],
                        mode="markers",
                        marker=dict(color=color_dict[val], size=10),
                        name=str(val),
                        text=hover_text,
                        hoverinfo="text+x+y",
                    )
                )

        else:
            # Modo "Todos", usa tu lógica original con phase

            hover_text = (
                "Model: "
                + df_pivot["model_name"]
                + "<br  >Algorithm: "
                + df_pivot["algorithm"]
                + "<br>Feature Extractor: "
                + df_pivot["feature_extractor"]
                + "<br>Phase: "
                + df_pivot["phase"]
                + "<br>Learning Rate: "
                + df_pivot["learning_rate"].astype(str)
                + "<br>Number of Companies: "
                + df_pivot["number_of_companies"].astype(str)
            )

            fig.add_trace(
                go.Scatter(
                    x=df_pivot[x_axis],
                    y=df_pivot[y_axis],
                    mode="markers",
                    marker=dict(color=color_map[0], size=10),
                    text=hover_text,
                    hoverinfo="text+x+y",
                )
            )

        # Agregar modelos seleccionados con highlight
        if selected_models:
            for selected_model in selected_models:
                df_selected_all = df_pivot[df_pivot["model_name"] == selected_model]

                for _, row in df_selected_all.iterrows():
                    hover_text = (
                        f"Model: {row['model_name']}"
                        f"<br>Algorithm: {row['algorithm']}"
                        f"<br>Feature Extractor: {row['feature_extractor']}"
                        f"<br>Phase: {row['phase']}"
                        f"<br>Learning Rate: {row['learning_rate']}"
                        f"<br>Number of Companies: {row['number_of_companies']}"
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=[row[x_axis]],
                            y=[row[y_axis]],
                            mode="markers",
                            marker=dict(
                                color=["red", "pink"],
                                size=12,
                                line=dict(width=2, color="black"),
                            ),
                            name=f"{row['phase']} - {row['model_name']}",
                            text=[hover_text],
                            hoverinfo="text+x+y",
                        )
                    )

        fig.layout.hovermode = "closest"

        st.plotly_chart(fig)
else:
    st.warning("No hay datos disponibles en la base de datos.")
