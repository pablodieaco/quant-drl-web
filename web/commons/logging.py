# web/commons/logging.py
import os
import sys
from loguru import logger

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logger.remove()  # Elimina el logger por defecto de stderr

# Logger a consola
logger.add(sys.stdout, level="INFO", enqueue=True)

# Logger a archivo
logger.add(
    f"{LOG_DIR}/web.log",
    rotation="10 MB",
    retention="10 days",
    enqueue=True,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
           "<level>{message}</level>",
)

# Exponer logger para importarlo
__all__ = ["logger"]