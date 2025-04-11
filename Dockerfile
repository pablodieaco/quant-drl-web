FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar el proyecto completo
COPY . /app/


# Añadir /app al PYTHONPATH para que los imports funcionen correctamente
ENV PYTHONPATH="/app"

# Puerto para Streamlit
EXPOSE 8501

# Comando por defecto (útil para la imagen web)
CMD ["streamlit", "run", "web/app.py", "--server.port=8501", "--server.enableCORS=false"]
