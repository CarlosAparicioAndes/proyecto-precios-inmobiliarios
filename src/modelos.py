"""Estimadores propios del proyecto.

TendenciaMasArboles: respuesta a "que hacer con YrSold".
Los arboles (Random Forest, Boosting) no extrapolan: para ventas de 2015-2017 repiten precios de
2014 y subestiman. Ridge si extrapola, pero describe mal las diferencias entre apartamentos.
Este modelo combina las dos ideas en dos etapas:
  1. Tendencia del mercado: regresion lineal de log(precio) contra el momento de venta
     (YrSold + MonthSold/12). Al ser lineal, se puede proyectar a anios posteriores.
  2. Diferencias entre apartamentos: un modelo de arboles (pipeline de scikit-learn) aprende el
     residuo log(precio) - tendencia con las variables del apartamento.
Prediccion = exp(tendencia + residuo), en unidades de precio (apta para la API y el tablero).
"""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.linear_model import LinearRegression


class TendenciaMasArboles(BaseEstimator, RegressorMixin):
    def __init__(self, modelo_residuo, col_anio="YrSold", col_mes="MonthSold"):
        self.modelo_residuo = modelo_residuo
        self.col_anio = col_anio
        self.col_mes = col_mes

    def _tiempo(self, X):
        t = X[self.col_anio].astype(float).to_numpy()
        if self.col_mes in X.columns:
            t = t + (X[self.col_mes].astype(float).to_numpy() - 1) / 12
        return t.reshape(-1, 1)

    def fit(self, X, y):
        X = pd.DataFrame(X)
        ylog = np.log(np.asarray(y, dtype=float))
        self.tendencia_ = LinearRegression().fit(self._tiempo(X), ylog)
        self.residuo_ = clone(self.modelo_residuo).fit(X, ylog - self.tendencia_.predict(self._tiempo(X)))
        return self

    def predict(self, X):
        X = pd.DataFrame(X)
        return np.exp(self.tendencia_.predict(self._tiempo(X)) + self.residuo_.predict(X))

    @property
    def crecimiento_anual(self):
        """Crecimiento anual del precio implicito en la tendencia (p. ej. 0.07 = 7 % por anio)."""
        return float(np.exp(self.tendencia_.coef_[0]) - 1)
