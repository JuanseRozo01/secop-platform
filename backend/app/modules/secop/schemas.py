import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Severidad = Literal["info", "warning", "critical"]
Orden = Literal["publicacion", "cierre", "valor"]


class Alerta(BaseModel):
    """Señal heurística derivada de los datos (no es asesoría legal)."""

    codigo: str
    severidad: Severidad
    mensaje: str


class ProcesoResumen(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id_proceso: str
    referencia: str | None = None
    entidad: str | None = None
    nit_entidad: str | None = None
    departamento: str | None = None
    ciudad: str | None = None
    orden_entidad: str | None = None
    nombre: str | None = None

    fase: str | None = None
    estado: str | None = None
    estado_resumen: str | None = None
    abierto: bool = False
    vigente: bool = False  # abierto + fecha límite futura + no contratación directa

    modalidad: str | None = None
    tipo_contrato: str | None = None
    subtipo_contrato: str | None = None
    precio_base: float | None = None
    duracion: int | None = None
    unidad_duracion: str | None = None

    fecha_publicacion: datetime | None = None
    fecha_ultima_publicacion: datetime | None = None
    fecha_cierre_ofertas: datetime | None = None
    fecha_apertura_ofertas: datetime | None = None
    dias_para_cierre: int | None = None

    unidad_contratacion: str | None = None
    ciudad_unidad: str | None = None

    unspsc_principal: str | None = None
    unspsc_adicionales: list[str] = Field(default_factory=list)

    proveedores_invitados: int | None = None
    visualizaciones: int | None = None
    manifestaciones_interes: int | None = None
    respuestas: int | None = None

    adjudicado: bool = False
    valor_adjudicado: float | None = None
    proveedor_adjudicado: str | None = None
    nit_proveedor_adjudicado: str | None = None
    fecha_adjudicacion: datetime | None = None

    url: str | None = None
    alertas: list[Alerta] = Field(default_factory=list)


class ProcesoDetalle(ProcesoResumen):
    descripcion: str | None = None
    justificacion_modalidad: str | None = None
    fecha_apertura_efectiva: datetime | None = None
    proveedores_con_invitacion: int | None = None
    respuestas_externas: int | None = None
    respuestas_a_ofertas: int | None = None
    proveedores_unicos_con_respuestas: int | None = None
    numero_lotes: int | None = None


class ProcesosPage(BaseModel):
    items: list[ProcesoResumen]
    limit: int
    offset: int
    count: int
    # True si la página vino llena (puede haber más). Es una estimación: la
    # deduplicación puede dejar páginas con menos de `limit` elementos.
    has_more: bool
    fuente: str
    consultado_en: datetime


class ProcesoFiltros(BaseModel):
    q: str | None = Field(default=None, min_length=2, max_length=100)
    departamento: str | None = Field(default=None, max_length=80)
    ciudad: str | None = Field(default=None, max_length=80)
    entidad: str | None = Field(default=None, max_length=120)
    nit_entidad: str | None = Field(default=None, pattern=r"^\d{5,15}$")
    modalidad: str | None = Field(default=None, max_length=120)
    tipo_contrato: str | None = Field(default=None, max_length=80)
    unspsc: str | None = Field(default=None, pattern=r"^\d{2,8}$")
    precio_min: float | None = Field(default=None, ge=0)
    precio_max: float | None = Field(default=None, ge=0)
    publicado_desde: date | None = None
    cierra_en_dias: int | None = Field(default=None, ge=0, le=365)
    solo_vigentes: bool = True
    orden: Orden = "publicacion"
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0, le=100_000)

    @model_validator(mode="after")
    def _check_ranges(self) -> "ProcesoFiltros":
        if (
            self.precio_min is not None
            and self.precio_max is not None
            and self.precio_min > self.precio_max
        ):
            raise ValueError("precio_min no puede ser mayor que precio_max")
        return self


ID_PROCESO_RE = re.compile(r"^[A-Za-z0-9._-]{3,64}$")
