"""Script de generación del PDF del Manual de Cálculo Fiscal y Mapeo AEAT."""

import os
from decimal import Decimal
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, HRFlowable, PageBreak
)

def build_pdf(filename: str):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    BLUE = colors.HexColor("#1a56db")
    DARK_BLUE = colors.HexColor("#0f3899")
    LIGHT_BLUE = colors.HexColor("#e8edfb")
    LIGHT_GRAY = colors.HexColor("#f8f9fa")
    BORDER_COLOR = colors.HexColor("#d1d5db")
    TEXT_COLOR = colors.HexColor("#1f2937")

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Title"],
        fontSize=18,
        leading=22,
        textColor=BLUE,
        alignment=0,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#6b7280"),
        spaceAfter=12,
    )
    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Heading1"],
        fontSize=13,
        leading=17,
        textColor=BLUE,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Heading2"],
        fontSize=11,
        leading=15,
        textColor=DARK_BLUE,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=TEXT_COLOR,
        spaceAfter=6,
    )
    bold_body_style = ParagraphStyle(
        "BoldBody_Custom",
        parent=body_style,
        fontName="Helvetica-Bold",
    )
    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
        textColor=TEXT_COLOR,
    )
    table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
        fontName="Helvetica-Bold",
        textColor=colors.white,
    )

    elements = []

    # Title Banner
    elements.append(Paragraph("MANUAL DE CÁLCULO FISCAL Y MAPEO AEAT", title_style))
    elements.append(Paragraph("Guía Completa de Contabilidad e Impuestos sobre el Alquiler (IRPF Modelo D-100)", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=BLUE, spaceAfter=12))

    # Section 1: Entradas de datos
    elements.append(Paragraph("1. ESTRUCTURA DE DATOS DE ENTRADA (INPUTS)", h1_style))
    elements.append(Paragraph(
        "Para realizar el cálculo del Rendimiento del Capital Inmobiliario, el sistema requiere tres bloques principales de información:",
        body_style
    ))

    inputs_data = [
        [Paragraph("Bloque de Entrada", table_header), Paragraph("Campos Requeridos", table_header), Paragraph("Finalidad Fiscal / Legal", table_header)],
        [
            Paragraph("<b>A. Datos de la Propiedad</b>", table_cell),
            Paragraph("• Referencia Catastral (20 caracteres)<br/>• Valor Catastral Suelo (€)<br/>• Valor Catastral Construcción (€)<br/>• Precio Compraventa (€)<br/>• Porción Construcción / Suelo (€)<br/>• Gastos Adquisición (ITP, Notaría, Registro)<br/>• Fecha de Compra", table_cell),
            Paragraph("Identificación oficial del inmueble y base de cálculo para la <b>amortización anual del 3%</b> sobre el valor de la edificación (excluyendo el suelo).", table_cell)
        ],
        [
            Paragraph("<b>B. Contratos de Arrendamiento</b>", table_cell),
            Paragraph("• Fecha Inicio y Fecha Fin<br/>• Tipo de Arrendamiento:<br/>  - <i>Vivienda Habitual</i><br/>  - <i>Temporal / Turístico / Comercial</i>", table_cell),
            Paragraph("Cálculo del <b>ratio de ocupación anual</b> (días alquilados) y aplicación de la <b>reducción del 60%</b> por vivienda habitual.", table_cell)
        ],
        [
            Paragraph("<b>C. Categorización de Gastos e Ingresos</b>", table_cell),
            Paragraph("• Importe (€) y Fecha<br/>• Categoría Fiscal AEAT (D-100)", table_cell),
            Paragraph("Asignación de importes a las casillas deducibles oficiales del Modelo D-100 de la Agencia Tributaria.", table_cell)
        ]
    ]

    t_inputs = Table(inputs_data, colWidths=[120, 190, 190])
    t_inputs.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("BACKGROUND", (0, 1), (-1, 1), LIGHT_GRAY),
        ("BACKGROUND", (0, 3), (-1, 3), LIGHT_GRAY),
    ]))
    elements.append(t_inputs)
    elements.append(Spacer(1, 10))

    # Categorías Fiscales Table
    elements.append(Paragraph("Categorías Fiscales de Gastos según la AEAT", h2_style))
    cat_data = [
        [Paragraph("Categoría Fiscal AEAT", table_header), Paragraph("Casilla D-100", table_header), Paragraph("Conceptos Incluidos", table_header)],
        [Paragraph("Intereses de Capital / Financiación", table_cell), Paragraph("<b>0076</b>", table_cell), Paragraph("Intereses de hipotecas o préstamos para la compra/mejora.", table_cell)],
        [Paragraph("Reparación y Conservación", table_cell), Paragraph("<b>0077</b>", table_cell), Paragraph("Pintura, reparación de averías, sustitución de instalaciones.", table_cell)],
        [Paragraph("Tributos, Tasas y Recargos", table_cell), Paragraph("<b>0079</b>", table_cell), Paragraph("IBI, tasa de basuras, vados y tributos no estatales.", table_cell)],
        [Paragraph("Primas de Seguros", table_cell), Paragraph("<b>0081</b>", table_cell), Paragraph("Seguro del hogar, impago de alquiler, responsabilidad civil.", table_cell)],
        [Paragraph("Servicios y Suministros", table_cell), Paragraph("<b>0082</b>", table_cell), Paragraph("Agua, luz, gas, internet y gastos de comunidad.", table_cell)],
        [Paragraph("Amortización de la Edificación", table_cell), Paragraph("<b>0083</b>", table_cell), Paragraph("3% anual sobre el mayor valor de construcción.", table_cell)],
        [Paragraph("Otros Gastos Deducibles", table_cell), Paragraph("<b>0084</b>", table_cell), Paragraph("Formalización contrato, saldos dudoso cobro, gestoría.", table_cell)],
    ]
    t_cat = Table(cat_data, colWidths=[160, 80, 260])
    t_cat.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_cat)
    elements.append(Spacer(1, 14))

    # Section 2: Algoritmo paso a paso
    elements.append(Paragraph("2. ALGORITMO DE CÁLCULO PASO A PASO (LIRPF)", h1_style))

    steps_text = [
        "<b>PASO 1 (Rendimientos Íntegros):</b> Suma total de los alquileres cobrados en el ejercicio fiscal (Casilla 0075).",
        "<b>PASO 2 (Ratio de Ocupación):</b> Fusión de intervalos de contratos para obtener los días reales alquilados. <i>Ratio = Días Alquilados / 365 (o 366)</i>.",
        "<b>PASO 3 (Prorrateo de Gastos):</b> Los gastos fijos (IBI, Seguros, Suministros, Amortización) se multiplican por el Ratio de Ocupación. Los intereses y reparaciones se deducen al 100%.",
        "<b>PASO 4 (Tope Art. 23.1.a LIRPF):</b> La suma de Intereses + Reparación no puede superar el Rendimiento Íntegro Total. El exceso no deducido se guarda para deducir en los 4 años siguientes.",
        "<b>PASO 5 (Amortización Art. 23.1.b LIRPF):</b> 3% sobre el mayor valor entre: 1) Coste de construcción + gastos de compra proporcionales, y 2) Valor catastral de la construcción. Se prorratea por ocupación.",
        "<b>PASO 6 (Rendimiento Neto Previo):</b> <i>Casilla 0075 (Ingresos) − Casilla 0085 (Total Gastos Deducibles)</i>.",
        "<b>PASO 7 (Reducción 60% Art. 23.2 LIRPF):</b> Si el neto es positivo y el contrato es de Vivienda Habitual, se aplica la reducción del 60% (Casilla 0087).",
        "<b>PASO 8 (Rendimiento Neto Reducido):</b> Resultado final a integrar en la base imponible del IRPF (Casilla 0088)."
    ]

    for step in steps_text:
        elements.append(Paragraph(f"• {step}", body_style))

    elements.append(Spacer(1, 14))

    # Section 3: Tabla de Mapeo AEAT D-100
    elements.append(Paragraph("3. MAPEO OFICIAL DE CASILLAS AEAT (MODELO D-100)", h1_style))

    aeat_mapping_data = [
        [Paragraph("Casilla", table_header), Paragraph("Denominación Oficial AEAT (Renta Web)", table_header), Paragraph("Concepto del Sistema / Fórmula", table_header)],
        [Paragraph("<b>0075</b>", table_cell), Paragraph("Rendimientos íntegros devengados", table_cell), Paragraph("Total ingresos de alquiler cobrados", table_cell)],
        [Paragraph("<b>0076</b>", table_cell), Paragraph("Intereses de capitales ajenos y gastos de financiación", table_cell), Paragraph("Intereses de hipoteca aplicados (con tope)", table_cell)],
        [Paragraph("<b>0077</b>", table_cell), Paragraph("Gastos de conservación y reparación", table_cell), Paragraph("Reparaciones y conservación aplicadas (con tope)", table_cell)],
        [Paragraph("<b>0079</b>", table_cell), Paragraph("Tributos, recargos y tasas no estatales", table_cell), Paragraph("IBI, basuras y tasas prorrateados por ocupación", table_cell)],
        [Paragraph("<b>0081</b>", table_cell), Paragraph("Primas de contratos de seguro", table_cell), Paragraph("Seguros prorrateados por ocupación", table_cell)],
        [Paragraph("<b>0082</b>", table_cell), Paragraph("Servicios y suministros", table_cell), Paragraph("Agua, luz, gas y comunidad prorrateados", table_cell)],
        [Paragraph("<b>0083</b>", table_cell), Paragraph("Amortización del inmueble", table_cell), Paragraph("3% amortización construcción prorrateada", table_cell)],
        [Paragraph("<b>0084</b>", table_cell), Paragraph("Otros gastos deducibles", table_cell), Paragraph("Formalización, dudoso cobro y otros prorrateados", table_cell)],
        [Paragraph("<b>0085</b>", table_cell), Paragraph("Total gastos deducibles", table_cell), Paragraph("Suma casillas 0076 a 0084", table_cell)],
        [Paragraph("<b>0086</b>", table_cell), Paragraph("Rendimiento neto", table_cell), Paragraph("Casilla 0075 − Casilla 0085", table_cell)],
        [Paragraph("<b>0087</b>", table_cell), Paragraph("Reducción por arrendamiento de vivienda habitual", table_cell), Paragraph("60% de reducción sobre rendimiento positivo VH", table_cell)],
        [Paragraph("<b>0088</b>", table_cell), Paragraph("Rendimiento neto reducido", table_cell), Paragraph("<b>Resultado Final a declarar (0086 − 0087)</b>", table_cell)],
    ]

    t_aeat = Table(aeat_mapping_data, colWidths=[55, 235, 210])
    t_aeat.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, -1), (-1, -1), LIGHT_BLUE),
    ]))
    elements.append(t_aeat)
    elements.append(Spacer(1, 14))

    # Section 4: Ejemplo Resuelto
    elements.append(Paragraph("4. EJEMPLO RESUELTO PASO A PASO", h1_style))
    elements.append(Paragraph(
        "<b>Supuesto:</b> Piso en alquiler durante todo el año (365 días, 100% ocupación) como Vivienda Habitual. "
        "Precio compra = 200.000 € (Construcción = 120.000 € / 60%), Gastos compra = 20.000 €. "
        "Ingresos = 12.000 €. Gastos: IBI 600 €, Seguro 400 €, Comunidad 1.000 €, Reparación 800 €, Intereses 1.200 €.",
        body_style
    ))

    example_data = [
        [Paragraph("Pasos del Cálculo", table_header), Paragraph("Cálculo Matemático", table_header), Paragraph("Resultado", table_header)],
        [Paragraph("1. Ingresos Íntegros (0075)", table_cell), Paragraph("12.000,00 €", table_cell), Paragraph("12.000,00 €", table_cell)],
        [Paragraph("2. Intereses (0076) + Reparación (0077)", table_cell), Paragraph("1.200 € + 800 € = 2.000 € (≤ 12.000 € tope)", table_cell), Paragraph("2.000,00 €", table_cell)],
        [Paragraph("3. IBI (0079) + Seguro (0081) + Comunidad (0082)", table_cell), Paragraph("600 € + 400 € + 1.000 €", table_cell), Paragraph("2.000,00 €", table_cell)],
        [Paragraph("4. Amortización 3% Construcción (0083)", table_cell), Paragraph("3% × (120.000 € + 12.000 € gastos) = 3% × 132.000 €", table_cell), Paragraph("3.960,00 €", table_cell)],
        [Paragraph("5. Total Gastos Deducibles (0085)", table_cell), Paragraph("2.000 € + 2.000 € + 3.960 €", table_cell), Paragraph("7.960,00 €", table_cell)],
        [Paragraph("6. Rendimiento Neto (0086)", table_cell), Paragraph("12.000 € − 7.960 €", table_cell), Paragraph("4.040,00 €", table_cell)],
        [Paragraph("7. Reducción Vivienda Habitual 60% (0087)", table_cell), Paragraph("4.040 € × 60%", table_cell), Paragraph("-2.424,00 €", table_cell)],
        [Paragraph("8. Rendimiento Neto Reducido Final (0088)", table_cell), Paragraph("4.040 € − 2.424 €", table_cell), Paragraph("<b>1.616,00 €</b>", table_cell)],
    ]

    t_example = Table(example_data, colWidths=[180, 220, 100])
    t_example.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, -1), (-1, -1), LIGHT_BLUE),
    ]))
    elements.append(t_example)

    doc.build(elements)

if __name__ == "__main__":
    out_dir = "/home/carlos/rental-handler/docs"
    os.makedirs(out_dir, exist_ok=True)
    pdf_path = os.path.join(out_dir, "manual_calculo_fiscal_aeat.pdf")
    build_pdf(pdf_path)
    print(f"PDF generado exitosamente en {pdf_path}")
