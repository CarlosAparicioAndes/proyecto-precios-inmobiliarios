"""Analisis de errores del modelo del tablero - Entrega 2.

Uso (desde la raiz del repo):  python src/evaluar_modelo.py

Pregunta: ¿en que tipo de apartamentos se equivoca mas el modelo elegido
(tendencia_hgb | maqueta | log)? Se usa la validacion temporal (entrena con ventas hasta 2014 y
predice 2015-2017), que es la mas parecida al uso real, y se compara con la aleatoria 80/20.

Salidas:
  reports/errores_por_segmento.csv     MAE, error porcentual (MAPE) y sesgo por segmento
  reports/figures/errores_modelo.png   figura para la seccion de observaciones del reporte
"""
import os, sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from preparar_tablero import CAMPOS_MAQUETA, CORTE_TEMPORAL, nuevo  # noqa: E402

DATA = Path("data/processed/train_clean.csv")
FIG = Path("reports/figures"); FIG.mkdir(parents=True, exist_ok=True)
AZUL, AZUL_CLARO, ROJO = "#1F3A5F", "#9DB4D3", "#B03A3A"


def resumen(d, col):
    g = d.groupby(col, observed=True)
    return pd.DataFrame({
        "n": g.size(),
        "mae": g.apply(lambda x: (x.pred - x.real).abs().mean()),
        "mape": g.apply(lambda x: ((x.pred - x.real).abs() / x.real).mean()),
        "sesgo": g.apply(lambda x: (x.pred - x.real).mean()),  # negativo = subestima
    })


def main():
    df = pd.read_csv(DATA)
    X, y = df[CAMPOS_MAQUETA], df.SalePrice
    df["tamano"] = pd.cut(df["Size.sqf."], [0, 600, 900, 1200, 3000],
                          labels=["<600", "600-900", "900-1200", ">1200"])

    # validacion temporal
    t = df.YrSold <= CORTE_TEMPORAL
    tem = df[~t].copy()
    tem["real"], tem["pred"] = y[~t], nuevo(X).fit(X[t], y[t]).predict(X[~t])
    # validacion aleatoria (misma particion que src/train.py)
    ia, ib = train_test_split(df.index, test_size=0.2, random_state=0)
    ale = df.loc[ib].copy()
    ale["real"], ale["pred"] = y.loc[ib], nuevo(X).fit(X.loc[ia], y.loc[ia]).predict(X.loc[ib])

    tablas = []
    for nombre, d in [("temporal", tem), ("aleatoria", ale)]:
        for col in ["YrSold", "SubwayStation", "HallwayType", "tamano"]:
            r = resumen(d, col).reset_index().rename(columns={col: "segmento"})
            r.insert(0, "variable", col); r.insert(0, "validacion", nombre)
            tablas.append(r)
    out = pd.concat(tablas)
    out.to_csv("reports/errores_por_segmento.csv", index=False, float_format="%.3f")

    # figura: 1) real vs predicho  2) sesgo por anio  3) MAPE por estacion  4) MAPE por tamano
    fig, ax = plt.subplots(2, 2, figsize=(10, 7))
    a = ax[0, 0]
    a.scatter(ale.real / 1000, ale.pred / 1000, s=6, alpha=.4, color=AZUL_CLARO, label="aleatoria")
    a.scatter(tem.real / 1000, tem.pred / 1000, s=6, alpha=.4, color=AZUL, label="temporal 2015-2017")
    lim = [0, max(df.SalePrice) / 1000 * 1.05]; a.plot(lim, lim, "k--", lw=.8)
    a.set(xlabel="Precio real (miles)", ylabel="Precio estimado (miles)", title="Real vs. estimado")
    a.legend(fontsize=8)

    a = ax[0, 1]; s = resumen(tem, "YrSold")
    a.bar(s.index.astype(str), s.sesgo / 1000, color=[ROJO if v < 0 else AZUL for v in s.sesgo])
    a.axhline(0, color="k", lw=.6); a.set(title="Sesgo por año (temporal)", ylabel="Estimado - real (miles)")

    a = ax[1, 0]
    st = resumen(tem, "SubwayStation").sort_values("mape")
    sa = resumen(ale, "SubwayStation").reindex(st.index)
    pos = np.arange(len(st))
    a.barh(pos - .2, sa.mape * 100, .4, color=AZUL_CLARO, label="aleatoria")
    a.barh(pos + .2, st.mape * 100, .4, color=AZUL, label="temporal")
    a.set_yticks(pos, [f"{i} (n={n})" for i, n in zip(st.index, st.n)], fontsize=7)
    a.set(title="Error porcentual por estación", xlabel="MAPE (%)"); a.legend(fontsize=8)

    a = ax[1, 1]
    tt, ta = resumen(tem, "tamano"), resumen(ale, "tamano")
    pos = np.arange(len(tt))
    a.bar(pos - .2, ta.mape * 100, .4, color=AZUL_CLARO, label="aleatoria")
    a.bar(pos + .2, tt.mape * 100, .4, color=AZUL, label="temporal")
    a.set_xticks(pos, tt.index.astype(str)); a.set(title="Error porcentual por tamaño (sqf)", ylabel="MAPE (%)")
    for a in ax.flat: a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(FIG / "errores_modelo.png", dpi=150); plt.close(fig)

    # hallazgos para el reporte
    print("Sesgo medio temporal por año (negativo = subestima):")
    print((resumen(tem, "YrSold").sesgo / 1000).round(1).to_string())
    print("\nMAPE temporal por estación:")
    print((st.mape * 100).round(1).to_string())
    print("\nMAPE por tamaño (aleatoria | temporal):")
    print(pd.DataFrame({"aleatoria": ta.mape * 100, "temporal": tt.mape * 100}).round(1).to_string())
    print("\nGuardado: reports/errores_por_segmento.csv y reports/figures/errores_modelo.png")


if __name__ == "__main__":
    main()
