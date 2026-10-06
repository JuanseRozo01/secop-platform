# SECOP Intelligence API

Backend (FastAPI) de una plataforma que ayuda a empresas y contratistas a
encontrar y gestionar oportunidades de contratación con el Estado a partir de
datos del SECOP, IA y asesoría de especialistas.

## Puesta en marcha

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
make install                     # o: pip install -r requirements-dev.txt
cp .env.example .env             # y define SECRET_KEY
make dev                         # http://127.0.0.1:8000/docs
```

En Windows sin `make` puedes usar `scripts\run_dev.bat`, `scripts\run_tests.bat`
y `scripts\check.bat`.

## Módulo SECOP

Consulta los **procesos de contratación de SECOP II** (datos abiertos, dataset `p6dx-8zbt`).

| Endpoint | Descripción |
|----------|-------------|
| `GET /api/v1/secop/procesos` | Búsqueda con filtros y paginación |
| `GET /api/v1/secop/procesos/{id}` | Detalle de un proceso (p. ej. `CO1.REQ.11069913`) |
| `GET /api/v1/secop/catalogos` | Modalidades, tipos de contrato y órdenes disponibles |
| `GET /api/v1/secop/status` | Estado del módulo (público) |

Filtros de `/procesos`: `q`, `departamento`, `ciudad`, `entidad`, `nit_entidad`, `modalidad`,
`tipo_contrato`, `unspsc` (prefijo, 2–8 dígitos), `precio_min`, `precio_max`,
`publicado_desde`, `cierra_en_dias`, `solo_vigentes` (por defecto `true`), `orden`
(`publicacion` · `cierre` · `valor`), `limit` (máx. 100), `offset`.

`solo_vigentes=true` devuelve solo **oportunidades reales**: procesos abiertos, con fecha
límite de ofertas igual o posterior a hoy y que no son contratación directa.

Ejemplo:

```
GET /api/v1/secop/procesos?unspsc=8011&departamento=Cesar&cierra_en_dias=15&orden=cierre
```

En producción los endpoints de datos exigen `Authorization: Bearer <token>`
(`SECOP_REQUIRE_AUTH` lo controla). Define `SECOP_APP_TOKEN` para evitar el throttling de datos.gov.co.

### Pruebas contra datos.gov.co real

Los tests normales no usan la red. Para validar contra la API real (necesitas internet):

```bash
make test-live            # o: RUN_LIVE_TESTS=1 pytest -m live -s
```

## Estructura

```
app/
  core/      config, seguridad (JWT), excepciones, logging, dependencias
  api/v1/    registro de routers de la versión 1
  modules/   un paquete por dominio (auth, secop, ...)
    secop/   client · query · mapper · service · router · schemas
tests/
```

## Configuración

Ver `.env.example`. En `ENVIRONMENT=production` la app **no arranca** sin una
`SECRET_KEY` de al menos 32 caracteres, y se desactivan `/docs` y `/openapi.json`.

## Siguientes módulos

Registra cada router en `app/api/v1/router.py` solo cuando exista:
`users`, `companies`, `opportunities`, `matching`, `alerts`, `documents`,
`ai`, `analytics`, `contracts`, `lawyers`.


Ver el avance y los próximos pasos en [`../ROADMAP.md`](../ROADMAP.md).
