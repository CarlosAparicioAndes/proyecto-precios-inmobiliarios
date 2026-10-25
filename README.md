# Predicción y monitoreo de precios inmobiliarios con MLOps

Proyecto del curso Despliegue de Soluciones Analíticas (MIAD, Uniandes).
Solución MLOps para estimar el precio de venta de apartamentos: modelos supervisados, API, tablero y despliegue con Docker.

## Estructura
- `data/raw/`: datos originales, versionados con DVC (no se suben a Git; se versiona el archivo `.dvc`).
- `src/eda.py`: exploración de datos y modelo base de referencia.
- `reports/figures/`: gráficas generadas y maqueta del tablero.

## Cómo reproducir
```bash
git clone <URL_DEL_REPO>
cd proyecto-precios-inmobiliarios
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
dvc pull            # descarga los datos desde el almacenamiento remoto
python src/eda.py data/raw/train_real_state.csv data/raw/test_real_state.csv reports/figures
```

## Equipo
- [COMPLETAR: integrantes y GitHub de cada uno]

## Notas sobre los datos
- La columna `SalePrice` del archivo de test es un identificador, no el precio real.
- Fuente y unidad del precio: [COMPLETAR].
