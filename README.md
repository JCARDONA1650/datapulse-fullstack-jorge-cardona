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

## Cómo ejecutar los tests

_Pendiente – se agrega al cerrar la fase de testing._

## Endpoints

Documentación completa en Swagger: `http://localhost:8000/api/docs/` (local) o en la URL desplegada (ver [Despliegue](#despliegue)).

## Manejo de errores

_Pendiente – se agrega al cerrar la fase de autenticación / manejo de errores transversal._

## Despliegue

_Pendiente._

## Credenciales de prueba

_Pendiente – se agrega al cerrar la fase de seed de datos._

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
