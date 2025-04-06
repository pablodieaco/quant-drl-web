import bcrypt
import streamlit as st
from commons.navigation import add_sidebar_navigation
from commons.style_utils import add_logo
from db.commons.db_connection import connect_db

# --- Initialize session state variables ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None


# --- Function to authenticate user ---
def authenticate_user(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    conn.close()

    if result:
        hashed_password = result[0]
        return bcrypt.checkpw(password.encode(), hashed_password.encode())
    return False


# --- Function to register users ---
def register_user(username, email, password):
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (username, email, hashed_password),
        )
        conn.commit()
        st.success("Usuario registrado exitosamente.")
        return True
    except Exception as e:
        st.error(f"Error al registrar usuario: {e}")
        return False
    finally:
        conn.close()


# --- Login Page ---
def login():
    st.title("Iniciar Sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if authenticate_user(username, password):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")


# --- Registration Page ---
def register():
    st.title("Registro de Usuario")

    username = st.text_input("Usuario")
    email = st.text_input("Correo Electrónico")
    password = st.text_input("Contraseña", type="password")
    confirm_password = st.text_input("Repetir Contraseña", type="password")

    if st.button("Registrarse"):
        if not username or not email or not password or not confirm_password:
            st.warning("Por favor, completa todos los campos.")
        elif password != confirm_password:
            st.error("Las contraseñas no coinciden.")
        else:
            if register_user(username, email, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.rerun()


# --- Main App Controller ---
def app():
    # change_theme_toogle()
    add_logo(with_name=True, sidebar=False)
    add_logo(with_name=False, sidebar=True)
    if st.session_state["logged_in"]:
        add_sidebar_navigation()
    else:
        login_page = st.Page(login, title="Log in", icon=":material/login:")
        register_page = st.Page(
            register, title="Register", icon=":material/assignment:"
        )

        pg = st.navigation(pages={"Cuenta": [login_page, register_page]})
        pg.run()


app()
