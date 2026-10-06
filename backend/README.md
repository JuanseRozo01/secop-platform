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

## Estructura

```
app/
  core/      config, seguridad (JWT), excepciones, logging, dependencias
  api/v1/    registro de routers de la versión 1
  modules/   un paquete por dominio (auth, secop, ...)
tests/
```

## Configuración

Ver `.env.example`. En `ENVIRONMENT=production` la app **no arranca** sin una
`SECRET_KEY` de al menos 32 caracteres, y se desactivan `/docs` y `/openapi.json`.

## Siguientes módulos

Registra cada router en `app/api/v1/router.py` solo cuando exista:
`users`, `companies`, `opportunities`, `matching`, `alerts`, `documents`,
`ai`, `analytics`, `contracts`, `lawyers`.
