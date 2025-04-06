import streamlit as st


def check_theme():
    if "theme" not in st.session_state:
        st.session_state.theme = "light"

    return st.session_state.theme


def change_theme_toogle():
    # label="🌙 Dark Mode"
    """Change the theme of the app."""

    # Determinar el tema actual
    actual_theme = check_theme()

    # Definir si el toggle está activado
    toggle_value = actual_theme == "dark"

    # Cambiar el label dinámicamente
    label_text = "🌙 Dark Mode" if toggle_value else "☀️ Light Mode"

    # Mostrar el toggle
    toggle = st.sidebar.toggle(
        label=label_text,
        value=toggle_value,
        key="theme_toggle",
        help="Cambiar el tema de la app",
    )

    if toggle != toggle_value:
        # Cambiar el estado del tema
        new_theme = "dark" if toggle else "light"
        st.session_state.theme = new_theme
        st.set_option("theme.base", new_theme)


def add_logo(with_name=False, sidebar=True):
    theme = check_theme()

    logo_path_name = (
        "web/images/logo-name-light-background.png"
        if theme == "light"
        else "web/images/logo-name-dark-background.png"
    )
    logo_path = (
        "web/images/logo-light-background.png"
        if theme == "light"
        else "web/images/logo-dark-background.png"
    )

    if sidebar:
        # st.sidebar.image(
        #     logo_path,
        #     # use_container_width=True,
        #     width=100,
        # )
        st.logo(
            logo_path_name,
            size="large",
            icon_image=logo_path,
        )

    else:
        st.image(
            logo_path_name,
            # use_container_width=True,
            width=400,
            output_format="auto",
        )
