# Diccionario de datos

Archivo: `data/raw/train_real_state.csv` (4.124 filas, 30 columnas; 3.932 filas únicas).
Ventas de apartamentos en Daegu (Corea del Sur) entre 2007 y 2017.
Las descripciones se basan en el nombre de cada columna y en sus valores observados; la fuente oficial del dataset está pendiente de confirmar.

## Variable objetivo

| Variable | Descripción | Tipo | Rango / valores |
|---|---|---|---|
| `SalePrice` | Precio de venta del apartamento (unidad monetaria por confirmar). En `test_real_state.csv` es un identificador, no un precio. | Numérica continua | 32.743 a 585.840 |

## Características del apartamento y del edificio

| Variable | Descripción | Tipo | Rango / valores |
|---|---|---|---|
| `Size.sqf.` | Área del apartamento en pies cuadrados | Numérica | 135 a 2.337 |
| `Floor` | Piso en el que está el apartamento | Numérica discreta | 1 a 43 |
| `YearBuilt` | Año de construcción del edificio | Numérica discreta | 1978 a 2015 |
| `HallwayType` | Tipo de pasillo del edificio | Categórica | `terraced`, `mixed`, `corridor` |
| `HeatingType` | Tipo de calefacción | Categórica binaria | `individual_heating`, `central_heating` |
| `AptManageType` | Tipo de administración del conjunto | Categórica binaria | `management_in_trust`, `self_management` |
| `N_APT` | Número de edificios (torres) del conjunto | Numérica discreta | 1 a 13 |
| `N_manager` | Número de administradores del conjunto | Numérica discreta | 1 a 14 |
| `N_elevators` | Número de ascensores | Numérica discreta | 0 a 27 |
| `N_FacilitiesInApt` | Número de instalaciones dentro del conjunto | Numérica discreta | 1 a 10 |
| `N_Parkinglot.Ground.` | Cupos de parqueadero en superficie | Numérica discreta | 0 a 713 |
| `N_Parkinglot.Basement.` | Cupos de parqueadero en sótano | Numérica discreta | 0 a 1.321 |

## Transporte

| Variable | Descripción | Tipo | Rango / valores |
|---|---|---|---|
| `TimeToBusStop` | Tiempo a pie a la parada de bus más cercana | Categórica ordinal | `0~5min`, `5min~10min`, `10min~15min` |
| `TimeToSubway` | Tiempo a pie a la estación de metro más cercana | Categórica ordinal | `0-5min`, `5min~10min`, `10min~15min`, `15min~20min`, `no_bus_stop_nearby` (*) |
| `SubwayStation` | Estación de metro más cercana | Categórica nominal | `Kyungbuk_uni_hospital`, `Myung-duk`, `Bangoge`, `Banwoldang`, `Sin-nam`, `Chil-sung-market`, `Daegu`, `no_subway_nearby` |

(*) `no_bus_stop_nearby` aparece en 162 filas que también tienen `SubwayStation = no_subway_nearby`; se interpreta como "sin metro cercano" y se unifica en `src/clean.py`.

## Entorno: instalaciones cercanas

| Variable | Descripción | Tipo | Rango |
|---|---|---|---|
| `N_FacilitiesNearBy.PublicOffice.` | Oficinas públicas cercanas | Numérica discreta | 0 a 7 |
| `N_FacilitiesNearBy.Hospital.` | Hospitales cercanos | Numérica discreta | 0 a 2 |
| `N_FacilitiesNearBy.Dpartmentstore.` | Grandes almacenes cercanos | Numérica discreta | 0 a 2 |
| `N_FacilitiesNearBy.Mall.` | Centros comerciales cercanos | Numérica discreta | 0 a 2 |
| `N_FacilitiesNearBy.Park.` | Parques cercanos | Numérica discreta | 0 a 2 |
| `N_FacilitiesNearBy.ETC.` | Otras instalaciones cercanas | Numérica discreta | 0 a 5 |
| `N_FacilitiesNearBy.Total.` | Total de instalaciones cercanas (suma de las anteriores) | Numérica discreta | 0 a 16 |

## Entorno: colegios cercanos

| Variable | Descripción | Tipo | Rango |
|---|---|---|---|
| `N_SchoolNearBy.Elementary.` | Escuelas primarias cercanas | Numérica discreta | 0 a 6 |
| `N_SchoolNearBy.Middle.` | Escuelas secundarias cercanas | Numérica discreta | 0 a 4 |
| `N_SchoolNearBy.High.` | Colegios de educación media cercanos | Numérica discreta | 0 a 5 |
| `N_SchoolNearBy.University.` | Universidades cercanas | Numérica discreta | 0 a 5 |
| `N_SchoolNearBy.Total.` | Total de colegios cercanos (suma de las anteriores) | Numérica discreta | 0 a 17 |

## Momento de la venta

| Variable | Descripción | Tipo | Rango |
|---|---|---|---|
| `YrSold` | Año de la venta | Numérica discreta | 2007 a 2017 |
| `MonthSold` | Mes de la venta | Numérica discreta | 1 a 12 |

## Variables derivadas (no están en el CSV)

| Variable | Cálculo | Dónde se usa |
|---|---|---|
| `AptAge` | `YrSold − YearBuilt` (antigüedad al vender) | `src/clean.py` |
| `PricePerSqf` | `SalePrice / Size.sqf.` | `notebooks/02_eda_precio_por_sqf.ipynb`, `notebooks/03_eda_servicios_cercanos.ipynb` |

## Notas para el modelo y la API
- Las columnas `*.Total.` son la suma de sus componentes: no conviene usar ambas a la vez en modelos lineales (multicolinealidad).
- `TimeToBusStop` y `TimeToSubway` son ordinales: pueden codificarse respetando el orden (más cerca, menor valor).
- Las variables de entorno son constantes dentro de cada conjunto de edificios y funcionan como un indicador de ubicación (ver `notebooks/03_eda_servicios_cercanos.ipynb`).
- Los rangos de esta tabla sirven para validar las entradas del formulario del tablero y de la API.
