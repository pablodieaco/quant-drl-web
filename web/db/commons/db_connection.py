import os

import psycopg2

from .connect_dotenv import load_env_from_project_root

# Cargar variables de entorno
load_env_from_project_root()

# Configuración de conexión
DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": "postgres",
    "port": "5432",
}


def connect_db():
    return psycopg2.connect(**DB_CONFIG)
