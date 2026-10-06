"""Normalización de filas crudas de Socrata al modelo de la plataforma."""

import re
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.modules.secop import constants as c
from app.modules.secop.schemas import Alerta, ProcesoDetalle, ProcesoResumen

# Colombia no tiene horario de verano: UTC-5 fijo (evita depender de tzdata).
COL_TZ = timezone(timedelta(hours=-5))


def now_colombia() -> datetime:
    return datetime.now(COL_TZ)


# ------------------------------------------------------------------ parseo
def parse_dt(value: Any) -> datetime | None:
    """Socrata entrega timestamps 'flotantes': 2026-09-22T00:00:00.000."""
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.strip())
    except ValueError:
        return None


def parse_number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", "").replace("$", "").strip())
    except ValueError:
        return None


def parse_int(value: Any) -> int | None:
    n = parse_number(value)
    return int(n) if n is not None else None


def parse_bool_si_no(value: Any) -> bool:
    return str(value or "").strip().lower() in {"si", "sí", "true", "1"}


def parse_url(value: Any) -> str | None:
    """Las columnas URL llegan como {"url": "..."}; en CSV como texto."""
    if isinstance(value, dict):
        value = value.get("url")
    return value.strip() if isinstance(value, str) and value.strip() else None


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalize_unspsc(token: str) -> str | None:
    """'V1.80111500' -> '80111500'; 'V172101500' -> '72101500'."""
    t = token.strip().upper()
    if not t.startswith("V"):
        return t if re.fullmatch(r"\d{8}", t) else None
    t = t[1:]
    if t.startswith("1."):
        t = t[2:]
    elif len(t) == 9 and t.startswith("1"):
        t = t[1:]
    return t if re.fullmatch(r"\d{8}", t) else None


def parse_unspsc_list(value: Any) -> list[str]:
    if not isinstance(value, str):
        return []
    codes = (normalize_unspsc(tok) for tok in value.split(","))
    return list(dict.fromkeys(code for code in codes if code))


# ------------------------------------------------------------------ alertas
def build_alertas(p: ProcesoResumen) -> list[Alerta]:
    alertas: list[Alerta] = []

    if p.vigente and p.dias_para_cierre is not None and p.dias_para_cierre <= 2:
        cuando = "hoy" if p.dias_para_cierre <= 0 else f"en {p.dias_para_cierre} día(s)"
        alertas.append(
            Alerta(
                codigo="CIERRE_INMINENTE",
                severidad="critical",
                mensaje=f"El plazo para presentar ofertas cierra {cuando}.",
            )
        )
    if not p.precio_base:
        alertas.append(
            Alerta(
                codigo="VALOR_NO_DEFINIDO",
                severidad="info",
                mensaje="El precio base es cero o no está definido "
                "(p. ej. convenios de valor cero o valor indeterminado).",
            )
        )
    if p.proveedores_invitados:
        alertas.append(
            Alerta(
                codigo="INVITACION_DIRIGIDA",
                severidad="warning",
                mensaje=f"La entidad invitó a {p.proveedores_invitados} proveedor(es) "
                "específico(s); verifica si el proceso admite otros oferentes.",
            )
        )
    if p.modalidad and "régimen especial" in p.modalidad.lower():
        alertas.append(
            Alerta(
                codigo="REGIMEN_ESPECIAL",
                severidad="info",
                mensaje="Régimen especial: la entidad se rige por reglas propias; "
                "revisa su manual de contratación.",
            )
        )
    if p.estado and p.estado.strip().lower() == "cancelado":
        alertas.append(
            Alerta(
                codigo="PROCESO_CANCELADO",
                severidad="warning",
                mensaje="El proceso aparece como cancelado.",
            )
        )
    return alertas


# ------------------------------------------------------------------ mapeo
def _resumen_kwargs(raw: dict[str, Any], today: date) -> dict[str, Any]:
    cierre = parse_dt(raw.get("fecha_de_recepcion_de"))
    abierto = (
        str(raw.get("estado_de_apertura_del_proceso", "")).strip().lower()
        == c.ESTADO_ABIERTO.lower()
    )
    modalidad = clean_text(raw.get("modalidad_de_contratacion"))
    es_directa = (modalidad or "").strip().lower() == c.MODALIDAD_DIRECTA.lower()
    dias = (cierre.date() - today).days if cierre else None

    return dict(
        id_proceso=str(raw["id_del_proceso"]),
        referencia=clean_text(raw.get("referencia_del_proceso")),
        entidad=clean_text(raw.get("entidad")),
        nit_entidad=clean_text(raw.get("nit_entidad")),
        departamento=clean_text(raw.get("departamento_entidad")),
        ciudad=clean_text(raw.get("ciudad_entidad")),
        orden_entidad=clean_text(raw.get("ordenentidad")),
        nombre=clean_text(raw.get("nombre_del_procedimiento")),
        fase=clean_text(raw.get("fase")),
        estado=clean_text(raw.get("estado_del_procedimiento")),
        estado_resumen=clean_text(raw.get("estado_resumen")),
        abierto=abierto,
        vigente=bool(abierto and cierre and dias is not None and dias >= 0 and not es_directa),
        modalidad=modalidad,
        tipo_contrato=clean_text(raw.get("tipo_de_contrato")),
        subtipo_contrato=clean_text(raw.get("subtipo_de_contrato")),
        precio_base=parse_number(raw.get("precio_base")),
        duracion=parse_int(raw.get("duracion")),
        unidad_duracion=clean_text(raw.get("unidad_de_duracion")),
        fecha_publicacion=parse_dt(raw.get("fecha_de_publicacion_del")),
        fecha_ultima_publicacion=parse_dt(raw.get("fecha_de_ultima_publicaci")),
        fecha_cierre_ofertas=cierre,
        fecha_apertura_ofertas=parse_dt(raw.get("fecha_de_apertura_de_respuesta")),
        dias_para_cierre=dias,
        unidad_contratacion=clean_text(raw.get("nombre_de_la_unidad_de")),
        ciudad_unidad=clean_text(raw.get("ciudad_de_la_unidad_de")),
        unspsc_principal=(
            normalize_unspsc(raw["codigo_principal_de_categoria"])
            if raw.get("codigo_principal_de_categoria")
            else None
        ),
        unspsc_adicionales=parse_unspsc_list(raw.get("categorias_adicionales")),
        proveedores_invitados=parse_int(raw.get("proveedores_invitados")),
        visualizaciones=parse_int(raw.get("visualizaciones_del")),
        manifestaciones_interes=parse_int(raw.get("proveedores_que_manifestaron")),
        respuestas=parse_int(raw.get("respuestas_al_procedimiento")),
        adjudicado=parse_bool_si_no(raw.get("adjudicado")),
        valor_adjudicado=parse_number(raw.get("valor_total_adjudicacion")),
        proveedor_adjudicado=clean_text(raw.get("nombre_del_proveedor")),
        nit_proveedor_adjudicado=clean_text(raw.get("nit_del_proveedor_adjudicado")),
        fecha_adjudicacion=parse_dt(raw.get("fecha_adjudicacion")),
        url=parse_url(raw.get("urlproceso")),
    )


def to_resumen(raw: dict[str, Any], today: date) -> ProcesoResumen:
    p = ProcesoResumen(**_resumen_kwargs(raw, today))
    p.alertas = build_alertas(p)
    return p


def to_detalle(raw: dict[str, Any], today: date) -> ProcesoDetalle:
    p = ProcesoDetalle(
        **_resumen_kwargs(raw, today),
        descripcion=clean_text(raw.get("descripci_n_del_procedimiento")),
        justificacion_modalidad=clean_text(raw.get("justificaci_n_modalidad_de")),
        fecha_apertura_efectiva=parse_dt(raw.get("fecha_de_apertura_efectiva")),
        proveedores_con_invitacion=parse_int(raw.get("proveedores_con_invitacion")),
        respuestas_externas=parse_int(raw.get("respuestas_externas")),
        respuestas_a_ofertas=parse_int(raw.get("conteo_de_respuestas_a_ofertas")),
        proveedores_unicos_con_respuestas=parse_int(raw.get("proveedores_unicos_con")),
        numero_lotes=parse_int(raw.get("numero_de_lotes")),
    )
    p.alertas = build_alertas(p)
    return p
