#!/bin/bash

set -e

TEMP_CORE="_core_temp"
SOURCE_CORE="../quant-drl-core"

# Verificar si se debe ejecutar el contenedor
EXECUTE_CONTAINER=${1:-"yes"}

echo "Construyendo la imagen de Docker para el proyecto quant-drl-core..."
echo "Ejecutar el contenedor: ${EXECUTE_CONTAINER}"
# 1. Copiar el core excluyendo carpetas grandes/innecesarias
echo "Copiando quant-drl-core a ./${TEMP_CORE} (excluyendo .venv, logs, models, notebooks)..."
rsync -av --progress "$SOURCE_CORE/" "$TEMP_CORE/" \
  --exclude '.venv' \
  --exclude 'logs' \
  --exclude 'models' \
  --exclude 'notebooks' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '*.pyo'

ls -la "$TEMP_CORE"
# 2. Construir la imagen
echo "Ejecutando docker-compose build ..."
docker-compose build

# 3. Limpiar
echo "Eliminando ${TEMP_CORE} ..."
rm -rf "$TEMP_CORE"

echo "Build completado correctamente."

# 4. Ejecutar el contenedor si se especifica
if [[ "$EXECUTE_CONTAINER" == "yes" ]]; then
  echo "Ejecutando el contenedor ..."
  docker-compose up -d
else
  echo "Ejecución del contenedor omitida."
fi