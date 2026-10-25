# Predicción y monitoreo de precios inmobiliarios con MLOps

Proyecto del curso Despliegue de Soluciones Analíticas (MIAD, Uniandes).
Solución MLOps para estimar el precio de venta de apartamentos: modelos supervisados, API, tablero y despliegue con Docker.

## Estructura
- `data/raw/`: datos originales, versionados con DVC (no se suben a Git; se versiona el archivo `.dvc`).
- `data/processed/`: datos limpios generados por `src/clean.py`, también versionados con DVC.
- `src/eda.py`: exploración de datos y modelo base de referencia.
- `src/clean.py`: limpieza de datos (duplicados, etiqueta inconsistente y variable `AptAge`).
- `notebooks/02_eda_precio_por_sqf.ipynb`: EDA complementario de precio por pie cuadrado por estación de metro, tiempo al metro y tipo de pasillo.
- `reports/figures/`: gráficas generadas y maqueta del tablero.

## Cómo reproducir
```bash
git clone https://github.com/CarlosAparicioAndes/proyecto-precios-inmobiliarios.git
cd proyecto-precios-inmobiliarios
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

### Conectarse a los datos (DVC)
Los datos viven en una carpeta compartida de OneDrive (`dvc-remote-precios`), usada como remoto local de DVC.
1. Acepta la invitación a la carpeta y, en OneDrive web, usa "Agregar acceso directo a Mi OneDrive" para que se sincronice en tu equipo.
   OneDrive puede renombrar el acceso directo con un prefijo, por ejemplo `Archivos de Carlos Francisco Aparicio Rojas - dvc-remote-precios`. Usa el nombre que aparezca en tu Explorador de archivos.
2. Configura **tu ruta local** (no se sube a Git):
   ```bash
   dvc remote modify --local storage url "RUTA_A_TU_CARPETA_dvc-remote-precios"
   dvc remote list   # verifica que aparezca tu ruta
   ```
3. Descarga los datos y corre el EDA:
   ```bash
   dvc pull
   python src/eda.py data/raw/train_real_state.csv data/raw/test_real_state.csv reports/figures
   ```
4. Para el EDA complementario, abre `notebooks/02_eda_precio_por_sqf.ipynb` y ejecuta todas las celdas.

### Flujo de trabajo del equipo
- Código: ramas por integrante y Pull Requests hacia `main`; commits pequeños con mensajes claros.
- Datos nuevos o cambiados: `dvc add <archivo>`, luego `git add <archivo>.dvc`, `git commit`, `dvc push` y `git push`.
- Después de cambiar de rama o hacer `git pull`: `dvc pull` (o `dvc checkout`).
- En Windows, cierra los notebooks abiertos antes de cambiar de rama: si un archivo está en uso, Git no puede actualizar la carpeta.

## Equipo (Grupo 39)
| Integrante | GitHub |
|---|---|
| Carlos Aparicio Rojas | [CarlosAparicioAndes](https://github.com/CarlosAparicioAndes) |
| Libardo Navas Quiroga | [libardo-navas-eng](https://github.com/libardo-navas-eng) |
| Gino Marcelo Ulloa Chacón | [COMPLETAR usuario] |

## Notas sobre los datos
- Ventas de apartamentos en Daegu (Corea del Sur) entre 2007 y 2017; las estaciones de metro del dataset pertenecen a la red de esa ciudad.
- `train_real_state.csv`: 4.124 filas y 30 columnas, sin valores nulos y con 192 filas duplicadas exactas, que se eliminan en la limpieza.
- `Size.sqf.` está en pies cuadrados.
- La columna `SalePrice` del archivo de test es un identificador, no el precio real; la evaluación usa particiones del archivo de entrenamiento.
- Fuente y unidad del precio: [COMPLETAR].
