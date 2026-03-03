"""
Policy Analysis Report Generator
Generates professional PDF reports for policy analysis data
"""
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

# Brand colors
BRAND_PRIMARY = colors.HexColor('#00847E')     # EAZR Teal
BRAND_SECONDARY = colors.HexColor('#00A99D')   # Lighter Teal
BRAND_ACCENT = colors.HexColor('#E6F7F6')      # Very light teal background
BRAND_DARK = colors.HexColor('#005A54')        # Dark teal
TEXT_PRIMARY = colors.HexColor('#1F2937')      # Dark gray for text
TEXT_SECONDARY = colors.HexColor('#6B7280')    # Medium gray
BORDER_COLOR = colors.HexColor('#E5E7EB')      # Light gray border

# Register Unicode-compatible font for rupee symbol support
UNICODE_FONT = 'Helvetica'
UNICODE_FONT_BOLD = 'Helvetica-Bold'
RUPEE_SYMBOL = 'Rs.'
SUPPORTS_RUPEE_SYMBOL = False

try:
    # Try multiple font paths for different systems
    font_paths = [
        "/System/Library/Fonts/Supplemental/DejaVuSans.ttf",  # macOS
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",     # Linux
        "C:\\Windows\\Fonts\\DejaVuSans.ttf",                  # Windows
        "/Library/Fonts/DejaVuSans.ttf",                       # macOS alternative
    ]

    font_registered = False
    for font_path in font_paths:
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
            # Try to register bold variant
            bold_path = font_path.replace('.ttf', '-Bold.ttf')
            if os.path.exists(bold_path):
                pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', bold_path))
                UNICODE_FONT_BOLD = 'DejaVuSans-Bold'
            else:
                UNICODE_FONT_BOLD = 'DejaVuSans'

            UNICODE_FONT = 'DejaVuSans'
            RUPEE_SYMBOL = '₹'
            SUPPORTS_RUPEE_SYMBOL = True
            font_registered = True
            logger.info(f"✓ DejaVuSans font registered from: {font_path}")
            break

    if not font_registered:
        logger.warning("⚠️ DejaVuSans font not found in standard locations, using 'Rs.' instead of ₹ symbol")
except Exception as e:
    logger.warning(f"⚠️ Could not register Unicode font: {e}, using 'Rs.' instead of ₹ symbol")


def add_header(canvas, doc):
    """Add professional header to each page"""
    canvas.saveState()

    # Header background
    canvas.setFillColor(BRAND_PRIMARY)
    canvas.rect(0, A4[1] - 0.8*inch, A4[0], 0.8*inch, fill=True, stroke=False)

    # EAZR Logo/Text
    canvas.setFont(UNICODE_FONT_BOLD, 24)
    canvas.setFillColor(colors.white)
    canvas.drawString(0.75*inch, A4[1] - 0.55*inch, "EAZR")

    # Tagline
    canvas.setFont(UNICODE_FONT, 9)
    canvas.drawString(0.75*inch, A4[1] - 0.72*inch, "Smart Insurance Analysis")

    # Page number
    canvas.setFont(UNICODE_FONT, 9)
    page_num_text = f"Page {doc.page}"
    canvas.drawRightString(A4[0] - 0.75*inch, A4[1] - 0.55*inch, page_num_text)

    canvas.restoreState()


def add_footer(canvas, doc):
    """Add professional footer to each page"""
    canvas.saveState()

    # Footer line
    canvas.setStrokeColor(BORDER_COLOR)
    canvas.setLineWidth(1)
    canvas.line(0.75*inch, 0.6*inch, A4[0] - 0.75*inch, 0.6*inch)

    # Footer text
    canvas.setFont(UNICODE_FONT, 8)
    canvas.setFillColor(TEXT_SECONDARY)

    # Left: Generated date
    date_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    canvas.drawString(0.75*inch, 0.4*inch, date_text)

    # Right: Confidential
    canvas.drawRightString(A4[0] - 0.75*inch, 0.4*inch, "CONFIDENTIAL - For policy holder use only")

    canvas.restoreState()


def generate_policy_analysis_report(policy_data, analysis_data):
    """
    Generate professional PDF report for policy analysis

    Args:
        policy_data: dict containing policy details
        analysis_data: dict containing policy analyzer data

    Returns:
        BytesIO: PDF buffer
    """
    try:
        # Create PDF buffer
        buffer = BytesIO()

        # Create PDF document with custom page template
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1.2*inch,      # Space for header
            bottomMargin=0.9*inch,   # Space for footer
            title="Policy Analysis Report",
            author="EAZR Insurance Platform"
        )

        # Container for PDF elements
        elements = []

        # ==================== STYLES ====================
        styles = getSampleStyleSheet()

        # Cover title style
        cover_title_style = ParagraphStyle(
            'CoverTitle',
            parent=styles['Heading1'],
            fontName=UNICODE_FONT_BOLD,
            fontSize=32,
            textColor=BRAND_PRIMARY,
            spaceAfter=12,
            alignment=TA_CENTER,
            leading=38
        )

        # Cover subtitle style
        cover_subtitle_style = ParagraphStyle(
            'CoverSubtitle',
            parent=styles['Normal'],
            fontName=UNICODE_FONT,
            fontSize=14,
            textColor=TEXT_SECONDARY,
            spaceAfter=30,
            alignment=TA_CENTER
        )

        # Section heading style
        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName=UNICODE_FONT_BOLD,
            fontSize=16,
            textColor=BRAND_PRIMARY,
            spaceAfter=16,
            spaceBefore=24,
            borderPadding=(8, 0, 0, 0),
            leftIndent=0
        )

        # Subheading style
        subheading_style = ParagraphStyle(
            'SubHeading',
            parent=styles['Heading3'],
            fontName=UNICODE_FONT_BOLD,
            fontSize=12,
            textColor=BRAND_DARK,
            spaceAfter=10,
            spaceBefore=16
        )

        # Normal text style
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=UNICODE_FONT,
            fontSize=10,
            textColor=TEXT_PRIMARY,
            leading=14,
            alignment=TA_LEFT
        )

        # Info box style
        info_box_style = ParagraphStyle(
            'InfoBox',
            parent=normal_style,
            fontSize=9,
            textColor=TEXT_SECONDARY,
            leftIndent=12,
            rightIndent=12,
            spaceAfter=8
        )

        # Helper function to safely format currency
        def format_currency(value):
            if value is None or value == 'N/A' or value == 0:
                return 'N/A'
            try:
                return f"{RUPEE_SYMBOL}{int(float(value)):,}"
            except (ValueError, TypeError):
                return 'N/A'

        # ==================== COVER PAGE ====================
        elements.append(Spacer(1, 1.5*inch))

        # Title
        elements.append(Paragraph("Insurance Policy", cover_title_style))
        elements.append(Paragraph("Analysis Report", cover_title_style))
        elements.append(Spacer(1, 0.3*inch))

        # Policy number box
        policy_num = policy_data.get('policyNumber', 'N/A')
        policy_box_data = [[Paragraph(f"<b>Policy Number:</b> {policy_num}", subheading_style)]]
        policy_box = Table(policy_box_data, colWidths=[5*inch])
        policy_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), BRAND_ACCENT),
            ('BOX', (0, 0), (-1, -1), 1, BRAND_PRIMARY),
            ('LEFTPADDING', (0, 0), (-1, -1), 20),
            ('RIGHTPADDING', (0, 0), (-1, -1), 20),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(policy_box)
        elements.append(Spacer(1, 0.5*inch))

        # Policy holder info
        holder_name = policy_data.get('policyHolderName', 'N/A')
        provider = policy_data.get('insuranceProvider', 'N/A')
        elements.append(Paragraph(f"Policy Holder: <b>{holder_name}</b>", cover_subtitle_style))
        elements.append(Paragraph(f"Insurance Provider: <b>{provider}</b>", cover_subtitle_style))

        # Protection Score (NEW)
        protection_score = analysis_data.get('protectionScore', 0)
        protection_label = analysis_data.get('protectionScoreLabel', 'N/A')

        # Score color based on value
        if protection_score >= 80:
            score_color = colors.HexColor('#10B981')  # Green
        elif protection_score >= 60:
            score_color = colors.HexColor('#F59E0B')  # Orange
        else:
            score_color = colors.HexColor('#DC2626')  # Red

        score_text = f"<b>Protection Score:</b> <font color='#{score_color.hexval()[2:]}'>{protection_score}/100</font> - {protection_label}"
        elements.append(Paragraph(score_text, cover_subtitle_style))

        # Report date
        elements.append(Spacer(1, 0.8*inch))
        report_date = datetime.now().strftime('%B %d, %Y')
        elements.append(Paragraph(f"Report Generated: {report_date}", info_box_style))

        elements.append(PageBreak())

        # ==================== POLICY DETAILS SECTION ====================
        elements.append(Paragraph("Policy Overview", heading_style))

        # Create a nice table for policy details
        policy_details_data = [
            ['Policy Information', ''],
            ['Policy Number', policy_data.get('policyNumber', 'N/A')],
            ['Insurance Provider', policy_data.get('insuranceProvider', 'N/A')],
            ['Policy Type', str(policy_data.get('policyType', 'N/A')).title()],
            ['', ''],
            ['Coverage Information', ''],
            ['Policy Holder', policy_data.get('policyHolderName', 'N/A')],
            ['Insured Person', policy_data.get('insuredName', 'N/A')],
            ['Coverage Amount', format_currency(policy_data.get('coverageAmount'))],
            ['Annual Premium', format_currency(policy_data.get('premium'))],
            ['Payment Frequency', str(policy_data.get('premiumFrequency', 'annually')).title()],
            ['', ''],
            ['Policy Period', ''],
            ['Start Date', policy_data.get('startDate', 'N/A')],
            ['End Date', policy_data.get('endDate', 'N/A')],
            ['Status', str(policy_data.get('status', 'N/A')).upper()],
        ]

        policy_table = Table(policy_details_data, colWidths=[2.5*inch, 3.5*inch])
        policy_table.setStyle(TableStyle([
            # Header rows (category headers) - MUST come after data rows to override
            ('BACKGROUND', (0, 0), (-1, 0), BRAND_PRIMARY),
            ('BACKGROUND', (0, 5), (-1, 5), BRAND_PRIMARY),
            ('BACKGROUND', (0, 12), (-1, 12), BRAND_PRIMARY),
            ('FONTNAME', (0, 0), (-1, 0), UNICODE_FONT_BOLD),
            ('FONTNAME', (0, 5), (-1, 5), UNICODE_FONT_BOLD),
            ('FONTNAME', (0, 12), (-1, 12), UNICODE_FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 5), (-1, 5), 11),
            ('FONTSIZE', (0, 12), (-1, 12), 11),
            ('SPAN', (0, 0), (-1, 0)),  # Merge header cells
            ('SPAN', (0, 5), (-1, 5)),
            ('SPAN', (0, 12), (-1, 12)),

            # Empty rows for spacing
            ('LINEABOVE', (0, 4), (-1, 4), 0, colors.white),
            ('LINEBELOW', (0, 4), (-1, 4), 0, colors.white),
            ('LINEABOVE', (0, 11), (-1, 11), 0, colors.white),
            ('LINEBELOW', (0, 11), (-1, 11), 0, colors.white),

            # Data rows
            ('BACKGROUND', (0, 1), (-1, 3), colors.white),
            ('BACKGROUND', (0, 6), (-1, 10), colors.white),
            ('BACKGROUND', (0, 13), (-1, 15), colors.white),
            ('FONTNAME', (0, 1), (0, -1), UNICODE_FONT_BOLD),  # Labels bold
            ('FONTNAME', (1, 1), (-1, -1), UNICODE_FONT),      # Values normal
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_PRIMARY),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('BOX', (0, 0), (-1, -1), 1.5, BRAND_PRIMARY),

            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),

            # Header text color - MUST come last to override everything
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 5), (-1, 5), colors.white),
            ('TEXTCOLOR', (0, 12), (-1, 12), colors.white),
        ]))

        elements.append(policy_table)
        elements.append(Spacer(1, 0.3*inch))

        # ==================== CRITICAL AREAS (NEW) ====================
        critical_areas_data = analysis_data.get('criticalAreas', {})
        critical_areas = critical_areas_data.get('areas', [])

        if critical_areas:
            elements.append(PageBreak())
            elements.append(Paragraph("Critical Areas to Review", heading_style))

            # Info box
            info_text = f"<b>{len(critical_areas)} critical area(s)</b> require your immediate attention. These are important policy conditions or limitations."
            info_para = Paragraph(info_text, info_box_style)
            info_table = Table([[info_para]], colWidths=[6*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FEE2E2')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#DC2626')),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            elements.append(info_table)
            elements.append(Spacer(1, 0.2*inch))

            # Display critical areas
            for i, area in enumerate(critical_areas, 1):
                area_name = area.get('name', 'N/A')
                area_desc = area.get('description', 'N/A')
                importance = area.get('importance', 'medium').upper()

                # Importance color
                importance_color = {
                    'HIGH': colors.HexColor('#DC2626'),
                    'MEDIUM': colors.HexColor('#F59E0B'),
                    'LOW': colors.HexColor('#10B981')
                }.get(importance, TEXT_SECONDARY)

                # Area header
                area_header = f"<b>{i}. {area_name}</b> - <font color='#{importance_color.hexval()[2:]}'>{importance}</font>"
                elements.append(Paragraph(area_header, subheading_style))

                # Area description
                desc_para = Paragraph(area_desc, normal_style)
                desc_table = Table([[desc_para]], colWidths=[6*inch])
                desc_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), BRAND_ACCENT),
                    ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                    ('LEFTPADDING', (0, 0), (-1, -1), 12),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ]))
                elements.append(desc_table)
                elements.append(Spacer(1, 0.15*inch))

        # ==================== KEY BENEFITS (NEW) ====================
        key_benefits_data = analysis_data.get('keyBenefits', {})
        key_benefits = key_benefits_data.get('benefits', [])

        if key_benefits:
            elements.append(PageBreak())
            elements.append(Paragraph("Key Benefits & Coverage", heading_style))

            benefits_count = key_benefits_data.get('count', len(key_benefits))
            elements.append(Paragraph(f"Your policy includes <b>{benefits_count} key benefit(s)</b>:", subheading_style))

            benefits_data = []
            for i, benefit in enumerate(key_benefits, 1):
                benefit_text = str(benefit)
                benefits_data.append([f"{i}.", benefit_text])

            if benefits_data:
                benefits_table = Table(benefits_data, colWidths=[0.4*inch, 5.6*inch])
                benefits_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (0, -1), UNICODE_FONT_BOLD),
                    ('FONTNAME', (1, 0), (1, -1), UNICODE_FONT),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('TEXTCOLOR', (0, 0), (0, -1), BRAND_PRIMARY),
                    ('TEXTCOLOR', (1, 0), (1, -1), TEXT_PRIMARY),
                    ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, BRAND_ACCENT]),
                ]))
                elements.append(benefits_table)
                elements.append(Spacer(1, 0.2*inch))

        # ==================== POLICY EXCLUSIONS (NEW) ====================
        exclusions_data = analysis_data.get('policyExclusions', {})
        exclusions = exclusions_data.get('exclusions', [])

        if exclusions:
            elements.append(PageBreak())
            elements.append(Paragraph("Policy Exclusions - What's NOT Covered", heading_style))

            exclusions_count = exclusions_data.get('count', len(exclusions))
            info_text = f"<b>{exclusions_count} exclusion(s)</b> apply to this policy. These situations are NOT covered by your insurance."
            info_para = Paragraph(info_text, info_box_style)
            info_table = Table([[info_para]], colWidths=[6*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FEF3C7')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#F59E0B')),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            elements.append(info_table)
            elements.append(Spacer(1, 0.2*inch))

            exclusions_table_data = []
            for i, exclusion in enumerate(exclusions, 1):
                exclusion_text = str(exclusion)
                exclusions_table_data.append([f"✗", exclusion_text])

            if exclusions_table_data:
                exclusions_table = Table(exclusions_table_data, colWidths=[0.4*inch, 5.6*inch])
                exclusions_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (0, -1), UNICODE_FONT_BOLD),
                    ('FONTNAME', (1, 0), (1, -1), UNICODE_FONT),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#DC2626')),
                    ('TEXTCOLOR', (1, 0), (1, -1), TEXT_PRIMARY),
                    ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#FEF3C7')]),
                ]))
                elements.append(exclusions_table)
                elements.append(Spacer(1, 0.2*inch))

        # ==================== COVERAGE GAPS ====================
        gaps_data = analysis_data.get('coverageGaps', {})
        # Handle both formats: list directly or dict with 'gaps' key
        if isinstance(gaps_data, list):
            gaps = gaps_data
        else:
            gaps = gaps_data.get('gaps', [])

        if gaps:
            elements.append(PageBreak())
            elements.append(Paragraph("Coverage Gaps & Recommendations", heading_style))

            # Info box
            gaps_count = gaps_data.get('count', len(gaps)) if isinstance(gaps_data, dict) else len(gaps)
            info_text = f"We identified <b>{gaps_count} potential gap(s)</b> in your current coverage. Review these carefully to ensure comprehensive protection."
            info_para = Paragraph(info_text, info_box_style)
            info_table = Table([[info_para]], colWidths=[6*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), BRAND_ACCENT),
                ('BOX', (0, 0), (-1, -1), 1, BRAND_SECONDARY),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            elements.append(info_table)
            elements.append(Spacer(1, 0.2*inch))

            # Display gaps
            for i, gap in enumerate(gaps, 1):
                severity = gap.get('severity', 'medium').upper()
                category = gap.get('category', 'General')
                description = gap.get('description', 'N/A')
                recommendation = gap.get('recommendation', 'N/A')
                cost = gap.get('estimatedCost', 0)

                # Severity color
                severity_color = {
                    'HIGH': colors.HexColor('#DC2626'),
                    'MEDIUM': colors.HexColor('#F59E0B'),
                    'LOW': colors.HexColor('#10B981')
                }.get(severity, TEXT_SECONDARY)

                # Gap header
                gap_header = f"<b>Gap #{i}: {category}</b> - <font color='#{severity_color.hexval()[2:]}'>{severity} Priority</font>"
                elements.append(Paragraph(gap_header, subheading_style))

                # Gap details - Use Paragraph for text wrapping
                gap_cell_style = ParagraphStyle(
                    'GapCell',
                    parent=normal_style,
                    fontSize=9,
                    leading=12,
                    alignment=TA_LEFT
                )

                gap_details = [
                    ['Issue', Paragraph(description, gap_cell_style)],
                    ['Recommendation', Paragraph(recommendation, gap_cell_style)],
                    ['Estimated Cost', f"{format_currency(cost)}/year" if cost > 0 else 'Contact insurer'],
                ]

                gap_table = Table(gap_details, colWidths=[1.5*inch, 4.5*inch])
                gap_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), BRAND_ACCENT),
                    ('FONTNAME', (0, 0), (0, -1), UNICODE_FONT_BOLD),
                    ('FONTNAME', (1, 0), (1, -1), UNICODE_FONT),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('TEXTCOLOR', (0, 0), (-1, -1), TEXT_PRIMARY),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ]))
                elements.append(gap_table)
                elements.append(Spacer(1, 0.15*inch))

        # ==================== RECOMMENDATIONS (NEW) ====================
        recommendations_data = analysis_data.get('recommendations', {})
        recommendations = recommendations_data.get('suggestions', [])

        if recommendations:
            elements.append(PageBreak())
            elements.append(Paragraph("Recommended Improvements", heading_style))

            recommendations_count = recommendations_data.get('count', len(recommendations))
            elements.append(Paragraph(f"We recommend <b>{recommendations_count} improvement(s)</b> to enhance your coverage:", subheading_style))

            # Group by priority
            high_priority = [r for r in recommendations if r.get('priority', '').upper() == 'HIGH']
            medium_priority = [r for r in recommendations if r.get('priority', '').upper() == 'MEDIUM']
            low_priority = [r for r in recommendations if r.get('priority', '').upper() == 'LOW']

            # Display by priority
            for priority_label, priority_list, priority_color in [
                ('HIGH PRIORITY', high_priority, colors.HexColor('#DC2626')),
                ('MEDIUM PRIORITY', medium_priority, colors.HexColor('#F59E0B')),
                ('LOW PRIORITY', low_priority, colors.HexColor('#10B981'))
            ]:
                if priority_list:
                    priority_header = f"<font color='#{priority_color.hexval()[2:]}'><b>{priority_label}</b></font>"
                    elements.append(Paragraph(priority_header, subheading_style))

                    for rec in priority_list:
                        category = rec.get('category', 'General')
                        suggestion = rec.get('suggestion', 'N/A')
                        est_cost = rec.get('estimatedCost', 0)

                        rec_text = f"<b>{category}:</b> {suggestion}"
                        if est_cost > 0:
                            rec_text += f" <i>(Estimated: {format_currency(est_cost)}/year)</i>"

                        rec_para = Paragraph(f"• {rec_text}", normal_style)
                        elements.append(rec_para)
                        elements.append(Spacer(1, 0.08*inch))

                    elements.append(Spacer(1, 0.15*inch))

        # ==================== COVERAGE DETAILS (NEW) ====================
        coverage_details = analysis_data.get('coverageDetails', {})

        if coverage_details:
            elements.append(PageBreak())
            elements.append(Paragraph("Complete Coverage Details", heading_style))

            # Inclusions
            inclusions = coverage_details.get('inclusions', [])
            if inclusions:
                elements.append(Paragraph("What IS Covered (Inclusions):", subheading_style))

                inclusions_data = []
                for i, inclusion in enumerate(inclusions, 1):
                    inclusions_data.append([f"✓", str(inclusion)])

                if inclusions_data:
                    inclusions_table = Table(inclusions_data, colWidths=[0.4*inch, 5.6*inch])
                    inclusions_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (0, -1), UNICODE_FONT_BOLD),
                        ('FONTNAME', (1, 0), (1, -1), UNICODE_FONT),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#10B981')),
                        ('TEXTCOLOR', (1, 0), (1, -1), TEXT_PRIMARY),
                        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#F0FDF4')]),
                    ]))
                    elements.append(inclusions_table)
                    elements.append(Spacer(1, 0.2*inch))

            # Exclusions (from coverage details)
            detail_exclusions = coverage_details.get('exclusions', [])
            if detail_exclusions:
                elements.append(Paragraph("What is NOT Covered (Exclusions):", subheading_style))

                detail_exclusions_data = []
                for i, exclusion in enumerate(detail_exclusions, 1):
                    detail_exclusions_data.append([f"✗", str(exclusion)])

                if detail_exclusions_data:
                    detail_exclusions_table = Table(detail_exclusions_data, colWidths=[0.4*inch, 5.6*inch])
                    detail_exclusions_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (0, -1), UNICODE_FONT_BOLD),
                        ('FONTNAME', (1, 0), (1, -1), UNICODE_FONT),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#DC2626')),
                        ('TEXTCOLOR', (1, 0), (1, -1), TEXT_PRIMARY),
                        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#FEE2E2')]),
                    ]))
                    elements.append(detail_exclusions_table)
                    elements.append(Spacer(1, 0.2*inch))

            # Waiting Periods
            waiting_periods = coverage_details.get('waitingPeriods', [])
            if waiting_periods:
                elements.append(Paragraph("Waiting Periods:", subheading_style))

                waiting_data = []
                for i, period in enumerate(waiting_periods, 1):
                    waiting_data.append([f"⏱", str(period)])

                if waiting_data:
                    waiting_table = Table(waiting_data, colWidths=[0.4*inch, 5.6*inch])
                    waiting_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (0, -1), UNICODE_FONT_BOLD),
                        ('FONTNAME', (1, 0), (1, -1), UNICODE_FONT),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#F59E0B')),
                        ('TEXTCOLOR', (1, 0), (1, -1), TEXT_PRIMARY),
                        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, BRAND_ACCENT]),
                    ]))
                    elements.append(waiting_table)
                    elements.append(Spacer(1, 0.2*inch))

        # ==================== DEEP ANALYSIS (EAZR V4.0) ====================
        deep_analysis = analysis_data.get('deepAnalysis', {})
        deep_sections = deep_analysis.get('sections', [])

        if deep_sections:
            elements.append(PageBreak())

            # Get analysis type for title
            analysis_type = deep_analysis.get('analysisType', 'POLICY').upper()
            report_version = deep_analysis.get('reportVersion', '4.0')

            # Title for deep analysis
            deep_title_style = ParagraphStyle(
                'DeepTitle',
                parent=styles['Heading1'],
                fontName=UNICODE_FONT_BOLD,
                fontSize=20,
                textColor=BRAND_PRIMARY,
                spaceAfter=12,
                alignment=TA_CENTER
            )

            elements.append(Paragraph(f"{analysis_type} INSURANCE ANALYSIS", deep_title_style))
            elements.append(Paragraph(f"EAZR Policy Intelligence Report V{report_version}", info_box_style))
            elements.append(Spacer(1, 0.3*inch))

            # Process each section from deepAnalysis
            for section in deep_sections:
                section_id = section.get('sectionId', '')
                section_title = section.get('sectionTitle', 'Section')
                section_subtitle = section.get('sectionSubtitle', '')
                display_order = section.get('displayOrder', 0)
                content = section.get('content', {})

                # Section header with number
                section_header = f"<b>{str(display_order).zfill(2)} {section_title.upper()}</b>"
                elements.append(Paragraph(section_header, heading_style))

                if section_subtitle:
                    elements.append(Paragraph(f"<i>{section_subtitle}</i>", info_box_style))

                elements.append(Spacer(1, 0.15*inch))

                # Process section content based on its structure
                def render_content_item(key, value, indent=0):
                    """Recursively render content items"""
                    result_elements = []

                    if isinstance(value, dict):
                        # Check if it has a title and items structure
                        title = value.get('title', '')
                        items = value.get('items', [])
                        members = value.get('members', [])
                        periods = value.get('periods', [])
                        metrics = value.get('metrics', [])
                        scenarios = value.get('scenarios', [])
                        gaps = value.get('gaps', [])
                        add_ons = value.get('addOns', [])
                        actions = value.get('actions', [])
                        description = value.get('description', '')
                        warning = value.get('warning', False)
                        note = value.get('note', '')

                        # Display title if present
                        if title:
                            title_para = Paragraph(f"<b>{title}</b>", subheading_style)
                            result_elements.append(title_para)

                        # Display description if present
                        if description:
                            # Use color without extra # - hexval() returns '0x1F2937', so [2:] gives '1F2937'
                            desc_color = 'DC2626' if warning else TEXT_PRIMARY.hexval()[2:]
                            desc_para = Paragraph(f"<font color='#{desc_color}'>{description}</font>", normal_style)
                            result_elements.append(desc_para)

                        # Display items (key-value pairs)
                        if items and isinstance(items, list):
                            table_data = []
                            for item in items:
                                if isinstance(item, dict):
                                    # Handle different item structures
                                    if 'component' in item and 'value' in item:
                                        table_data.append([item.get('component', ''), str(item.get('value', ''))])
                                    elif 'label' in item and 'value' in item:
                                        table_data.append([item.get('label', ''), str(item.get('value', ''))])
                                    elif 'detail' in item and 'value' in item:
                                        table_data.append([item.get('detail', ''), str(item.get('value', ''))])
                                    elif 'item' in item and 'amount' in item:
                                        amount = item.get('amount', 0)
                                        amount_str = format_currency(abs(amount)) if isinstance(amount, (int, float)) else str(amount)
                                        if amount < 0:
                                            amount_str = f"-{amount_str}"
                                        item_note = item.get('note', '')
                                        display_val = f"{amount_str} ({item_note})" if item_note else amount_str
                                        table_data.append([item.get('item', ''), display_val])
                                    elif 'status' in item and 'value' in item:
                                        table_data.append([item.get('status', ''), str(item.get('value', ''))])
                                    elif 'metric' in item:
                                        your_policy = item.get('yourPolicy', 'N/A')
                                        benchmark = item.get('marketBenchmark', '')
                                        table_data.append([item.get('metric', ''), f"{your_policy} (Benchmark: {benchmark})" if benchmark else str(your_policy)])
                                    elif 'factor' in item:
                                        status = item.get('yourStatus', item.get('status', 'N/A'))
                                        impact = item.get('impact', '')
                                        table_data.append([item.get('factor', ''), f"{status} - {impact}" if impact else str(status)])

                            if table_data:
                                items_table = Table(table_data, colWidths=[2.5*inch, 3.5*inch])
                                items_table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (0, -1), BRAND_ACCENT),
                                    ('FONTNAME', (0, 0), (0, -1), UNICODE_FONT_BOLD),
                                    ('FONTNAME', (1, 0), (1, -1), UNICODE_FONT),
                                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                                    ('TEXTCOLOR', (0, 0), (-1, -1), TEXT_PRIMARY),
                                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                                    ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                                ]))
                                result_elements.append(items_table)
                                result_elements.append(Spacer(1, 0.1*inch))

                        # Display members (family members)
                        if members and isinstance(members, list):
                            members_data = [['Member', 'Age', 'Status']]
                            for member in members:
                                if isinstance(member, dict):
                                    members_data.append([
                                        member.get('name', 'N/A'),
                                        str(member.get('age', 'N/A')),
                                        member.get('waitingPeriodStatus', member.get('status', 'N/A'))
                                    ])

                            if len(members_data) > 1:
                                members_table = Table(members_data, colWidths=[2*inch, 1*inch, 3*inch])
                                members_table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), BRAND_PRIMARY),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                                    ('FONTNAME', (0, 0), (-1, 0), UNICODE_FONT_BOLD),
                                    ('FONTNAME', (0, 1), (-1, -1), UNICODE_FONT),
                                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                    ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                                ]))
                                result_elements.append(members_table)
                                result_elements.append(Spacer(1, 0.1*inch))

                        # Display waiting periods
                        if periods and isinstance(periods, list):
                            periods_data = [['Condition', 'Waiting Period', 'Status']]
                            for period in periods:
                                if isinstance(period, dict):
                                    periods_data.append([
                                        period.get('condition', 'N/A'),
                                        period.get('waitingPeriod', 'N/A'),
                                        period.get('status', 'N/A')
                                    ])

                            if len(periods_data) > 1:
                                periods_table = Table(periods_data, colWidths=[2.5*inch, 1.5*inch, 2*inch])
                                periods_table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F59E0B')),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                                    ('FONTNAME', (0, 0), (-1, 0), UNICODE_FONT_BOLD),
                                    ('FONTNAME', (0, 1), (-1, -1), UNICODE_FONT),
                                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                    ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                                ]))
                                result_elements.append(periods_table)
                                result_elements.append(Spacer(1, 0.1*inch))

                        # Display scenarios (major illness preparedness)
                        if scenarios and isinstance(scenarios, list):
                            scenarios_data = [['Scenario', 'Typical Cost', 'Your Coverage', 'Gap']]
                            for scenario in scenarios:
                                if isinstance(scenario, dict):
                                    gap_text = scenario.get('gap', 'N/A')
                                    gap_color = '#DC2626' if 'Gap' in str(gap_text) else '#10B981'
                                    scenarios_data.append([
                                        scenario.get('scenario', 'N/A'),
                                        scenario.get('typicalCost', 'N/A'),
                                        format_currency(scenario.get('yourCoverage', 0)),
                                        gap_text
                                    ])

                            if len(scenarios_data) > 1:
                                scenarios_table = Table(scenarios_data, colWidths=[1.8*inch, 1.3*inch, 1.4*inch, 1.5*inch])
                                scenarios_table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), BRAND_PRIMARY),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                                    ('FONTNAME', (0, 0), (-1, 0), UNICODE_FONT_BOLD),
                                    ('FONTNAME', (0, 1), (-1, -1), UNICODE_FONT),
                                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                    ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                                ]))
                                result_elements.append(scenarios_table)
                                result_elements.append(Spacer(1, 0.1*inch))

                        # Display gaps (improvement opportunities)
                        if gaps and isinstance(gaps, list):
                            gaps_data = [['Gap Identified', 'Impact', 'Solution']]
                            for gap in gaps:
                                if isinstance(gap, dict):
                                    gaps_data.append([
                                        gap.get('gap', gap.get('gapIdentified', 'N/A')),
                                        gap.get('impact', gap.get('impactOnYou', 'N/A')),
                                        gap.get('solution', 'N/A')
                                    ])

                            if len(gaps_data) > 1:
                                gaps_table = Table(gaps_data, colWidths=[2*inch, 2*inch, 2*inch])
                                gaps_table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DC2626')),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                                    ('FONTNAME', (0, 0), (-1, 0), UNICODE_FONT_BOLD),
                                    ('FONTNAME', (0, 1), (-1, -1), UNICODE_FONT),
                                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                    ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                                ]))
                                result_elements.append(gaps_table)
                                result_elements.append(Spacer(1, 0.1*inch))

                        # Display add-ons (motor insurance)
                        if add_ons and isinstance(add_ons, list):
                            addons_data = [['Add-On', 'Status', 'What It Does', 'Value Assessment']]
                            for addon in add_ons:
                                if isinstance(addon, dict):
                                    status = addon.get('yourStatus', addon.get('status', 'N/A'))
                                    status_icon = '✓' if status == 'Yes' else '✗'
                                    addons_data.append([
                                        addon.get('addOn', addon.get('name', 'N/A')),
                                        f"{status_icon} {status}",
                                        addon.get('whatItDoes', addon.get('description', 'N/A')),
                                        addon.get('valueAssessment', addon.get('recommendation', 'N/A'))
                                    ])

                            if len(addons_data) > 1:
                                addons_table = Table(addons_data, colWidths=[1.3*inch, 0.8*inch, 2*inch, 1.9*inch])
                                addons_table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), BRAND_PRIMARY),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                                    ('FONTNAME', (0, 0), (-1, 0), UNICODE_FONT_BOLD),
                                    ('FONTNAME', (0, 1), (-1, -1), UNICODE_FONT),
                                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                    ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                                    ('LEFTPADDING', (0, 0), (-1, -1), 5),
                                    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                                ]))
                                result_elements.append(addons_table)
                                result_elements.append(Spacer(1, 0.1*inch))

                        # Display actions (recommended actions)
                        if actions and isinstance(actions, list):
                            for idx, action in enumerate(actions, 1):
                                if isinstance(action, dict):
                                    priority = action.get('priority', idx)
                                    action_text = action.get('action', 'N/A')
                                    timeline = action.get('timeline', 'N/A')
                                    urgency = action.get('urgency', 'Medium').upper()

                                    urgency_color = {
                                        'CRITICAL': '#DC2626',
                                        'HIGH': '#F59E0B',
                                        'MEDIUM': '#3B82F6',
                                        'LOW': '#10B981'
                                    }.get(urgency, '#6B7280')

                                    action_para = Paragraph(
                                        f"<b>{priority}.</b> {action_text} <font color='{urgency_color}'>[{timeline} - {urgency}]</font>",
                                        normal_style
                                    )
                                    result_elements.append(action_para)
                                    result_elements.append(Spacer(1, 0.05*inch))

                        # Handle note if present
                        if note:
                            note_para = Paragraph(f"<i>Note: {note}</i>", info_box_style)
                            result_elements.append(note_para)

                        # Process remaining nested dicts
                        for nested_key, nested_value in value.items():
                            if nested_key not in ['title', 'items', 'members', 'periods', 'scenarios', 'gaps',
                                                   'add_ons', 'addOns', 'actions', 'description', 'warning', 'note',
                                                   'metrics', 'yourStatus', 'marketBenchmark', 'highlight']:
                                if isinstance(nested_value, dict):
                                    nested_elements = render_content_item(nested_key, nested_value, indent + 1)
                                    result_elements.extend(nested_elements)

                    elif isinstance(value, list):
                        # Handle list items
                        for item in value:
                            if isinstance(item, str):
                                bullet_para = Paragraph(f"• {item}", normal_style)
                                result_elements.append(bullet_para)
                            elif isinstance(item, dict):
                                nested_elements = render_content_item('', item, indent)
                                result_elements.extend(nested_elements)

                    elif isinstance(value, str) and value:
                        text_para = Paragraph(value, normal_style)
                        result_elements.append(text_para)

                    return result_elements

                # Render all content in section
                for content_key, content_value in content.items():
                    content_elements = render_content_item(content_key, content_value)
                    elements.extend(content_elements)

                elements.append(Spacer(1, 0.2*inch))

            # Add ASSESSMENT section at the end
            assessment = None
            for section in deep_sections:
                if section.get('sectionId') == 'assessment':
                    assessment = section.get('content', {})
                    break

            if assessment:
                # Assessment box
                assessment_status = assessment.get('assessmentStatus', 'REVIEW RECOMMENDED')
                key_finding = assessment.get('keyFinding', '')
                recommended_action = assessment.get('recommendedAction', '')

                # Status color
                status_color = BRAND_PRIMARY
                if 'WELL' in assessment_status.upper() or 'COMPREHENSIVE' in assessment_status.upper():
                    status_color = colors.HexColor('#10B981')
                elif 'ACTION' in assessment_status.upper() or 'NEEDS' in assessment_status.upper():
                    status_color = colors.HexColor('#DC2626')
                elif 'ADEQUATE' in assessment_status.upper():
                    status_color = colors.HexColor('#F59E0B')

                assessment_title = Paragraph(
                    f"<font color='#{status_color.hexval()[2:]}'><b>ASSESSMENT: {assessment_status}</b></font>",
                    heading_style
                )
                elements.append(assessment_title)

                if key_finding:
                    elements.append(Paragraph(f"<b>Key Finding:</b> {key_finding}", normal_style))
                if recommended_action:
                    elements.append(Paragraph(f"<b>Recommended Action:</b> {recommended_action}", normal_style))

                elements.append(Spacer(1, 0.3*inch))

        # ==================== SUMMARY ====================
        summary = analysis_data.get('summary', {})
        if summary:
            elements.append(PageBreak())
            elements.append(Paragraph("Executive Summary", heading_style))

            # Summary stats
            total_gaps = summary.get('totalGaps', 0)
            high_gaps = summary.get('highSeverityGaps', 0)
            medium_gaps = summary.get('mediumSeverityGaps', 0)
            low_gaps = summary.get('lowSeverityGaps', 0)
            additional_coverage = summary.get('recommendedAdditionalCoverage', 0)

            summary_data = [
                ['Summary Statistics', ''],
                ['Protection Score', f"{protection_score}/100 - {protection_label}"],
                ['Total Coverage Gaps', str(total_gaps)],
                ['High Priority Gaps', str(high_gaps)],
                ['Medium Priority Gaps', str(medium_gaps)],
                ['Low Priority Gaps', str(low_gaps)],
                ['Recommended Additional Coverage', format_currency(additional_coverage)],
            ]

            summary_table = Table(summary_data, colWidths=[3.5*inch, 2.5*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), BRAND_PRIMARY),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_PRIMARY),
                ('FONTNAME', (0, 0), (-1, 0), UNICODE_FONT_BOLD),
                ('FONTNAME', (0, 1), (0, -1), UNICODE_FONT_BOLD),
                ('FONTNAME', (1, 1), (1, -1), UNICODE_FONT),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, BORDER_COLOR),
                ('BOX', (0, 0), (-1, -1), 2, BRAND_PRIMARY),
                ('SPAN', (0, 0), (-1, 0)),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 0.3*inch))

        # ==================== BUILD PDF ====================
        # Build with header and footer
        doc.build(
            elements,
            onFirstPage=lambda canvas, doc: (add_header(canvas, doc), add_footer(canvas, doc)),
            onLaterPages=lambda canvas, doc: (add_header(canvas, doc), add_footer(canvas, doc))
        )

        # Reset buffer position
        buffer.seek(0)

        logger.info("✅ Professional PDF report generated successfully with complete policyAnalyzer data")
        return buffer

    except Exception as e:
        logger.error(f"❌ Error generating PDF report: {str(e)}", exc_info=True)
        raise
