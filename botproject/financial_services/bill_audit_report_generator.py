"""
Hospital Bill Audit Report Generator
Generates PDF reports for hospital bill audit analysis using ReportLab.
"""

import logging
from io import BytesIO
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch, cm
    from reportlab.lib.colors import HexColor, white, black
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        Flowable, KeepTogether, PageBreak
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.graphics.shapes import Drawing, Rect, Circle, String, Line
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab not available, PDF report generation disabled")


# Color palette (matches existing EAZR report style)
COLORS = {
    "primary": HexColor("#6366F1") if REPORTLAB_AVAILABLE else None,
    "secondary": HexColor("#8B5CF6") if REPORTLAB_AVAILABLE else None,
    "success": HexColor("#10B981") if REPORTLAB_AVAILABLE else None,
    "warning": HexColor("#F59E0B") if REPORTLAB_AVAILABLE else None,
    "danger": HexColor("#EF4444") if REPORTLAB_AVAILABLE else None,
    "info": HexColor("#06B6D4") if REPORTLAB_AVAILABLE else None,
    "light_bg": HexColor("#F8FAFC") if REPORTLAB_AVAILABLE else None,
    "dark_text": HexColor("#1E293B") if REPORTLAB_AVAILABLE else None,
    "muted": HexColor("#94A3B8") if REPORTLAB_AVAILABLE else None,
}


def get_severity_color(severity: str):
    if not REPORTLAB_AVAILABLE:
        return None
    colors = {
        "critical": COLORS["danger"],
        "high": COLORS["danger"],
        "medium": COLORS["warning"],
        "low": COLORS["info"],
        "informational": COLORS["muted"],
    }
    return colors.get(severity, COLORS["muted"])


def get_coverage_color(status: str):
    if not REPORTLAB_AVAILABLE:
        return None
    colors = {"covered": COLORS["success"], "partial": COLORS["warning"], "not_covered": COLORS["danger"]}
    return colors.get(status, COLORS["muted"])


class ReportHeader(Flowable):
    """Custom header flowable with gradient background."""

    def __init__(self, width, height, title, subtitle=""):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.title = title
        self.subtitle = subtitle

    def draw(self):
        canvas = self.canv
        # Gradient background
        canvas.setFillColor(COLORS["primary"])
        canvas.roundRect(0, 0, self.width, self.height, 10, fill=1, stroke=0)

        # Title
        canvas.setFillColor(white)
        canvas.setFont("Helvetica-Bold", 20)
        canvas.drawCentredString(self.width / 2, self.height - 35, self.title)

        # Subtitle
        if self.subtitle:
            canvas.setFont("Helvetica", 11)
            canvas.drawCentredString(self.width / 2, self.height - 55, self.subtitle)


def create_styles():
    """Create paragraph styles for the report."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='ReportTitle',
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=COLORS["dark_text"],
        spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name='SectionTitle',
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=COLORS["primary"],
        spaceAfter=8,
        spaceBefore=16,
    ))
    styles.add(ParagraphStyle(
        name='BodyText2',
        fontName='Helvetica',
        fontSize=10,
        textColor=COLORS["dark_text"],
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name='SmallText',
        fontName='Helvetica',
        fontSize=8,
        textColor=COLORS["muted"],
    ))

    return styles


def generate_bill_audit_report(audit_data: Dict[str, Any]) -> BytesIO:
    """
    Generate a comprehensive PDF report for a hospital bill audit.

    Args:
        audit_data: Complete audit result dict

    Returns:
        BytesIO buffer containing the PDF
    """
    if not REPORTLAB_AVAILABLE:
        raise Exception("ReportLab is required for PDF report generation")

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=30,
        bottomMargin=30,
    )

    styles = create_styles()
    elements = []
    page_width = A4[0] - 80  # Account for margins

    bill_data = audit_data.get("bill_data", {})
    discrepancies = audit_data.get("discrepancies", [])
    savings = audit_data.get("savings", {})
    coverage = audit_data.get("coverage_analysis")
    bill_health = audit_data.get("bill_health_score", {})
    validation = audit_data.get("extraction_validation", {})

    # ===== HEADER =====
    subtitle = f"Generated on {datetime.utcnow().strftime('%d %B %Y, %H:%M UTC')} | Audit ID: {audit_data.get('audit_id', 'N/A')}"
    elements.append(ReportHeader(page_width, 70, "Hospital Bill Audit Report", subtitle))
    elements.append(Spacer(1, 20))

    # ===== BILL HEALTH SCORE =====
    if bill_health:
        elements.append(Paragraph("Bill Health Score", styles['SectionTitle']))
        score = bill_health.get("score", 0)
        grade = bill_health.get("grade", "N/A")
        interpretation = bill_health.get("interpretation", "")

        score_data = [
            ["Overall Score", f"{score}/100 (Grade {grade})"],
            ["Assessment", interpretation],
        ]
        factors = bill_health.get("factors", {})
        for factor, val in factors.items():
            label = factor.replace("_", " ").title()
            score_data.append([label, f"{val}"])

        score_table = Table(score_data, colWidths=[page_width * 0.35, page_width * 0.65])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), COLORS["light_bg"]),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), COLORS["dark_text"]),
            ('GRID', (0, 0), (-1, -1), 0.5, COLORS["muted"]),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(score_table)
        elements.append(Spacer(1, 15))

    # ===== BILL SUMMARY =====
    elements.append(Paragraph("Bill Summary", styles['SectionTitle']))
    summary = bill_data.get("bill_summary", {})
    metadata = bill_data.get("metadata", {})
    patient = bill_data.get("patient_details", {})
    hospital_ctx = bill_data.get("hospital_context", audit_data.get("hospital_context", {}))

    summary_data = [
        ["Hospital", str(metadata.get("hospital_name", hospital_ctx.get("hospital_name", "N/A")))],
        ["Hospital Type", str(hospital_ctx.get("hospital_type", "N/A")).replace("_", " ").title()],
        ["Patient", str(patient.get("patient_name", "N/A"))],
        ["Diagnosis", str(patient.get("primary_diagnosis", "N/A"))],
        ["Procedure", str(patient.get("procedure_performed", "N/A"))],
        ["Admission", str(patient.get("admission_date", "N/A"))],
        ["Discharge", str(patient.get("discharge_date", "N/A"))],
        ["LOS (Days)", str(patient.get("los_days", "N/A"))],
        ["Total Bill", f"Rs. {summary.get('gross_amount', 0):,.2f}"],
        ["Patient Payable", f"Rs. {summary.get('patient_payable', 0):,.2f}"],
    ]

    summary_table = Table(summary_data, colWidths=[page_width * 0.3, page_width * 0.7])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), COLORS["light_bg"]),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), COLORS["dark_text"]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, COLORS["muted"]),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 15))

    # ===== EXTRACTION VALIDATION =====
    if validation:
        confidence = validation.get("extraction_confidence", "medium")
        reason = validation.get("confidence_reason", "")
        elements.append(Paragraph(f"Extraction Confidence: {confidence.upper()}", styles['BodyText2']))
        if reason:
            elements.append(Paragraph(f"({reason})", styles['SmallText']))
        elements.append(Spacer(1, 10))

    # ===== COVERAGE ANALYSIS =====
    if coverage:
        elements.append(Paragraph("Coverage Analysis", styles['SectionTitle']))

        cov_data = [
            ["Total Bill Amount", f"Rs. {coverage.get('total_bill_amount', 0):,.2f}"],
            ["Covered by Insurance", f"Rs. {coverage.get('total_covered', 0):,.2f}"],
            ["Not Covered", f"Rs. {coverage.get('total_not_covered', 0):,.2f}"],
            ["Co-pay Amount", f"Rs. {coverage.get('copay_amount', 0):,.2f}"],
            ["Est. Out-of-Pocket", f"Rs. {coverage.get('estimated_out_of_pocket', 0):,.2f}"],
            ["Coverage %", f"{coverage.get('coverage_percentage', 0)}%"],
        ]

        cov_table = Table(cov_data, colWidths=[page_width * 0.4, page_width * 0.6])
        cov_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), COLORS["light_bg"]),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), COLORS["dark_text"]),
            ('GRID', (0, 0), (-1, -1), 0.5, COLORS["muted"]),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(cov_table)

        if coverage.get("si_exhaustion_warning"):
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(
                "<b>Warning:</b> Your Sum Insured may be exhausted with this claim.",
                styles['BodyText2']
            ))
        if coverage.get("proportionate_deduction_warning"):
            elements.append(Paragraph(
                "<b>Note:</b> Room rent exceeds policy limit. Proportionate deduction may apply to entire bill.",
                styles['BodyText2']
            ))
        elements.append(Spacer(1, 15))

    # ===== DISCREPANCIES =====
    if discrepancies:
        elements.append(Paragraph(f"Discrepancies Found ({len(discrepancies)})", styles['SectionTitle']))

        disc_header = ["#", "Type", "Item", "Severity", "Amount", "Action"]
        disc_rows = [disc_header]
        for i, d in enumerate(discrepancies, 1):
            disc_rows.append([
                str(i),
                d.get("type", "").replace("_", " ").title(),
                str(d.get("item_name", ""))[:30],
                d.get("severity", "").upper(),
                f"Rs. {d.get('overcharged_amount', 0):,.0f}" if d.get("overcharged_amount") else "-",
                str(d.get("action", ""))[:40],
            ])

        col_widths = [page_width * w for w in [0.05, 0.18, 0.2, 0.1, 0.12, 0.35]]
        disc_table = Table(disc_rows, colWidths=col_widths, repeatRows=1)

        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), COLORS["primary"]),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, COLORS["muted"]),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, COLORS["light_bg"]]),
        ]

        for i, d in enumerate(discrepancies, 1):
            sev_color = get_severity_color(d.get("severity", "low"))
            if sev_color:
                table_style.append(('TEXTCOLOR', (3, i), (3, i), sev_color))
                table_style.append(('FONTNAME', (3, i), (3, i), 'Helvetica-Bold'))

        disc_table.setStyle(TableStyle(table_style))
        elements.append(disc_table)
        elements.append(Spacer(1, 15))

    # ===== SAVINGS SUMMARY =====
    if savings:
        elements.append(Paragraph("Potential Savings", styles['SectionTitle']))

        savings_data = [
            ["Savings Tier", "Amount", "Recovery Likelihood"],
            ["High Confidence", f"Rs. {savings.get('high_confidence_savings', 0):,.2f}", "90%+"],
            ["Medium Confidence", f"Rs. {savings.get('medium_confidence_savings', 0):,.2f}", "~50-75%"],
            ["Low Confidence", f"Rs. {savings.get('low_confidence_savings', 0):,.2f}", "~25-30%"],
            ["", "", ""],
            ["Conservative Estimate", f"Rs. {savings.get('conservative_estimate', 0):,.2f}", "Recommended"],
            ["Moderate Estimate", f"Rs. {savings.get('moderate_estimate', 0):,.2f}", "Likely"],
            ["Optimistic Estimate", f"Rs. {savings.get('optimistic_estimate', 0):,.2f}", "Best case"],
        ]

        sav_table = Table(savings_data, colWidths=[page_width * 0.35, page_width * 0.35, page_width * 0.3])
        sav_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLORS["success"]),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, COLORS["muted"]),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 5), (-1, 7), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 5), (-1, 5), HexColor("#ECFDF5")),
            ('BACKGROUND', (0, 6), (-1, 6), HexColor("#F0FDF4")),
            ('BACKGROUND', (0, 7), (-1, 7), HexColor("#F0FDF4")),
        ]))
        elements.append(sav_table)
        elements.append(Spacer(1, 15))

    # ===== DISCLAIMER =====
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Disclaimer", styles['SectionTitle']))
    disclaimer_text = (
        "This analysis is informational only. EAZR is not making accusations of fraud or malpractice. "
        "Each hospital sets its own tariff rates — pricing differences between hospitals are normal and not inherently wrong. "
        "This audit checks only for billing errors, duplicates, arithmetic mistakes, and practices that violate consumer protection laws (DPCO). "
        "User should verify findings before disputing. Healthcare decisions should involve treating physician. "
        "EAZR is not liable for dispute outcomes."
    )
    elements.append(Paragraph(disclaimer_text, styles['SmallText']))

    # ===== FOOTER =====
    elements.append(Spacer(1, 10))
    footer_text = f"EAZR Hospital Bill Audit Intelligence v2.0 | Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | Confidential"
    elements.append(Paragraph(footer_text, styles['SmallText']))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)

    logger.info(f"Hospital bill audit report generated, {buffer.getbuffer().nbytes} bytes")
    return buffer
