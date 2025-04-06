import argparse
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from commons.connect_dotenv import load_env_from_project_root

from web.commons.logging import logger
from web.db.commons.db_connection import connect_db

# ========================
# Configuración
# ========================

load_env_from_project_root()
DEFAULT_CSV_PATH = Path(
    os.getenv("RESULTS_CSV_PATH", "examples/results/evaluation_results.csv")
)


def parse_args():
    parser = argparse.ArgumentParser(description="Upload evaluation data from CSV")
    parser.add_argument(
        "--csv-file",
        type=Path,
        default=DEFAULT_CSV_PATH,
        help="Path to the evaluation results CSV file",
    )
    return parser.parse_args()


# ========================
# Utilidades
# ========================


def convert_timestamp_format(df):
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y%m%d-%H%M%S")
    return df


def insert_evaluation(cursor, model_id, start_date, end_date, num_evals, notes, phase):
    query = """
        INSERT INTO evaluations (model_id, start_date, end_date, num_evaluations, evaluation_notes, phase)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING evaluation_id;
    """
    cursor.execute(query, (model_id, start_date, end_date, num_evals, notes, phase))
    return cursor.fetchone()[0]


def insert_metrics(cursor, evaluation_id, metrics: dict):
    query = """
        INSERT INTO evaluation_metrics (evaluation_id, metric_name, value)
        VALUES (%s, %s, %s);
    """
    for name, value in metrics.items():
        cursor.execute(query, (evaluation_id, name, value))


# ========================
# Lógica principal
# ========================


def insert_data_from_csv(csv_file: Path):
    conn = None
    inserted = 0
    skipped = 0

    logger.info(f"Reading CSV file: {csv_file}")
    if not csv_file.exists():
        logger.error(f"CSV file not found: {csv_file}")
        return

    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            df = pd.read_csv(csv_file, sep=";", decimal=",", header=0)
            df = convert_timestamp_format(df)

            for _, row in df.iterrows():
                model_name = row.get("model_name")
                phase = row.get("phase")

                if not model_name or not phase:
                    logger.warning("Row with missing data — skipping.")
                    skipped += 1
                    continue

                if phase == "eval":
                    end_date = datetime(2022, 6, 30)
                    start_date = datetime(2018, 6, 30)
                else:
                    end_date = datetime(2018, 6, 30)
                    start_date = datetime(2008, 6, 30)

                cursor.execute(
                    "SELECT model_id FROM models WHERE name = %s", (model_name,)
                )
                result = cursor.fetchone()
                if not result:
                    logger.warning(f"Model not found in database: {model_name}")
                    skipped += 1
                    continue

                model_id = result[0]
                notes = f"Algorithm: {row['algorithm']}, Feature: {row['feature']}"

                evaluation_id = insert_evaluation(
                    cursor, model_id, start_date, end_date, 50, notes, phase
                )

                metrics = {
                    col: row[col]
                    for col in df.columns
                    if col.startswith("mean_")
                    or col.startswith("std_")
                    or col == "final_drawdowns"
                }

                insert_metrics(cursor, evaluation_id, metrics)
                logger.info(f"Inserted: {model_name} | {phase}")
                inserted += 1

            conn.commit()
            logger.info(
                f"Finished insertion. Total inserted: {inserted}, skipped: {skipped}"
            )

    except Exception as e:
        logger.exception(f"Error during evaluation data upload: {e}")

    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed.")


if __name__ == "__main__":
    args = parse_args()
    insert_data_from_csv(args.csv_file)
