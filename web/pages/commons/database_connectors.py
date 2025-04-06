import os
import sys
from datetime import datetime as timestamp

import pandas as pd
import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from web.db.commons.db_connection import connect_db


# INFORMACION FINANCIERA
def fetch_companies():
    """Fetch companies from the PostgreSQL database."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT company_id, name, ticker, sector FROM companies;")
    companies = cursor.fetchall()
    conn.close()

    return companies  # Returns a dictionary { 'Company Name': 'Ticker' }


def fetch_favorite_portfolios(user_id):
    """Fetch favorite portfolios for the user from the database."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT f.favorite_id, p.name, ARRAY_AGG(c.ticker) 
        FROM favorites f 
        JOIN portfolios p ON f.reference_id = p.portfolio_id 
        JOIN portfolio_companies pc ON p.portfolio_id = pc.portfolio_id
        JOIN companies c ON pc.company_id = c.company_id
        WHERE f.type = 'portfolio' AND f.user_id = %s
        GROUP BY f.favorite_id, p.name;
    """,
        (user_id,),
    )  # Replace with real user_id
    portfolios = cursor.fetchall()
    conn.close()

    return {p[1]: p[2] for p in portfolios}


def save_favorite_portfolio(portfolio_name, selected_tickers):
    """Save the selected portfolio as a favorite."""
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Insert portfolio
        cursor.execute(
            "INSERT INTO portfolios (user_id, name) VALUES (%s, %s) RETURNING portfolio_id;",
            (st.session_state.get("user_id", 1), portfolio_name),
        )
        portfolio_id = cursor.fetchone()[0]

        # Insert companies into portfolio
        for ticker in selected_tickers:
            cursor.execute(
                "INSERT INTO portfolio_companies (portfolio_id, company_id) VALUES (%s, (SELECT company_id FROM companies WHERE ticker = %s));",
                (portfolio_id, ticker),
            )

        # Mark as favorite
        cursor.execute(
            "INSERT INTO favorites (user_id, type, reference_id, name) VALUES (%s, 'portfolio', %s, %s);",
            (st.session_state.get("user_id", 1), portfolio_id, portfolio_name),
        )

        conn.commit()
        st.success(f"Portafolio '{portfolio_name}' guardado como favorito.")
    except Exception as e:
        conn.rollback()
        st.error(f"Error al guardar el portafolio: {e}")
    finally:
        conn.close()


# EVALUACION DE MODELOS
def get_model_information(model_id: str) -> str:
    query = """
        SELECT file_path, normalization, algorithm, feature_extractor, ncompanies
        FROM models
        WHERE model_id = %s;
        """
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(query, (model_id,))
        file_path, normalization, algorithm, feature_extractor, num_assets = (
            cursor.fetchone()
        )
        cursor.close()
        return file_path, normalization, algorithm, feature_extractor, num_assets
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return ""


def get_models() -> dict:
    """Función que obtiene todos los modelos de la base de datos y sus compañías asociadas."""
    query = """
        SELECT m.model_id, m.name
        FROM models m
        """
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(query)
        modelos = pd.DataFrame(
            cursor.fetchall(), columns=[desc[0] for desc in cursor.description]
        )
        cursor.close()
        return dict(zip(modelos["name"], modelos["model_id"]))
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return {}


def get_companies_from_model(model_id: str) -> dict:
    """Función que obtiene las compañías asociadas a un modelo."""
    query = """
        SELECT c.name AS company_name, c.ticker AS company_abv
        FROM model_companies mc
        JOIN companies c ON mc.company_id = c.company_id
        JOIN models m ON mc.model_id = m.model_id
        WHERE m.model_id = %s;
        """

    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(query, (model_id,))
        companies = pd.DataFrame(
            cursor.fetchall(), columns=[desc[0] for desc in cursor.description]
        )
        cursor.close()
        return dict(zip(companies["company_name"], companies["company_abv"]))
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return {}


def get_models_by_companies(companies_abv: list, add_extras: bool = False):
    """
    Obtiene los modelos que tienen exactamente las compañías especificadas.

    :param companies: Lista de nombres de compañías.
    :return: DataFrame con los modelos filtrados.
    """
    if not companies_abv:
        return {}

    placeholders = ",".join(["%s"] * len(companies_abv))
    query = f"""
        SELECT m.model_id, m.name, m.algorithm, m.feature_extractor, m.normalization
        FROM model_companies mc
        JOIN models m ON mc.model_id = m.model_id
        JOIN companies c ON mc.company_id = c.company_id
        WHERE c.ticker IN ({placeholders}) AND m.ncompanies = %s
        GROUP BY m.model_id, m.name
        HAVING 
            COUNT(DISTINCT c.ticker) = %s
            AND COUNT(*) = %s;
    """

    params = (
        *companies_abv,
        len(companies_abv) - 1,
        len(companies_abv),
        len(companies_abv),
    )

    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(query, params)
        modelos = pd.DataFrame(
            cursor.fetchall(), columns=[desc[0] for desc in cursor.description]
        )
        cursor.close()
        if add_extras:
            return modelos
        return dict(zip(modelos["name"], modelos["model_id"]))
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return {}


def get_favorite_models(user_id: int) -> list:
    """Obtener los modelos favoritos de un usuario."""
    query = """
        SELECT m.model_id AS model_id, m.name AS name, f.name AS favorite_name
        FROM favorites f
        JOIN models m ON f.reference_id = m.model_id
        WHERE f.user_id = %s AND f.type = 'model';
        """
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        modelos = pd.DataFrame(
            cursor.fetchall(), columns=[desc[0] for desc in cursor.description]
        )
        cursor.close()
        return list(
            tuple(zip(modelos["favorite_name"], modelos["name"], modelos["model_id"]))
        )
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return []


def save_favorite_model(user_id: int, model_id: int, favorite_name: str = None) -> bool:
    """Save the selected model as a favorite for the user."""
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO favorites (user_id, type, reference_id, name) VALUES (%s, 'model', %s, %s);",
            (user_id, model_id, favorite_name),
        )
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error al guardar el modelo favorito: {e}")
        return False


# ANALISIS METRICAS MODELOS
def get_evaluations():
    """Returns evaluation metrics for each model in the database."""
    query = """
        SELECT ev.evaluation_id, ev.model_id, m.name AS model_name, m.algorithm, m.feature_extractor, m.normalization,
               ev.start_date, ev.end_date, ev.num_evaluations, ev.phase, 
               evm.metric_name, evm.value
        FROM evaluations ev
        JOIN evaluation_metrics evm ON ev.evaluation_id = evm.evaluation_id
        JOIN models m ON ev.model_id = m.model_id
    """

    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(query)
        model_information = pd.DataFrame(
            cursor.fetchall(), columns=[desc[0] for desc in cursor.description]
        )
        conn.close()
        return model_information
    except Exception as e:
        st.error(f"Error fetching model information: {e}")
        return pd.DataFrame()


def get_evaluation_by_model(model_id):
    """Fetch evaluation metrics for a specific model."""
    query = """
        SELECT ev.evaluation_id, ev.start_date, ev.end_date, ev.num_evaluations, ev.phase,
               evm.metric_name, evm.value
        FROM evaluations ev
        JOIN evaluation_metrics evm ON ev.evaluation_id = evm.evaluation_id
        WHERE ev.model_id = %s
    """

    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(query, (model_id,))
        model_evaluation = pd.DataFrame(
            cursor.fetchall(), columns=[desc[0] for desc in cursor.description]
        )
        conn.close()
        return model_evaluation
    except Exception as e:
        st.error(f"Error fetching evaluation for model {model_id}: {e}")
        return pd.DataFrame()


#
def get_portfolios_from_user(user_id: str):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM portfolios WHERE user_id = {user_id}")
    portfolios = cursor.fetchall()
    return portfolios


def get_companies_from_portfolio(portfolio_id):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT c.company_id, c.name, c.ticker, c.sector, c.market_cap 
        FROM portfolio_companies pc
        JOIN companies c ON pc.company_id = c.company_id
        WHERE pc.portfolio_id = %s
        """,
        (portfolio_id,),
    )
    companies = cursor.fetchall()
    cursor.close()
    db.close()
    return companies


def check_if_portfolio_has_assets_weights(portfolio_id):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM portfolio_weights WHERE portfolio_id = %s",
        (portfolio_id,),
    )
    has_weights = cursor.fetchone()[0] > 0
    cursor.close()
    db.close()
    return has_weights


def get_weights_for_portfolio(portfolio_id):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT c.name, c.ticker, pw.weight, pw.recorded_at, p.portfolio_value, pw.weight * p.portfolio_value as invested
        FROM portfolio_weights as pw
        JOIN companies as c ON pw.company_id = c.company_id
        JOIN portfolios as p ON pw.portfolio_id = p.portfolio_id
        WHERE pw.portfolio_id = %s ORDER BY pw.recorded_at DESC;
        """,
        (portfolio_id,),
    )
    weights = cursor.fetchall()
    db.close()
    print("Weights:", weights)
    return weights


def save_weights_for_portfolio(portfolio_id, companies_weights):
    db = connect_db()
    cursor = db.cursor()
    date = timestamp.now().date()

    # Verificar si las empresas están registradas en portfolio_companies
    cursor.execute(
        "SELECT company_id FROM portfolio_companies WHERE portfolio_id = %s",
        (portfolio_id,),
    )
    registered_companies = {row[0] for row in cursor.fetchall()}
    input_companies = set(companies_weights.keys())

    print("Registered companies:", registered_companies)
    print("Input companies:", input_companies)

    if input_companies != registered_companies:
        missing = registered_companies - input_companies
        extra = input_companies - registered_companies
        error_msg = []
        if missing:
            error_msg.append(f"Faltan empresas: {missing}")
        if extra:
            error_msg.append(f"Empresas no registradas: {extra}")
        st.error(" | ".join(error_msg))
        return False

    # Guardar pesos
    for company_id, weight in companies_weights.items():
        cursor.execute(
            "INSERT INTO portfolio_weights (portfolio_id, company_id, weight, recorded_at) VALUES (%s, %s, %s, %s)",
            (portfolio_id, company_id, weight, date),
        )

    db.commit()
    cursor.close()
    db.close()
    st.success("Pesos actualizados correctamente.")
    return True


def save_favorite_portfolio(portfolio_name, selected_tickers, portfolio_value=0.0):
    """Save the selected portfolio as a favorite."""
    conn = connect_db()
    cursor = conn.cursor()

    selected_tickers.append("CASH")

    try:
        # Insert portfolio
        cursor.execute(
            "INSERT INTO portfolios (user_id, name, portfolio_value) VALUES (%s, %s, %s) RETURNING portfolio_id;",
            (st.session_state.get("user_id", 1), portfolio_name, portfolio_value),
        )
        portfolio_id = cursor.fetchone()[0]

        # Insert companies into portfolio
        for ticker in selected_tickers:
            cursor.execute(
                "INSERT INTO portfolio_companies (portfolio_id, company_id) VALUES (%s, (SELECT company_id FROM companies WHERE ticker = %s));",
                (portfolio_id, ticker),
            )

        # Mark as favorite
        cursor.execute(
            "INSERT INTO favorites (user_id, type, reference_id, name) VALUES (%s, 'portfolio', %s, %s);",
            (st.session_state.get("user_id", 1), portfolio_id, portfolio_name),
        )

        conn.commit()
        st.success(f"Portafolio '{portfolio_name}' guardado como favorito.")

        return portfolio_id
    except Exception as e:
        conn.rollback()
        st.error(f"Error al guardar el portafolio: {e}")
    finally:
        conn.close()


def delete_portfolio(portfolio_id):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM portfolios WHERE portfolio_id = %s", (portfolio_id,))
    db.commit()
    cursor.close()
    db.close()
    st.warning("Portafolio eliminado.")


def search_cash_company():
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT company_id FROM companies WHERE ticker = 'CASH'")
    cash_id = cursor.fetchone()[0]
    cursor.close()
    db.close()
    return cash_id


def insert_model(
    name,
    algorithm,
    feature_extractor,
    companies_abv,
    file_path,
    created_at,
    normalization,
):
    db = connect_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO models (algorithm, feature_extractor, ncompanies, file_path, created_at, name, normalization)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING model_id;
            """,
            (
                algorithm,
                feature_extractor,
                len(companies_abv),
                file_path,
                created_at,
                name,
                normalization,
            ),
        )
        model_id = cursor.fetchone()[0]

        if model_id:
            # companies_abv.append("CASH")
            for ticker in companies_abv:
                company_id = search_company(cursor, ticker)
                if company_id:
                    cursor.execute(
                        "INSERT INTO model_companies (model_id, company_id) VALUES (%s, %s);",
                        (model_id, company_id),
                    )
                else:
                    raise ValueError(
                        f"Error: Company with ticker '{ticker}' not found in the database."
                    )

        db.commit()
        cursor.close()
        db.close()
        return model_id
    except Exception as e:
        db.rollback()
        st.error(f"Error al insertar modelo: {e}")
        return None
    finally:
        cursor.close()
        db.close()


def search_company(cursor, ticker):
    """Busca una compañía en la base de datos."""
    cursor.execute("SELECT company_id FROM Companies WHERE ticker = %s", (ticker,))
    return cursor.fetchone()
