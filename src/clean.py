"""Limpieza de datos - Entrega 1.
Uso (desde la raiz del repo): python src/clean.py
Lee data/raw/*.csv y escribe data/processed/*_clean.csv (versionados con DVC).

Decisiones de limpieza (revisar y confirmar con el equipo):
1. Se eliminan las filas duplicadas exactas del archivo de entrenamiento.
2. TimeToSubway = 'no_bus_stop_nearby' parece una etiqueta mal puesta: todas esas filas tienen
   SubwayStation = 'no_subway_nearby'. Se renombra a 'no_subway_nearby' (supuesto a confirmar).
3. Se crea la variable AptAge = YrSold - YearBuilt (antiguedad del apartamento al vender).
4. El archivo de test no se deduplica; su columna SalePrice es un identificador, no un precio,
   asi que se renombra a Id para evitar confusiones.
"""
import os
import pandas as pd

RAW = "data/raw"; OUT = "data/processed"
os.makedirs(OUT, exist_ok=True)

def limpiar(df):
    df = df.copy()
    df["TimeToSubway"] = df["TimeToSubway"].replace("no_bus_stop_nearby", "no_subway_nearby")
    df["AptAge"] = df["YrSold"] - df["YearBuilt"]
    return df

tr = pd.read_csv(f"{RAW}/train_real_state.csv")
n0 = len(tr)
tr = limpiar(tr.drop_duplicates()).reset_index(drop=True)
print(f"train: {n0} filas -> {len(tr)} tras eliminar {n0-len(tr)} duplicados")
tr.to_csv(f"{OUT}/train_clean.csv", index=False)

te = pd.read_csv(f"{RAW}/test_real_state.csv").rename(columns={"SalePrice": "Id"})
te = limpiar(te)
print(f"test: {len(te)} filas (SalePrice renombrada a Id)")
te.to_csv(f"{OUT}/test_clean.csv", index=False)

print("AptAge (train): min", tr.AptAge.min(), "max", tr.AptAge.max())
print("TimeToSubway:", tr.TimeToSubway.value_counts().to_dict())
