# Predicción y monitoreo de precios inmobiliarios con MLOps

Proyecto del curso Despliegue de Soluciones Analíticas (MIAD, Uniandes).
Solución MLOps para estimar el precio de venta de apartamentos: modelos supervisados, API, tablero y despliegue con Docker.

## Estructura
- `data/raw/`: datos originales, versionados con DVC (no se suben a Git; se versiona el archivo `.dvc`).
- `src/eda.py`: exploración de datos y modelo base de referencia.
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
2. Configura **tu ruta local** (no se sube a Git):
   ```bash
   dvc remote modify --local storage url "RUTA_A_TU_CARPETA_dvc-remote-precios"
   ```
3. Descarga los datos y corre el EDA:
   ```bash
   dvc pull
   python src/eda.py data/raw/train_real_state.csv data/raw/test_real_state.csv reports/figures
   ```

### Flujo de trabajo del equipo
- Código: ramas por integrante y Pull Requests hacia `main`; commits pequeños con mensajes claros.
- Datos nuevos o cambiados: `dvc add <archivo>`, luego `git add <archivo>.dvc`, `git commit`, `dvc push` y `git push`.
- Después de cambiar de rama o hacer `git pull`: `dvc pull` (o `dvc checkout`).

## Equipo
- [COMPLETAR: integrantes y GitHub de cada uno]

## Notas sobre los datos
- La columna `SalePrice` del archivo de test es un identificador, no el precio real.
- Fuente y unidad del precio: [COMPLETAR].
