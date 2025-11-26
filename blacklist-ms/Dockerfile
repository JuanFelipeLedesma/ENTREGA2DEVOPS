# Imagen base
FROM python:3.11-slim

# Evita bytecode y buffering
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    PIP_NO_CACHE_DIR=1

# Instalar dependencias del sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar requirements e instalar
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip setuptools wheel \
 && pip install -r /app/requirements.txt

# Copiar el resto de la app
COPY . /app

# Exponer puerto HTTP
EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "application:application", "--workers", "2", "--threads", "4"]