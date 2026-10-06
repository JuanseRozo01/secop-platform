"""Filas con la forma real de la API Socrata (valores como texto, columnas
nulas omitidas, URL como objeto o texto). Basadas en filas publicadas en
datos.gov.co/resource/p6dx-8zbt; las fechas se ajustan a un 'hoy' fijo."""

from datetime import date, datetime

HOY = date(2026, 10, 5)
AHORA = datetime(2026, 10, 5, 9, 0)


def fila_vigente(**over):
    """Selección abreviada abierta, cierra en 3 días."""
    row = {
        "id_del_proceso": "CO1.REQ.11069913",
        "referencia_del_proceso": "SAMC-04-2026",
        "entidad": "MUNICIPIO DE TIMBIO",
        "nit_entidad": "891500742",
        "departamento_entidad": "Cauca",
        "ciudad_entidad": "Timbío",
        "ordenentidad": "Territorial",
        "nombre_del_procedimiento": "REALIZAR LAS OBRAS DE MEJORAMIENTO DE LA PLANTA",
        "descripci_n_del_procedimiento": "Obras de mejoramiento de la planta de beneficio",
        "fase": "Presentación de oferta",
        "estado_del_procedimiento": "Abierto",
        "estado_resumen": "Presentación de oferta",
        "estado_de_apertura_del_proceso": "Abierto",
        "modalidad_de_contratacion": "Selección Abreviada de Menor Cuantía",
        "justificaci_n_modalidad_de": "Presupuesto menor al 10% de la Menor Cuantía",
        "tipo_de_contrato": "Obra",
        "subtipo_de_contrato": "No Definido",
        "precio_base": "68789970",
        "duracion": "0",
        "unidad_de_duracion": "día(s)",
        "fecha_de_publicacion_del": "2026-09-30T00:00:00.000",
        "fecha_de_ultima_publicaci": "2026-09-30T00:00:00.000",
        "fecha_de_recepcion_de": "2026-10-08T00:00:00.000",
        "fecha_de_apertura_de_respuesta": "2026-10-08T00:00:00.000",
        "codigo_principal_de_categoria": "V1.72101500",
        "categorias_adicionales": "V172101500, V172103300",
        "proveedores_invitados": "0",
        "visualizaciones_del": "31",
        "respuestas_al_procedimiento": "0",
        "adjudicado": "No",
        "urlproceso": {"url": "https://community.secop.gov.co/Public/Tendering/"
                       "OpportunityDetail/Index?noticeUID=CO1.NTC.10926809"},
    }
    row.update(over)
    return row


def fila_directa():
    """Contratación directa: 'Abierto' pero NO es una oportunidad."""
    return {
        "id_del_proceso": "CO1.REQ.9845111",
        "entidad": "INVIAS",
        "nit_entidad": "800215807",
        "departamento_entidad": "Distrito Capital de Bogotá",
        "estado_del_procedimiento": "Seleccionado",
        "estado_de_apertura_del_proceso": "Abierto",
        "modalidad_de_contratacion": "Contratación directa",
        "precio_base": "48620250",
        "fecha_de_publicacion_del": "2026-01-22T00:00:00.000",
        "codigo_principal_de_categoria": "V1.80111701",
        "adjudicado": "No",
        "urlproceso": "https://community.secop.gov.co/Public/Tendering/"
                      "OpportunityDetail/Index?noticeUID=CO1.NTC.9690232",
    }


def fila_adjudicada():
    return {
        "id_del_proceso": "CO1.REQ.9500237",
        "entidad": "ALCALDIA DE FLORIDABLANCA",
        "estado_del_procedimiento": "Seleccionado",
        "estado_de_apertura_del_proceso": "Cerrado",
        "modalidad_de_contratacion": "Selección Abreviada de Menor Cuantía",
        "precio_base": "305813941",
        "fecha_de_recepcion_de": "2025-12-31T00:00:00.000",
        "proveedores_invitados": "10",
        "adjudicado": "Si",
        "valor_total_adjudicacion": "305644297",
        "nombre_del_proveedor": "CONSTRUOBRAS ISAVAL S.A.S",
        "nit_del_proveedor_adjudicado": "No Definido",
        "fecha_adjudicacion": "2026-01-27T00:00:00.000",
        "codigo_principal_de_categoria": "UNSPECIFIED",
        "categorias_adicionales": "V155101519",
    }
