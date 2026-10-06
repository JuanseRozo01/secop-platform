"""Construcción de consultas SoQL (Socrata) para el dataset de procesos."""

from datetime import date, datetime, timedelta

from app.modules.secop import constants as c
from app.modules.secop.schemas import ProcesoFiltros


def soql_quote(value: str) -> str:
    """Literal de texto SoQL (comillas simples duplicadas)."""
    return "'" + value.replace("'", "''") + "'"


def _contains(column: str, value: str) -> str:
    # '%' es comodín en SoQL: se elimina de la entrada del usuario.
    clean = value.replace("%", " ").strip().upper()
    return f"upper({column}) like {soql_quote('%' + clean + '%')}"


def _day_start(d: date) -> str:
    return datetime(d.year, d.month, d.day).strftime("%Y-%m-%dT00:00:00")


def build_where(f: ProcesoFiltros, today: date) -> str | None:
    clauses: list[str] = []

    if f.solo_vigentes:
        clauses += [
            f"estado_de_apertura_del_proceso = {soql_quote(c.ESTADO_ABIERTO)}",
            f"{c.COL_CIERRE} >= {soql_quote(_day_start(today))}",
            "upper(modalidad_de_contratacion) != "
            + soql_quote(c.MODALIDAD_DIRECTA.upper()),
        ]

    if f.cierra_en_dias is not None:
        limite = today + timedelta(days=f.cierra_en_dias)
        clauses.append(
            f"{c.COL_CIERRE} <= {soql_quote(limite.strftime('%Y-%m-%dT23:59:59'))}"
        )
        if not f.solo_vigentes:
            clauses.append(f"{c.COL_CIERRE} >= {soql_quote(_day_start(today))}")

    if f.departamento:
        clauses.append(_contains("departamento_entidad", f.departamento))
    if f.ciudad:
        clauses.append(_contains("ciudad_entidad", f.ciudad))
    if f.entidad:
        clauses.append(_contains("entidad", f.entidad))
    if f.nit_entidad:
        clauses.append(f"nit_entidad = {soql_quote(f.nit_entidad)}")
    if f.modalidad:
        clauses.append(_contains("modalidad_de_contratacion", f.modalidad))
    if f.tipo_contrato:
        clauses.append(_contains("tipo_de_contrato", f.tipo_contrato))

    if f.unspsc:
        # Principal: "V1.80111500"; adicionales: "V172101500, V172103300".
        clauses.append(
            f"(codigo_principal_de_categoria like {soql_quote('V1.' + f.unspsc + '%')}"
            f" OR categorias_adicionales like {soql_quote('%V1' + f.unspsc + '%')})"
        )

    if f.precio_min is not None:
        clauses.append(f"{c.COL_PRECIO} >= {f.precio_min:.0f}")
    if f.precio_max is not None:
        clauses.append(f"{c.COL_PRECIO} <= {f.precio_max:.0f}")
    if f.publicado_desde:
        clauses.append(
            f"{c.COL_PUBLICACION} >= {soql_quote(_day_start(f.publicado_desde))}"
        )

    return " AND ".join(clauses) if clauses else None


def build_list_params(f: ProcesoFiltros, today: date) -> dict[str, str]:
    params: dict[str, str] = {
        "$select": ",".join(c.LIST_COLUMNS),
        "$order": c.ORDENES[f.orden],
        "$limit": str(f.limit),
        "$offset": str(f.offset),
    }
    where = build_where(f, today)
    if where:
        params["$where"] = where
    if f.q:
        params["$q"] = f.q.strip()
    return params


def build_detail_params(id_proceso: str) -> dict[str, str]:
    return {
        "$select": ",".join(c.DETAIL_COLUMNS),
        "$where": f"{c.COL_ID} = {soql_quote(id_proceso)}",
        # Si hay filas repetidas, la más recientemente publicada primero.
        "$order": f"{c.COL_ULTIMA_PUBLICACION} DESC",
        "$limit": "1",
    }
