"""Prepara el modelo y los datos de apoyo que usa el tablero - Entrega 2.

Uso (desde la raiz del repo):  python src/preparar_tablero.py

Entrena el modelo elegido en los experimentos de MLflow (src/train.py):
  tendencia_hgb | maqueta | log  ->  menor MAE temporal, con solo los 8 campos del formulario.
Usa las mismas particiones que src/train.py (aleatoria 80/20 con random_state=0 y temporal
<=2014 vs 2015-2017) y guarda:
  models/modelo.joblib   modelo reentrenado con todos los datos
  models/metadata.json   metricas, intervalo de error, valores tipicos, deriva y medianas
"""
import json, os, sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modelos import TendenciaMasArboles  # noqa: E402

DATA = Path("data/processed/train_clean.csv")
OUT = Path("models"); OUT.mkdir(exist_ok=True)
CORTE_TEMPORAL = 2014
NUM = ["Size.sqf.", "YearBuilt", "Floor", "N_Parkinglot.Basement.", "YrSold"]
CAT = ["HallwayType", "SubwayStation", "AptManageType"]
CAMPOS_MAQUETA = NUM + CAT


def nuevo(X):
    """Mismo modelo que el run tendencia_hgb|maqueta|log de src/train.py."""
    pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT),
                             ("num", "passthrough", NUM)])
    hgb = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=0)
    return TendenciaMasArboles(Pipeline([("pre", pre), ("modelo", hgb)]))


def psi(ref, act, bins=10):
    """Population Stability Index (> 0,2 suele leerse como deriva importante)."""
    cortes = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    cortes[0], cortes[-1] = -np.inf, np.inf
    r = np.histogram(ref, cortes)[0] / len(ref) + 1e-4
    a = np.histogram(act, cortes)[0] / len(act) + 1e-4
    return float(np.sum((a - r) * np.log(a / r)))


def psi_cat(ref, act):
    r, a = ref.value_counts(normalize=True), act.value_counts(normalize=True)
    idx = r.index.union(a.index)
    r, a = r.reindex(idx, fill_value=0) + 1e-4, a.reindex(idx, fill_value=0) + 1e-4
    return float(np.sum((a - r) * np.log(a / r)))


def main():
    df = pd.read_csv(DATA)
    X, y = df[CAMPOS_MAQUETA], df.SalePrice

    # validacion aleatoria (mismas particiones que src/train.py)
    ia, ib = train_test_split(df.index, test_size=0.2, random_state=0)
    pa = nuevo(X).fit(X.loc[ia], y.loc[ia]).predict(X.loc[ib])
    rel_a = (y.loc[ib].values - pa) / pa
    # validacion temporal
    t = df.YrSold <= CORTE_TEMPORAL
    pt = nuevo(X).fit(X[t], y[t]).predict(X[~t])
    rel_t = (y[~t].values - pt) / pt

    final = nuevo(X).fit(X, y)
    joblib.dump(final, OUT / "modelo.joblib")

    deriva = {c: psi(df.loc[t, c].values, df.loc[~t, c].values) for c in NUM}
    deriva.update({c: psi_cat(df.loc[t, c], df.loc[~t, c]) for c in CAT})

    meta = {
        "modelo": "tendencia_hgb|maqueta|log", "familia": "tendencia_hgb", "version": "v1",
        "entrenado": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "crecimiento_anual_tendencia": round(final.crecimiento_anual, 4),
        "metricas": {
            "aleatoria_mae": mean_absolute_error(y.loc[ib], pa), "aleatoria_r2": r2_score(y.loc[ib], pa),
            "aleatoria_mape": mean_absolute_percentage_error(y.loc[ib], pa),
            "temporal_mae": mean_absolute_error(y[~t], pt), "temporal_r2": r2_score(y[~t], pt),
            "temporal_mape": mean_absolute_percentage_error(y[~t], pt),
            "temporal_sesgo": float(np.mean(pt - y[~t])),
        },
        # cuantiles 10 % y 90 % del error relativo -> intervalo del 80 % alrededor de la estimacion
        "intervalo_rel_aleatoria": [float(np.quantile(rel_a, .1)), float(np.quantile(rel_a, .9))],
        "intervalo_rel_temporal": [float(np.quantile(rel_t, .1)), float(np.quantile(rel_t, .9))],
        "deriva_psi": {k: round(v, 3) for k, v in deriva.items()},
        "entradas": {"num_rango": {c: [float(df[c].min()), float(df[c].max())] for c in NUM},
                     "categorias": {c: sorted(df[c].unique().tolist()) for c in CAT}},
        "moda": {**{c: float(df[c].median()) for c in NUM}, **{c: df[c].mode()[0] for c in CAT}},
        "mediana_estacion": df.groupby("SubwayStation").SalePrice.median().round(0).to_dict(),
        "n_estacion": df.SubwayStation.value_counts().to_dict(),
        "mediana_anio": {int(k): v for k, v in df.groupby("YrSold").SalePrice.median().round(0).items()},
        "filas_entrenamiento": int(len(df)),
    }
    json.dump(meta, open(OUT / "metadata.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    m = meta["metricas"]
    print(f"MAE aleatoria {m['aleatoria_mae']:,.0f} | MAE temporal {m['temporal_mae']:,.0f} | "
          f"R2 temporal {m['temporal_r2']:.2f} | crecimiento anual {final.crecimiento_anual:.1%}")
    print(f"Guardado: {OUT/'modelo.joblib'} y {OUT/'metadata.json'}")


if __name__ == "__main__":
    main()
