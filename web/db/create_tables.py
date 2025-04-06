from web.commons.logging import logger
from web.db.commons.db_connection import connect_db

# Definir las consultas de creación de tablas
TABLES = {
    "users": """
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(username),
            UNIQUE(email)
        );
    """,
    "models": """
        CREATE TABLE IF NOT EXISTS models (
            model_id SERIAL PRIMARY KEY,
            algorithm VARCHAR(255) NOT NULL,
            feature_extractor VARCHAR(255),
            ncompanies INT,
            file_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            name VARCHAR(255) NOT NULL,
            normalization VARCHAR(255) DEFAULT 'standard',
            UNIQUE(name, algorithm, feature_extractor)
        );
    """,
    "companies": """
        CREATE TABLE IF NOT EXISTS companies (
            company_id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            ticker VARCHAR(50) UNIQUE NOT NULL,
            sector VARCHAR(255),
            market_cap BIGINT,
            UNIQUE(name, ticker)
        );
    """,
    "model_companies": """
        CREATE TABLE IF NOT EXISTS model_companies (
            model_id INT REFERENCES models(model_id) ON DELETE CASCADE,
            company_id INT REFERENCES companies(company_id) ON DELETE CASCADE,
            weight FLOAT,
            PRIMARY KEY (model_id, company_id)
        );
    """,
    "favorites": """
        CREATE TABLE IF NOT EXISTS favorites (
            favorite_id SERIAL PRIMARY KEY,
            user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
            type VARCHAR(50) CHECK (type IN ('model', 'portfolio')),
            reference_id INT NOT NULL,
            name TEXT,
            UNIQUE(user_id, type, reference_id)
        );
    """,
    "portfolios": """
        CREATE TABLE IF NOT EXISTS portfolios (
            portfolio_id SERIAL PRIMARY KEY,
            user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            portfolio_value FLOAT DEFAULT 0,
            UNIQUE(user_id, name)
        );
    """,
    "portfolio_companies": """
        CREATE TABLE IF NOT EXISTS portfolio_companies (
            portfolio_id INT REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
            company_id INT REFERENCES companies(company_id) ON DELETE CASCADE,
            PRIMARY KEY (portfolio_id, company_id),
            UNIQUE(company_id, portfolio_id)
        );
    """,
    "portfolio_weights": """
        CREATE TABLE IF NOT EXISTS portfolio_weights (
            portfolio_id INT REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
            company_id INT REFERENCES companies(company_id) ON DELETE CASCADE,
            weight FLOAT,
            recorded_at DATE DEFAULT CURRENT_DATE,
            PRIMARY KEY (portfolio_id, company_id, recorded_at),
            UNIQUE(company_id, portfolio_id, recorded_at)
        );
    """,
    "evaluations": """
        CREATE TABLE IF NOT EXISTS evaluations (
            evaluation_id SERIAL PRIMARY KEY,
            model_id INT REFERENCES models(model_id) ON DELETE CASCADE,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            num_evaluations INT NOT NULL,
            evaluation_notes TEXT,
            phase VARCHAR(50),
            UNIQUE(model_id, phase)
        );
    """,
    "evaluation_metrics": """
        CREATE TABLE IF NOT EXISTS evaluation_metrics (
            metric_id SERIAL PRIMARY KEY,
            evaluation_id INT REFERENCES evaluations(evaluation_id) ON DELETE CASCADE,
            metric_name VARCHAR(255) NOT NULL,
            value FLOAT NOT NULL
        );
    """,
}


def create_tables():
    """Conecta a PostgreSQL y crea las tablas definidas en TABLES."""
    conn = None
    try:
        logger.info("Conectando a la base de datos...")
        conn = connect_db()

        with conn.cursor() as cursor:
            for table_name, query in TABLES.items():
                logger.info(f"Creando tabla: {table_name}")
                cursor.execute(query)

        conn.commit()
        logger.success("¡Todas las tablas fueron creadas correctamente!")

    except Exception as e:
        logger.error(f"Error al crear tablas: {e}")
    finally:
        if conn:
            conn.close()
            logger.info("Conexión cerrada.")


if __name__ == "__main__":
    create_tables()
