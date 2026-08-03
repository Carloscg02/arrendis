"""Adaptador de renderizado PDF — genera borrador fiscal AEAT con reportlab."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from backend.domain.ports import FiscalReportRendererPort
from backend.domain.value_objects import FiscalReport

# Mapeo para el Modelo D-100, Ejercicio 2024
AEAT_CASILLA_MAP_2024: dict[str, str] = {
    "rendimiento_integro": "0075",
    "intereses_capital": "0076",
    "reparacion_conservacion": "0077",
    "tributos": "0079",
    "seguros": "0081",
    "suministros": "0082",
    "amortizacion": "0083",
    "otros_gastos": "0084",
    "total_gastos_deducibles": "0085",
    "rendimiento_neto": "0086",
    "reduccion_vivienda": "0087",
    "rendimiento_neto_reducido": "0088",
}


class AEATPdfRendererAdapter(FiscalReportRendererPort):
    """Genera un PDF con formato de borrador fiscal AEAT usando reportlab."""

    BLUE = colors.HexColor("#1a56db")
    LIGHT_BLUE = colors.HexColor("#e8edfb")
    LIGHT_GRAY = colors.HexColor("#f5f5f5")
    DARK_GRAY = colors.HexColor("#333333")

    def __init__(self, casilla_map: dict[str, str] | None = None) -> None:
        self._casilla_map = casilla_map or AEAT_CASILLA_MAP_2024

    def render(self, report: FiscalReport, property_name: str, property_address: str) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )
        elements = self._build_elements(report, property_name, property_address)
        doc.build(elements)
        return buffer.getvalue()

    def content_type(self) -> str:
        return "application/pdf"

    def file_extension(self) -> str:
        return "pdf"

    # ── Internal builders ──

    def _build_elements(
        self, report: FiscalReport, property_name: str, property_address: str
    ) -> list:
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "TitleCustom",
            parent=styles["Title"],
            fontSize=16,
            textColor=self.BLUE,
            spaceAfter=6,
        )
        subtitle_style = ParagraphStyle(
            "SubtitleCustom",
            parent=styles["Normal"],
            fontSize=10,
            textColor=self.DARK_GRAY,
            spaceAfter=4,
        )
        section_style = ParagraphStyle(
            "SectionCustom",
            parent=styles["Heading2"],
            fontSize=12,
            textColor=self.BLUE,
            spaceBefore=14,
            spaceAfter=6,
        )
        disclaimer_style = ParagraphStyle(
            "Disclaimer",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.gray,
            spaceBefore=12,
        )

        elements: list = []

        # Header
        elements.append(Paragraph("BORRADOR FISCAL — Rendimientos del Capital Inmobiliario", title_style))
        elements.append(Paragraph(f"Ejercicio Fiscal: {report.fiscal_year}", subtitle_style))
        elements.append(Paragraph(f"Propiedad: {property_name}", subtitle_style))
        if property_address:
            elements.append(Paragraph(f"Dirección: {property_address}", subtitle_style))
        elements.append(Paragraph(f"Fecha de generación: {date.today().strftime('%d/%m/%Y')}", subtitle_style))
        elements.append(Spacer(1, 12))

        # Section 1: Rendimientos Íntegros
        elements.append(Paragraph("1. RENDIMIENTOS ÍNTEGROS", section_style))
        elements.append(self._build_table([
            ["Concepto", "Casilla", "Importe"],
            ["Rendimiento íntegro", self._casilla_map.get("rendimiento_integro", "—"), self._fmt(report.total_income)],
        ], has_header=True))

        # Section 2: Gastos Deducibles
        elements.append(Paragraph("2. GASTOS DEDUCIBLES", section_style))
        expense_rows = [
            ["Concepto", "Casilla", "Importe"],
            ["Intereses de capital", self._casilla_map.get("intereses_capital", "—"), self._fmt(report.expenses_intereses)],
            ["Reparación y conservación", self._casilla_map.get("reparacion_conservacion", "—"), self._fmt(report.expenses_reparacion)],
            ["Tributos (IBI, tasas)", self._casilla_map.get("tributos", "—"), self._fmt(report.expenses_tributos)],
            ["Seguros", self._casilla_map.get("seguros", "—"), self._fmt(report.expenses_seguros)],
            ["Suministros", self._casilla_map.get("suministros", "—"), self._fmt(report.expenses_suministros)],
            ["Amortización", self._casilla_map.get("amortizacion", "—"), self._fmt(report.amortization_prorated)],
            ["Otros gastos deducibles", self._casilla_map.get("otros_gastos", "—"),
             self._fmt(report.expenses_formalizacion + report.expenses_dudoso_cobro + report.expenses_otros)],
            ["TOTAL GASTOS DEDUCIBLES", self._casilla_map.get("total_gastos_deducibles", "—"), self._fmt(report.total_deductible_expenses)],
        ]
        elements.append(self._build_table(expense_rows, has_header=True, highlight_last=True))

        # Section 3: Rendimiento Neto
        elements.append(Paragraph("3. RENDIMIENTO NETO", section_style))
        net_rows = [
            ["Concepto", "Casilla", "Importe"],
            ["Rendimiento neto", self._casilla_map.get("rendimiento_neto", "—"), self._fmt(report.net_income_before_reduction)],
            ["Reducción vivienda habitual", self._casilla_map.get("reduccion_vivienda", "—"), self._fmt(-report.reduction_amount)],
            ["RENDIMIENTO NETO REDUCIDO", self._casilla_map.get("rendimiento_neto_reducido", "—"), self._fmt(report.net_income_final)],
        ]
        elements.append(self._build_table(net_rows, has_header=True, highlight_last=True))

        # Section 4: Detalle del cálculo
        elements.append(Paragraph("4. DETALLE DEL CÁLCULO", section_style))
        detail_rows = [
            ["Concepto", "Valor"],
            ["Días alquilados", f"{report.rented_days}/{report.total_days_in_year} ({self._pct(report.occupation_ratio)})"],
            ["Base amortización", self._fmt(report.amortization_base)],
            ["Amortización anual completa (3%)", self._fmt(report.amortization_full_year)],
            ["Amortización prorrateada", self._fmt(report.amortization_prorated)],
            ["Tope reparación+intereses aplicado", "Sí" if report.repair_interest_excess > 0 else "No"],
            ["Exceso pendiente (4 años siguientes)", self._fmt(report.repair_interest_excess)],
            ["Días vivienda habitual", str(report.vivienda_habitual_days)],
            ["Reducción VH", f"{self._pct(report.reduction_percentage)} sobre {self._fmt(report.reduction_base)}"],
        ]
        elements.append(self._build_table(detail_rows, has_header=True))

        # Section 5: Avisos
        elements.append(Paragraph("5. AVISOS", section_style))
        if report.has_warnings:
            elements.append(Paragraph(
                f"⚠ Hay {report.unclassified_income_count} ingreso(s) y "
                f"{report.unclassified_expense_count} gasto(s) sin clasificar fiscalmente. "
                "Estos registros NO se han incluido en el cálculo.",
                styles["Normal"],
            ))
        elements.append(Spacer(1, 8))

        # Disclaimer
        elements.append(Paragraph(
            "Este documento es un borrador orientativo generado automáticamente. "
            "Los datos deben trasladarse manualmente a Renta Web (AEAT). "
            "No constituye presentación telemática ante la AEAT. "
            f"Generado por Gestión de Alquileres — {date.today().strftime('%d/%m/%Y')}",
            disclaimer_style,
        ))

        return elements

    def _build_table(self, data: list[list], *, has_header: bool = False, highlight_last: bool = False) -> Table:
        col_widths = [240, 60, 100] if len(data[0]) == 3 else [240, 160]
        table = Table(data, colWidths=col_widths)

        style_commands: list = [
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]

        if has_header:
            style_commands.extend([
                ("BACKGROUND", (0, 0), (-1, 0), self.BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ])

        # Alternate row colors
        for i in range(1, len(data)):
            if i % 2 == 0:
                style_commands.append(("BACKGROUND", (0, i), (-1, i), self.LIGHT_GRAY))

        if highlight_last and len(data) > 1:
            style_commands.extend([
                ("BACKGROUND", (0, -1), (-1, -1), self.LIGHT_BLUE),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ])

        table.setStyle(TableStyle(style_commands))
        return table

    @staticmethod
    def _fmt(value: Decimal) -> str:
        """Formatea un Decimal como moneda española: 1.234,56 €"""
        formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{formatted} €"

    @staticmethod
    def _pct(value: Decimal) -> str:
        """Formatea un ratio como porcentaje: 0.6 → 60,00%"""
        return f"{value * 100:,.2f}%".replace(".", ",")
