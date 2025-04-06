import streamlit as st


def logged_in():
    return st.session_state["logged_in"]


def check_login():
    if not logged_in():
        st.error("Debes iniciar sesión para acceder a esta página.")
        st.stop()
