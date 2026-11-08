"""Tablero de valoracion de apartamentos (Daegu) - Entrega 2.

Uso (desde la raiz del repo):
    python src/preparar_tablero.py   # genera models/modelo.joblib y models/metadata.json
    python dashboard/app.py      # abre http://localhost:8050

Sigue la maqueta de la Entrega 1 (reports/figures/maqueta.png):
  1. Formulario con las caracteristicas del apartamento.
  KPIs: precio estimado con intervalo, mediana de la estacion y version del modelo.
  2. Factores que mas pesan en esta estimacion.
  3. Precio mediano por anio de venta.
  4. Monitoreo del modelo (error en validacion temporal y deriva de datos).

Inferencia: por ahora el tablero carga el modelo localmente. Si se define la variable de entorno
API_URL (p. ej. http://<ip>:8001/api/v1/predict), envia las entradas a la API (Entrega 3),
con el formato del Taller 6: {"inputs": [...]} -> {"predictions": [...]}.
"""
import json, os, sys
from pathlib import Path

import joblib
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))  # para cargar TendenciaMasArboles
MODELO = joblib.load(RAIZ / "models" / "modelo.joblib")
META = json.load(open(RAIZ / "models" / "metadata.json", encoding="utf-8"))
API_URL = os.getenv("API_URL")

NOMBRES = {"Size.sqf.": "Tamaño", "YearBuilt": "Año de construcción", "Floor": "Piso",
           "N_Parkinglot.Basement.": "Parqueaderos sótano", "YrSold": "Año de venta",
           "HallwayType": "Tipo de pasillo", "SubwayStation": "Estación de metro",
           "AptManageType": "Gestión"}
ORDEN = ["Size.sqf.", "YearBuilt", "Floor", "HallwayType", "SubwayStation", "AptManageType",
         "N_Parkinglot.Basement.", "YrSold"]
AZUL, AZUL_CLARO, ROJO = "#1F3A5F", "#6C8EBF", "#B03A3A"


def estimar(filas: pd.DataFrame):
    """Devuelve el precio estimado para cada fila (modelo local o API)."""
    if API_URL:
        import requests
        r = requests.post(API_URL, json={"inputs": filas.to_dict(orient="records")}, timeout=10)
        r.raise_for_status()
        return list(r.json()["predictions"])
    return list(MODELO.predict(filas[ORDEN]))


def fmt(x):
    return f"{x:,.0f}".replace(",", ".")


# ------------------------------------------------------------------ componentes
def campo(etiqueta, comp):
    return html.Div([html.Label(etiqueta, className="lbl"), comp], className="campo")


def num(id_, valor, minimo, maximo, paso=1):
    return dcc.Input(id=id_, type="number", value=valor, min=minimo, max=maximo, step=paso,
                     className="inp", debounce=True)


def lista(id_, col, valor):
    return dcc.Dropdown(id=id_, options=META["entradas"]["categorias"][col], value=valor,
                        clearable=False, className="dd")


rng = META["entradas"]["num_rango"]
formulario = html.Div([
    html.H3("1. Características del apartamento"),
    campo("Tamaño (sqf)", num("size", 914, rng["Size.sqf."][0], rng["Size.sqf."][1])),
    campo("Año de construcción", num("built", 2005, rng["YearBuilt"][0], rng["YearBuilt"][1])),
    campo("Piso", num("floor", 8, rng["Floor"][0], rng["Floor"][1])),
    campo("Tipo de pasillo", lista("hall", "HallwayType", "terraced")),
    campo("Estación de metro cercana", lista("station", "SubwayStation", "Banwoldang")),
    campo("Gestión", lista("manage", "AptManageType", "management_in_trust")),
    campo("Parqueaderos en sótano", num("park", 184, rng["N_Parkinglot.Basement."][0],
                                        rng["N_Parkinglot.Basement."][1])),
    campo("Año de venta", num("sold", 2017, 2007, 2019)),
    html.Button("Estimar precio", id="btn", n_clicks=0, className="btn"),
], className="card form")


def kpi(titulo, id_valor, id_sub, grande=False, id_titulo=None):
    t = html.Div(titulo, className="kt", id=id_titulo) if id_titulo else html.Div(titulo, className="kt")
    return html.Div([t,
                     html.Div(id=id_valor, className="kv big" if grande else "kv"),
                     html.Div(id=id_sub, className="ks")], className="card kpi")


m = META["metricas"]
deriva = {k: v for k, v in META["deriva_psi"].items() if k != "YrSold"}
alerta = [NOMBRES[k] for k, v in sorted(deriva.items(), key=lambda x: -x[1]) if v > 0.2]

anios = sorted(META["mediana_anio"], key=int)
fig_anio = go.Figure(go.Scatter(x=[int(a) for a in anios], y=[META["mediana_anio"][a] for a in anios],
                                mode="lines+markers", line=dict(color=AZUL, width=2.5)))
fig_anio.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=210, plot_bgcolor="white",
                       yaxis=dict(gridcolor="#E6E9EF", tickformat=",.0f"), xaxis=dict(dtick=1))

monitoreo = html.Div([
    html.H3("4. Monitoreo del modelo"),
    html.Div([
        html.Div([html.Div("Error (MAE) en ventas 2015-2017", className="kt"),
                  html.Div(f"{m['temporal_mae']/1000:.1f} mil", className="kv"),
                  html.Div(f"Entrenado hasta 2014 · MAPE {m['temporal_mape']*100:.0f} %", className="ks")]),
        html.Div([html.Div("Deriva de datos (PSI > 0,2)", className="kt"),
                  html.Div("Alerta: " + ", ".join(alerta).lower() if alerta else "Sin alerta",
                           className="kv", style={"color": ROJO if alerta else AZUL}),
                  html.Div("Ventas 2015-2017 frente a 2007-2014; el año de venta se excluye "
                           "porque cambia por construcción", className="ks")]),
        html.Div([html.Div("Última actualización", className="kt"),
                  html.Div(META["entrenado"], className="kv"),
                  html.Div(f"{META['filas_entrenamiento']:,} ventas de entrenamiento".replace(",", "."),
                           className="ks")]),
    ], className="mon"),
], className="card full")

# Como en el Taller 1: Dash carga solo los estilos de dashboard/assets/ y
# server = app.server permite publicarlo con gunicorn (gunicorn dashboard.app:server).
app = Dash(__name__, title="Valoración de apartamentos · Daegu")
server = app.server
app.layout = html.Div([
    html.Header([html.Span("Valoración de apartamentos · Daegu"),
                 html.Small("prototipo · Grupo 39")]),
    html.Div([
        formulario,
        html.Div([
            html.Div([kpi("Precio estimado", "precio", "intervalo", grande=True),
                      kpi("", "mediana", "comp", id_titulo="mediana_t"),
                      html.Div([html.Div("Versión del modelo", className="kt"),
                                html.Div(f"{META['version']} · { {'tendencia_hgb': 'tendencia + boosting'}.get(META['familia'], META['familia'].replace('_', ' ')) }",
                                         className="kv"),
                                html.Div(f"MAE de validación aleatoria: {m['aleatoria_mae']/1000:.1f} mil",
                                         className="ks")], className="card kpi")], className="kpis"),
            html.Div([
                html.Div([html.H3("2. Factores que más pesan en esta estimación"),
                          html.Div("Cambio en el precio si cada variable tomara su valor típico",
                                   className="ks"),
                          dcc.Graph(id="factores", config={"displayModeBar": False})],
                         className="card"),
                html.Div([html.H3("3. Precio mediano por año de venta"),
                          dcc.Graph(figure=fig_anio, config={"displayModeBar": False}),
                          html.Div("Evolución 2007 a 2017 según los datos históricos", className="ks")],
                         className="card"),
            ], className="mid"),
            monitoreo,
        ], className="right"),
    ], className="grid"),
], className="page")


@app.callback(
    Output("precio", "children"), Output("intervalo", "children"),
    Output("mediana_t", "children"), Output("mediana", "children"), Output("comp", "children"), Output("factores", "figure"),
    Input("btn", "n_clicks"),
    State("size", "value"), State("built", "value"), State("floor", "value"), State("hall", "value"),
    State("station", "value"), State("manage", "value"), State("park", "value"), State("sold", "value"),
)
def actualizar(_, size, built, floor, hall, station, manage, park, sold):
    fila = {"Size.sqf.": size, "YearBuilt": built, "Floor": floor, "HallwayType": hall,
            "SubwayStation": station, "AptManageType": manage, "N_Parkinglot.Basement.": park,
            "YrSold": sold}
    if any(v is None for v in fila.values()):
        vacio = go.Figure().update_layout(height=230, plot_bgcolor="white")
        return "—", "Complete todos los campos", "Mediana de la zona", "—", "", vacio
    # fila original + una fila por variable con su valor tipico (efecto local de cada entrada)
    filas = [fila] + [{**fila, c: META["moda"][c]} for c in ORDEN]
    p = estimar(pd.DataFrame(filas))
    precio, efectos = p[0], {NOMBRES[c]: abs(p[0] - p[i + 1]) for i, c in enumerate(ORDEN)}
    lo, hi = META["intervalo_rel_aleatoria"]
    intervalo = f"Intervalo 80 %: {fmt(precio * (1 + lo))} a {fmt(precio * (1 + hi))}"
    if sold > 2017:
        lo, hi = META["intervalo_rel_temporal"]
        intervalo = (f"Año fuera de los datos: intervalo amplio {fmt(precio * (1 + lo))} "
                     f"a {fmt(precio * (1 + hi))}")
    med = META["mediana_estacion"][station]
    dif = (precio / med - 1) * 100
    comp = f"Tu estimación está {abs(dif):.0f} % {'por encima' if dif >= 0 else 'por debajo'}"
    if META["n_estacion"][station] < 100:
        comp += f" · solo {META['n_estacion'][station]} ventas"
    top = sorted(efectos.items(), key=lambda x: x[1])[-5:]
    fig = go.Figure(go.Bar(x=[v for _, v in top], y=[k for k, _ in top], orientation="h",
                           marker_color=AZUL_CLARO, text=[fmt(v) for _, v in top],
                           textposition="outside", cliponaxis=False))
    fig.update_layout(margin=dict(l=10, r=40, t=10, b=10), height=230, plot_bgcolor="white",
                      xaxis=dict(visible=False), yaxis=dict(tickfont=dict(size=12)))
    return fmt(precio), intervalo, f"Mediana de la zona ({station})", fmt(med), comp, fig




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8050)), debug=False)
