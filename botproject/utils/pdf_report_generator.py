"""
Shared PDF Report Generator for Insurance Gap Analysis
This module provides a unified PDF generation function used by both the /ask endpoint
and the report regeneration endpoint to ensure consistent styling and branding.
"""

from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import re


def create_gap_analysis_pdf(
    report_text: str,
    filename: str,
    is_regenerated: bool = False,
    uin: str = None,
    policy_type: str = None
) -> BytesIO:
    """
    Creates a professionally formatted PDF report for insurance gap analysis.

    This function generates a PDF with consistent styling, branding, and formatting
    used across all gap analysis reports in the system.

    Args:
        report_text: The markdown-formatted analysis text
        filename: The original policy document filename
        is_regenerated: Whether this is a regenerated report (adds suffix to title)
        uin: Unique Identification Number of the policy (optional)
        policy_type: Type of insurance policy (optional)

    Returns:
        BytesIO: Buffer containing the generated PDF

    Styling Features:
        - Teal color scheme (#008B8B) for branding
        - Professional header with eazr branding
        - Metadata box with report details
        - Markdown parsing with support for:
            * ## Section headings (uppercase, teal, with background)
            * ** Sub-headings (bold)
            * Bullet points (- or *) with teal bullets
            * Numbered lists
            * Bold (**text**) and italic (*text*) inline formatting
        - Professional footer with disclaimer
    """

    buffer = BytesIO()

    # Create PDF with letter size and margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75*inch,
        rightMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=0.75*inch
    )

    elements = []
    styles = getSampleStyleSheet()

    # ========== CUSTOM STYLES ==========

    # Title Style - Professional header with teal
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#008B8B'),  # Teal color
        spaceAfter=8,
        spaceBefore=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=32
    )

    # Subtitle style
    subtitle_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#555555'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica',
        leading=16
    )

    # Section Heading (##)
    section_heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#008B8B'),  # Teal
        spaceAfter=15,
        spaceBefore=25,
        fontName='Helvetica-Bold',
        borderWidth=0,
        borderColor=colors.HexColor('#008B8B'),  # Teal
        borderPadding=8,
        backColor=colors.HexColor('#E0F2F2'),  # Light teal background
        leftIndent=10,
        leading=20
    )

    # Sub-heading (bold text **)
    subheading_style = ParagraphStyle(
        'SubHeading',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=colors.HexColor('#006666'),  # Darker teal
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold',
        leftIndent=5,
        leading=16
    )

    # Body text
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=colors.HexColor('#333333'),
        alignment=TA_LEFT,
        spaceAfter=8,
        leading=16,
        leftIndent=10
    )

    # Bullet style with teal bullets
    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=colors.HexColor('#333333'),
        spaceAfter=6,
        leading=15,
        leftIndent=25,
        bulletIndent=10
    )

    # ========== BUILD REPORT HEADER ==========

    # Add eazr branding
    brand_style = ParagraphStyle(
        'BrandStyle',
        parent=styles['Normal'],
        fontSize=32,
        textColor=colors.HexColor('#008B8B'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=5,
        leading=38
    )

    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph("eazr", brand_style))

    # Add tagline
    tagline_style = ParagraphStyle(
        'TaglineStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
        fontName='Helvetica',
        spaceAfter=20
    )
    elements.append(Paragraph("Insurance Gap Analysis Platform", tagline_style))

    # Add title (with regenerated suffix if applicable)
    title_text = "INSURANCE GAP ANALYSIS REPORT"
    if is_regenerated:
        title_text += " (REGENERATED)"

    elements.append(Paragraph(title_text, title_style))
    elements.append(Paragraph("Comprehensive Policy Review & Risk Assessment", subtitle_style))

    # Add separator line with teal color
    line_table = Table([['']], colWidths=[6.5*inch])
    line_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 3, colors.HexColor('#008B8B')),  # Teal
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor('#CCCCCC')),
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 0.15*inch))

    # Add metadata box with teal accent
    metadata_box_style = ParagraphStyle(
        'MetadataBox',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#333333'),
        spaceAfter=3,
        alignment=TA_LEFT,
        leftIndent=15,
        rightIndent=15
    )

    # Create attractive metadata box
    elements.append(Spacer(1, 0.1*inch))

    # Build metadata dynamically based on available information
    metadata_data = []

    # Report generation timestamp
    timestamp_text = "Regenerated" if is_regenerated else "Generated"
    metadata_data.append([
        Paragraph(
            f'<font color="#008B8B"><b>●</b></font> <b>Report {timestamp_text}:</b> {datetime.now().strftime("%d %B %Y at %I:%M %p")}',
            metadata_box_style
        ),
    ])

    # Policy document filename
    metadata_data.append([
        Paragraph(
            f'<font color="#008B8B"><b>●</b></font> <b>Policy Document:</b> {filename}',
            metadata_box_style
        ),
    ])

    # Analysis type
    metadata_data.append([
        Paragraph(
            f'<font color="#008B8B"><b>●</b></font> <b>Analysis Type:</b> Comprehensive Insurance Gap Analysis',
            metadata_box_style
        ),
    ])

    # Optional: Add UIN if provided
    if uin:
        metadata_data.append([
            Paragraph(
                f'<font color="#008B8B"><b>●</b></font> <b>UIN:</b> {uin}',
                metadata_box_style
            ),
        ])

    # Optional: Add policy type if provided
    if policy_type:
        metadata_data.append([
            Paragraph(
                f'<font color="#008B8B"><b>●</b></font> <b>Policy Type:</b> {policy_type}',
                metadata_box_style
            ),
        ])

    metadata_table = Table(metadata_data, colWidths=[6.5*inch])
    metadata_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0FAFA')),  # Very light teal
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#008B8B')),  # Teal border
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(metadata_table)
    elements.append(Spacer(1, 0.3*inch))

    # ========== PROCESS REPORT CONTENT ==========

    lines = report_text.split('\n')

    for line in lines:
        line_stripped = line.strip()

        # Skip empty lines with minimal spacing
        if not line_stripped:
            elements.append(Spacer(1, 0.08*inch))
            continue

        # Main Section Heading (## )
        if line_stripped.startswith('## '):
            heading_text = line_stripped.replace('##', '').strip()
            # Remove numbering like "1. ", "2. " from headings
            heading_text = re.sub(r'^\d+\.\s*', '', heading_text)
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph(heading_text.upper(), section_heading_style))

        # Sub-heading (**text**)
        elif line_stripped.startswith('**') and line_stripped.endswith('**'):
            subheading_text = line_stripped.replace('**', '').strip()
            elements.append(Paragraph(subheading_text, subheading_style))

        # Bullet points with dash
        elif line_stripped.startswith('- '):
            bullet_text = line_stripped[2:].strip()
            # Clean up markdown bold using regex
            bullet_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', bullet_text)
            # Use teal colored bullet
            elements.append(Paragraph(f'<font color="#008B8B">●</font> {bullet_text}', bullet_style))

        # Bullet points with asterisk
        elif line_stripped.startswith('* '):
            bullet_text = line_stripped[2:].strip()
            # Clean up markdown bold using regex
            bullet_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', bullet_text)
            # Use teal colored bullet
            elements.append(Paragraph(f'<font color="#008B8B">●</font> {bullet_text}', bullet_style))

        # Numbered lists (1. 2. 3. etc.)
        elif re.match(r'^\d+\.\s+', line_stripped):
            # Clean up markdown formatting in numbered lists too
            numbered_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line_stripped)
            elements.append(Paragraph(numbered_text, bullet_style))

        # Regular paragraph
        else:
            # Process inline markdown formatting
            paragraph_text = line_stripped
            # Bold text
            paragraph_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', paragraph_text)
            # Italic text
            paragraph_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', paragraph_text)

            elements.append(Paragraph(paragraph_text, body_style))

    # ========== ADD FOOTER ==========
    elements.append(Spacer(1, 0.5*inch))

    footer_line = Table([['']], colWidths=[6.5*inch])
    footer_line.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#CCCCCC')),
    ]))
    elements.append(footer_line)

    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#999999'),
        alignment=TA_CENTER,
        spaceAfter=5
    )

    # Add eazr branding in footer
    eazr_footer_style = ParagraphStyle(
        'EazrFooter',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#008B8B'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=4
    )

    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph("eazr - Insurance Gap Analysis Platform", eazr_footer_style))
    elements.append(Paragraph("This comprehensive analysis report should be reviewed by a certified insurance advisor.", footer_style))
    elements.append(Paragraph("For questions or clarifications, please consult with your insurance provider or IRDAI-registered advisor.", footer_style))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
