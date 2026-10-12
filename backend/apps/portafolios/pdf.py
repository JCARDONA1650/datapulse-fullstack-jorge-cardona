from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .services import calcular_resumen_portafolio


def generar_pdf_portafolio(portafolio):
    buffer = BytesIO()
    documento = SimpleDocTemplate(buffer, pagesize=letter)
    estilos = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph(f'Portafolio: {portafolio.nombre}', estilos['Title']))
    elementos.append(Paragraph(f'Propietario: {portafolio.usuario.nombre_completo}', estilos['Normal']))
    elementos.append(Paragraph(f'Descripcion: {portafolio.descripcion or "-"}', estilos['Normal']))
    elementos.append(Spacer(1, 12))

    resumen = calcular_resumen_portafolio(portafolio)
    elementos.append(Paragraph(f'Monto total invertido: USD {resumen["monto_total_usd"]:,.2f}', estilos['Normal']))
    if resumen['riesgo_promedio_ponderado'] is not None:
        elementos.append(Paragraph(f'Riesgo promedio ponderado (IRPC): {resumen["riesgo_promedio_ponderado"]}', estilos['Normal']))
    elementos.append(Spacer(1, 16))

    datos_tabla = [['Pais', 'Tipo activo', 'Monto USD', 'Fecha entrada', 'Fecha salida']]
    for posicion in portafolio.posiciones.select_related('pais').all():
        datos_tabla.append([
            posicion.pais.nombre,
            posicion.tipo_activo,
            f'{posicion.monto_inversion_usd:,.2f}',
            posicion.fecha_entrada.isoformat(),
            posicion.fecha_salida.isoformat() if posicion.fecha_salida else '-',
        ])

    tabla = Table(datos_tabla)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    elementos.append(tabla)

    documento.build(elementos)
    return buffer.getvalue()
