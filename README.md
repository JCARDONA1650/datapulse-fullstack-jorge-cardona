# DataPulse Latam

Plataforma web para centralizar el monitoreo de indicadores económicos, tipos de cambio e índices de riesgo país de 10 economías latinoamericanas, y para gestionar portafolios simulados de inversión.

Prueba técnica Fullstack (Angular + Django) para Mission S.A.S.

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Django 6 + Django REST Framework |
| Frontend | Angular 20 (standalone, strict mode) + Angular Material |
| Base de datos | PostgreSQL |
| Autenticación | JWT (djangorestframework-simplejwt) |
| Documentación API | drf-spectacular (Swagger / Redoc) |
| Tareas programadas | Django management commands |

## Decisiones técnicas y alternativas consideradas

- **Angular standalone en vez de NgModules**: menos boilerplate, es el estilo recomendado por el equipo de Angular desde la v15+ y el requerimiento solo exige Angular 12+, sin especificar el estilo.
- **Management commands en vez de Celery + Redis**: las 3 tareas (sincronización de indicadores, recálculo de IRPC, tipos de cambio) se ejecutan bajo demanda o por cron, sin necesidad de una cola de tareas. Esto simplifica el despliegue (sin Redis ni worker adicional) y el requerimiento lo permite explícitamente.
- **PostgreSQL en Docker para desarrollo local**: se reutiliza el mismo `docker-compose.yml` que suma puntos extra, evitando instalar PostgreSQL de forma nativa.
- **ADMIN puede editar/eliminar cualquier portafolio**, no solo los propios (un ANALISTA solo gestiona los suyos). Es la única lectura que hace consistente el escenario de prueba obligatorio #5 ("dos usuarios editan el mismo portafolio público"): sin esta regla, un portafolio solo lo puede editar su dueño y la concurrencia entre dos usuarios distintos nunca podría darse. Confirmado con Mission S.A.S. como un alcance válido (ver `documentacion/INCONSISTENCIAS.md`, punto 3).
- **Mapa de riesgo como scatter de coordenadas reales, no un mapa SVG/GeoJSON de Latinoamerica.** El stack permitido para gráficos es ngx-charts, Chart.js o Plotly — ninguno trae mapas de paises listos sin una librería adicional (Leaflet, d3-geo). Usar latitud/longitud reales de cada país como ejes X/Y de un scatter de Chart.js, coloreado por nivel de riesgo, da una lectura geográfica razonable sin sumar una dependencia nueva fuera de lo permitido.
- **`gunicorn` + `whitenoise`** para servir el backend en Docker/producción (en vez de `runserver`, que no es apto para producción). Whitenoise evita depender de un servidor de archivos estáticos aparte solo para el admin de Django y los assets de Swagger UI.
- **E2E con Playwright** en vez de Cypress o Protractor: Angular CLI ya no incluye Protractor por defecto, y Playwright no exige un runner de navegador adicional ni configuración extra para correr en modo headless.
- Resolución de los puntos ambiguos de los requerimientos: ver sección [Puntos ambiguos resueltos](#puntos-ambiguos-resueltos).

## Arquitectura

_Diagrama pendiente – se agrega al cerrar las fases de backend y frontend._

## Diagrama entidad-relación

_Pendiente – se agrega al cerrar la fase de modelo de datos._

## Instalación y ejecución local

### Requisitos

- Python 3.12+
- Node.js 22+
- Docker y Docker Compose

### 1. Variables de entorno

```
cp .env.example .env
cp .env.example backend/.env
```

En `backend/.env`, cambiar `POSTGRES_HOST` a `localhost` (en `.env` de la raíz se usa `db`, el nombre del servicio dentro de docker-compose).

### 2. Base de datos

```
docker compose up -d db
```

### 3. Backend

```
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows (Git Bash)
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

API disponible en `http://localhost:8000/api/`. Documentación interactiva en `http://localhost:8000/api/docs/`.

### 4. Frontend

```
cd frontend
npm install
npm start
```

Aplicación disponible en `http://localhost:4200/`.

### 5. (Alternativa) Todo con Docker

```
cp .env.example .env
docker compose up -d --build
docker compose exec backend python manage.py seed_data
```

Backend en `http://localhost:8000/`, frontend en `http://localhost:4200/`. El `Dockerfile` del backend corre `collectstatic` y sirve con `gunicorn`; el del frontend es multi-stage (build con Node, se sirve con `nginx`, con fallback de rutas para la SPA). El build del frontend recibe la URL del backend por `ARG API_URL` (en `docker-compose.yml` apunta a `http://localhost:8000/api` para uso local; en producción el Dockerfile usa por defecto la URL de Render).

## Cómo ejecutar los tests

```
cd backend
python manage.py test        # 76 tests (auth + paises + riesgo + alertas + portafolios + dashboard)

cd frontend
npm test -- --watch=false --browsers=ChromeHeadless   # 16 tests unitarios (servicios, guards, interceptor, componente)
npm run e2e                                           # 3 tests E2E con Playwright (requiere backend y frontend corriendo)
```

## Endpoints

Documentación completa en Swagger: `http://localhost:8000/api/docs/` (local) o en la URL desplegada (ver [Despliegue](#despliegue)). También hay Redoc en `/api/redoc/`.

**Postman:** importar `backend/openapi-schema.yml` (Postman → Import → File) o directamente la URL `http://localhost:8000/api/schema/`; Postman genera la colección completa con ejemplos a partir del schema OpenAPI.

## Tareas programadas

```
python manage.py sync_indicadores     # World Bank, 10 paises x 6 indicadores
python manage.py sync_tipos_cambio    # ExchangeRate-API, tasa diaria
python manage.py calcular_riesgo      # IRPC de los 10 paises
```

Nota: ejecutar estos comandos sobre una base ya poblada por `seed_data` reemplaza los valores de ejemplo de Colombia (usados en el caso de prueba del IRPC) por datos reales de las APIs.

## Manejo de errores

- **Backend**: `apps/core/exceptions.py` define un manejador de excepciones de DRF que estandariza toda respuesta de error como `{"error": true, "status_code": ..., "mensaje": ...}`. Un middleware propio (`apps/core/middleware.py`) registra en el logger `apps.requests` el método, path, usuario y duración de cada request. Las acciones de login quedan en el modelo `LogActividad`.
- **Frontend**: `core/interceptors/error.interceptor.ts` muestra un snackbar ante errores de red, 403, 404 y 5xx, y redirige a `/login` con un mensaje claro cuando el token expira (401). Los errores 400 (validaciones de formulario) se dejan pasar para que cada componente los asocie al campo correspondiente.

## CI/CD

`.github/workflows/ci.yml` corre en cada push/PR a `develop` y `main`: tests del backend (contra Postgres real, servicio de GitHub Actions) y tests + build del frontend. El **deploy** no se dispara desde Actions: Render y Vercel despliegan automáticamente al detectar un push en la rama conectada (su integración nativa con GitHub), que es el patrón estándar para estas plataformas y evita depender de tokens/deploy-hooks adicionales en el pipeline.

## Despliegue

**Backend (Render)**
1. Crear cuenta en [render.com](https://render.com) con GitHub.
2. New → Blueprint → conectar el repo `datapulse-fullstack-jorge-cardona`, rama `develop`. Render lee `render.yaml` (en la raíz) y crea la base de datos Postgres y el servicio web automáticamente.
3. Verificar en el servicio `datapulse-backend` → Environment que las variables quedaron bien (las que dependen de la base de datos se linkean solas; `DJANGO_ALLOWED_HOSTS` y `CORS_ALLOWED_ORIGINS` traen un valor por defecto que hay que confirmar o ajustar una vez se conozca la URL real de cada servicio).
4. No hace falta correr el seed a mano: el plan free de Render no tiene Shell, así que el comando de arranque del contenedor ya hace `migrate && seed_data && gunicorn` en cada deploy. `seed_data` es idempotente (usa `get_or_create`/`update_or_create`), así que correrlo en cada arranque no duplica datos ni falla.

**Nota sobre el plan free:** el servicio se "duerme" tras un rato sin tráfico; la primera petición después de eso puede tardar **~1 minuto** en responder mientras el contenedor arranca de nuevo. Las siguientes son normales. Tenerlo en cuenta al grabar el video demostrativo (hacer un primer request de "calentamiento" antes de grabar).

**Frontend (Vercel)**
1. Crear cuenta en [vercel.com](https://vercel.com) con GitHub.
2. Add New → Project → importar el mismo repo, root directory `frontend`. Vercel lee `frontend/vercel.json` para el build command y el output directory.
3. Confirmar que el dominio asignado sea `datapulse-frontend.vercel.app` (o actualizar `CORS_ALLOWED_ORIGINS` en Render con el dominio real que Vercel asigne).

**Nota de transparencia:** no tengo acceso a las cuentas de Render/Vercel ni a sus CLIs desde este entorno, así que `render.yaml` y `vercel.json` están escritos según la documentación de cada plataforma pero no pude probarlos contra un despliegue real. Si Render o Vercel muestran un error de validación en el blueprint, revisar los nombres de campo contra su documentación vigente.

- URL del backend: _pendiente de desplegar_
- URL del frontend: _pendiente de desplegar_

## Credenciales de prueba

Ejecutar `python manage.py seed_data` (crea los 3 usuarios, los 10 paises con 3 años de indicadores, 30 dias de tipo de cambio, el IRPC calculado y 2 portafolios de ejemplo con posiciones):

| Email | Password | Rol |
|---|---|---|
| admin@datapulse.com | DataPulse2026! | ADMIN |
| analista@datapulse.com | DataPulse2026! | ANALISTA |
| viewer@datapulse.com | DataPulse2026! | VIEWER |

## Puntos ambiguos resueltos

El requerimiento (`HU_GLOBAL.md`, sección 13) señala 9 puntos no definidos explícitamente. Las decisiones tomadas:

1. **URL de REST Countries**: la del documento original tiene un error de escritura. La vigente es `https://restcountries.com/v3.1/`. El seed no depende de ninguna API externa: los datos de cada país van hardcodeados, y la URL de bandera se construye de forma estática contra `flagcdn.com`.
2. **Ecuador (USD) y Panamá (PAB)**: Ecuador no genera registros de `TipoCambio` (USD→USD no aporta información) y su Score Cambiario se fija en 100 por definición. Panamá se sincroniza normalmente contra ExchangeRate-API; si no estuviera disponible, se usa tasa fija 1.0 como fallback.
3. **`moneda_codigo` único**: se agregó `unique=True` en `Pais.moneda_codigo`. El FK de `TipoCambio.moneda_origen` usa `to_field='moneda_codigo'`.
4. **"Indicador en riesgo"**: se cuenta cada indicador entre `INFLACION`, `DESEMPLEO` y `DEUDA_PIB` que generó penalización en el Score Económico (se excluye `PIB_PERCAPITA`, que es un indicador de nivel/estructura, no de riesgo coyuntural). Esta regla reproduce el valor "3" del caso de prueba de Colombia.
5. **Año de crecimiento del PIB**: se usa el último año con dato disponible contra el año inmediatamente anterior con dato disponible (no año calendario - 1), por el rezago habitual de World Bank.
6. **Depreciación acumulada 30 días**: variación porcentual entre la primera y la última tasa del período (no la suma de variaciones diarias).
7. **Alertas globales**: un solo registro compartido (`usuario` null); al marcar `leida`, se marca para todos los que la ven.
8. **`Usuario.activo` vs `is_active`**: se reutiliza `is_active` de `AbstractUser`; no se duplica el campo. El serializer expone `activo` como alias de `is_active`.
9. **Concurrencia en portafolios**: optimistic locking simple. El cliente envía `fecha_modificacion` tal como la recibió; si no coincide con la del servidor al guardar, se responde `409 Conflict` con un mensaje claro.

## Inconsistencias y deuda técnica

Hallazgos del propio desarrollo (no señalados como ambiguos por el documento original), la decisión tomada y la forma óptima de resolverlos: ver [`documentacion/INCONSISTENCIAS.md`](documentacion/INCONSISTENCIAS.md).
