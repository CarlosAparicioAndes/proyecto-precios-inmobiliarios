"""API de valoracion de apartamentos en Daegu - Entrega 3.

Sirve el modelo registrado en MLflow como version 2 de `precio-apartamentos-daegu`
(tendencia + boosting, con los 8 campos del formulario del tablero).

Endpoints (prefijo /api/v1):
    GET  /api/v1/health   estado de la API y version del modelo
    GET  /api/v1/modelo   metricas y datos del entrenamiento del modelo (para el monitoreo)
    POST /api/v1/predict  {"inputs": [ {8 campos}, ... ]} -> {"predictions": [precio, ...]}

Ejecucion local (desde la raiz del repo):
    uvicorn app.main:app --app-dir api --port 8001
En Docker se usa api/Dockerfile (la variable de entorno PORT define el puerto).
"""
import json
import os
import sys
from pathlib import Path
from typing import List

import joblib
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field

API_VERSION = "0.2.0"
AQUI = Path(__file__).resolve()


def _primero_que_exista(candidatos):
    for c in candidatos:
        if c is not None and Path(c).exists():
            return Path(c)
    raise FileNotFoundError(f"No se encontro ninguno de: {candidatos}")


# Carpeta del modelo: variable MODEL_DIR, o ./models (Docker) o models/ en la raiz del repo (local)
MODEL_DIR = _primero_que_exista([os.getenv("MODEL_DIR"), AQUI.parents[1] / "models", AQUI.parents[2] / "models"])
# El modelo guardado usa la clase TendenciaMasArboles (src/modelos.py): debe poder importarse
for carpeta in (AQUI.parents[1], AQUI.parents[2] / "src"):
    if (carpeta / "modelos.py").exists():
        sys.path.insert(0, str(carpeta))
MODELO = joblib.load(MODEL_DIR / "modelo.joblib")
META = json.load(open(MODEL_DIR / "metadata.json", encoding="utf-8"))
# Orden de las columnas con el que se entreno el modelo
CAMPOS = ["Size.sqf.", "YearBuilt", "Floor", "HallwayType", "SubwayStation", "AptManageType",
          "N_Parkinglot.Basement.", "YrSold"]


class Apartamento(BaseModel):
    """Los 8 campos del formulario del tablero (nombres de columna del dataset)."""
    model_config = ConfigDict(populate_by_name=True)
    size: float = Field(alias="Size.sqf.", gt=0, le=10000, description="Tamano en sqf")
    year_built: int = Field(alias="YearBuilt", ge=1900, le=2035, description="Ano de construccion")
    floor: int = Field(alias="Floor", ge=0, le=100, description="Piso")
    hallway: str = Field(alias="HallwayType", description="corridor, mixed o terraced")
    station: str = Field(alias="SubwayStation", description="Estacion de metro cercana")
    manage: str = Field(alias="AptManageType", description="management_in_trust o self_management")
    parking: int = Field(alias="N_Parkinglot.Basement.", ge=0, le=5000, description="Parqueaderos de sotano")
    year_sold: int = Field(alias="YrSold", ge=1990, le=2050, description="Ano de venta")


class Entradas(BaseModel):
    inputs: List[Apartamento] = Field(min_length=1, max_length=100)


class Salida(BaseModel):
    predictions: List[float]
    version: str
    modelo: str


app = FastAPI(title="API de valoracion de apartamentos - Daegu", version=API_VERSION,
              openapi_url="/api/v1/openapi.json")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def inicio():
    return ("<h1>API de valoracion de apartamentos en Daegu - Grupo 39</h1>"
            "<p>Documentacion: <a href='/docs'>/docs</a></p>")


@app.get("/api/v1/health")
def health():
    return {"estado": "ok", "api_version": API_VERSION, "modelo": META["modelo"],
            "version_modelo": META["version"], "entrenado": META["entrenado"]}


@app.get("/api/v1/modelo")
def modelo():
    return {"modelo": META["modelo"], "version": META["version"], "entrenado": META["entrenado"],
            "filas_entrenamiento": META["filas_entrenamiento"], "metricas": META["metricas"],
            "intervalo_rel_aleatoria": META["intervalo_rel_aleatoria"],
            "intervalo_rel_temporal": META["intervalo_rel_temporal"], "deriva_psi": META["deriva_psi"]}


@app.post("/api/v1/predict", response_model=Salida)
def predict(entradas: Entradas):
    filas = pd.DataFrame([e.model_dump(by_alias=True) for e in entradas.inputs])[CAMPOS]
    precios = [float(p) for p in MODELO.predict(filas)]
    return Salida(predictions=precios, version=META["version"], modelo=META["modelo"])
