# HU Global – DataPulse Latam

Prueba técnica: Desarrollador Fullstack (Angular + Django) – Mission S.A.S.
Repositorio: `datapulse-fullstack-jorge-cardona`
Inicio: 08-Oct-2026 08:00 | Entrega: 14-Oct-2026 18:00

---

## 1. Contexto del negocio

DataPulse Latam es una consultora financiera que asesora fondos de inversión sobre mercados latinoamericanos. Hoy sus analistas trabajan de forma manual:

- Recopilan indicadores económicos (PIB, inflación, desempleo) de varias fuentes.
- Arman portafolios simulados en hojas de cálculo.
- Calculan índices de riesgo país combinando variables económicas, cambiarias y sociales.
- Generan reportes en Word/PDF copiando datos.
- Monitorean tipos de cambio para decisiones de cobertura.

Se requiere una plataforma web que centralice estas operaciones, permita a varios analistas trabajar al mismo tiempo y ofrezca visualizaciones interactivas.

## 2. Stack obligatorio y restricciones

| Capa | Tecnología |
|---|---|
| Backend | Django 4+ y Django REST Framework |
| Frontend | Angular 12+ (strict mode) con Angular Material |
| Base de datos | PostgreSQL (SQLite aceptado solo para desarrollo) |
| Autenticación | JWT |
| Gráficos | ngx-charts, Chart.js o Plotly |
| Tareas | Celery o Django management commands |

Restricciones:

- No usar RPA comerciales ni templates de admin completos (AdminLTE, etc.).
- No copiar código completo de repositorios existentes.
- Se permiten librerías de npm/pip.
- Tailwind u otra librería CSS es opcional, pero Angular Material debe ser la base de UI.
- El código debe ejecutarse en local siguiendo el README.
- Responsive para desktop (1920px) y tablet (768px). Móvil no es requerido.

## 3. Países a monitorear

| Código | País | Moneda | Región | Latitud | Longitud |
|---|---|---|---|---|---|
| CO | Colombia | COP | ANDINA | 4.5709 | -74.2973 |
| BR | Brasil | BRL | CONO_SUR | -14.2350 | -51.9253 |
| MX | México | MXN | CENTROAMERICA | 23.6345 | -102.5528 |
| AR | Argentina | ARS | CONO_SUR | -38.4161 | -63.6167 |
| CL | Chile | CLP | CONO_SUR | -35.6751 | -71.5430 |
| PE | Perú | PEN | ANDINA | -9.1900 | -75.0152 |
| EC | Ecuador | USD | ANDINA | -1.8312 | -78.1834 |
| UY | Uruguay | UYU | CONO_SUR | -32.5228 | -55.7658 |
| PY | Paraguay | PYG | CONO_SUR | -23.4425 | -58.4438 |
| PA | Panamá | PAB | CENTROAMERICA | 8.5380 | -80.7821 |

---

## 4. Modelo de datos

Implementar con migraciones de Django. Agregar índices en campos de búsqueda y filtro frecuente.

### Usuario (extiende AbstractUser)
- `email` (único, usado como login)
- `nombre_completo`
- `rol` (ADMIN | ANALISTA | VIEWER)
- `fecha_creacion`
- `activo`

### Pais
- `codigo_iso` (PK, ej: "CO")
- `nombre`
- `moneda_codigo` (ej: "COP")
- `moneda_nombre`
- `region` (ANDINA | CONO_SUR | CENTROAMERICA | CARIBE)
- `latitud`, `longitud`
- `poblacion`
- `activo`

### IndicadorEconomico
- `pais` (FK → Pais)
- `tipo` (PIB | INFLACION | DESEMPLEO | BALANZA_COMERCIAL | DEUDA_PIB | PIB_PERCAPITA)
- `valor`
- `unidad` (PORCENTAJE | USD | USD_MILES_MILLONES)
- `anio`
- `fuente` (WORLD_BANK | MANUAL)
- `fecha_actualizacion`

### TipoCambio
- `moneda_origen` (FK → Pais.moneda_codigo)
- `moneda_destino` (default "USD")
- `tasa`
- `fecha`
- `variacion_porcentual` (respecto al día anterior)
- `fuente`

### Portafolio
- `nombre`
- `descripcion`
- `usuario` (FK → Usuario, creador)
- `fecha_creacion`, `fecha_modificacion`
- `activo`
- `es_publico` (visible para otros usuarios)

### Posicion
- `portafolio` (FK → Portafolio)
- `pais` (FK → Pais)
- `tipo_activo` (RENTA_FIJA | RENTA_VARIABLE | COMMODITIES | MONEDA)
- `monto_inversion_usd`
- `fecha_entrada`
- `fecha_salida` (nullable)
- `notas`

### IndiceRiesgo (calculado por el sistema)
- `pais` (FK → Pais)
- `fecha_calculo`
- `score_economico` (0-100)
- `score_cambiario` (0-100)
- `score_estabilidad` (0-100)
- `indice_compuesto` (0-100)
- `nivel_riesgo` (BAJO | MODERADO | ALTO | CRITICO)
- `detalle_calculo` (JSONField con el desglose)

### Alerta
- `usuario` (FK → Usuario, nullable para alertas globales)
- `pais` (FK → Pais)
- `tipo_alerta` (RIESGO | TIPO_CAMBIO | INDICADOR)
- `severidad` (INFO | WARNING | CRITICAL)
- `titulo`, `mensaje`
- `leida`
- `fecha_creacion`

### LogActividad
- `usuario` (FK → Usuario)
- `accion` (CREAR | EDITAR | ELIMINAR | CONSULTAR | LOGIN | EXPORT)
- `entidad_afectada` (nombre del modelo)
- `entidad_id`
- `detalle` (JSONField)
- `ip_address`
- `fecha`

### Restricciones de integridad
1. Un usuario no puede tener dos portafolios con el mismo nombre.
2. No puede haber dos IndicadorEconomico para el mismo país + tipo + año.
3. Si una posición tiene `fecha_salida`, debe ser mayor que `fecha_entrada`.
4. `indice_compuesto` debe estar entre 0 y 100.
5. Un VIEWER no puede crear ni editar portafolios.

---

## 5. Historias de usuario

Roles: **ADMIN**, **ANALISTA**, **VIEWER**.

### Épica 1 – Autenticación

**HU-01 Registro**
Como visitante quiero registrarme para acceder a la plataforma.
- `POST /api/auth/register/`
- Formulario reactivo con validaciones.
- Error claro si el email ya existe.

**HU-02 Login**
Como usuario quiero iniciar sesión con mi email.
- `POST /api/auth/login/` retorna access y refresh token.
- `POST /api/auth/refresh/` renueva el token.
- Error claro con credenciales inválidas.
- Redirección al dashboard tras el login.
- Token persistido en localStorage.

**HU-03 Perfil**
Como usuario autenticado quiero ver y editar mi perfil.
- `GET /api/auth/me/` y `PUT /api/auth/me/`.

**HU-04 Sesión expirada**
Como usuario quiero que, si mi token expira, el sistema me lleve al login con un mensaje claro.
- Error 401 → redirección a login + mensaje.

### Épica 2 – Países e indicadores

**HU-05 Listado de países**
- `GET /api/paises/` con filtro por región, búsqueda por texto y ordenamiento.

**HU-06 Detalle de país**
Como analista quiero ver la información completa de un país.
- `GET /api/paises/{codigo_iso}/` con indicadores.
- `GET /api/paises/{codigo_iso}/indicadores/` con filtro por tipo y año.
- `GET /api/paises/{codigo_iso}/tipo-cambio/` con filtro por rango de fechas.
- Vista con: bandera, nombre, moneda, región, población.
- Indicadores económicos en tarjetas con valores actuales.
- Gráfico histórico de indicadores (5 años).
- Gráfico de línea del tipo de cambio (últimos 30 días).
- Índice de riesgo actual con desglose visual (3 scores + compuesto).
- Tabla con el histórico del IRPC.

**HU-07 Sincronización de indicadores**
Como ADMIN quiero disparar la sincronización desde APIs externas.
- `POST /api/paises/sync-indicadores/` (solo ADMIN).
- Ver Épica 7.

### Épica 3 – Portafolios y posiciones

**HU-08 Listado de portafolios**
- `GET /api/portafolios/` retorna los del usuario + los públicos.
- Búsqueda por texto, ordenamiento y paginación.
- En el frontend, badge que diferencie propios y públicos.

**HU-09 Crear / editar / eliminar portafolio**
Como ANALISTA o ADMIN quiero gestionar mis portafolios.
- `POST /api/portafolios/`, `PUT /api/portafolios/{id}/`.
- `DELETE /api/portafolios/{id}/` es soft delete (`activo = False`).
- Un VIEWER recibe 403 y no ve botones de crear/editar.
- Diálogo de confirmación antes de eliminar.
- Formulario:
  - Nombre: requerido, min 3, max 100, único por usuario (validación async contra la API).
  - Descripción: max 500, con contador de caracteres visible.
  - Es público: checkbox.

**HU-10 Detalle de portafolio**
- `GET /api/portafolios/{id}/` con posiciones y métricas.
- `GET /api/portafolios/{id}/resumen/` con distribución por país, tipo_activo y riesgo.
- Tabla editable de posiciones.
- Gráfico pie: distribución por país.
- Gráfico donut: distribución por tipo_activo.
- Cálculo en tiempo real: monto total invertido y riesgo promedio ponderado.

**HU-11 Gestión de posiciones**
- `POST /api/portafolios/{id}/posiciones/` agregar.
- `PUT /api/portafolios/{id}/posiciones/{id}/` editar.
- `DELETE /api/portafolios/{id}/posiciones/{id}/` cierra la posición (asigna `fecha_salida`).
- Formulario:
  - País: requerido, autocomplete.
  - Tipo activo: requerido, selector.
  - Monto USD: requerido, numérico, min 1.000, max 10.000.000, con separador de miles.
  - Fecha entrada: requerida, no puede ser futura.
  - Notas: opcional, max 200.
- Validaciones cruzadas (backend y frontend):
  - No se permite tipo MONEDA para un país cuya moneda es USD.
  - El monto total del portafolio no puede superar 50.000.000 USD.
  - Máximo 2 posiciones activas del mismo tipo_activo en el mismo país.

**HU-12 Exportar PDF**
- `GET /api/portafolios/{id}/export/pdf/`.
- Botón de exportar en el detalle.
- Registrar acción EXPORT en LogActividad.

### Épica 4 – Índice de Riesgo País Compuesto (IRPC)

**HU-13 Consulta de riesgo**
- `GET /api/riesgo/` ranking de países por IRPC.
- `GET /api/riesgo/{codigo_iso}/` detalle con histórico.
- `GET /api/riesgo/{codigo_iso}/historico/` con filtro por rango.

**HU-14 Recalcular riesgo**
- `POST /api/riesgo/calcular/` (solo ADMIN) recalcula los 10 países.

**Fórmula**

```
IRPC = (Score_Economico * 0.40) + (Score_Cambiario * 0.30) + (Score_Estabilidad * 0.30)
```

**Score Económico (0-100)** – parte de 100:

| Variable | Condición | Penalización |
|---|---|---|
| PIB per cápita | < 3000 / < 6000 / < 12000 | -30 / -15 / -5 |
| Inflación | > 50 / > 10 / > 5 | -40 / -25 / -10 |
| Desempleo | > 15 / > 10 / > 7 | -25 / -15 / -5 |
| Deuda/PIB | > 80 / > 50 | -20 / -10 |

**Score Cambiario (0-100)** – parte de 100:

| Variable | Condición | Penalización |
|---|---|---|
| Volatilidad (desv. estándar de variaciones diarias, 30 días) | > 3.0 / > 1.5 / > 0.5 | -40 / -25 / -10 |
| Depreciación acumulada 30 días | > 10 / > 5 / > 2 | -30 / -15 / -5 |

**Score Estabilidad (0-100)** – parte de 100:

| Variable | Condición | Penalización |
|---|---|---|
| Balanza comercial (% PIB) | < -10 / < -5 / < 0 | -25 / -15 / -5 |
| Crecimiento PIB (último año vs anterior) | < -2 / < 0 / < 1 | -30 / -20 / -10 |
| Indicadores en riesgo | cada uno | -5 |

Todos los scores usan `max(0, score)`.

**Clasificación**

| IRPC | Nivel | Color | Hex | Acción |
|---|---|---|---|---|
| 75-100 | BAJO | Verde | #22c55e | Favorable para inversión |
| 50-74 | MODERADO | Amarillo | #eab308 | Invertir con precaución |
| 25-49 | ALTO | Naranja | #f97316 | Reducir exposición |
| 0-24 | CRITICO | Rojo | #ef4444 | Evitar nueva inversión |

**Caso de prueba obligatorio (Colombia, datos hipotéticos)**

| Entrada | Valor | Penalización |
|---|---|---|
| PIB per cápita | 6.800 | -5 |
| Inflación | 9.2 | -25 |
| Desempleo | 11.3 | -15 |
| Deuda/PIB | 55 | -10 |
| Volatilidad | 0.8 | -10 |
| Depreciación 30d | 1.5 | 0 |
| Balanza comercial | -4.2 | -5 |
| Crecimiento PIB | 1.5 | 0 |
| Indicadores negativos | 3 | -15 |

```
Score Economico  = 45
Score Cambiario  = 90
Score Estabilidad = 80
IRPC = 18 + 27 + 24 = 69 → MODERADO (amarillo)
```

**Datos incompletos:** si un país no tiene todos los indicadores, el cálculo debe funcionar con los disponibles y registrar los faltantes en `detalle_calculo`.

### Épica 5 – Alertas

**HU-15 Generación automática**
El sistema genera alertas cuando:
1. CRITICAL: IRPC menor a 25 para cualquier país.
2. WARNING: IRPC cae más de 15 puntos respecto al cálculo anterior.
3. WARNING: variación del tipo de cambio > 3% en un día.
4. INFO: nuevos datos económicos disponibles tras sincronización.
5. CRITICAL: inflación mayor a 50% (hiperinflación).

**HU-16 Panel de alertas**
- `GET /api/alertas/` con filtros: leídas/no leídas, tipo.
- `PUT /api/alertas/{id}/leer/` marcar una.
- `PUT /api/alertas/leer-todas/` marcar todas.
- `GET /api/alertas/resumen/` conteo por tipo y severidad.
- Filtros en la vista: tipo, severidad, leídas/no leídas.
- Iconos y colores diferenciados por severidad.
- Badge en la navbar con el conteo de no leídas (polling cada 30 s).

### Épica 6 – Dashboard

**HU-17 Dashboard principal**
- `GET /api/dashboard/resumen/` KPIs globales.
- `GET /api/dashboard/mapa/` países con coordenadas, IRPC y color.
- `GET /api/dashboard/tendencias/` indicadores de los últimos 5 años.
- Vista:
  - Mapa de Latinoamérica con cada país coloreado según IRPC.
  - 4 tarjetas KPI: total países monitoreados, alertas activas, portafolios del usuario, promedio IRPC región.
  - Tabla ranking de los 10 países: País, IRPC, Nivel, Variación, Tendencia.
  - Gráfico de líneas: selector de indicador + comparación de 3 países seleccionables, últimos 5 años.

### Épica 7 – Integraciones externas y tareas automatizadas

**Fuentes externas**

A. World Bank API – `https://api.worldbank.org/v2/`
Ejemplo: `https://api.worldbank.org/v2/country/CO/indicator/NY.GDP.MKTP.CD?date=2019:2023&format=json`

| Indicador | Código | Tipo en BD |
|---|---|---|
| PIB (USD corrientes) | NY.GDP.MKTP.CD | PIB |
| Inflación (% anual) | FP.CPI.TOTL.ZG | INFLACION |
| Desempleo (% total) | SL.UEM.TOTL.ZS | DESEMPLEO |
| Balanza comercial (% PIB) | NE.RSB.GNFS.ZS | BALANZA_COMERCIAL |
| Deuda gobierno (% PIB) | GC.DOD.TOTL.GD.ZS | DEUDA_PIB |
| PIB per cápita (USD) | NY.GDP.PCAP.CD | PIB_PERCAPITA |

B. ExchangeRate-API – `https://api.exchangerate-api.com/v4/latest/USD`
Tasa actual USD vs monedas de los 10 países. La variación diaria se calcula guardando histórico.

C. REST Countries API – nombre oficial, moneda, población, coordenadas, URL de bandera.

**HU-18 Tarea 1 – Sincronización de indicadores**
- Bajo demanda (endpoint solo ADMIN) o programada.
- Consulta World Bank para los 10 países y 6 indicadores.
- Si falla un país, continúa con los demás y registra el error.
- Log de inicio, fin, países procesados y errores.
- Genera alerta INFO al terminar.

**HU-19 Tarea 2 – Recálculo de IRPC**
- Se ejecuta después de cada sincronización.
- Calcula el IRPC de los 10 países según la Épica 4.
- Compara con el cálculo anterior y genera alertas si aplica.
- Guarda el resultado con el detalle completo.

**HU-20 Tarea 3 – Tipos de cambio**
- Consulta ExchangeRate-API.
- Guarda la tasa diaria de cada moneda.
- Calcula la variación respecto al día anterior.
- Genera alerta si la variación es > 3%.

### Épica 8 – Manejo de errores y logs

**Backend**
- Logging con `logging` de Python (INFO operaciones normales, ERROR fallos).
- Registro en LogActividad de las acciones CRUD.
- Middleware propio que registre método, path, usuario y duración de cada request.
- Custom exception handler en DRF con formato de error consistente.

**Frontend**
- Interceptor de errores que muestre snackbar con mensaje descriptivo.
- Manejo de errores de red (sin conexión).
- Redirección a login con 401.
- Página 404 para rutas no encontradas.

---

## 6. Requisitos transversales de la API

- Paginación en todos los listados (`page_size` configurable, default 20).
- Filtros por query params donde se especifica.
- Ordenamiento (`ordering`) en listados.
- Búsqueda (`search`) en países y portafolios.
- Respuestas de error estandarizadas.
- Throttling: 100 req/min autenticados, 20 req/min anónimos.
- Permisos por rol (ADMIN, ANALISTA, VIEWER).
- Validaciones de negocio con mensajes claros en español.

## 7. Requisitos técnicos del frontend

Estructura requerida:

```
src/app/
├── core/
│   ├── auth/
│   │   ├── services/auth.service.ts
│   │   ├── guards/auth.guard.ts
│   │   ├── guards/role.guard.ts
│   │   └── interceptors/jwt.interceptor.ts
│   ├── services/
│   │   ├── api.service.ts
│   │   ├── pais.service.ts
│   │   ├── portafolio.service.ts
│   │   ├── riesgo.service.ts
│   │   └── alerta.service.ts
│   └── interceptors/
│       ├── error.interceptor.ts
│       └── loading.interceptor.ts
├── modules/
│   ├── auth/          (login/, register/)
│   ├── dashboard/     (mapa-riesgo/, kpi-cards/, tabla-ranking/, grafico-tendencias/)
│   ├── paises/        (lista-paises/, detalle-pais/)
│   ├── portafolios/   (lista/, crear/, detalle/, posicion-form/, distribucion-chart/)
│   └── alertas/       (panel-alertas/, alerta-badge/)
└── shared/            (loading-spinner/, confirm-dialog/, pipes/, directives/)
```

- Angular strict mode.
- ReactiveFormsModule en todos los formularios.
- Lazy loading de dashboard, paises, portafolios y alertas.
- Guards: AuthGuard y RoleGuard.
- Interceptors: JWT, errores y loading.
- Servicio de estado con BehaviorSubject/Observable (o NgRx) en al menos un feature.
- UX: estados de carga, estados vacíos y mensajes de error.
- Los formularios inválidos muestran errores específicos sin enviar request al backend.

## 8. Despliegue y datos iniciales

**Despliegue**
- URL pública del backend (API accesible, con /api/ o Swagger).
- URL pública del frontend.
- CORS configurado entre ambos.
- Variables de entorno; ningún secreto en el código.
- HTTPS.

Opciones gratuitas sugeridas: Render, Railway, PythonAnywhere, Fly.io (backend); Vercel, Netlify, GitHub Pages, Firebase (frontend); PostgreSQL en Railway/Render; Redis en Railway/Upstash si se usa Celery.

**Seed (`python manage.py seed_data`)**
- 10 países con datos completos.
- Mínimo 3 años de indicadores por país.
- 30 días de histórico de tipo de cambio.
- Usuarios:
  - admin@datapulse.com / DataPulse2026! (ADMIN)
  - analista@datapulse.com / DataPulse2026! (ANALISTA)
  - viewer@datapulse.com / DataPulse2026! (VIEWER)
- 2 portafolios de ejemplo con posiciones.
- IRPC calculado para todos los países.

El seed debe funcionar sin depender de las APIs externas.

## 9. Escenarios de prueba obligatorios

1. **API externa caída:** la sincronización continúa con lo que obtenga y registra los errores.
2. **Token expirado:** el frontend redirige al login con mensaje.
3. **Permisos insuficientes:** un VIEWER que intenta crear un portafolio recibe 403 y no ve los botones.
4. **Datos incompletos:** el IRPC se calcula con lo disponible y marca los faltantes.
5. **Concurrencia:** si dos usuarios editan el mismo portafolio público al tiempo, se informa con un mensaje apropiado.
6. **Validaciones de formulario:** datos inválidos muestran errores específicos sin llamar al backend.

## 10. Entregables

**Repositorio GitHub público**
- `/backend` y `/frontend`.
- `docker-compose.yml` (opcional, suma puntos).
- `.env.example` con todas las variables.
- `.gitignore` adecuado.
- Commits incrementales; ramas `main` y `develop`.

**README.md**
- Arquitectura con diagrama.
- Diagrama entidad-relación.
- Decisiones técnicas y alternativas consideradas.
- Instalación y ejecución local paso a paso.
- Cómo ejecutar tests.
- Endpoints documentados (puede ser enlace a Swagger/Redoc).
- Manejo de errores y cómo se registran.
- URLs de despliegue.
- Credenciales de prueba.

**Video demostrativo (5-8 min)** – lo graba el candidato.

**Email de entrega** – lo envía el candidato.

## 11. Puntos adicionales (opcionales)

| Extra | Puntos | Contenido |
|---|---|---|
| Testing | +10 | Unit tests Django (models, serializers, IRPC), unit tests Angular, 1 test E2E |
| Docker | +8 | docker-compose funcional, Dockerfile multi-stage para Angular, documentación |
| API interactiva | +5 | Swagger con drf-spectacular o drf-yasg, colección Postman |
| Tiempo real | +7 | WebSockets (Django Channels) para alertas, dashboard sin refresh |
| Exportación avanzada | +5 | PDF con gráficos, exportar a Excel |
| CI/CD | +5 | GitHub Actions con tests y deploy automático |

## 12. Criterios de evaluación

| Área | Peso |
|---|---|
| Arquitectura y diseño de BD | 20% |
| Backend API | 25% |
| Frontend Angular | 25% |
| Integración y despliegue | 15% |
| Calidad general | 15% |

---

## 13. Puntos ambiguos a definir antes de implementar

Estos puntos no están claros en el requerimiento original. La decisión que se tome debe quedar documentada en el README.

1. **URL de REST Countries:** el documento indica `https://api.restcountries.com/contries/v5/` (con error de escritura). Verificar la URL vigente antes de implementar.
2. **Ecuador (USD) y Panamá (PAB):** Ecuador usa USD, por lo que USD→USD tiene tasa fija 1 y variación 0. El PAB está atado al USD. Definir cómo se maneja el tipo de cambio y el score cambiario de estos países.
3. **TipoCambio.moneda_origen como FK a Pais.moneda_codigo:** requiere que `moneda_codigo` sea único. Validar que el diseño lo soporte.
4. **`contar_indicadores_en_riesgo`:** el documento no define qué es un "indicador en riesgo". Proponer una regla (por ejemplo, cada indicador que generó penalización) y documentarla.
5. **Año para el crecimiento del PIB:** World Bank suele tener rezago de 1-2 años. Usar el último año disponible y el anterior.
6. **Depreciación acumulada:** definir si es la suma de variaciones diarias o la variación entre la primera y la última tasa de los 30 días.
7. **Alertas globales (usuario null) y estado `leida`:** si es un solo registro compartido, al marcarla un usuario se marca para todos. Definir el enfoque.
8. **Campo `activo` del Usuario vs `is_active` de AbstractUser:** definir si se reutiliza o se mapea.
9. **Concurrencia en portafolios públicos:** definir mecanismo (por ejemplo, comparar `fecha_modificacion` enviada por el cliente y responder 409 si cambió).
