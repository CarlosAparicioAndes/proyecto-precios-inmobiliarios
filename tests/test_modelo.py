"""Pruebas del modelo del tablero - Entrega 2.

Uso (desde la raiz del repo, despues de `python src/preparar_tablero.py`):
    python -m pytest tests -v

Verifican que el modelo guardado en models/ sirve para el tablero (y luego para la API):
carga, recibe las 8 entradas del formulario, entrega precios razonables y su error de
validacion temporal no empeora frente al mejor modelo lineal de los experimentos de MLflow.
"""
import json, sys
from pathlib import Path

import joblib
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

APTO = {"Size.sqf.": 914, "YearBuilt": 2005, "Floor": 8, "HallwayType": "terraced",
        "SubwayStation": "Banwoldang", "AptManageType": "management_in_trust",
        "N_Parkinglot.Basement.": 184, "YrSold": 2017}


@pytest.fixture(scope="module")
def modelo():
    return joblib.load(RAIZ / "models" / "modelo.joblib")


@pytest.fixture(scope="module")
def meta():
    return json.load(open(RAIZ / "models" / "metadata.json", encoding="utf-8"))


def predecir(modelo, **cambios):
    return float(modelo.predict(pd.DataFrame([{**APTO, **cambios}]))[0])


def test_predice_precio_positivo_y_en_rango(modelo):
    p = predecir(modelo)
    assert 30_000 < p < 700_000  # rango observado en los datos: 32.743 a 585.840


def test_varias_filas(modelo):
    df = pd.DataFrame([APTO] * 5)
    assert len(modelo.predict(df)) == 5


def test_mas_grande_vale_mas(modelo):
    assert predecir(modelo, **{"Size.sqf.": 1400}) > predecir(modelo, **{"Size.sqf.": 600})


def test_tendencia_anio_venta(modelo):
    # la tendencia lineal permite estimar ventas posteriores a 2017 con precios mayores
    assert predecir(modelo, YrSold=2018) > predecir(modelo, YrSold=2017)


def test_estacion_desconocida_no_falla(modelo):
    assert predecir(modelo, SubwayStation="estacion_nueva") > 0


def test_mejora_frente_a_ridge(meta):
    # mejor modelo lineal en MLflow (ridge | maqueta | log): MAE temporal 48.397
    assert meta["metricas"]["temporal_mae"] < 48_397


def test_metadata_completa(meta):
    for clave in ["metricas", "intervalo_rel_aleatoria", "moda", "mediana_estacion",
                  "deriva_psi", "mediana_anio"]:
        assert clave in meta
