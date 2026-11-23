# API de valoracion de apartamentos (FastAPI + modelo registrado en MLflow, version 2)
# Construir desde la RAIZ del repo:  docker build -f api/Dockerfile -t precios-api .
FROM python:3.12-slim

# Usuario sin privilegios para ejecutar la API
RUN adduser --disabled-password --gecos '' api-user

WORKDIR /opt/api

# Dependencias (se copian primero para aprovechar la cache de Docker)
COPY api/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Codigo, clase del modelo (necesaria para cargar el modelo) y archivos del modelo
COPY api/app ./app
COPY src/modelos.py ./modelos.py
COPY models/modelo.joblib models/metadata.json ./models/
RUN chown -R api-user:api-user /opt/api

USER api-user
ENV PORT=8001
EXPOSE 8001

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
