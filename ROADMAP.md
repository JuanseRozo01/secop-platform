# ROADMAP — Plataforma de contratación estatal (SECOP + IA + asesoría)

> **Este archivo es la fuente de verdad del avance.** Se actualiza al cerrar cada paso:
> se marcan las casillas, se agrega una entrada al [Changelog](#changelog) y se mueven los
> supuestos a "verificados" cuando se comprueban. Si algo cambia de rumbo, se registra en
> [Decisiones](#decisiones-de-arquitectura).

**Visión.** Acompañar a una empresa desde encontrar una oportunidad en SECOP hasta gestionar
su contrato con el Estado: datos abiertos + IA que explica requisitos, fechas, riesgos y
compatibilidad + abogados y especialistas para asesoría.

**Leyenda:** ✅ hecho · 🚧 en curso · ⬜ pendiente · ⚠️ hecho pero con supuestos por verificar

**Última actualización:** 2026-10-05 · **Paso actual:** Fase 1 (SECOP) · **Siguiente:** Fase 2

---

## Resumen de fases

| # | Fase | Estado |
|---|------|--------|
| 0 | Fundaciones del backend | ✅ |
| 1 | Conexión y búsqueda en SECOP (datos abiertos) | ⚠️ |
| 2 | Persistencia e ingesta incremental | ⬜ |
| 3 | Usuarios y perfil de empresa | ⬜ |
| 4 | Matching oportunidad ↔ empresa | ⬜ |
| 5 | IA: explicación de requisitos, riesgos y compatibilidad | ⬜ |
| 6 | Alertas y seguimiento de oportunidades | ⬜ |
| 7 | Documentos del proceso (pliegos, anexos) | ⬜ |
| 8 | Marketplace de abogados y especialistas | ⬜ |
| 9 | Seguimiento de contratos (ejecución) | ⬜ |
| 10 | Frontend, producción y cumplimiento | ⬜ |

---

## Fase 0 — Fundaciones del backend ✅

- [x] FastAPI modular (`modules/<dominio>`), versionado `/api/v1`, `lifespan`
- [x] Configuración con `pydantic-settings`; `SECRET_KEY` obligatoria en producción
- [x] JWT con PyJWT (`iat`, `exp`, `jti`, `type`), errores distinguibles (expirado / inválido)
- [x] Dependencia `get_current_subject` y ruta protegida `/auth/me`
- [x] Manejo uniforme de errores (`AppException`, validación 422, 500 con `error_id`)
- [x] CORS configurable, `/docs` apagado en producción
- [x] Tests + ruff, `requirements*.txt`, `.env.example`, Makefile, README

## Fase 1 — Conexión y búsqueda en SECOP ⚠️

Dataset: **SECOP II – Procesos de Contratación** (`p6dx-8zbt`, datos.gov.co / API Socrata).

- [x] Cliente HTTP async con reintentos (429/5xx/timeouts), `Retry-After`, token de app opcional
- [x] Constructor SoQL seguro (escape de comillas, comodines saneados, orden estable)
- [x] Normalización: fechas, montos, URL (texto u objeto), UNSPSC (`V1.80111500` / `V172101500`)
- [x] Definición de **oportunidad vigente**: abierto + fecha límite ≥ hoy + no contratación directa
- [x] Alertas heurísticas por proceso (cierre inminente, valor no definido, invitación dirigida, régimen especial, cancelado)
- [x] Deduplicación de filas repetidas y caché TTL en memoria
- [x] Endpoints: `GET /secop/procesos` (filtros), `/secop/procesos/{id}`, `/secop/catalogos`
- [x] Acceso protegido por token (obligatorio por defecto en producción)
- [x] 96 tests (cliente, query, mapper, servicio, router) + prueba E2E con servidor Socrata simulado
- [ ] ⚠️ Ejecutar los **tests live** contra datos.gov.co real y cerrar los supuestos de abajo
- [ ] Contratos adjudicados (dataset de contratos electrónicos SECOP II) — *requiere verificar ID/columnas*
- [ ] SECOP I (procesos históricos) — *requiere verificar ID/columnas*
- [ ] Catálogo de entidades y búsqueda por proveedor/competidor

**Cómo cerrar el ⚠️:** `RUN_LIVE_TESTS=1 pytest -m live -s` (ver README). Cada prueba live
valida uno de los supuestos de la tabla siguiente.

## Fase 2 — Persistencia e ingesta incremental ⬜

- [ ] PostgreSQL + SQLAlchemy 2.0 (async) + Alembic; Docker Compose para desarrollo
- [ ] Job de ingesta incremental (por `fecha_de_ultima_publicaci`), idempotente, con métricas
- [ ] Tabla de procesos normalizada + historial de cambios de fase
- [ ] Índices: UNSPSC, departamento, fecha de cierre, texto completo (`tsvector`/`pg_trgm`)
- [ ] Migrar `/secop/procesos` de consulta en vivo a lectura local (la API viva queda como fallback)
- [ ] Reemplazar caché en memoria por Redis si hay más de una instancia

> **Por qué:** consultar datos.gov.co en cada petición limita la velocidad, expone al
> throttling y no permite enriquecer ni combinar datos. Es el requisito de las fases 4–6.

## Fase 3 — Usuarios y perfil de empresa ⬜

- [ ] Registro/login, hash de contraseñas (argon2), refresh tokens, roles (empresa / abogado / admin)
- [ ] Perfil de empresa: NIT, UNSPSC de interés, regiones, rango de cuantías, capacidad financiera, experiencia, certificaciones
- [ ] Verificación de empresa (RUP / cámara de comercio) — *definir alcance*
- [ ] Rate limiting por usuario y por IP

## Fase 4 — Matching oportunidad ↔ empresa ⬜

- [ ] Etapa 1: filtros duros (UNSPSC, ubicación, cuantía vs capacidad, modalidad, fechas)
- [ ] Etapa 2: scoring explicable (pesos configurables, razones por criterio)
- [ ] Señales de competencia (histórico de adjudicaciones por entidad / UNSPSC)
- [ ] Métricas de calidad (precisión de recomendaciones con feedback del usuario)

## Fase 5 — IA ⬜

- [ ] Proveedor de IA detrás de una interfaz (`AI_PROVIDER`), con límites de costo
- [ ] Extracción estructurada de requisitos habilitantes, fechas y garantías desde el pliego
- [ ] Resumen de riesgos y compatibilidad **con cita de fuente** (URL/ID del proceso y sección)
- [ ] Evaluaciones automáticas (casos dorados) para detectar alucinaciones antes de cada release
- [ ] Mensajes claros: la salida de la IA es informativa, no asesoría legal

## Fase 6 — Alertas y seguimiento ⬜

- [ ] Búsquedas guardadas + alertas por correo/WhatsApp/push
- [ ] Calendario de hitos (observaciones, cierre, adjudicación)
- [ ] Tablero de oportunidades (guardada / preparando / presentada / adjudicada / perdida)

## Fase 7 — Documentos ⬜

- [ ] Descarga y almacenamiento de pliegos/anexos (almacenamiento de objetos)
- [ ] Parsing (PDF/Word) y OCR; indexación para IA
- [ ] Listas de verificación de oferta generadas por proceso

## Fase 8 — Marketplace de abogados y especialistas ⬜

- [ ] Perfiles verificados (tarjeta profesional), especialidades, tarifas, disponibilidad
- [ ] Solicitud de asesoría, mensajería, compartir proceso/documentos con consentimiento
- [ ] Pagos y facturación; términos de servicio y de intermediación
- [ ] Reseñas y resolución de disputas

## Fase 9 — Seguimiento de contratos ⬜

- [ ] Vincular proceso adjudicado ↔ contrato ↔ ejecución
- [ ] Hitos, pólizas/garantías, modificaciones, prórrogas, liquidación
- [ ] Alertas de vencimientos contractuales

## Fase 10 — Frontend, producción y cumplimiento ⬜

- [ ] Frontend web (búsqueda, detalle de proceso, tablero, chat con especialistas)
- [ ] CI/CD (lint + tests + build), Docker, secretos gestionados, observabilidad (logs, métricas, trazas)
- [ ] Cumplimiento: **Ley 1581 de 2012** (habeas data), política de privacidad, autorizaciones, retención
- [ ] Revisión legal de términos, responsabilidad de la IA y modelo de intermediación con abogados
- [ ] Pruebas de carga y plan de respaldo/recuperación

---

## Supuestos por verificar (Fase 1)

Verificados **leyendo el encabezado y filas publicadas** del dataset, pero **no ejecutados
contra la API real** (el entorno de desarrollo asistido no tiene acceso a datos.gov.co).

| # | Supuesto | Cómo se verifica | Estado |
|---|----------|------------------|--------|
| 1 | `precio_base` es numérico en Socrata (filtros `>=`/`<=` válidos) | `test_price_filter_is_numeric` (live) | ⬜ |
| 2 | `fecha_de_recepcion_de` es el límite para presentar ofertas | Comparar 5–10 procesos contra su página en SECOP II | ⬜ |
| 3 | `upper()` y `like` funcionan con tildes (`CONTRATACIÓN DIRECTA`, `BOGOTÁ`) | `test_vigentes_search_returns_valid_opportunities` (live) | ⬜ |
| 4 | `$q` combinado con `$where` y `$order` responde en tiempos razonables | `test_unspsc_and_keyword_filters` (live) | ⬜ |
| 5 | `like '%V1xxxx%'` sobre `categorias_adicionales` no es prohibitivo en 1,8 M de filas | Medir latencia; si es alta → resolver en Fase 2 | ⬜ |
| 6 | "Abierto" + fecha futura ⇒ proceso al que aún se puede ofertar | Muestreo manual; ajustar `solo_vigentes` | ⬜ |
| 7 | Los nombres de columna `$select` existen todos (36 + 8 de detalle) | Cualquier test live (la API responde 400 si falta una) | ⬜ |

## Hechos verificados sobre el SECOP (referencia)

- Dataset `p6dx-8zbt` = *SECOP II – Procesos de Contratación*, ~1,8 M filas, 58 columnas,
  actualizado a diario por Colombia Compra Eficiente.
- Los nombres de campo de la API están **truncados** por Socrata
  (`fecha_de_publicacion_del`, `descripci_n_del_procedimiento`, `fecha_de_ultima_publicaci`…).
- Hay **filas repetidas** del mismo `id_del_proceso`; el servicio deduplica.
- La mayor parte de los registros es **contratación directa** (no es oportunidad competitiva)
  y hay procesos con estado "Abierto" desde años atrás: por eso se exige fecha límite futura.
- UNSPSC: principal `V1.80111500` (con punto); adicionales `V172101500, V172103300` (sin punto).
- Las columnas URL pueden llegar como texto o como objeto `{"url": ...}`.
- Colombia no tiene horario de verano: se usa UTC-5 fijo (sin depender de `tzdata`).

## Decisiones de arquitectura

| Fecha | Decisión | Motivo |
|-------|----------|--------|
| 2026-10-05 | PyJWT en lugar de `python-jose` | Biblioteca mantenida; menos CVEs |
| 2026-10-05 | `SECRET_KEY` obligatoria en producción | Evitar tokens forjables con clave por defecto |
| 2026-10-05 | Consulta en vivo a Socrata **como paso intermedio**, con caché TTL | Entregar valor ya; la ingesta llega en Fase 2 |
| 2026-10-05 | "Oportunidad vigente" = abierto + cierre ≥ hoy + no directa | Filtrar el ruido del dataset |
| 2026-10-05 | Alertas **heurísticas y deterministas** antes que IA | Baratas, explicables y comprobables |
| 2026-10-05 | Endpoints SECOP protegidos por token por defecto en producción | Evitar usar la API como proxy público de datos.gov.co |
| 2026-10-05 | Búsqueda por texto vía `$q` de Socrata | Indexada por la plataforma; evita `like` sobre descripciones largas |

## Riesgos abiertos

- **Throttling/disponibilidad de datos.gov.co** → mitigado con reintentos y caché; resuelto de raíz en Fase 2.
- **Cambios de esquema del dataset** → los tests live y el 400 explícito lo detectan temprano.
- **Responsabilidad por errores de la IA** (fechas, requisitos) → citar siempre la fuente (Fase 5) y revisar términos legales (Fase 10).
- **Datos personales** de empresas/abogados → Ley 1581 y minimización de datos desde Fase 3.

## Changelog

### 2026-10-05 — Fase 1: módulo SECOP (primera entrega)
- Nuevo módulo `app/modules/secop` (cliente, query, mapper, servicio, router, deps).
- Nuevo `app/core/cache.py` (caché TTL) y variables `SECOP_*` en configuración.
- 96 tests (92 unitarios/integración + 4 *live* opcionales). Ruff limpio.
- Prueba E2E con servidor Socrata simulado: URL, parámetros SoQL, token y errores 503 verificados.
- **Pendiente:** ejecutar los tests live en una máquina con acceso a datos.gov.co.

### 2026-10-05 — Fase 0: correcciones iniciales
- App volvió a arrancar (imports de módulos inexistentes), prefijo `/auth` corregido,
  `SECRET_KEY` endurecida, migración a PyJWT, `requirements.txt` completo, 28 tests.
