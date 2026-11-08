"""Entrenamiento y experimentos con MLflow - Entrega 2.
Prediccion del precio de venta de apartamentos (Daegu).

Uso (desde la raiz del repo, con los datos limpios descargados con `dvc pull`):
    python src/train.py                                     # registra en ./mlflow.db (local, SQLite)
    python src/train.py --tracking-uri http://IP_EC2:5000   # registra en el servidor MLflow de la EC2
    python src/train.py --autor carlos --register           # ademas registra el mejor modelo

Cada corrida (run) combina: modelo x conjunto de variables x transformacion del precio.
Cada una se evalua con las dos validaciones del Entrega 1:
  - aleatoria 80/20 (optimista: apartamentos del mismo edificio quedan en ambas particiones)
  - temporal: entrena con ventas hasta 2014 y evalua con 2015 a 2017 (mas parecida al uso real)
Luego se reentrena con todos los datos y ese modelo es el que se guarda en MLflow.
"""
import argparse
import os
import sys

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from mlflow.models import infer_signature
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modelos import TendenciaMasArboles  # noqa: E402  (tendencia lineal + arboles, ver src/modelos.py)

TARGET = "SalePrice"
CORTE_TEMPORAL = 2014  # train: YrSold <= 2014 ; test: YrSold >= 2015

# --- Conjuntos de variables -------------------------------------------------
# "completo": todas las variables + AptAge (creada en clean.py)
# "sin_tiempo_venta": quita YrSold, MonthSold y AptAge (esta ultima depende de YrSold);
#     sirve para ver cuanto del desempeno viene de saber CUANDO se vendio
# "maqueta": solo los campos del formulario de la maqueta del tablero (8 entradas)
CAMPOS_MAQUETA = ["Size.sqf.", "YearBuilt", "Floor", "HallwayType", "SubwayStation",
                  "AptManageType", "N_Parkinglot.Basement.", "YrSold"]
TIEMPO_VENTA = ["YrSold", "MonthSold", "AptAge"]


def columnas(df, conjunto):
    todas = [c for c in df.columns if c != TARGET]
    if conjunto == "completo":
        return todas
    if conjunto == "sin_tiempo_venta":
        return [c for c in todas if c not in TIEMPO_VENTA]
    if conjunto == "maqueta":
        return CAMPOS_MAQUETA
    raise ValueError(conjunto)


def modelos():
    return {
        "ridge": (Ridge(alpha=1.0), True),
        "random_forest": (RandomForestRegressor(n_estimators=300, min_samples_leaf=2,
                                                random_state=0, n_jobs=-1), False),
        "hist_gradient_boosting": (HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05,
                                                                  random_state=0), False),
        # tendencia lineal del mercado (YrSold) + boosting sobre el residuo; siempre en log
        "tendencia_hgb": (HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05,
                                                         random_state=0), False),
    }


def armar(nombre, X, estimador, escalar, log_precio):
    if nombre == "tendencia_hgb":
        return TendenciaMasArboles(armar_pipeline(X, estimador, escalar, False))
    return armar_pipeline(X, estimador, escalar, log_precio)


def armar_pipeline(X, estimador, escalar, log_precio=False):
    cat = X.select_dtypes(exclude="number").columns.tolist()
    num = X.select_dtypes(include="number").columns.tolist()
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat),
        ("num", StandardScaler() if escalar else "passthrough", num),
    ])
    pipe = Pipeline([("pre", pre), ("modelo", estimador)])
    if log_precio:  # entrena con log(precio) pero PREDICE en unidades de precio (apto para la API)
        return TransformedTargetRegressor(regressor=pipe, func=np.log, inverse_func=np.exp)
    return pipe


def metricas(y_real, y_pred, prefijo):
    return {
        f"mae_{prefijo}": float(mean_absolute_error(y_real, y_pred)),
        f"rmse_{prefijo}": float(mean_squared_error(y_real, y_pred) ** 0.5),
        f"r2_{prefijo}": float(r2_score(y_real, y_pred)),
        f"sesgo_{prefijo}": float(np.mean(y_pred - y_real)),  # negativo = subestima
    }


def ajustar_y_predecir(pipe, Xa, ya, Xb):
    return pipe.fit(Xa, ya).predict(Xb)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/processed/train_clean.csv")
    ap.add_argument("--tracking-uri", default=os.environ.get("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"))
    ap.add_argument("--experiment", default="precios-apartamentos-daegu")
    ap.add_argument("--autor", default=os.environ.get("USERNAME", os.environ.get("USER", "equipo")))
    ap.add_argument("--register", action="store_true", help="registra el mejor modelo en el Model Registry")
    ap.add_argument("--registered-name", default="precio-apartamentos-daegu")
    ap.add_argument("--resumen", default="reports/experimentos_resumen.csv")
    args = ap.parse_args()

    df = pd.read_csv(args.data)
    print(f"Datos: {df.shape[0]} filas, {df.shape[1]} columnas ({args.data})")
    mlflow.set_tracking_uri(args.tracking_uri)
    mlflow.set_experiment(args.experiment)

    idx_a, idx_b = train_test_split(df.index, test_size=0.2, random_state=0)
    mask_t = df["YrSold"] <= CORTE_TEMPORAL
    y = df[TARGET]
    filas = []

    for conjunto in ["completo", "sin_tiempo_venta", "maqueta"]:
        X = df[columnas(df, conjunto)]
        for nombre, (est, escalar) in modelos().items():
            for log_precio in [False, True]:
                if nombre == "tendencia_hgb" and (not log_precio or "YrSold" not in X.columns):
                    continue  # necesita YrSold y trabaja internamente en log
                run_name = f"{nombre}|{conjunto}|{'log' if log_precio else 'precio'}"
                with mlflow.start_run(run_name=run_name) as run:
                    mlflow.set_tags({"autor": args.autor, "datos": os.path.basename(args.data),
                                     "validacion": "aleatoria 80/20 y temporal (<=2014 vs 2015-2017)"})
                    mlflow.log_params({
                        "modelo": nombre, "conjunto_variables": conjunto, "n_variables": X.shape[1],
                        "precio_en_log": log_precio, "corte_temporal": CORTE_TEMPORAL,
                        **{f"hp_{k}": v for k, v in est.get_params().items()
                           if isinstance(v, (int, float, str, bool, type(None)))},
                    })
                    m = {}
                    pipe = armar(nombre, X, est, escalar, log_precio)
                    p = ajustar_y_predecir(pipe, X.loc[idx_a], y.loc[idx_a], X.loc[idx_b])
                    m.update(metricas(y.loc[idx_b], p, "aleatorio"))
                    pipe = armar(nombre, X, est, escalar, log_precio)
                    p = ajustar_y_predecir(pipe, X[mask_t], y[mask_t], X[~mask_t])
                    m.update(metricas(y[~mask_t], p, "temporal"))
                    mlflow.log_metrics(m)

                    # modelo final: reentrenado con todos los datos (el que se serviria)
                    final = armar(nombre, X, est, escalar, log_precio).fit(X, y)
                    if nombre == "random_forest":
                        interno = final.regressor_ if log_precio else final
                        nombres = interno.named_steps["pre"].get_feature_names_out()
                        imp = pd.Series(interno.named_steps["modelo"].feature_importances_, index=nombres)
                        mlflow.log_dict(imp.sort_values(ascending=False).round(4).to_dict(),
                                        "importancia_variables.json")
                    firma = infer_signature(X.head(50), final.predict(X.head(50)))
                    mlflow.sklearn.log_model(final, artifact_path="modelo", signature=firma,
                                             input_example=X.head(3),
                                             serialization_format="cloudpickle",
                                             code_paths=[os.path.join(os.path.dirname(
                                                 os.path.abspath(__file__)), "modelos.py")])
                    filas.append({"run_id": run.info.run_id, "run_name": run_name, **m})
                    print(f"{run_name:55s} MAE aleatorio {m['mae_aleatorio']:>9,.0f} | "
                          f"MAE temporal {m['mae_temporal']:>9,.0f} | R2 temporal {m['r2_temporal']:6.2f}")

    res = pd.DataFrame(filas).sort_values("mae_temporal")
    os.makedirs(os.path.dirname(args.resumen) or ".", exist_ok=True)
    res.to_csv(args.resumen, index=False)
    print("\nTop 5 por MAE temporal (criterio sugerido: refleja el uso real con ventas futuras):")
    print(res.head(5)[["run_name", "mae_aleatorio", "mae_temporal", "r2_temporal", "sesgo_temporal"]]
          .to_string(index=False, float_format=lambda v: f"{v:,.2f}"))

    if args.register:
        mejor = res.iloc[0]
        try:
            mv = mlflow.register_model(f"runs:/{mejor['run_id']}/modelo", args.registered_name)
            print(f"\nRegistrado: {args.registered_name} v{mv.version} ({mejor['run_name']})")
        except Exception as e:  # el servidor puede no tener Model Registry habilitado
            print(f"\nNo se pudo registrar el modelo: {e}")


if __name__ == "__main__":
    main()
