from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import ValidationError

from app.core.config import settings
from app.core.exceptions import AppException
from app.modules.secop import constants as c
from app.modules.secop.deps import get_secop_service, secop_access
from app.modules.secop.schemas import (
    Orden,
    ProcesoDetalle,
    ProcesoFiltros,
    ProcesosPage,
)
from app.modules.secop.service import SecopService

router = APIRouter(prefix="/secop", tags=["secop"])
protected = APIRouter(dependencies=[Depends(secop_access)])


def get_filtros(
    q: Annotated[str | None, Query(description="Palabras clave (texto completo)")] = None,
    departamento: Annotated[str | None, Query(description="Contiene, sin tildes exactas")] = None,
    ciudad: str | None = None,
    entidad: Annotated[str | None, Query(description="Nombre de la entidad (contiene)")] = None,
    nit_entidad: str | None = None,
    modalidad: str | None = None,
    tipo_contrato: Annotated[str | None, Query(description="Obra, Suministros, ...")] = None,
    unspsc: Annotated[
        str | None,
        Query(description="Código UNSPSC por prefijo (2 a 8 dígitos), p. ej. 8011"),
    ] = None,
    precio_min: float | None = None,
    precio_max: float | None = None,
    publicado_desde: date | None = None,
    cierra_en_dias: Annotated[
        int | None, Query(description="Solo procesos que cierran en N días o menos")
    ] = None,
    solo_vigentes: Annotated[
        bool,
        Query(
            description="Abiertos, con fecha límite futura y sin contratación directa"
        ),
    ] = True,
    orden: Orden = "publicacion",
    limit: int = 20,
    offset: int = 0,
) -> ProcesoFiltros:
    try:
        return ProcesoFiltros(
            q=q, departamento=departamento, ciudad=ciudad, entidad=entidad,
            nit_entidad=nit_entidad, modalidad=modalidad, tipo_contrato=tipo_contrato,
            unspsc=unspsc, precio_min=precio_min, precio_max=precio_max,
            publicado_desde=publicado_desde, cierra_en_dias=cierra_en_dias,
            solo_vigentes=solo_vigentes, orden=orden, limit=limit, offset=offset,
        )
    except ValidationError as exc:
        detalle = "; ".join(
            f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors()
        )
        raise AppException(f"Filtros inválidos: {detalle}", 422) from None


@router.get("/status")
async def status() -> dict[str, str]:
    return {
        "module": "secop",
        "status": "ready",
        "dataset": settings.SECOP_PROCESOS_DATASET,
    }


@protected.get("/catalogos")
async def catalogos() -> dict[str, list[str]]:
    """Valores observados en los datos, útiles para poblar filtros en la UI."""
    return {
        "modalidades": c.MODALIDADES_OBSERVADAS,
        "tipos_contrato": c.TIPOS_CONTRATO_OBSERVADOS,
        "ordenes": list(c.ORDENES),
    }


@protected.get("/procesos", response_model=ProcesosPage)
async def buscar_procesos(
    filtros: Annotated[ProcesoFiltros, Depends(get_filtros)],
    service: Annotated[SecopService, Depends(get_secop_service)],
) -> ProcesosPage:
    return await service.buscar(filtros)


@protected.get("/procesos/{id_proceso}", response_model=ProcesoDetalle)
async def obtener_proceso(
    id_proceso: str,
    service: Annotated[SecopService, Depends(get_secop_service)],
) -> ProcesoDetalle:
    return await service.obtener(id_proceso)


router.include_router(protected)
