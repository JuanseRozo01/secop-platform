import pytest

from app.modules.secop.mapper import (
    normalize_unspsc,
    parse_dt,
    parse_number,
    parse_unspsc_list,
    parse_url,
    to_detalle,
    to_resumen,
)
from tests.secop_fixtures import HOY, fila_adjudicada, fila_directa, fila_vigente


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("V1.80111500", "80111500"),
        ("V172101500", "72101500"),
        ("V155101519", "55101519"),
        ("V124102000", "24102000"),
        ("UNSPECIFIED", None),
        ("", None),
        ("V1.123", None),
    ],
)
def test_normalize_unspsc(raw, expected):
    assert normalize_unspsc(raw) == expected


def test_parse_unspsc_list_dedupes_and_skips_garbage():
    assert parse_unspsc_list("V172101500, V172103300, V172101500, basura") == [
        "72101500",
        "72103300",
    ]
    assert parse_unspsc_list(None) == []


def test_parse_helpers():
    assert parse_dt("2026-10-08T00:00:00.000").day == 8
    assert parse_dt("no-fecha") is None and parse_dt(None) is None
    assert parse_number("68789970") == 68789970.0
    assert parse_number("1,500,000") == 1500000.0
    assert parse_number("abc") is None and parse_number("") is None
    assert parse_url({"url": " https://x.co "}) == "https://x.co"
    assert parse_url("https://y.co") == "https://y.co"
    assert parse_url(None) is None and parse_url({}) is None


def test_vigente_process_is_mapped_and_flagged():
    p = to_resumen(fila_vigente(), HOY)
    assert p.id_proceso == "CO1.REQ.11069913"
    assert p.vigente and p.abierto
    assert p.dias_para_cierre == 3
    assert p.precio_base == 68789970.0
    assert p.unspsc_principal == "72101500"
    assert p.unspsc_adicionales == ["72101500", "72103300"]
    assert p.url.endswith("CO1.NTC.10926809")
    assert p.alertas == []


def test_direct_contracting_is_open_but_never_vigente():
    p = to_resumen(fila_directa(), HOY)
    assert p.abierto is True
    assert p.vigente is False
    assert p.url and p.url.startswith("https://")


def test_expired_deadline_is_not_vigente():
    p = to_resumen(fila_vigente(fecha_de_recepcion_de="2026-10-04T00:00:00.000"), HOY)
    assert p.dias_para_cierre == -1
    assert p.vigente is False


def test_closing_today_is_still_vigente_with_critical_alert():
    p = to_resumen(fila_vigente(fecha_de_recepcion_de="2026-10-05T00:00:00.000"), HOY)
    assert p.vigente and p.dias_para_cierre == 0
    alerta = next(a for a in p.alertas if a.codigo == "CIERRE_INMINENTE")
    assert alerta.severidad == "critical" and "hoy" in alerta.mensaje


def test_adjudicated_process_fields_and_alerts():
    p = to_resumen(fila_adjudicada(), HOY)
    assert p.adjudicado and p.valor_adjudicado == 305644297.0
    assert p.proveedor_adjudicado == "CONSTRUOBRAS ISAVAL S.A.S"
    assert p.unspsc_principal is None
    assert p.unspsc_adicionales == ["55101519"]
    codigos = {a.codigo for a in p.alertas}
    assert "INVITACION_DIRIGIDA" in codigos
    assert p.vigente is False


def test_zero_price_and_special_regime_alerts():
    p = to_resumen(
        fila_vigente(precio_base="0", modalidad_de_contratacion="Contratación régimen especial"),
        HOY,
    )
    codigos = {a.codigo for a in p.alertas}
    assert {"VALOR_NO_DEFINIDO", "REGIMEN_ESPECIAL"} <= codigos


def test_detail_includes_extra_fields_and_missing_columns_are_none():
    d = to_detalle(fila_vigente(), HOY)
    assert d.descripcion.startswith("Obras de mejoramiento")
    assert d.justificacion_modalidad
    assert d.numero_lotes is None
    sparse = to_resumen({"id_del_proceso": "CO1.REQ.1"}, HOY)
    assert sparse.entidad is None and sparse.vigente is False and sparse.dias_para_cierre is None
