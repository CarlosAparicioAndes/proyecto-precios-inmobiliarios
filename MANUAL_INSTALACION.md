# Manual de instalación

**Guía de uso del tablero de valoración de apartamentos**

Despliegue de Soluciones Analíticas · Proyecto, Entrega 3

Grupo 39: Carlos Aparicio, Libardo Navas, Gino Ulloa · 24 de noviembre de 2026

Repositorio: https://github.com/CarlosAparicioAndes/proyecto-precios-inmobiliarios

## 1. Objetivo y arquitectura

El objetivo de este manual es explicar cómo poner en funcionamiento la solución de predicción de precios inmobiliarios del Grupo 39. En la Entrega 3 se separó el tablero del modelo, de manera que el usuario interactúa con Dash y el tablero solicita las predicciones a una API desarrollada en FastAPI. Los dos servicios se ejecutan en contenedores independientes.

## 2. Requisitos previos

| Recurso                | Requisito                                                                                                         |
|------------------------|-------------------------------------------------------------------------------------------------------------------|
| Equipo local           | Windows, Linux o macOS con Docker en ejecución, Git, navegador e Internet                                         |
| Docker                 | Docker Engine o Docker Desktop con Docker Compose v2 o compatible (comando docker compose)                        |
| AWS (opcional)         | Acceso a AWS Academy o una cuenta AWS, permisos EC2 y clave SSH.                                                  |
| Recursos de referencia | EC2 t3.small, 2 vCPU, 2 GiB RAM, 20 GiB de disco, Ubuntu Server 24.04 LTS, us-east-1. No son mínimos certificados |
| Puertos                | 8050 para el tablero; 8001 para la API; 22 para SSH en EC2                                                        |

Los contenedores usan Python 3.12-slim. No se necesita instalar Python en el equipo anfitrión para el flujo con Docker. El repositorio incluye modelo.joblib y metadata.json, por lo que no es necesario descargar los datos mediante DVC ni tener MLflow activo para usar el modelo ya entrenado.

## 3. Instalación local con Docker Compose

Paso 1. Abra PowerShell o una terminal y compruebe que Git y Docker estén disponibles:

```bash
git --version
docker --version
docker compose version
```

Paso 2. Clone el repositorio y ubíquese en la carpeta raíz. Si descargó el ZIP, extráigalo y abra una terminal en la carpeta que contiene docker-compose.yml.

```bash
git clone https://github.com/CarlosAparicioAndes/proyecto-precios-inmobiliarios.git
cd proyecto-precios-inmobiliarios
```

Paso 3. Compruebe que existan models/modelo.joblib, models/metadata.json, api/Dockerfile, dashboard/Dockerfile y docker-compose.yml. Ejecute desde la raíz:

```bash
docker compose up --build -d
docker compose ps
```

*Compose* construye precios-api y precios-tablero, crea la red interna y espera a que la API esté saludable antes de iniciar el tablero. La variable API_URL ya está configurada en docker-compose.yml como http://api:8001/api/v1/predict; no requiere un archivo .env para esta instalación.

## 4. Verificación de funcionamiento

| Servicio | Dirección local                     |
|----------|-------------------------------------|
| Tablero  | http://localhost:8050               |
| Swagger  | http://localhost:8001/docs          |
| Estado   | http://localhost:8001/api/v1/health |
| Métricas | http://localhost:8001/api/v1/modelo |

En docker compose ps, la API debe aparecer en estado healthy y el tablero en ejecución. Abra la ruta health y compruebe estado: ok, api_version: 0.2.0 y version_modelo: v2. En el tablero, diligencie los campos y presione Estimar precio.

Para probar directamente la API, abra Swagger, seleccione POST /api/v1/predict, presione Try it out y pegue el siguiente cuerpo JSON. Luego seleccione Execute.

```json
{
  "inputs": [
    {
      "Size.sqf.": 914,
      "YearBuilt": 2005,
      "Floor": 8,
      "HallwayType": "terraced",
      "SubwayStation": "Banwoldang",
      "AptManageType": "management_in_trust",
      "N_Parkinglot.Basement.": 184,
      "YrSold": 2017
    }
  ]
}
```

Se espera una respuesta HTTP 200 con predictions (lista de precios), version y modelo. El precio de referencia del reporte para estos datos es aproximadamente 240.339. La API recibe de 1 a 100 apartamentos por solicitud. Las entradas numéricas inválidas o los campos faltantes generan HTTP 422; las categorías se reciben como cadenas y no cuentan con una lista explícita de validación en la API de esta versión.

## 5. Despliegue en AWS EC2

Paso 1. Inicie el laboratorio de AWS Academy, si aplica. Cree una instancia EC2 con Ubuntu Server 24.04 LTS, tipo t3.small y 20 GiB de almacenamiento, según la configuración usada por el equipo. Seleccione una clave SSH y conserve el archivo .pem en un lugar seguro.

Paso 2. Configure el grupo de seguridad: permita TCP 22 desde su IP para SSH y TCP 8050 desde las IP autorizadas para el tablero. Habilite TCP 8001 desde las IP autorizadas solo si necesita acceder a Swagger de forma externa. El reporte registra reglas abiertas a 0.0.0.0/0 para la demostración; se recomienda restringirlas debido a que el prototipo no incorpora autenticación ni HTTPS.

Paso 3. Copie la IP pública actual desde la consola EC2 y conéctese desde su terminal. Reemplace los valores de ejemplo por la ruta de su llave y la IP de la instancia.

```bash
ssh -i "RUTA_A_LA_LLAVE.pem" ubuntu@IP_PUBLICA
```

Paso 4. Instale Git, Docker Engine y el complemento Compose. Los siguientes comandos son una opción de instalación para Ubuntu 24.04 mediante sus paquetes; verifique su disponibilidad en la instancia.

```bash
sudo apt update
sudo apt install -y git docker.io docker-compose-v2
sudo systemctl enable --now docker
sudo docker compose version
```

Paso 5. Clone el repositorio y levante los servicios con Compose.

```bash
git clone https://github.com/CarlosAparicioAndes/proyecto-precios-inmobiliarios.git
cd proyecto-precios-inmobiliarios
sudo docker compose up --build -d
sudo docker compose ps
```

Paso 6. Desde el navegador de su equipo, ingrese a http://IP_PUBLICA:8050 y, si el puerto 8001 está habilitado, a http://IP_PUBLICA:8001/docs. Repita las pruebas de la sección 4. La IP de la instancia puede cambiar al detenerla y volverla a iniciar.

```bash
sudo docker compose logs --tail=50 api
sudo docker compose logs --tail=50 tablero
```

Los registros permiten revisar si el tablero envía solicitudes POST a la API y detectar errores de comunicación.

## 6. Alternativas de instalación

### 6.1 Contenedores independientes

Si se requiere ejecutar cada componente sin Compose, cree una red Docker compartida. En la raíz del repositorio ejecute los comandos siguientes (en EC2, anteponga sudo si es necesario).

```bash
docker network create precios-red
docker build -f api/Dockerfile -t precios-api .
docker run -d --name precios-api --network precios-red -p 8001:8001 precios-api
```

Compruebe que la API responda en /api/v1/health antes de iniciar el tablero. La variable API_URL debe apuntar al nombre del contenedor en la red compartida, no a localhost.

```bash
docker build -f dashboard/Dockerfile -t precios-tablero .
docker run -d --name precios-tablero --network precios-red -p 8050:8050 -e API_URL=http://precios-api:8001/api/v1/predict precios-tablero
```

No ejecute esta alternativa al mismo tiempo que Compose, porque ambos flujos utilizan los mismos puertos.

### 6.2 Ejecución local sin Docker

Como alternativa de desarrollo, instale Python (se recomienda 3.12, por ser la versión base de los contenedores). Desde la raíz cree y active un entorno virtual:

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux/macOS (en lugar del comando de Windows)
source .venv/bin/activate
python -m pip install -r requirements.txt -r api/requirements.txt -r dashboard/requirements.txt
python -m uvicorn app.main:app --app-dir api --port 8001
```

Abra otra terminal en la raíz, active el mismo entorno virtual y configure la dirección de la API según su sistema operativo:

```bash
# Windows PowerShell
$env:API_URL = "http://localhost:8001/api/v1/predict"
# Linux/macOS (en lugar del comando de Windows)
export API_URL=http://localhost:8001/api/v1/predict
python dashboard/app.py
```

Si no se define API_URL, el tablero carga el modelo localmente, como en la Entrega 2. Para comprobar la integración de la Entrega 3 se debe mantener la variable configurada.

## 7. Pruebas y mantenimiento

En el entorno virtual con las dependencias instaladas, ejecute las pruebas desde la raíz:

```bash
python -m pip install pytest httpx
python -m pytest tests -v
```

El reporte registra 15 pruebas aprobadas: 8 para la API y 7 para el modelo. Esta es la referencia esperada, no el resultado de una nueva ejecución. Para actualizar los archivos del modelo, mantenga modelo.joblib y metadata.json sincronizados y reconstruya ambos contenedores, ya que el tablero también incorpora los metadatos.

```bash
git pull
docker compose up --build -d
docker compose ps
```

## 8. Solución de problemas

| Problema                  | Acción sugerida                                                                              |
|---------------------------|----------------------------------------------------------------------------------------------|
| Docker no está disponible | Inicie Docker Desktop o el servicio Docker de Ubuntu. Verifique docker compose version.      |
| Puerto ocupado            | Detenga el servicio que usa 8001 o 8050; compruebe que no esté ejecutando dos instalaciones. |
| API unhealthy             | Revise docker compose logs api y la presencia de los archivos en models/.                    |
| Tablero sin predicción    | Revise docker compose logs tablero y API_URL. Confirme que health responda.                  |
| No hay acceso desde EC2   | Verifique IP pública actual, reglas de entrada, estado de instancia y contenedores.          |
| HTTP 422                  | Revise el JSON, los ocho campos, los tipos y rangos numéricos.                               |

## 9. Detención de la solución

Para detener los servicios de Compose y eliminar sus contenedores y red (sin eliminar los archivos del repositorio), ejecute:

```bash
docker compose down
```

Para la alternativa de contenedores independientes:

```bash
docker rm -f precios-tablero precios-api
docker network rm precios-red
```

Si está en EC2, use sudo cuando corresponda, cierre la conexión SSH y detenga la instancia desde la consola AWS cuando ya no la necesite. No la termine si desea conservarla. Revise los recursos asociados que puedan seguir generando costos.
