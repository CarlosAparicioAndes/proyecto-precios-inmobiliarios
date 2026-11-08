# Entrega 2 - Entrenamiento con MLflow (borrador para el equipo)

`train.py` va en `src/train.py` del repo `proyecto-precios-inmobiliarios` (crear rama, p. ej. `modelos-carlos`, y abrir Pull Request).
Agregar `mlflow` a `requirements.txt`, y `mlflow.db`, `mlruns/` y `mlartifacts/` al `.gitignore`.

## Qué hace
Entrena 20 combinaciones y registra cada una como un run en MLflow:
- **Modelos:** Ridge, Random Forest, HistGradientBoosting y tendencia + boosting (`src/modelos.py`: tendencia lineal de log(precio) con el año de venta + boosting sobre el residuo; solo en log y con `YrSold`).
- **Conjuntos de variables:** `completo` (todas + AptAge), `sin_tiempo_venta` (quita YrSold, MonthSold, AptAge), `maqueta` (solo los 8 campos del formulario del tablero).
- **Precio:** normal o en logaritmo (el modelo guardado ya devuelve el precio en unidades originales, sin que la API tenga que invertir el log).
- **Validaciones (las del Entrega 1):** aleatoria 80/20 y temporal (entrena hasta 2014, evalúa 2015-2017). Métricas: MAE, RMSE, R2 y sesgo (negativo = subestima).
- Cada run guarda parámetros, métricas, el modelo (reentrenado con todos los datos, con firma y ejemplo de entrada) y, en Random Forest, la importancia de variables.
- `--register` registra el mejor por MAE temporal en el Model Registry (`precio-apartamentos-daegu`).

## Cómo correrlo
```bash
dvc pull                                  # baja data/processed/train_clean.csv
pip install -r requirements.txt           # con mlflow incluido
python src/train.py --autor carlos        # prueba local (SQLite: ./mlflow.db); ver con: mlflow ui --backend-store-uri sqlite:///mlflow.db
```
Para la entrega, los runs deben estar en **MLflow sobre una EC2**:
```bash
# en la EC2 (puerto 5000 abierto en el grupo de seguridad)
mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///mlflow.db --artifacts-destination ./mlartifacts --serve-artifacts
# (si el comando del Taller 4 ya funcionaba con tu versión de MLflow, usa ese)
# desde la EC2 (clonando el repo) o desde tu PC:
python src/train.py --autor carlos --tracking-uri http://IP_EC2:5000 --register
```
Tiempo: ~1,5 min en un portátil.

Servidor con el comando del Taller 4 (MLflow 3.x exige `--allowed-hosts` y `--cors-allowed-origins` para entrar por la IP pública):
```bash
mlflow server -h 0.0.0.0 -p 8050 --allowed-hosts "localhost:8050,IP_EC2:8050" --cors-allowed-origins "http://IP_EC2:8050"
python src/train.py --autor carlos --tracking-uri http://localhost:8050 --register
```

## Resultados de una corrida de prueba (datos limpios, 3.932 filas)
Ver `resultados_prueba_local.csv`. Para la reunión:
1. **Aleatoria vs temporal:** con partición aleatoria, Random Forest y Boosting llegan a MAE ~10-11 mil (R2 ~0,98); con partición temporal el MAE sube a 57-69 mil y el R2 baja a ~0,5. Es lo que ya mostraba el Entrega 1.
2. **El mejor en temporal es Ridge con precio en log y solo los campos de la maqueta** (MAE 48 mil, R2 0,75). Un modelo lineal extrapola la tendencia de precios; los árboles no pueden salirse del rango visto. Aun así todos subestiman (sesgo entre -22 mil y -52 mil).
3. **Sin variables de tiempo de venta** el MAE aleatorio sube de ~10 mil a ~36 mil: `YrSold`/`AptAge` aportan mucha información en la partición aleatoria (ventas del mismo edificio en el mismo año). Hay que discutir con cuidado qué se interpreta como "buen modelo".
4. **Los campos de la maqueta bastan:** con solo los 8 campos del formulario el desempeño temporal es igual o mejor que con todas las variables. Eso simplifica la API y el tablero.
5. Ejemplo de la maqueta (914 sqf, 2005, piso 8, terraced, Banwoldang, trust, 184, 2017): predicción ~310 mil (la maqueta muestra 286 mil con datos ilustrativos).

## Decisiones tomadas
- Criterio de selección: **MAE temporal** (el uso real es estimar ventas posteriores al entrenamiento).
- `YrSold`: se modela con una **tendencia lineal** (≈7,5 % anual) que sí extrapola, y los árboles aprenden el resto. `tendencia_hgb|maqueta|log` baja el MAE temporal de 48,4 mil (Ridge) a 32,9 mil, con R2 0,85, y mantiene el MAE aleatorio en 10,6 mil. Es el modelo del tablero.

## Decisiones iniciales para el equipo
- Criterio de selección del modelo: MAE temporal (sugerido) frente a aleatorio.
- Qué hacer con `YrSold` en producción (años futuros fuera del rango de entrenamiento).
- Qué más probar (ajuste de hiperparámetros, validación temporal con varios cortes, otras variables).

## Capturas para el reporte (MLflow en EC2, usuario y IP visibles)
Lista de experimentos/runs, comparación de runs (métricas), detalle de un run (parámetros, métricas, artefactos) y modelo registrado. Al final, **detener** (no terminar) la EC2 de MLflow.
