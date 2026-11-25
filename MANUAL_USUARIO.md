# Manual de usuario

**Guía de uso del tablero de valoración de apartamentos**

Despliegue de Soluciones Analíticas · Proyecto, Entrega 3

Grupo 39: Carlos Aparicio, Libardo Navas, Gino Ulloa · 24 de noviembre de 2026

Repositorio: https://github.com/CarlosAparicioAndes/proyecto-precios-inmobiliarios

## 1. Objetivo y acceso

Este manual busca facilitar el uso del tablero desarrollado por el Grupo 39. La herramienta permite que un asesor inmobiliario estime el precio de venta de un apartamento en Daegu a partir de ocho características, compare el resultado con los precios históricos de la zona y revise el desempeño del modelo. No se requieren conocimientos de programación.

Para ingresar, abra el navegador y escriba http://localhost:8050 si la solución está instalada en su equipo. Si está desplegada en AWS, utilice http://IP_PUBLICA:8050, reemplazando IP_PUBLICA por la dirección vigente que le entregue el encargado de la instalación. La instancia y los servicios deben estar activos.

## 2. Formulario de características

En el lado izquierdo de la pantalla se encuentran los campos que se deben diligenciar. Los valores numéricos tienen límites definidos en el formulario y los campos categóricos se seleccionan en listas desplegables.

| **Campo**                 | **Qué ingresar / opciones**                                                                                                    |
|---------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| Tamaño (sqf)              | Área del apartamento en pies cuadrados: de 135 a 2337                                                                          |
| Año de construcción       | Año en que se construyó: 1978 a 2015                                                                                           |
| Piso                      | Número del piso: 1 a 43                                                                                                        |
| Tipo de pasillo           | corridor, mixed o terraced                                                                                                     |
| Estación de metro cercana | Bangoge, Banwoldang, Chil-sung-market, Daegu, Kyungbuk_uni_hospital, Myung-duk, Sin-nam o no_subway_nearby (sin metro cercano) |
| Gestión                   | management_in_trust (administración delegada) o self_management                                                                |
| Parqueaderos en sótano    | Cantidad de parqueaderos del conjunto o edificio: 0 a 1.321                                                                    |
| Año de venta              | 2007 a 2019; los años 2018 y 2019 están fuera del periodo histórico                                                            |

## 3. Estimación del precio

1.  Verifique las características del inmueble y diligencie los ocho campos.

2.  Seleccione las categorías que correspondan al apartamento.

3.  Presione el botón Estimar precio. El tablero consulta la API y actualiza las tarjetas y la gráfica de factores.

4.  Revise el precio, su intervalo y la comparación con la zona. Para evaluar otro inmueble, modifique los campos y vuelva a presionar el botón.

## 4. Interpretación de los resultados

- Precio estimado: corresponde al valor calculado por el modelo v2 (tendencia + boosting). El intervalo del 80 % es una referencia construida con los errores históricos de validación; no garantiza que el precio real se encuentre dentro de esos límites. Para ventas posteriores a 2017, el tablero utiliza un intervalo más amplio basado en la validación temporal.

- Mediana de la zona: muestra el precio mediano histórico de los apartamentos asociados a la estación seleccionada y el porcentaje que separa la estimación de esa referencia. Cuando hay menos de 100 ventas, se indica el número de observaciones. La comparación no equivale a una tasación de mercado actual.

- Versión del modelo: permite identificar la versión v2 y el MAE de validación aleatoria (10,6 mil). Este error no debe confundirse con el error temporal mostrado en el monitoreo.

- Factores que más pesan: la gráfica presenta las cinco variables con mayor cambio absoluto en el precio cuando cada una se reemplaza por su valor típico, manteniendo las demás constantes. Una barra larga indica mayor sensibilidad de esa estimación, no necesariamente un aumento del precio ni una relación causal.

- Precio mediano por año de venta: muestra la evolución histórica entre 2007 y 2017. Sirve para contextualizar la tendencia del mercado y no representa una proyección de precios futuros.

## 5. Monitoreo del modelo

| **Indicador**        | **Interpretación**                                                                                                                                    |
|----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| MAE temporal: 32.924 | En promedio, la estimación se desvía 32.924 unidades de precio en las ventas de 2015 a 2017                                                           |
| MAPE temporal: 13 %  | Error porcentual absoluto medio, redondeado en el tablero                                                                                             |
| Deriva (PSI \> 0,2)  | Alerta por cambios en la distribución del año de construcción (0,427) y los parqueaderos de sótano (0,205). El año de venta se excluye de esta alerta |
| Última actualización | Fecha del entrenamiento registrada en metadata.json: 8 de noviembre de 2026, 17:49. Se muestran 3.932 ventas                                          |

El monitoreo corresponde a una comparación histórica entre 2007–2014 y 2015–2017. No se actualiza automáticamente con las consultas que realiza el usuario.

## 6. Ejemplo práctico

Como primer ejercicio se utilizan los valores iniciales del tablero: tamaño 914 sqf, construcción 2005, piso 8, pasillo terraced, estación Banwoldang, gestión management_in_trust, 184 parqueaderos y año de venta 2017. Según el reporte, la estimación es 240339, con un intervalo de 221020 a 259107 y una diferencia del 26 % por debajo de la mediana de la zona (326548).

Para comparar, cambie el tamaño a 1.500 sqf, el año de construcción a 2013, el piso a 20 y la estación a Kyungbuk_uni_hospital, dejando los otros campos iguales. Presione Estimar precio. En la demostración del proyecto se obtuvo 505863, aproximadamente 104 % por encima de la mediana de esa zona (247787).

## 7. Errores y recomendaciones

| **Situación**                                   | **Qué hacer**                                                                                                                                      |
|-------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Complete todos los campos                       | Revise que ningún campo esté vacío y vuelva a estimar.                                                                                             |
| Valor numérico fuera de rango                   | Corrija el valor según la tabla del formulario. No fuerce datos por fuera de los límites.                                                          |
| No se carga el tablero o no cambia el resultado | Revise la conexión y confirme con el encargado que la API y el tablero estén activos. No interprete una salida anterior como una nueva estimación. |

La herramienta es un prototipo de apoyo a la decisión, no una tasación oficial. El modelo subestima las ventas de 2015 a 2017 en unas 17 mil unidades en promedio y tiene mayor error en apartamentos pequeños y sin metro cercano. La unidad monetaria de SalePrice todavía no está confirmada en el repositorio; por ello no se presentan los resultados como pesos, dólares o wones.
