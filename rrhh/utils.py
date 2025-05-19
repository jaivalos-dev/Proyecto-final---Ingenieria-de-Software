# rrhh/utils.py
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generar_reporte_nomina(nominas, tipo_nomina, fecha_inicio, fecha_fin, fecha_generacion):
    """Generar un reporte PDF de una nómina"""
    buffer = io.BytesIO()
    
    # Crear el documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Título
    elements.append(Paragraph(f"Reporte de Nómina {tipo_nomina.nombre}", title_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Información general
    elements.append(Paragraph(f"Período: {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}", subtitle_style))
    elements.append(Paragraph(f"Fecha de generación: {fecha_generacion.strftime('%d/%m/%Y')}", normal_style))
    elements.append(Paragraph(f"Total de empleados: {len(nominas)}", normal_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Tabla de nóminas
    data = [
        ['#', 'Empleado', 'Puesto', 'Departamento', 'Devengado', 'Deducciones', 'Total']
    ]
    
    # Añadir datos de las nóminas
    for i, nomina in enumerate(nominas, 1):
        empleado = nomina.empleado
        data.append([
            i,
            f"{empleado.nombre} {empleado.apellido}",
            empleado.puesto.nombre,
            empleado.puesto.departamento.nombre,
            f"Q{nomina.total_devengado:.2f}",
            f"Q{nomina.total_deducciones:.2f}",
            f"Q{nomina.total_pagar:.2f}"
        ])
    
    # Añadir totales
    total_devengado = sum(n.total_devengado for n in nominas)
    total_deducciones = sum(n.total_deducciones for n in nominas)
    total_pagar = sum(n.total_pagar for n in nominas)
    
    data.append(['', '', '', 'TOTALES', f"Q{total_devengado:.2f}", f"Q{total_deducciones:.2f}", f"Q{total_pagar:.2f}"])
    
    # Crear tabla
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (4, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    
    # Añadir pie de página
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Este es un documento generado automáticamente por el sistema de nóminas.", normal_style))
    elements.append(Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
    
    # Construir PDF
    doc.build(elements)
    
    # Reposicionar el cursor al principio del buffer
    buffer.seek(0)
    return buffer