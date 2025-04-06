import io
import json
import os
import re
import time
from typing import Optional, Union

import matplotlib.colors as mcolors
import matplotx
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from matplotlib import pyplot as plt
from quant_drl.configurations import get_companies, get_complete_configuration
from quant_drl.tester.tester import Tester

from web.commons.session import check_login
from web.commons.style_utils import add_logo
from web.pages.commons.database_connectors import (
    fetch_favorite_portfolios,
    get_companies_from_model,
    get_favorite_models,
    get_model_information,
    get_models,
    get_models_by_companies,
    save_favorite_model,
)

# change_theme_toogle()
add_logo(with_name=False, sidebar=True)
check_login()


## Funciones auxiliares


def color_name_to_rgba(color_name, alpha=0.2):
    """Convierte un nombre de color (e.g., 'blue') a formato rgba con opacidad."""
    rgb = mcolors.to_rgb(color_name)
    return (
        f"rgba({int(rgb[0] * 255)}, {int(rgb[1] * 255)}, {int(rgb[2] * 255)}, {alpha})"
    )


def count_financial_days(start_date, end_date) -> int:
    import yfinance

    data = yfinance.download("AAPL", start=start_date, end=end_date)

    if data.empty:
        return 0, None, None
    return len(data), data.index.min().date(), data.index.max().date()


def plot_box_plot(data, title, y_label, color):
    fig = go.Figure()
    fig.add_trace(
        go.Box(
            y=data,
            name=title,
            boxpoints="outliers",
            line=dict(color=color),
            fillcolor=color,
        )
    )
    fig.update_layout(title=title, yaxis_title=y_label, template="plotly_white")
    return fig


def plot_hist_plot(data, title, x_label, color):
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=data, name=title, opacity=0.75, marker_color=color))
    fig.update_layout(
        barmode="overlay", title=title, xaxis_title=x_label, template="plotly_white"
    )
    return fig


def plot_evolution_mean_std(data, title, color="blue"):
    mean_data = np.mean(data, axis=0)
    std_data = np.std(data, axis=0)
    steps = list(range(len(mean_data)))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=steps,
            y=mean_data,
            mode="lines",
            name="Mean",
            line=dict(color=color),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=steps + steps[::-1],
            y=(mean_data + std_data).tolist() + (mean_data - std_data).tolist()[::-1],
            fill="toself",
            fillcolor=color_name_to_rgba(color, 0.2),
            line=dict(color=color),
            name="Std",
        )
    )
    fig.update_layout(title=title, template="plotly_white")
    return fig


def render_animation(path):
    with open(path) as f:
        return json.load(f)


def map_model_steps_size(
    model_base_path: str, model_size: str
) -> Optional[Union[str, None]]:
    """
    Mapea el tamaño del modelo (Small, Medium, Large) al path del modelo correspondiente.
    - Small: modelo con menor cantidad de steps.
    - Medium: modelo con cantidad de steps intermedia.
    - Large: modelo final (model_final.zip).
    """
    files = os.listdir(model_base_path)

    # step_model_files = []
    step_values = []
    has_final = False

    for file in files:
        if match := re.match(r"model_(\d+)_steps\.zip", file):
            step_values.append(int(match.group(1)))
        elif file == "model_final.zip":
            has_final = True

    step_values.sort()

    if model_size == "Large":
        if has_final:
            return None
        elif step_values:
            return step_values[-1]
        else:
            FileNotFoundError(f"There are no saved models for {model_base_path}.")

    if not step_values:
        raise FileNotFoundError("No se encontraron modelos con steps.")

    step_values.sort()

    if model_size == "Small":
        return step_values[0]
    elif model_size == "Medium":
        return step_values[len(step_values) // 2]
    else:
        raise ValueError("Tamaño de modelo no válido. Usa: 'Small', 'Medium', 'Large'.")


##


# st.set_page_config(page_title="Evaluación de Modelos", layout="wide")

# Cargar modelos en Streamlit
st.title("🧠 Evaluación de Modelos")

continue_flag = False
selected_model = None
modelos_dict = None
selected_model_id = None
selected_companies_abv = []
selected_companies_names = []
selection_mode_models = "Global"
# --- Selection Mode ---
selection_mode = st.sidebar.radio(
    "Seleccione un módo de búsqueda", ["Por Portfolio", "Por Nombre"], horizontal=True
)
if selection_mode == "Por Portfolio":
    # Lista de empresas (ejemplo con tickers de Yahoo Finance)
    companies_abv, companies_names = get_companies()
    # Diccionario de empresas
    companies_dict = dict(zip(companies_names, companies_abv))

    selected_companies_abv = []
    selected_companies_names = []

    # --- Favorite Portfolio Selection ---
    favorite_portfolios = fetch_favorite_portfolios(st.session_state.get("user_id", 1))

    if not favorite_portfolios:
        st.warning(
            "No se encontraron portafolios favoritos. Visita la sección de 'Gestión de Carteras' para crear uno."
        )
        st.stop()

    favorite_selected = st.sidebar.selectbox(
        "Seleccione un Portafolio", list(favorite_portfolios.keys())
    )
    if favorite_selected:
        selected_companies_abv = favorite_portfolios[favorite_selected]
        selected_companies_names = [
            name
            for name, abv in companies_dict.items()
            if abv in selected_companies_abv
        ]

        modelos_dict = get_models_by_companies(selected_companies_abv)

    if not modelos_dict:
        st.warning("No se encontraron modelos con las empresas seleccionadas.")
        st.stop()
    else:
        selected_model = st.sidebar.selectbox(
            "Seleccione un modelo", modelos_dict.keys()
        )
        selected_model_id = modelos_dict[selected_model]


else:  # Por Modelos
    # --- Selection Mode ---
    selection_mode_models = st.sidebar.radio(
        "Seleccione un tipo de búsqueda de modelos",
        ["Favoritos", "Todos"],
        horizontal=True,
    )

    if selection_mode_models == "Todos":
        modelos_dict = get_models()

        selected_model = st.sidebar.selectbox(
            "Seleccione un modelo", modelos_dict.keys()
        )
    else:
        modelos_list = get_favorite_models(st.session_state.get("user_id", 1))

        if modelos_list:
            favorites_names = list(map(lambda x: x[0], modelos_list))

            selected_model = st.sidebar.selectbox(
                "Seleccione un modelo",
                favorites_names,
            )

            selected_model = list(
                filter(lambda x: x[0] == selected_model, modelos_list)
            )[0][1]

            modelos_dict = dict(
                zip(
                    list(map(lambda x: x[1], modelos_list)),
                    list(map(lambda x: x[2], modelos_list)),
                ),
            )
        else:
            st.warning("No se encontraron modelos favoritos")

if not selected_model:
    st.warning("Seleccione un modelo para continuar.")
    st.stop()

selected_model_id = modelos_dict[selected_model]

associated_companies = get_companies_from_model(selected_model_id)

if not associated_companies:
    st.warning("No se encontraron empresas asociadas al modelo seleccionado.")
    st.stop()

selected_companies_abv = list(associated_companies.values())
selected_companies_names = list(associated_companies.keys())
selected_companies_abv.remove("CASH")
selected_companies_names.remove("Cash")
continue_flag = True

if selection_mode_models == "Todos":
    # Guardar modelo favorito
    favorite_name = st.sidebar.text_input(
        "Asignar nombre al modelo",
        placeholder="Alias para el modelo.",
    )
    if st.sidebar.button("⭐ Guardar como Favorito") and favorite_name:
        save_favorite_model(
            st.session_state.get("user_id", 1),
            selected_model_id,
            favorite_name,
        )

model_size = st.sidebar.select_slider(
    "Modelos", ["Small", "Medium", "Large"], value="Medium"
)
# Mostrar al usuario las empresas asociadas al modelo

with st.expander("Ver Empresas Asociadas", expanded=False, icon="ℹ️"):
    st.subheader("Empresas Asociadas al Modelo")
    df_companies = pd.DataFrame(
        list(associated_companies.items()), columns=["Empresa", "Ticker"]
    )
    st.dataframe(df_companies, use_container_width=True, hide_index=True)

# Botón para actualizar
if st.sidebar.button("Actualizar Datos"):
    st.rerun()
    time.sleep(0.5)

if not continue_flag:
    st.stop()

companies_pairs = list(zip(selected_companies_abv, selected_companies_names))

configuration = get_complete_configuration(companies_pairs=companies_pairs)
time.sleep(1)

# # Selección de fechas para evaluación
evaluation_type = st.radio(
    "Tipo de Evaluación", ["En Lote", "Individual"], horizontal=True
)
st.subheader("Seleccione métricas para la evaluación")
min_date = pd.to_datetime("2010-01-01")
max_date = pd.Timestamp.today().date()


if evaluation_type == "Individual":
    start_date, end_date = st.date_input(
        label="Rango de fechas",
        value=(pd.to_datetime("2024-03-01"), pd.to_datetime("2024-05-31")),
        min_value=min_date,
        max_value=max_date,
    )
    number_of_days, start_eval, end_eval = count_financial_days(start_date, end_date)
    if number_of_days == 0:
        st.error("No hay datos para el rango de fechas seleccionado.")
        st.stop()

    st.markdown(f"Rango de fechas con mercado abierto: {start_date} - {end_date}")

    configuration["steps"] = number_of_days
    configuration["length_train_data"] = 1

    if st.button("Cargar y Evaluar Modelo"):
        try:
            (model_path, normalization, algorithm, feature_extractor, num_assets) = (
                get_model_information(selected_model_id)
            )
            full_path, _ = model_path.rsplit("/", 1)
            base_path, model_name = full_path.rsplit("/", 1)

            configuration["normalize"] = normalization

            tester = Tester(configuration, setup=False)
            tester.reset_data_env(
                start_eval_date=start_eval,
                end_eval_date=end_eval,
                random_initialization=False,
            )
            steps_selected = map_model_steps_size(
                model_base_path=full_path, model_size=model_size
            )
            with st.spinner("Cargando el modelo... Esto puede tardar unos segundos."):
                tester.load_model(
                    base_path,
                    model_name,
                    algorithm=algorithm,
                    steps=steps_selected,
                    feature_extractor=feature_extractor,
                    num_assets=num_assets,
                )
                st.success(
                    f"Modelo cargado correctamente. {model_name} con {steps_selected} steps."
                )
        except Exception as e:
            st.error(f"Error al cargar el modelo: {e}")

        st.subheader("Evaluación en Progreso")

        # Mostrar animación mientras se evalúa el modelo
        with st.spinner("Evaluando el modelo... Esto puede tardar unos segundos."):
            info_eval = tester.evaluate(num_episodes=1)

        internal_env = tester.port_eval_env.envs[0].env
        filtered_dates = list(
            filter(
                lambda x: x >= start_eval and x <= end_eval,
                map(lambda x: x.date(), internal_env.dates),
            )
        )

        dates_str = [d.strftime("%Y-%m-%d") for d in filtered_dates]

        # Ocultar animación y mostrar mensaje de éxito
        st.success("Evaluación completada.")

        # Extraer métricas de la evaluación
        rewards = np.array(info_eval["all_rewards"][0])
        rewards = rewards.reshape(-1)
        acumulated_rewards = np.array(info_eval["all_episode_rewards"][0])
        sharpes = np.array(info_eval["all_sharpes"][0])
        pvs = np.array(info_eval["all_pvs"][0])
        actions = np.array(info_eval["all_actions"][0])

        # Sección de gráficos
        st.subheader("Resultados de la Evaluación")

        # Gráficos de evolución
        st.markdown("### Evolución de las Métricas Durante la Simulación")
        col1, col2 = st.columns(2)
        steps = list(range(len(rewards)))

        fig_rewards = go.Figure()
        fig_rewards.add_trace(
            go.Scatter(x=dates_str, y=rewards, mode="lines", name="Rewards")
        )
        fig_rewards.update_layout(
            title="Evolución de los Rewards", template="plotly_white"
        )
        col1.plotly_chart(fig_rewards)

        fig_acumulated_rewards = go.Figure()
        fig_acumulated_rewards.add_trace(
            go.Scatter(
                x=dates_str,
                y=acumulated_rewards,
                mode="lines",
                name="Acumulated Rewards",
            )
        )
        fig_acumulated_rewards.update_layout(
            title="Evolución de los Rewards Acumulados", template="plotly_white"
        )
        col2.plotly_chart(fig_acumulated_rewards)

        st.markdown("### Evolución de Portfolio Value y Sharpe Ratio")
        col1, col2 = st.columns(2)
        fig_pvs = go.Figure()
        fig_pvs.add_trace(
            go.Scatter(x=dates_str, y=pvs, mode="lines", name="Portfolio Value")
        )
        fig_pvs.update_layout(
            title="Evolución de Portfolio Value", template="plotly_white"
        )
        col1.plotly_chart(fig_pvs)

        fig_sharpes = go.Figure()
        fig_sharpes.add_trace(
            go.Scatter(x=dates_str, y=sharpes, mode="lines", name="Sharpe Ratio")
        )
        fig_sharpes.update_layout(
            title="Evolución de Sharpe Ratio", template="plotly_white"
        )
        col2.plotly_chart(fig_sharpes)

        st.markdown("### Evolución de los pesos del portfolio")
        actions_reshaped = actions.reshape(-1, len(selected_companies_abv) + 1)

        with plt.style.context(matplotx.styles.dracula):
            fig, ax = plt.subplots(figsize=(12, 6))

            colors = plt.cm.tab20.colors

            ax.stackplot(
                dates_str,
                actions_reshaped.T,
                labels=["Cash"] + selected_companies_names,
                alpha=0.8,
                colors=colors,
            )

            ax.set_xlabel("Steps", fontsize=12, color="white")
            ax.tick_params(axis="x", rotation=90)
            ax.set_ylabel("Cantidad Asignada", fontsize=12, color="white")
            legend = ax.legend(
                loc="upper right",
                bbox_to_anchor=(
                    1.3,
                    1,
                ),
                fontsize=10,
                facecolor="black",
                edgecolor="white",
                framealpha=0.9,
            )

            st.pyplot(fig)

else:
    col1, col2 = st.columns(2)
    start_eval, end_eval = col1.date_input(
        label="Rango de fechas",
        value=(pd.to_datetime("2023-01-01"), pd.to_datetime("2024-12-31")),
        min_value=min_date,
        max_value=max_date,
    )

    num_episodes = col2.number_input("Número de Simulaciones", 1, 100, 50, format="%d")

    if (end_eval - start_eval).days < 150:
        st.warning(
            "El rango de fechas para la evaluación en lote debe ser de al menos de 6 meses."
        )
        st.stop()

    if st.button("Cargar y Evaluar Modelo"):
        try:
            model_path, normalization, algorithm, feature_extractor, num_assets = (
                get_model_information(selected_model_id)
            )
            full_path, _ = model_path.rsplit("/", 1)
            base_path, model_name = full_path.rsplit("/", 1)

            configuration["normalize"] = normalization

            tester = Tester(configuration, setup=False)
            tester.reset_data_env(
                start_eval_date=start_eval,
                end_eval_date=end_eval,
                random_initialization=True,
            )

            steps_selected = map_model_steps_size(
                model_base_path=full_path, model_size=model_size
            )
            with st.spinner("Cargando el modelo... Esto puede tardar unos segundos."):
                tester.load_model(
                    base_path,
                    model_name,
                    algorithm=algorithm,
                    steps=steps_selected,
                    feature_extractor=feature_extractor,
                    num_assets=num_assets,
                )
                st.success(
                    f"Modelo cargado correctamente. {model_name} con {steps_selected} steps."
                )
        except Exception as e:
            st.error(f"Error al cargar el modelo: {e}")

        with st.spinner("Evaluando el modelo... Esto puede tardar unos segundos."):
            info_eval = tester.evaluate(num_episodes=num_episodes)
            st.success("Evaluación completada.")

        # Extraer métricas
        final_rewards = info_eval["final_rewards"]
        final_pvs = info_eval["final_pvs"]
        all_episode_rewards = info_eval["all_episode_rewards"]
        all_pvs = info_eval["all_pvs"]
        all_sharpes = info_eval["all_sharpes"]

        df_resultados = pd.DataFrame(
            {
                "Simulación": [f"Sim {i + 1}" for i in range(len(final_rewards))],
                "Recompensa Final": info_eval["final_rewards"],
                "Valor Portfolio Final": info_eval["final_pvs"],
                "Final MDD": info_eval["final_drawdowns"],
                "Media Sharpe Ratio": info_eval["mean_sharpes"],
                "Media Reward": info_eval["mean_rewards"],
                "Media Portfolio Value": info_eval["mean_pvs"],
                "Std Sharpe Ratio": info_eval["std_sharpes"],
                "Std Reward": info_eval["std_rewards"],
                "Std Portfolio Value": info_eval["std_pvs"],
            }
        )

        df_stats = df_resultados.describe().T

        df_stats["Feature"] = [
            "Recompensa Final",
            "Valor Portfolio Final",
            "Final MDD",
            "Media Sharpe Ratio",
            "Media Reward",
            "Media Portfolio Value",
            "Std Sharpe Ratio",
            "Std Reward",
            "Std Portfolio Value",
        ]

        col1, col2 = st.columns(2)

        # Convertir el DataFrame a un CSV en memoria
        csv_buffer = io.StringIO()
        df_resultados.to_csv(csv_buffer, index=False, sep=";", decimal=",")
        csv_data = csv_buffer.getvalue()

        col1.download_button(
            label="📥 Descargar Resultados en CSV",
            data=csv_data,
            file_name="resultados_evaluacion.csv",
            mime="text/csv",
        )

        # csv_buffer.close()

        csv_buffer_stats = io.StringIO()
        df_stats.to_csv(csv_buffer_stats, index=False, sep=";", decimal=",")
        csv_data_stats = csv_buffer_stats.getvalue()

        col2.download_button(
            label="📥 Descargar Estadísticas en CSV",
            data=csv_data_stats,
            file_name="estadisticas_evaluacion.csv",
            mime="text/csv",
        )

        # Sección de gráficos
        st.header("Resultados de la Evaluación")

        # Gráficos de Boxplots
        with st.expander("Boxplots de Resultados", expanded=False):
            col1, col2 = st.columns(2)
            col1.plotly_chart(
                plot_box_plot(
                    final_rewards, "Recompensa final", "Recompensa", color="blue"
                )
            )
            col2.plotly_chart(
                plot_box_plot(
                    final_pvs,
                    "Valor del portfolio final",
                    "Valor del portfolio (USD)",
                    color="green",
                )
            )

        # Gráficos de Histogramas
        with st.expander("#### Histogramas de Resultados", expanded=False):
            col1, col2 = st.columns(2)
            col1.plotly_chart(
                plot_hist_plot(
                    final_rewards, "Recompensa final", "Recompensa", color="blue"
                )
            )
            col2.plotly_chart(
                plot_hist_plot(
                    final_pvs,
                    "Valor del portfolio final",
                    "Valor del portfolio (USD)",
                    color="green",
                )
            )

        # Gráficos de Evolución de las métricas en
        with st.expander("#### Evolución de las Métricas", expanded=False):
            st.plotly_chart(
                plot_evolution_mean_std(
                    all_episode_rewards,
                    "Recompensa acumulada (Promedio por día)",
                    color="blue",
                )
            )
            st.plotly_chart(
                plot_evolution_mean_std(
                    all_pvs, "Valor del Portfolio (Promedio por día)", color="green"
                )
            )
            st.plotly_chart(
                plot_evolution_mean_std(
                    all_sharpes, "Valor del Sharpe Ratio (Promedio)", color="purple"
                )
            )

        with st.expander("#### Simulaciones Individuales", expanded=False):
            fig_sim_rewards = go.Figure()
            fig_sim_pvs = go.Figure()

            for i in range(len(all_episode_rewards)):  # Iterar sobre cada simulación
                fig_sim_rewards.add_trace(
                    go.Box(
                        y=all_episode_rewards[i],
                        name=f"Sim {i + 1}",
                        marker_color="blue",
                    )
                )
                fig_sim_pvs.add_trace(
                    go.Box(y=all_pvs[i], name=f"Sim {i + 1}", marker_color="green")
                )

            fig_sim_rewards.update_layout(
                title="Distribución de recompensa por Simulación",
                template="plotly_white",
            )
            fig_sim_pvs.update_layout(
                title="Distribución del valor del portfolio por Simulación",
                template="plotly_white",
            )

            st.plotly_chart(fig_sim_rewards)
            st.plotly_chart(fig_sim_pvs)

        st.success("Análisis completado con éxito.")
