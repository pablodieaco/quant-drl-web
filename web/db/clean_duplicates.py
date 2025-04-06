from commons.db_connection import connect_db

DELETE_MODEL_COMPANIES = """
DELETE FROM model_companies
WHERE model_id = %s;
"""

DELETE_MODEL = """
DELETE FROM models
WHERE model_id = %s;
"""

FIND_DUPLICATES = """
SELECT name, array_agg(model_id ORDER BY created_at DESC NULLS LAST) AS ids
FROM models
GROUP BY name
HAVING COUNT(*) > 1;
"""


FIND_DUPLICATES = """
SELECT model_id, phase, array_agg(evaluation_id ORDER BY end_date DESC NULLS LAST) AS ids
FROM evaluations
GROUP BY model_id, phase
HAVING COUNT(*) > 1;
"""

DELETE_EVALUATION = """
DELETE FROM evaluations
WHERE evaluation_id = %s;
"""


def clean_evaluation_duplicates():
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(FIND_DUPLICATES)
        duplicates = cursor.fetchall()
        print(f"Combinaciones duplicadas encontradas: {len(duplicates)}")

        for model_id, phase, ids in duplicates:
            # Mantener el más reciente (primer ID), eliminar el resto
            to_delete = ids[1:]
            for eval_id in to_delete:
                cursor.execute(DELETE_EVALUATION, (eval_id,))
                print(
                    f"Eliminado evaluation_id={eval_id} (model_id={model_id}, phase='{phase}')"
                )

        conn.commit()
        cursor.close()
        conn.close()
        print("Limpieza de evaluaciones completada correctamente.")

    except Exception as e:
        print(f"Error durante la limpieza de evaluaciones: {e}")


def clean_model_duplicates():
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(FIND_DUPLICATES)
        duplicates = cursor.fetchall()

        print(f"Modelos duplicados encontrados: {len(duplicates)}")

        for name, ids in duplicates:
            # Mantener el primero (más reciente), borrar el resto
            to_delete = ids[1:]
            for model_id in to_delete:
                cursor.execute(DELETE_MODEL_COMPANIES, (model_id,))
                cursor.execute(DELETE_MODEL, (model_id,))
                print(f"Eliminado modelo duplicado: {model_id} (name='{name}')")

        conn.commit()
        cursor.close()
        conn.close()
        print("Limpieza completada correctamente.")

    except Exception as e:
        print(f"Error durante la limpieza: {e}")


if __name__ == "__main__":
    clean_model_duplicates()
    clean_evaluation_duplicates()
