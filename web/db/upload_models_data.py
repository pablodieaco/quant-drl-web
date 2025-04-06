import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path

from commons.configurations import get_companies
from commons.connect_dotenv import load_env_from_project_root

from web.commons.logging import logger
from web.db.commons.db_connection import connect_db

# Carga variables desde .env
load_env_from_project_root()

DEFAULT_JSON_PATH = Path(os.getenv("MODEL_HIERARCHY", "models/metadata/hierarchy.json"))

INSERT_MODEL_QUERY = """
    INSERT INTO models (algorithm, feature_extractor, ncompanies, file_path, created_at, name, normalization)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    RETURNING model_id;
"""

INSERT_COMPANY_QUERY = """
    INSERT INTO model_companies (model_id, company_id)
    VALUES (%s, %s);
"""


def parse_args():
    parser = argparse.ArgumentParser(
        description="Upload model metadata from hierarchy JSON"
    )
    parser.add_argument(
        "--json-file",
        type=Path,
        default=DEFAULT_JSON_PATH,
        help="Path to the model hierarchy JSON file",
    )
    return parser.parse_args()


def extract_ncompanies(model_name):
    match = re.search(r"ncompanies_(\d+)", model_name)
    return int(match.group(1)) if match else None


def extract_datetime_from_name(name):
    match = re.search(r"(\d{8}-\d{6})", name)
    if match:
        return datetime.strptime(match.group(1), "%Y%m%d-%H%M%S")
    return None


def detect_normalization(name):
    if "min_max" in name:
        return "min_max"
    return "standard"  # Default normalization


def search_company(cursor, ticker):
    cursor.execute("SELECT company_id FROM companies WHERE ticker = %s", (ticker,))
    return cursor.fetchone()


def insert_models_from_json(json_path: Path):
    """Insert model metadata into the database from a JSON file."""
    conn = None
    if not json_path.exists():
        logger.error(f"JSON not found: {json_path}")
        return

    try:
        with open(json_path, "r") as f:
            data = json.load(f)

        conn = connect_db()
        with conn.cursor() as cursor:
            for algorithm, features in data.get("gym_models", {}).items():
                for feature_extractor, models in features.items():
                    for name in models:
                        ncompanies = extract_ncompanies(name)
                        created_at = extract_datetime_from_name(name)
                        normalization = detect_normalization(name)
                        file_path = f"models/{algorithm}/{feature_extractor}/{name}/"

                        if not ncompanies:
                            logger.warning(
                                f"Skipped: No 'ncompanies' in model name: {name}"
                            )
                            continue

                        cursor.execute(
                            INSERT_MODEL_QUERY,
                            (
                                algorithm,
                                feature_extractor,
                                ncompanies,
                                file_path,
                                created_at,
                                name,
                                normalization,
                            ),
                        )
                        model_id = cursor.fetchone()[0]
                        logger.info(f"Inserted model '{name}' with ID {model_id}")

                        companies_abv, _ = get_companies(ncompanies)
                        companies_abv.append("CASH")

                        for ticker in companies_abv:
                            result = search_company(cursor, ticker)
                            if result:
                                cursor.execute(
                                    INSERT_COMPANY_QUERY, (model_id, result[0])
                                )
                            else:
                                raise ValueError(f"Company not found in DB: {ticker}")

            conn.commit()
            logger.success("Model metadata inserted successfully!")

    except Exception as e:
        logger.exception(f"Error during model metadata upload: {e}")

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    args = parse_args()
    insert_models_from_json(args.json_file)
