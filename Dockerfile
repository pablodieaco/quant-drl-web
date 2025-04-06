FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copiar el proyecto completo
COPY . . /app/

# Añadir /app al PYTHONPATH para que los imports funcionen correctamente
ENV PYTHONPATH="/app"

# Mover y registrar quant-drl-core como editable
RUN mv /app/_core_temp /app/quant-drl-core

RUN pip install /app/quant-drl-core

# Puerto para Streamlit
EXPOSE 8501

# Comando por defecto (útil para la imagen web)
CMD ["streamlit", "run", "web/app.py", "--server.port=8501", "--server.enableCORS=false"]
