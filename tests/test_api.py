"""Pruebas de la API - Entrega 3.

Uso (desde la raiz del repo, con el modelo ya generado en models/):
    pip install -r api/requirements.txt httpx pytest
    python -m pytest tests -v
"""
import sys
from pathlib import Path

import joblib
import pandas as pd
import pytest
from fastapi.testclient import TestClient

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "api"))
sys.path.insert(0, str(RAIZ / "src"))

from app.main import CAMPOS, app  # noqa: E402

cliente = TestClient(app)
APTO = {"Size.sqf.": 914, "YearBuilt": 2005, "Floor": 8, "HallwayType": "terraced",
        "SubwayStation": "Banwoldang", "AptManageType": "management_in_trust",
        "N_Parkinglot.Basement.": 184, "YrSold": 2017}


def pedir(*aptos):
    return cliente.post("/api/v1/predict", json={"inputs": list(aptos)})


def test_health():
    r = cliente.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["estado"] == "ok"
    assert r.json()["version_modelo"] == "v2"  # version del modelo en el Model Registry de MLflow


def test_modelo_expone_metricas():
    r = cliente.get("/api/v1/modelo").json()
    assert r["metricas"]["temporal_mae"] < 48_397  # mejor que Ridge en los experimentos de MLflow


def test_predict_coincide_con_el_modelo():
    r = pedir(APTO)
    assert r.status_code == 200
    esperado = float(joblib.load(RAIZ / "models" / "modelo.joblib").predict(pd.DataFrame([APTO])[CAMPOS])[0])
    assert r.json()["predictions"][0] == pytest.approx(esperado)
    assert 30_000 < esperado < 700_000


def test_predict_varias_filas():
    r = pedir(APTO, {**APTO, "Size.sqf.": 1400}, {**APTO, "YrSold": 2018})
    assert r.status_code == 200
    p = r.json()["predictions"]
    assert len(p) == 3
    assert p[1] > p[0]  # mas grande vale mas
    assert p[2] > p[0]  # la tendencia sube con el ano de venta


def test_estacion_desconocida_no_falla():
    assert pedir({**APTO, "SubwayStation": "estacion_nueva"}).status_code == 200


def test_falta_un_campo_da_422():
    incompleto = {k: v for k, v in APTO.items() if k != "Floor"}
    assert pedir(incompleto).status_code == 422


def test_valor_fuera_de_rango_da_422():
    assert pedir({**APTO, "Size.sqf.": -5}).status_code == 422


def test_entradas_vacias_da_422():
    assert cliente.post("/api/v1/predict", json={"inputs": []}).status_code == 422
