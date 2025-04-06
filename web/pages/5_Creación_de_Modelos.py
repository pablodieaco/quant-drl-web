import os
import subprocess
import time
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from quant_drl.configurations import get_complete_configuration
from quant_drl.trainer.trainer import Trainer

from web.commons.session import check_login
from web.commons.style_utils import add_logo
from web.pages.commons.database_connectors import (
    fetch_companies,
    fetch_favorite_portfolios,
    get_models_by_companies,
    insert_model,
    save_favorite_model,
    save_favorite_portfolio,
)


## Auxiliar Functions
def launch_tensorboard(logdir, port=6006):
    try:
        subprocess.Popen(
            ["tensorboard", f"--logdir={logdir}/", f"--port={port}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        # Esperamos un poco para que TensorBoard arranque
        time.sleep(3)
    except Exception as e:
        st.error(f"Error lanzando TensorBoard: {e}")


if "create_new_model" not in st.session_state:
    st.session_state.create_new_model = False
if "model_submitted" not in st.session_state:
    st.session_state.model_submitted = False
if "model_trained" not in st.session_state:
    st.session_state.model_trained = False
# change_theme_toogle()
add_logo(with_name=False, sidebar=True)
check_login()
# st.set_page_config(page_title="Creación de Modelos", layout="wide")


# Cargar modelos en Streamlit
st.title("🛠️ Creación de Modelos de Inversión")

# Selección de empresas y/o portafolios
selection_mode = st.sidebar.radio(
    "Seleccionar por:", ["Empresas", "Portafolios Favoritos"]
)

companies = fetch_companies()

companies_dict = {k: v for _, k, v, _ in companies}

if selection_mode == "Empresas":
    selected_companies_names = st.sidebar.multiselect(
        "Selecciona empresas", list(companies_dict.keys())
    )

    selected_companies_abv = [companies_dict[name] for name in selected_companies_names]

    # Guardar portfolio como Favorito
    portfolio_name = st.sidebar.text_input("Nombre del Portafolio:")
    if st.sidebar.button("Guardar como Favorito") and selected_companies_abv:
        save_favorite_portfolio(portfolio_name, selected_companies_abv)

elif selection_mode == "Portafolios Favoritos":
    favorite_portfolios = fetch_favorite_portfolios(st.session_state.get("user_id", 1))

    # --- Favorite Portfolio Selection ---
    favorite_selected = st.sidebar.selectbox(
        "Cargar Portafolio Favorito", list(favorite_portfolios.keys())
    )

    if favorite_selected:
        selected_companies_abv = favorite_portfolios[favorite_selected]
        if selected_companies_abv:
            selected_companies_names = [
                name
                for name, abv in companies_dict.items()
                if abv in selected_companies_abv
            ]

if not selected_companies_abv:
    st.warning("Selecciona al menos una empresa o portafolio favorito.")
    st.stop()

search_models = st.sidebar.button("Buscar Modelos")

if search_models:
    modelos = get_models_by_companies(selected_companies_abv, add_extras=True)
    if modelos is not None:
        df_modelos = pd.DataFrame(
            modelos,
            columns=[
                "model_id",
                "name",
                "algorithm",
                "feature_extractor",
                "normalization",
            ],
        )

        column_config = {
            "model_id": "Model ID",
            "algorithm": "Algoritmo",
            "feature_extractor": "Extractor de Características",
            "normalization": "Normalización",
            "name": "Nombre",
        }

        st.write("Modelos encontrados:")
        st.dataframe(
            df_modelos,
            column_config=column_config,
            hide_index=True,
        )

    else:
        st.warning("No se encontraron modelos para las empresas seleccionadas.")


# Model Creation
if st.sidebar.button("Crear Nuevo Modelo"):
    st.session_state.create_new_model = True

if st.session_state.create_new_model and not st.session_state.model_submitted:
    st.title("Creación de Modelos")

    st.write("Para crear un nuevo modelo, selecciona las características deseadas.")

    with st.form("form_model_creation"):
        model_name = st.text_input("Nombre del Modelo")
        algorithm = st.selectbox("Algoritmo", ["PPO", "SAC"])
        feature_extractor = st.selectbox(
            "Extractor de Características", ["Default", "LSTM", "CNNLSTM"]
        )
        learning_rate = st.number_input(
            "Tasa de Aprendizaje",
            min_value=1e-5,
            max_value=1e-2,
            value=1e-3,
            step=1e-5,
            format="%.5f",
        )
        normalization = st.selectbox(
            "Normalización", ["StandardScaler", "MinMaxScaler"]
        )
        years_train = st.number_input("Años de Entrenamiento", 3, 15, 10)
        years_test = st.number_input("Años de Prueba", 1, 5, 4)
        final_date = st.date_input(
            "Fecha Final de Evaluación",
            value=pd.Timestamp("2022-06-30"),
            max_value=pd.Timestamp("2022-06-30"),
            min_value=pd.Timestamp("2010-06-30"),
        )
        total_timesteps = st.number_input(
            "Total de Pasos de entrenamiento", 1e4, 1e6, 3e5
        )
        checkpoint_freq = st.number_input("Frecuencia de Checkpoints", 1e4, 1e5, 5e4)

        submitted = st.form_submit_button("Entrenar y Subir Modelo")

    if submitted:
        normalization_map = {
            "StandardScaler": "standard",
            "MinMaxScaler": "min_max",
        }

        st.session_state.form_values = {
            "model_name": model_name,
            "algorithm": algorithm,
            "feature_extractor": feature_extractor,
            "learning_rate": learning_rate,
            "normalization": normalization_map[normalization],
            "years_train": years_train,
            "years_test": years_test,
            "final_date": final_date,
            "total_timesteps": total_timesteps,
            "checkpoint_freq": checkpoint_freq,
        }

        st.session_state.model_submitted = True

if st.session_state.model_submitted and not st.session_state.model_trained:
    st.info("Configuración recibida. Comenzando entrenamiento...")
    values = st.session_state.form_values
    selected_companies_abv.remove("CASH")
    selected_companies_names.remove("Cash")
    configuration = get_complete_configuration(
        companies_pairs=list(zip(selected_companies_abv, selected_companies_names)),
        key_value_pairs={
            "algorithm": values["algorithm"],
            "feature": values["feature_extractor"],
            "normalize": values["normalization"],
            "length_train_data": values["years_train"],
            "length_eval_data": values["years_test"],
            "end_date": values["final_date"],
            "total_timesteps": values["total_timesteps"],
            "checkpoint_freq": values["checkpoint_freq"],
            "model_name": values["model_name"],
            "user_id": st.session_state.get("user_id", 1),
        },
    )

    trainer = Trainer(
        configuration,
        generate_default_name=False,
        run=False,
        logs_dir="../logs/",
        save_dir="../models/",
    )

    # Directorio de logs por usuario
    user_id = st.session_state.get("user_id", 1)
    logdir = os.path.abspath(f"../logs/USERS/{user_id}")
    launch_tensorboard(logdir)

    # Mostrar TensorBoard embebido
    components.iframe("http://localhost:6006", height=600)

    # Entrenar modelo
    with st.spinner("Creando Modelo..."):
        trainer.run_experiment()

    selected_companies_abv.append("CASH")
    selected_companies_names.append("Cash")
    model_id = insert_model(
        name=values["model_name"],
        algorithm=values["algorithm"],
        feature_extractor=values["feature_extractor"],
        companies_abv=selected_companies_abv,
        file_path=trainer.save_path,
        created_at=datetime.now(),
        normalization=values["normalization"],
    )

    if model_id:
        saved = save_favorite_model(
            user_id=st.session_state.get("user_id", 1),
            model_id=model_id,
            favorite_name=model_name,
        )
        if saved:
            st.success("✅ Modelo creado exitosamente.")
            st.balloons()
        st.session_state.model_trained = True
    else:
        st.error("❌ Error al crear el modelo.")

if st.session_state.model_trained:
    st.write("Puedes ahora pasar a la evaluación del modelo.")
