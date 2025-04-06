from pathlib import Path

from dotenv import load_dotenv


def load_env_from_project_root(filename=".env"):
    """
    Carga el archivo .env desde la raíz del proyecto o donde se encuentre en la jerarquía de carpetas.
    """
    current_path = Path(__file__).resolve()
    for parent in [current_path] + list(current_path.parents):
        env_path = parent / filename
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
            print(f".env cargado desde: {env_path}")
            return True
    print("No se encontró el archivo .env")
    return False
