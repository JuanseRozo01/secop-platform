import pytest
from pydantic import ValidationError

from app.modules.secop.query import (
    build_detail_params,
    build_list_params,
    build_where,
    soql_quote,
)
from app.modules.secop.schemas import ProcesoFiltros
from tests.secop_fixtures import HOY


def test_soql_quote_escapes_single_quotes():
    assert soql_quote("O'Brien") == "'O''Brien'"
    assert soql_quote("x' OR 1=1 --") == "'x'' OR 1=1 --'"


def test_default_filters_define_vigente_opportunity():
    where = build_where(ProcesoFiltros(), HOY)
    assert "estado_de_apertura_del_proceso = 'Abierto'" in where
    assert "fecha_de_recepcion_de >= '2026-10-05T00:00:00'" in where
    assert "upper(modalidad_de_contratacion) != 'CONTRATACIÓN DIRECTA'" in where


def test_no_filters_when_not_only_vigentes():
    assert build_where(ProcesoFiltros(solo_vigentes=False), HOY) is None


def test_text_filters_are_sanitized():
    f = ProcesoFiltros(solo_vigentes=False, departamento="Antio%quia'; DROP")
    where = build_where(f, HOY)
    assert "%" not in where.replace("like '%", "").replace("%'", "")
    assert "ANTIO QUIA''; DROP" in where


def test_unspsc_covers_principal_and_additional_formats():
    where = build_where(ProcesoFiltros(solo_vigentes=False, unspsc="8011"), HOY)
    assert "codigo_principal_de_categoria like 'V1.8011%'" in where
    assert "categorias_adicionales like '%V18011%'" in where


@pytest.mark.parametrize("bad", ["8", "abc", "123456789", "80 11"])
def test_unspsc_validation(bad):
    with pytest.raises(ValidationError):
        ProcesoFiltros(unspsc=bad)


def test_price_range_validation():
    with pytest.raises(ValidationError):
        ProcesoFiltros(precio_min=10, precio_max=5)


def test_cierra_en_dias_adds_upper_bound():
    where = build_where(ProcesoFiltros(cierra_en_dias=7), HOY)
    assert "fecha_de_recepcion_de <= '2026-10-12T23:59:59'" in where


def test_params_include_order_with_tiebreaker_and_pagination():
    params = build_list_params(ProcesoFiltros(orden="cierre", limit=10, offset=30, q="aseo"), HOY)
    assert params["$order"] == "fecha_de_recepcion_de ASC, id_del_proceso ASC"
    assert params["$limit"] == "10" and params["$offset"] == "30"
    assert params["$q"] == "aseo"
    assert "id_del_proceso" in params["$select"]
    assert "descripci_n_del_procedimiento" not in params["$select"]


def test_detail_params_quote_id():
    params = build_detail_params("CO1.REQ.123")
    assert params["$where"] == "id_del_proceso = 'CO1.REQ.123'"
    assert "descripci_n_del_procedimiento" in params["$select"]
    assert params["$limit"] == "1"
