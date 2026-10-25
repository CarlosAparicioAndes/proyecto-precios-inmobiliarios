"""EDA - Entrega 1 - Prediccion de precios de apartamentos (Despliegue de Soluciones Analiticas)
Uso (desde la raiz del repo): python src/eda.py data/raw/train_real_state.csv data/raw/test_real_state.csv reports/figures"""
import sys, json, pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
tr_p, te_p, out = sys.argv[1:4]
tr=pd.read_csv(tr_p); te=pd.read_csv(te_p)
plt.rcParams.update({"font.size":9,"axes.spines.top":False,"axes.spines.right":False,"figure.dpi":130})
C="#1F3A5F"; res={}
res["shape_train"]=tr.shape; res["shape_test"]=te.shape
res["dups_train"]=int(tr.duplicated().sum()); res["nulls"]=int(tr.isna().sum().sum())
res["price"]=tr.SalePrice.describe().round(0).to_dict(); res["skew"]=float(tr.SalePrice.skew())
q1,q3=tr.SalePrice.quantile([.25,.75]); iqr=q3-q1
res["price_outliers"]=int(((tr.SalePrice>q3+1.5*iqr)|(tr.SalePrice<q1-1.5*iqr)).sum())
q1,q3=tr["Size.sqf."].quantile([.25,.75]); iqr=q3-q1
res["size_outliers"]=int(((tr["Size.sqf."]>q3+1.5*iqr)|(tr["Size.sqf."]<q1-1.5*iqr)).sum())
# 1 distribucion del precio
f,ax=plt.subplots(1,2,figsize=(8,3))
ax[0].hist(tr.SalePrice,bins=40,color=C); ax[0].set_title("Distribución del precio de venta"); ax[0].set_xlabel("SalePrice")
ax[1].hist(np.log(tr.SalePrice),bins=40,color="#6C8EBF"); ax[1].set_title("Logaritmo del precio"); ax[1].set_xlabel("log(SalePrice)")
f.tight_layout(); f.savefig(f"{out}/fig1_precio.png"); plt.close(f)
# 2 tamano vs precio
f,ax=plt.subplots(figsize=(5,3.4)); ax.scatter(tr["Size.sqf."],tr.SalePrice,s=5,alpha=.35,color=C)
ax.set_xlabel("Tamaño (sqf)"); ax.set_ylabel("Precio de venta"); ax.set_title("Tamaño vs. precio (r = %.2f)"%tr["Size.sqf."].corr(tr.SalePrice))
f.tight_layout(); f.savefig(f"{out}/fig2_tamano.png"); plt.close(f)
# 3 correlaciones con el precio
num=tr.select_dtypes("number"); cor=num.corr()["SalePrice"].drop("SalePrice").sort_values()
res["corr"]=cor.round(2).to_dict()
f,ax=plt.subplots(figsize=(6,5.2)); ax.barh(cor.index,cor.values,color=[C if v>0 else "#C0504D" for v in cor.values])
ax.set_title("Correlación de cada variable con el precio"); ax.axvline(0,color="k",lw=.6); f.tight_layout(); f.savefig(f"{out}/fig3_correlaciones.png"); plt.close(f)
# 4 categoricas
cats=["SubwayStation","HallwayType","HeatingType","AptManageType"]
f,axs=plt.subplots(2,2,figsize=(8,5.6))
for a,c in zip(axs.flat,cats):
    order=tr.groupby(c).SalePrice.median().sort_values().index
    a.boxplot([tr.SalePrice[tr[c]==k] for k in order],tick_labels=order,showfliers=False,patch_artist=True,boxprops=dict(facecolor="#DCE6F2"),medianprops=dict(color=C))
    a.set_title(f"Precio por {c}"); a.tick_params(axis="x",labelsize=7); plt.setp(a.get_xticklabels(),rotation=40,ha="right")
f.tight_layout(); f.savefig(f"{out}/fig4_categoricas.png"); plt.close(f)
res["median_by_station"]=tr.groupby("SubwayStation").SalePrice.median().round(0).sort_values().to_dict()
res["median_by_hall"]=tr.groupby("HallwayType").SalePrice.median().round(0).to_dict()
res["n_by_station"]=tr.SubwayStation.value_counts().to_dict()
# 5 edad y piso
f,ax=plt.subplots(1,2,figsize=(8,3))
m=tr.groupby("YearBuilt").SalePrice.median(); ax[0].plot(m.index,m.values,marker="o",color=C); ax[0].set_title("Precio mediano por año de construcción"); ax[0].set_xlabel("YearBuilt")
m=tr.groupby("Floor").SalePrice.median(); ax[1].plot(m.index,m.values,marker="o",color=C); ax[1].set_title("Precio mediano por piso"); ax[1].set_xlabel("Floor")
f.tight_layout(); f.savefig(f"{out}/fig5_edad_piso.png"); plt.close(f)
# 6 temporal
f,ax=plt.subplots(1,2,figsize=(8,3)); m=tr.groupby("YrSold").SalePrice.median()
ax[0].plot(m.index,m.values,marker="o",color=C); ax[0].set_title("Precio mediano por año de venta")
ax[1].bar(tr.YrSold.value_counts().sort_index().index,tr.YrSold.value_counts().sort_index().values,color="#6C8EBF"); ax[1].set_title("Número de ventas por año")
f.tight_layout(); f.savefig(f"{out}/fig6_temporal.png"); plt.close(f)
res["median_by_year"]=m.round(0).to_dict()
# calidad
res["subway_labels"]=tr.TimeToSubway.value_counts().to_dict()
res["odd_rows"]=int((tr.TimeToSubway=="no_bus_stop_nearby").sum())
res["cross_tab_odd"]=pd.crosstab(tr.TimeToSubway=="no_bus_stop_nearby",tr.SubwayStation=="no_subway_nearby").to_dict()
# train vs test
res["test_year_share"]=te.YrSold.value_counts(normalize=True).sort_index().round(3).to_dict()
res["train_year_share"]=tr.YrSold.value_counts(normalize=True).sort_index().round(3).to_dict()
# modelo base (el test no trae precio: su columna SalePrice es un identificador 1..5891)
from sklearn.model_selection import train_test_split
res["test_SalePrice_es_id"]=bool(te.SalePrice.min()>=1 and te.SalePrice.max()<=len(tr)+len(te) and te.SalePrice.is_unique)
dd=tr.drop_duplicates().reset_index(drop=True)
def prep(d): return pd.get_dummies(d.drop(columns="SalePrice")).astype(float)
X=prep(dd); y=dd.SalePrice
Xa,Xb,ya,yb=train_test_split(X,y,test_size=.2,random_state=0)
for name,m in [("Regresión lineal",LinearRegression()),("Random Forest",RandomForestRegressor(n_estimators=300,random_state=0,n_jobs=-1))]:
    m.fit(Xa,ya); p=m.predict(Xb)
    res.setdefault("modelos_aleatorio",{})[name]={"MAE":float(mean_absolute_error(yb,p)),"RMSE":float(mean_squared_error(yb,p)**.5),"R2":float(r2_score(yb,p))}
    if name=="Random Forest": rf=m
imp=pd.Series(rf.feature_importances_,index=X.columns).sort_values().tail(12)
res["importancias"]=imp.round(3).sort_values(ascending=False).to_dict()
f,ax=plt.subplots(figsize=(6,3.6)); ax.barh(imp.index,imp.values,color=C); ax.set_title("Importancia de variables (Random Forest base)")
f.tight_layout(); f.savefig(f"{out}/fig7_importancias.png"); plt.close(f)
# prueba temporal: entrenar con ventas hasta 2014 y evaluar con 2015-2017
a=dd[dd.YrSold<=2014]; b=dd[dd.YrSold>=2015]
Xa2=prep(a); Xb2=prep(b).reindex(columns=Xa2.columns,fill_value=0)
r=RandomForestRegressor(n_estimators=300,random_state=0,n_jobs=-1).fit(Xa2,a.SalePrice); pb=r.predict(Xb2)
res["temporal"]={"R2":float(r2_score(b.SalePrice,pb)),"MAE":float(mean_absolute_error(b.SalePrice,pb)),"bias_medio":float((pb-b.SalePrice).mean()),"n_train":len(a),"n_test":len(b)}
rl=LinearRegression().fit(Xa2,a.SalePrice); pl=rl.predict(Xb2)
res["temporal_lineal"]={"R2":float(r2_score(b.SalePrice,pl)),"MAE":float(mean_absolute_error(b.SalePrice,pl))}
json.dump(res,open(f"{out}/resultados.json","w"),indent=1,default=str,ensure_ascii=False)
print(json.dumps(res,indent=1,default=str,ensure_ascii=False))
