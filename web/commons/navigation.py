import streamlit as st

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))


# --- Página de bienvenida ---
def welcome():
    # st.set_page_config(page_title="Inicio", layout="wide")
    st.title("Bienvenido 👋")
    st.markdown(f"### Hola, {st.session_state['username']}, nos alegra verte de nuevo.")
    st.markdown("---")
    st.subheader("Accesos rápidos")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Información Financiera"):
            st.switch_page("pages/1_Información_Financiera.py")

        if st.button("🧠 Evaluación de Modelos"):
            st.switch_page("pages/2_Evaluación_Modelos.py")

    with col2:
        if st.button("📈 Análisis de Métricas"):
            st.switch_page("pages/3_Análisis_Métricas_Modelos.py")

        if st.button("💼 Gestión de Carteras"):
            st.switch_page("pages/4_Gestión_de_Carteras.py")

    with col3:
        if st.button("🛠️ Creación de Modelos"):
            st.switch_page("pages/5_Creación_de_Modelos.py")


# --- Botón de logout ---
def logout():
    if st.button("Cerrar sesión"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()


# --- Barra de navegación lateral ---
def add_sidebar_navigation() -> st.navigation:
    welcome_page = st.Page(welcome, title="Inicio", icon=":material/home:")
    logout_page = st.Page(logout, title="Cerrar sesión", icon=":material/logout:")

    informacion_financiera_page = st.Page(
        "pages/1_Información_Financiera.py",
        title="Información Financiera",
        icon=":material/attach_money:",
    )

    evaluacion_modelos_page = st.Page(
        "pages/2_Evaluación_Modelos.py",
        title="Evaluación de Modelos",
        icon=":material/assessment:",
    )

    analisis_metricas_page = st.Page(
        "pages/3_Análisis_Métricas_Modelos.py",
        title="Análisis de Métricas de Modelos",
        icon=":material/leaderboard:",
    )

    gestion_carteras_page = st.Page(
        "pages/4_Gestión_de_Carteras.py",
        title="Gestión de Carteras",
        icon=":material/account_balance_wallet:",
    )

    creacion_modelos = st.Page(
        "pages/5_Creación_de_Modelos.py",
        title="Creación de Modelos",
        icon=":material/architecture:",
    )

    pg = st.navigation(
        pages={
            "Páginas": [
                welcome_page,
                informacion_financiera_page,
                evaluacion_modelos_page,
                analisis_metricas_page,
                gestion_carteras_page,
                creacion_modelos,
            ],
            "Cuenta": [logout_page],
        }
    )

    pg.run()
