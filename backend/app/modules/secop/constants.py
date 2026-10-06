"""Constantes del dataset SECOP II - Procesos de Contratación (p6dx-8zbt).

Los nombres de columna son los de la API Socrata de datos.gov.co: están
truncados por la plataforma (p. ej. ``fecha_de_recepcion_de``), por eso no
se pueden deducir del nombre legible. Verificados contra el encabezado
publicado del dataset (oct-2026).
"""

FUENTE = "SECOP II - Procesos de Contratación (datos.gov.co)"

# Modalidad que NO es una oportunidad competitiva (la entidad ya eligió).
MODALIDAD_DIRECTA = "Contratación directa"

ESTADO_ABIERTO = "Abierto"  # columna estado_de_apertura_del_proceso

COL_ID = "id_del_proceso"
COL_PUBLICACION = "fecha_de_publicacion_del"
COL_ULTIMA_PUBLICACION = "fecha_de_ultima_publicaci"
COL_CIERRE = "fecha_de_recepcion_de"  # recepción de respuestas (límite ofertas)
COL_PRECIO = "precio_base"

LIST_COLUMNS = [
    "id_del_proceso", "referencia_del_proceso", "entidad", "nit_entidad",
    "departamento_entidad", "ciudad_entidad", "ordenentidad",
    "nombre_del_procedimiento", "fase", "estado_del_procedimiento",
    "estado_resumen", "estado_de_apertura_del_proceso",
    "modalidad_de_contratacion", "tipo_de_contrato", "subtipo_de_contrato",
    "precio_base", "duracion", "unidad_de_duracion",
    "fecha_de_publicacion_del", "fecha_de_ultima_publicaci",
    "fecha_de_recepcion_de", "fecha_de_apertura_de_respuesta",
    "ciudad_de_la_unidad_de", "nombre_de_la_unidad_de",
    "codigo_principal_de_categoria", "categorias_adicionales",
    "proveedores_invitados", "visualizaciones_del",
    "proveedores_que_manifestaron", "respuestas_al_procedimiento",
    "adjudicado", "valor_total_adjudicacion", "nombre_del_proveedor",
    "nit_del_proveedor_adjudicado", "fecha_adjudicacion", "urlproceso",
]

DETAIL_EXTRA_COLUMNS = [
    "descripci_n_del_procedimiento", "justificaci_n_modalidad_de",
    "fecha_de_apertura_efectiva", "proveedores_con_invitacion",
    "respuestas_externas", "conteo_de_respuestas_a_ofertas",
    "proveedores_unicos_con", "numero_de_lotes",
]

DETAIL_COLUMNS = LIST_COLUMNS + DETAIL_EXTRA_COLUMNS

# Orden -> cláusula $order (con desempate estable para paginar).
ORDENES = {
    "publicacion": f"{COL_PUBLICACION} DESC, {COL_ID} DESC",
    "cierre": f"{COL_CIERRE} ASC, {COL_ID} ASC",
    "valor": f"{COL_PRECIO} DESC, {COL_ID} DESC",
}

# Valores observados en los datos (no es una lista oficial exhaustiva).
MODALIDADES_OBSERVADAS = [
    "Contratación directa",
    "Contratación Directa (con ofertas)",
    "Contratación régimen especial",
    "Contratación régimen especial (con ofertas)",
    "Licitación pública Obra Publica",
    "Selección abreviada subasta inversa",
    "Selección Abreviada de Menor Cuantía",
    "Mínima cuantía",
    "Solicitud de información a los Proveedores",
    "Enajenación de bienes con subasta",
]
TIPOS_CONTRATO_OBSERVADOS = [
    "Obra", "Suministros", "Prestación de servicios", "Compraventa",
    "Arrendamiento de muebles", "Venta muebles", "Otro",
]
