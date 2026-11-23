# Tablero de valoracion de apartamentos (Dash). Pide los precios a la API (variable API_URL).
# Construir desde la RAIZ del repo:  docker build -f dashboard/Dockerfile -t precios-tablero .
FROM python:3.12-slim

# Usuario sin privilegios para ejecutar el tablero
RUN adduser --disabled-password --gecos '' dash-user

WORKDIR /opt/app

COPY dashboard/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# El tablero solo necesita su codigo y metadata.json (valores tipicos, metricas y deriva);
# el modelo no se copia porque los precios los entrega la API.
COPY dashboard ./dashboard
COPY models/metadata.json ./models/metadata.json
RUN chown -R dash-user:dash-user /opt/app

USER dash-user
ENV PORT=8050 \
    API_URL=http://localhost:8001/api/v1/predict
EXPOSE 8050

CMD ["sh", "-c", "gunicorn dashboard.app:server -b 0.0.0.0:${PORT} --timeout 60"]
