"""
Travel Insurance Policy Analysis Report Generator
Based on EAZR_Travel_Insurance_Analysis_Template_V9.md
Modern, Sophisticated & Human-Advisory Style Report

Covers:
- Trip Details
- What You Actually Bought
- Medical Cover Assessment
- Pre-Existing Conditions
- Adventure Activities Coverage
- Trip Protection (Cancellation, Interruption, Delay)
- Baggage Coverage
- Schengen Compliance (if applicable)
- Full Exclusions List
- Claim Vulnerabilities
- My Assessment
- What You Should Do
- How to Claim - Emergency Guide
"""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, HRFlowable, KeepTogether, ListFlowable, ListItem
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)

# ==================== MODERN COLOR PALETTE ====================
BRAND_PRIMARY = colors.HexColor('#00847E')
BRAND_SECONDARY = colors.HexColor('#00A99D')
BRAND_DARK = colors.HexColor('#004D47')
BRAND_LIGHT = colors.HexColor('#E8F5F4')
BRAND_LIGHTER = colors.HexColor('#F0FAF9')

CHARCOAL = colors.HexColor('#1A1A2E')
SLATE = colors.HexColor('#374151')
MEDIUM_GRAY = colors.HexColor('#6B7280')
LIGHT_GRAY = colors.HexColor('#9CA3AF')
WHISPER = colors.HexColor('#F9FAFB')
BORDER_LIGHT = colors.HexColor('#E5E7EB')
WHITE = colors.HexColor('#FFFFFF')

SUCCESS_GREEN = colors.HexColor('#059669')
SUCCESS_LIGHT = colors.HexColor('#D1FAE5')
WARNING_AMBER = colors.HexColor('#D97706')
WARNING_LIGHT = colors.HexColor('#FEF3C7')
DANGER_RED = colors.HexColor('#DC2626')
DANGER_LIGHT = colors.HexColor('#FEE2E2')
INFO_BLUE = colors.HexColor('#2563EB')
INFO_LIGHT = colors.HexColor('#DBEAFE')

# ==================== V10 TRAVEL-SPECIFIC COLORS ====================
TRAVEL_INTL_BADGE = colors.HexColor('#6366F1')     # Indigo
TRAVEL_DOMESTIC_BADGE = colors.HexColor('#14B8A6')  # Teal
SCHENGEN_COMPLIANT_CLR = colors.HexColor('#22C55E')  # Green
SCHENGEN_NONCOMPLIANT_CLR = colors.HexColor('#EF4444')  # Red
COVERAGE_COVERED_CLR = colors.HexColor('#22C55E')    # Green
COVERAGE_NOT_COVERED_CLR = colors.HexColor('#EF4444')  # Red
COVERAGE_LIMITED_CLR = colors.HexColor('#EAB308')    # Yellow
EMERGENCY_BG = colors.HexColor('#1E293B')            # Dark navy
EMERGENCY_TEXT = colors.HexColor('#FFFFFF')           # White
EMERGENCY_ACCENT = colors.HexColor('#38BDF8')        # Sky blue
SCORE_EXCELLENT = colors.HexColor('#22C55E')
SCORE_STRONG = colors.HexColor('#84CC16')
SCORE_ADEQUATE = colors.HexColor('#EAB308')
SCORE_BASIC = colors.HexColor('#F97316')
SCORE_LOW = colors.HexColor('#6B7280')

# ==================== FONT CONFIGURATION ====================
FONT_REGULAR = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'
FONT_ITALIC = 'Helvetica-Oblique'
RUPEE_SYMBOL = 'Rs.'
USD_SYMBOL = '$'

try:
    font_paths = [
        "/System/Library/Fonts/Supplemental/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:\\Windows\\Fonts\\DejaVuSans.ttf",
        "/Library/Fonts/DejaVuSans.ttf",
    ]
    for font_path in font_paths:
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
            bold_path = font_path.replace('.ttf', '-Bold.ttf')
            if os.path.exists(bold_path):
                pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', bold_path))
                FONT_BOLD = 'DejaVuSans-Bold'
            else:
                FONT_BOLD = 'DejaVuSans'
            FONT_REGULAR = 'DejaVuSans'
            RUPEE_SYMBOL = '₹'
            break
except Exception as e:
    logger.warning(f"Could not register Unicode font: {e}")


def format_currency(value, currency='INR', show_symbol=True):
    """Format currency with proper symbol and commas"""
    if value is None or value == 'N/A' or value == '' or value == 0:
        return 'N/A'
    try:
        val = int(float(str(value).replace(',', '').replace('$', '').replace('₹', '').replace('Rs.', '').strip()))
        formatted = f"{val:,}"
        if show_symbol:
            if currency == 'USD':
                return f"${formatted}"
            else:
                return f"{RUPEE_SYMBOL}{formatted}"
        return formatted
    except (ValueError, TypeError):
        return str(value) if value else 'N/A'


def safe_int(value, default=0):
    """Safely convert value to int"""
    if value is None or value == 'N/A' or value == '':
        return default
    try:
        return int(float(str(value).replace(',', '').replace('$', '').replace('₹', '').replace('Rs.', '').strip()))
    except (ValueError, TypeError):
        return default


def safe_str(value, default='N/A'):
    """Safely convert value to string"""
    if value is None or value == '' or value == 'N/A':
        return default
    return str(value)


def get_score_color(score):
    if score >= 80:
        return SUCCESS_GREEN
    elif score >= 60:
        return WARNING_AMBER
    else:
        return DANGER_RED


def get_score_bg_color(score):
    if score >= 80:
        return SUCCESS_LIGHT
    elif score >= 60:
        return WARNING_LIGHT
    else:
        return DANGER_LIGHT


def get_travel_claims_helpline(insurer_name: str) -> str:
    """Get claims helpline number for travel insurance providers"""
    if not insurer_name or insurer_name == 'N/A':
        return "See policy document"

    insurer_lower = insurer_name.lower()

    helplines = {
        'hdfc ergo': '1800-266-0700',
        'hdfc': '1800-266-0700',
        'icici lombard': '1800-266-7766',
        'icici': '1800-266-7766',
        'bajaj allianz': '1800-209-5858',
        'bajaj': '1800-209-5858',
        'tata aig': '1800-266-7780',
        'tata': '1800-266-7780',
        'new india': '1800-209-1415',
        'oriental': '1800-118-485',
        'united india': '1800-425-3333',
        'national': '1800-220-430',
        'sbi general': '1800-22-1111',
        'sbi': '1800-22-1111',
        'reliance': '1800-102-0101',
        'kotak': '1800-266-6665',
        'royal sundaram': '1800-568-9999',
        'sundaram': '1800-568-9999',
        'future generali': '1800-220-233',
        'iffco tokio': '1800-103-5499',
        'cholamandalam': '1800-103-6040',
        'chola ms': '1800-103-6040',
        'bharti axa': '1800-102-4444',
        'digit': '1800-258-5956',
        'acko': '1800-266-2256',
        'go digit': '1800-258-5956',
        'care': '1800-102-4488',
        'star': '1800-425-2255',
    }

    for key, number in helplines.items():
        if key in insurer_lower:
            return number

    return "See policy document"


def get_destination_healthcare_costs(destination: str) -> dict:
    """Get typical healthcare costs for different destinations"""
    if not destination:
        destination = 'europe'

    destination_lower = destination.lower()

    # USA - Most expensive
    if any(x in destination_lower for x in ['usa', 'united states', 'america', 'us']):
        return {
            'region': 'USA',
            'er_visit': '$500 - $3,000',
            'hospital_day': '$3,000 - $5,000',
            'icu_day': '$5,000 - $10,000',
            'appendix_surgery': '$30,000 - $50,000',
            'cardiac_treatment': '$50,000 - $150,000',
            'fracture_treatment': '$5,000 - $15,000',
            'air_ambulance': '$50,000 - $100,000',
            'recommended_cover': 250000,  # USD
            'tier': 'Very High Cost'
        }

    # UK
    elif any(x in destination_lower for x in ['uk', 'united kingdom', 'england', 'britain']):
        return {
            'region': 'UK',
            'er_visit': '£150 - £500',
            'hospital_day': '£1,000 - £2,500',
            'icu_day': '£2,500 - $5,000',
            'appendix_surgery': '£10,000 - £20,000',
            'cardiac_treatment': '£20,000 - £50,000',
            'fracture_treatment': '£2,000 - £8,000',
            'air_ambulance': '£30,000 - £60,000',
            'recommended_cover': 100000,  # USD equivalent
            'tier': 'High Cost'
        }

    # Europe / Schengen
    elif any(x in destination_lower for x in ['europe', 'schengen', 'germany', 'france', 'italy', 'spain', 'netherlands', 'belgium', 'austria', 'switzerland', 'portugal', 'greece']):
        return {
            'region': 'Europe/Schengen',
            'er_visit': '€200 - €800',
            'hospital_day': '€1,000 - €2,000',
            'icu_day': '€2,000 - €4,000',
            'appendix_surgery': '€8,000 - €15,000',
            'cardiac_treatment': '€15,000 - €40,000',
            'fracture_treatment': '€1,500 - €5,000',
            'air_ambulance': '€25,000 - €50,000',
            'recommended_cover': 50000,  # USD - Schengen minimum €30,000
            'tier': 'Moderate-High Cost'
        }

    # Australia / New Zealand
    elif any(x in destination_lower for x in ['australia', 'new zealand', 'aus', 'nz']):
        return {
            'region': 'Australia/NZ',
            'er_visit': 'A$300 - $1,000',
            'hospital_day': 'A$1,500 - $3,000',
            'icu_day': 'A$3,000 - $6,000',
            'appendix_surgery': 'A$15,000 - $25,000',
            'cardiac_treatment': 'A$30,000 - $80,000',
            'fracture_treatment': 'A$3,000 - $10,000',
            'air_ambulance': 'A$30,000 - $60,000',
            'recommended_cover': 100000,  # USD
            'tier': 'High Cost'
        }

    # Southeast Asia
    elif any(x in destination_lower for x in ['thailand', 'singapore', 'malaysia', 'indonesia', 'vietnam', 'philippines', 'bali', 'southeast asia']):
        return {
            'region': 'Southeast Asia',
            'er_visit': '$100 - $500',
            'hospital_day': '$300 - $1,000',
            'icu_day': '$500 - $2,000',
            'appendix_surgery': '$3,000 - $8,000',
            'cardiac_treatment': '$10,000 - $30,000',
            'fracture_treatment': '$500 - $3,000',
            'air_ambulance': '$15,000 - $40,000',
            'recommended_cover': 50000,  # USD
            'tier': 'Moderate Cost'
        }

    # Middle East (Dubai, UAE)
    elif any(x in destination_lower for x in ['dubai', 'uae', 'abu dhabi', 'qatar', 'saudi', 'middle east']):
        return {
            'region': 'Middle East',
            'er_visit': '$300 - $1,000',
            'hospital_day': '$1,000 - $2,500',
            'icu_day': '$2,000 - $5,000',
            'appendix_surgery': '$10,000 - $20,000',
            'cardiac_treatment': '$25,000 - $60,000',
            'fracture_treatment': '$2,000 - $8,000',
            'air_ambulance': '$25,000 - $50,000',
            'recommended_cover': 100000,  # USD
            'tier': 'High Cost'
        }

    # Default - Rest of World
    else:
        return {
            'region': 'International',
            'er_visit': '$200 - $800',
            'hospital_day': '$500 - $1,500',
            'icu_day': '$1,000 - $3,000',
            'appendix_surgery': '$5,000 - $15,000',
            'cardiac_treatment': '$15,000 - $40,000',
            'fracture_treatment': '$1,000 - $5,000',
            'air_ambulance': '$20,000 - $50,000',
            'recommended_cover': 50000,  # USD
            'tier': 'Moderate Cost'
        }


def is_schengen_country(destination: str) -> bool:
    """Check if destination is a Schengen country"""
    if not destination:
        return False

    schengen_countries = [
        'austria', 'belgium', 'czech', 'czechia', 'denmark', 'estonia', 'finland',
        'france', 'germany', 'greece', 'hungary', 'iceland', 'italy', 'latvia',
        'liechtenstein', 'lithuania', 'luxembourg', 'malta', 'netherlands', 'norway',
        'poland', 'portugal', 'slovakia', 'slovenia', 'spain', 'sweden', 'switzerland',
        'schengen', 'europe'
    ]

    destination_lower = destination.lower()
    return any(country in destination_lower for country in schengen_countries)


class ModernHeader:
    @staticmethod
    def draw(canvas, doc_template):
        canvas.saveState()
        canvas.setFillColor(BRAND_PRIMARY)
        canvas.rect(0, A4[1] - 0.6*inch, A4[0], 0.6*inch, fill=True, stroke=False)

        canvas.setFont(FONT_BOLD, 18)
        canvas.setFillColor(WHITE)
        canvas.drawString(0.6*inch, A4[1] - 0.4*inch, "EAZR")

        canvas.setFont(FONT_REGULAR, 8)
        canvas.setFillColor(colors.HexColor('#B0E0DC'))
        canvas.drawString(0.6*inch, A4[1] - 0.52*inch, "Travel Insurance Analysis")

        canvas.setFont(FONT_REGULAR, 8)
        canvas.setFillColor(WHITE)
        canvas.drawRightString(A4[0] - 0.6*inch, A4[1] - 0.4*inch, f"Page {doc_template.page}")

        canvas.restoreState()


class ModernFooter:
    @staticmethod
    def draw(canvas, doc_template):
        canvas.saveState()
        canvas.setStrokeColor(BORDER_LIGHT)
        canvas.setLineWidth(0.5)
        canvas.line(0.6*inch, 0.5*inch, A4[0] - 0.6*inch, 0.5*inch)

        canvas.setFont(FONT_REGULAR, 7)
        canvas.setFillColor(LIGHT_GRAY)
        canvas.drawString(0.6*inch, 0.35*inch, "EAZR Policy Analysis | Clarity Before Crisis")
        canvas.drawRightString(A4[0] - 0.6*inch, 0.35*inch, f"Generated: {datetime.now().strftime('%d %b %Y')}")

        canvas.restoreState()


def on_page(canvas, doc):
    ModernHeader.draw(canvas, doc)
    ModernFooter.draw(canvas, doc)


def create_styles():
    """Create modern paragraph styles"""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'main_title',
        parent=styles['Heading1'],
        fontName=FONT_BOLD,
        fontSize=22,
        textColor=BRAND_DARK,
        spaceAfter=6,
        alignment=TA_LEFT,
        leading=26
    ))

    styles.add(ParagraphStyle(
        'subtitle',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=11,
        textColor=MEDIUM_GRAY,
        spaceAfter=16,
        alignment=TA_LEFT
    ))

    styles.add(ParagraphStyle(
        'section_header',
        parent=styles['Heading2'],
        fontName=FONT_BOLD,
        fontSize=14,
        textColor=BRAND_DARK,
        spaceBefore=16,
        spaceAfter=10,
        borderPadding=(0, 0, 0, 8),
        alignment=TA_LEFT
    ))

    styles.add(ParagraphStyle(
        'subsection_header',
        parent=styles['Heading3'],
        fontName=FONT_BOLD,
        fontSize=11,
        textColor=CHARCOAL,
        spaceBefore=12,
        spaceAfter=6,
        alignment=TA_LEFT
    ))

    styles.add(ParagraphStyle(
        'body',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=9,
        textColor=SLATE,
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        leading=14
    ))

    styles.add(ParagraphStyle(
        'body_emphasis',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=9,
        textColor=CHARCOAL,
        spaceAfter=4,
        alignment=TA_LEFT
    ))

    styles.add(ParagraphStyle(
        'advisory_intro',
        parent=styles['Normal'],
        fontName=FONT_ITALIC,
        fontSize=10,
        textColor=MEDIUM_GRAY,
        spaceAfter=12,
        alignment=TA_LEFT,
        leading=15
    ))

    styles.add(ParagraphStyle(
        'warning_text',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=9,
        textColor=DANGER_RED,
        spaceAfter=6,
        alignment=TA_LEFT
    ))

    styles.add(ParagraphStyle(
        'success_text',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=9,
        textColor=SUCCESS_GREEN,
        spaceAfter=6,
        alignment=TA_LEFT
    ))

    styles.add(ParagraphStyle(
        'highlight_text',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=9,
        textColor=CHARCOAL,
        spaceBefore=4,
        spaceAfter=4,
        leftIndent=10,
        rightIndent=10,
        leading=13
    ))

    return styles


def create_section_header(title, styles):
    """Create a section header with accent bar"""
    header_table = Table(
        [[Paragraph(title, styles['section_header'])]],
        colWidths=[6.3*inch]
    )
    header_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEABOVE', (0, 0), (-1, 0), 3, BRAND_PRIMARY),
        ('BACKGROUND', (0, 0), (-1, -1), BRAND_LIGHTER),
    ]))
    return header_table


def create_subsection_header(title):
    """Create a subsection header"""
    return Paragraph(f"<b>{title}</b>", ParagraphStyle(
        'subsection',
        fontName=FONT_BOLD,
        fontSize=10,
        textColor=CHARCOAL,
        spaceBefore=10,
        spaceAfter=6
    ))


def create_highlight_box(text, bg_color, border_color):
    """Create a highlighted info/warning box"""
    style = ParagraphStyle(
        'highlight',
        fontName=FONT_REGULAR,
        fontSize=9,
        textColor=CHARCOAL,
        leading=13
    )
    content = [[Paragraph(text, style)]]
    table = Table(content, colWidths=[6.2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_color),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LINEABOVE', (0, 0), (-1, 0), 2, border_color),
        ('BOX', (0, 0), (-1, -1), 0.5, border_color),
    ]))
    return table


def create_modern_table(data, col_widths, header_bg=BRAND_PRIMARY, alt_rows=True):
    """Create a modern styled table with optional alternating rows"""
    table = Table(data, colWidths=col_widths)
    style_commands = [
        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('FONTNAME', (0, 1), (-1, -1), FONT_REGULAR),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('TEXTCOLOR', (0, 1), (-1, -1), CHARCOAL),
        ('BACKGROUND', (0, 0), (-1, 0), header_bg),
        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, 0), 1, header_bg),
    ]

    if alt_rows and len(data) > 1:
        for i in range(1, len(data)):
            if i % 2 == 0:
                style_commands.append(('BACKGROUND', (0, i), (-1, i), WHISPER))
            else:
                style_commands.append(('BACKGROUND', (0, i), (-1, i), WHITE))

    style_commands.append(('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT))
    style_commands.append(('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT))

    table.setStyle(TableStyle(style_commands))
    return table


def create_key_value_table(data, col_widths, accent_color=BRAND_PRIMARY):
    """Create a key-value style table"""
    table = Table(data, colWidths=col_widths)
    style_commands = [
        ('FONTNAME', (0, 0), (-1, -1), FONT_REGULAR),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), MEDIUM_GRAY),
        ('TEXTCOLOR', (1, 0), (1, -1), CHARCOAL),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEABOVE', (0, 0), (-1, 0), 2, accent_color),
        ('LINEBELOW', (0, -1), (-1, -1), 0.5, BORDER_LIGHT),
        ('BACKGROUND', (0, 0), (-1, -1), WHISPER),
    ]
    table.setStyle(TableStyle(style_commands))
    return table


def create_info_card(items, accent_color):
    """Create an info card with key details"""
    data = [[item[0], item[1]] for item in items]
    return create_key_value_table(data, [2.5*inch, 3.5*inch], accent_color)


def generate_travel_insurance_report(policy_data: dict, analysis_data: dict) -> BytesIO:
    """Router: dispatch to V10 or V9 report generator based on analysis data."""
    if (analysis_data.get("analysisVersion") == "10.0" and
            analysis_data.get("protectionReadiness") and
            isinstance(analysis_data.get("protectionReadiness"), dict)):
        try:
            return _generate_travel_report_v10(policy_data, analysis_data)
        except Exception as e:
            logger.warning(f"V10 travel report failed, falling back to V9: {e}", exc_info=True)
    return _generate_travel_report_v9(policy_data, analysis_data)


def _generate_travel_report_v9(policy_data: dict, analysis_data: dict) -> BytesIO:
    """
    Generate a comprehensive travel insurance analysis report based on V9 template.
    Uses KeepTogether to prevent page-break issues with tables.
    """
    try:
        buffer = BytesIO()
        pdf_doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=0.6*inch, leftMargin=0.6*inch,
            topMargin=0.85*inch, bottomMargin=0.7*inch,
            title="Travel Insurance Policy Analysis",
            author="EAZR Insurance Platform"
        )

        elements = []
        styles = create_styles()

        # ==================== EXTRACT ALL DATA ====================
        policy_number = policy_data.get('policyNumber', 'N/A')
        insurer_name = policy_data.get('insuranceProvider', 'N/A')
        policy_holder_name = policy_data.get('policyHolderName', 'Dear Policyholder')
        first_name = policy_holder_name.split()[0] if policy_holder_name and policy_holder_name != 'N/A' else 'there'

        # Remove common prefixes
        if first_name.lower() in ['mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'shri', 'smt']:
            parts = policy_holder_name.split()
            first_name = parts[1] if len(parts) > 1 else 'there'

        premium = safe_int(policy_data.get('premium', 0))
        start_date = policy_data.get('startDate', 'N/A')
        end_date = policy_data.get('endDate', 'N/A')

        category_data = policy_data.get('categorySpecificData', {})
        policy_identification = category_data.get('policyIdentification', {})
        trip_details = category_data.get('tripDetails', {})
        traveller_details = category_data.get('travellerDetails', [])
        coverage_summary = category_data.get('coverageSummary', {})
        exclusions_data = category_data.get('exclusions', {})
        emergency_contacts = category_data.get('emergencyContacts', {})
        premium_data = category_data.get('premium', {})

        # Analysis data
        protection_score = safe_int(analysis_data.get('protectionScore', 70))
        protection_label = analysis_data.get('protectionScoreLabel', 'Adequate Coverage')

        # Extract coverage gaps - try 'coverageGaps' first, then fallback to 'keyConcerns' for backward compatibility
        coverage_gaps_data = analysis_data.get('coverageGaps', {})
        if isinstance(coverage_gaps_data, dict):
            key_concerns = coverage_gaps_data.get('gaps', [])
        else:
            key_concerns = []
        # Fallback to keyConcerns if coverageGaps is empty
        if not key_concerns:
            key_concerns = analysis_data.get('keyConcerns', [])

        policy_strengths = analysis_data.get('policyStrengths', [])

        # Extract recommendations - try multiple keys for flexibility
        recommendations = analysis_data.get('whatYouShouldDo', {})
        if not recommendations:
            recommendations = analysis_data.get('recommendations', [])
        if not recommendations and isinstance(coverage_gaps_data, dict):
            recommendations = coverage_gaps_data.get('recommendations', [])

        # Trip details
        plan_name = policy_identification.get('productName', policy_data.get('policyType', 'Travel Insurance'))
        trip_type = policy_identification.get('tripType') or trip_details.get('tripType', 'Single Trip')
        destination_countries = trip_details.get('destinationCountries', [])
        if isinstance(destination_countries, list):
            destination = ', '.join(destination_countries) if destination_countries else 'International'
        else:
            destination = str(destination_countries) if destination_countries else 'International'

        trip_start = trip_details.get('tripStartDate', start_date)
        trip_end = trip_details.get('tripEndDate', end_date)
        trip_duration = trip_details.get('tripDuration', 'N/A')
        trip_purpose = trip_details.get('purposeOfTravel', 'Leisure')

        # Coverage amounts
        medical_cover = safe_int(coverage_summary.get('medicalExpenses', 0))
        evacuation_cover = safe_int(coverage_summary.get('emergencyMedicalEvacuation', 0))
        trip_cancel_cover = safe_int(coverage_summary.get('tripCancellation', 0))
        trip_delay_cover = safe_int(coverage_summary.get('tripDelay') or coverage_summary.get('flightDelay', 0))
        baggage_loss_cover = safe_int(coverage_summary.get('baggageLoss', 0))
        baggage_delay_cover = safe_int(coverage_summary.get('baggageDelay', 0))
        pa_cover = safe_int(coverage_summary.get('accidentalDeath') or coverage_summary.get('personalAccident', 0))
        liability_cover = safe_int(coverage_summary.get('personalLiability', 0))

        # Get destination healthcare costs
        destination_costs = get_destination_healthcare_costs(destination)
        is_schengen = is_schengen_country(destination)

        # Get helpline
        claims_helpline = get_travel_claims_helpline(insurer_name)
        emergency_helpline = emergency_contacts.get('emergencyHelpline24x7', claims_helpline)
        claims_email = emergency_contacts.get('claimsEmail', 'See policy document')

        # ==================== TITLE PAGE ====================
        elements.append(Paragraph("Travel Insurance Policy Analysis", styles['main_title']))
        elements.append(Paragraph(f"Prepared for {policy_holder_name}", styles['subtitle']))
        elements.append(Paragraph(f"Trip: {destination} ({trip_start} to {trip_end})", styles['subtitle']))
        elements.append(Paragraph(f"Policy: {insurer_name} - {plan_name}", styles['subtitle']))
        elements.append(Spacer(1, 0.2*inch))

        # ==================== ADVISORY INTRO ====================
        intro_text = f"""
        {first_name}, I've reviewed your travel insurance policy in detail. This analysis is not a summary of your
        policy document - you already have that. This is my assessment of what this policy will actually pay if
        something goes wrong abroad, where the hidden exclusions lie, and whether you're adequately covered for this trip.

        Medical emergencies abroad can be financially devastating. A week in a US hospital can cost {RUPEE_SYMBOL}50 Lakhs to
        {RUPEE_SYMBOL}1 Crore. I'd rather you discover any gaps in your cover now - not when you're lying in a foreign hospital.
        """
        elements.append(Paragraph(intro_text, styles['advisory_intro']))
        elements.append(Spacer(1, 0.15*inch))

        # ==================== YOUR TRIP DETAILS ====================
        elements.append(create_section_header("Your Trip Details", styles))
        elements.append(Spacer(1, 0.1*inch))

        trip_info = [
            ("Traveler(s)", policy_holder_name),
            ("Destination", f"{destination} ({destination_costs['region']})"),
            ("Travel Dates", f"{trip_start} to {trip_end}"),
            ("Duration", f"{trip_duration} days" if trip_duration != 'N/A' else "See policy"),
            ("Trip Purpose", trip_purpose),
            ("Trip Type", trip_type),
        ]
        elements.append(create_info_card(trip_info, BRAND_PRIMARY))
        elements.append(Spacer(1, 0.15*inch))

        # Travelers list if multiple
        if traveller_details and len(traveller_details) > 0:
            elements.append(create_subsection_header("Members Covered"))
            traveler_data = [["Name", "Age", "Relationship"]]
            for traveler in traveller_details:
                if isinstance(traveler, dict):
                    name = traveler.get('name', traveler.get('travellerName', 'N/A'))
                    age = str(traveler.get('age', traveler.get('travellerAge', 'N/A')))
                    relationship = traveler.get('relationship', traveler.get('travellerRelationship', 'N/A'))
                    traveler_data.append([name, age, relationship])

            if len(traveler_data) > 1:
                traveler_table = create_modern_table(traveler_data, [2.5*inch, 1.2*inch, 2.5*inch])
                elements.append(traveler_table)
                elements.append(Spacer(1, 0.15*inch))

        # Protection Score
        score_color = get_score_color(protection_score)
        score_bg = get_score_bg_color(protection_score)
        score_text = f"<b>Protection Score: {protection_score}/100 - {protection_label}</b>"
        elements.append(create_highlight_box(score_text, score_bg, score_color))
        elements.append(Spacer(1, 0.2*inch))

        # ==================== WHAT YOU ACTUALLY BOUGHT ====================
        elements.append(create_section_header("What You Actually Bought", styles))
        elements.append(Spacer(1, 0.1*inch))

        elements.append(Paragraph(
            f"Your policy is a <b>{trip_type}</b> travel insurance plan covering your trip to {destination}.",
            styles['body']
        ))
        elements.append(Spacer(1, 0.1*inch))

        elements.append(create_subsection_header("Your Coverage at a Glance"))

        # Coverage adequacy assessment
        def get_adequacy_emoji(amount, recommended):
            if amount >= recommended:
                return "Adequate"
            elif amount >= recommended * 0.5:
                return "Moderate"
            else:
                return "Low"

        recommended_medical = destination_costs['recommended_cover']

        coverage_data = [
            ["Benefit", "Cover Amount", "Assessment"],
            ["Medical Expenses", format_currency(medical_cover, 'USD'), get_adequacy_emoji(medical_cover, recommended_medical)],
            ["Emergency Evacuation", format_currency(evacuation_cover, 'USD'), get_adequacy_emoji(evacuation_cover, 50000)],
            ["Trip Cancellation", format_currency(trip_cancel_cover), get_adequacy_emoji(trip_cancel_cover, 100000)],
            ["Trip/Flight Delay", format_currency(trip_delay_cover), "Standard" if trip_delay_cover > 0 else "Not covered"],
            ["Baggage Loss", format_currency(baggage_loss_cover), get_adequacy_emoji(baggage_loss_cover, 50000)],
            ["Baggage Delay", format_currency(baggage_delay_cover), "Standard" if baggage_delay_cover > 0 else "Not covered"],
            ["Personal Accident", format_currency(pa_cover), get_adequacy_emoji(pa_cover, 1000000)],
            ["Personal Liability", format_currency(liability_cover), get_adequacy_emoji(liability_cover, 500000)],
        ]
        coverage_table = create_modern_table(coverage_data, [2.2*inch, 2*inch, 2*inch])
        elements.append(KeepTogether([coverage_table]))
        elements.append(Spacer(1, 0.2*inch))

        # ==================== MEDICAL COVER - THE MOST CRITICAL PART ====================
        elements.append(create_section_header("Medical Cover - The Most Critical Part", styles))
        elements.append(Spacer(1, 0.1*inch))

        elements.append(Paragraph(
            "If you're hospitalized abroad, this is what saves you from financial ruin. Let me assess whether your cover is adequate.",
            styles['body']
        ))
        elements.append(Spacer(1, 0.1*inch))

        elements.append(create_subsection_header(f"Healthcare Costs at Your Destination ({destination_costs['region']})"))

        healthcare_data = [
            ["Treatment", f"Typical Cost in {destination_costs['region']}"],
            ["Emergency room visit", destination_costs['er_visit']],
            ["Hospital stay (per day)", destination_costs['hospital_day']],
            ["ICU (per day)", destination_costs['icu_day']],
            ["Appendix surgery", destination_costs['appendix_surgery']],
            ["Heart attack treatment", destination_costs['cardiac_treatment']],
            ["Fracture treatment", destination_costs['fracture_treatment']],
            ["Air ambulance evacuation", destination_costs['air_ambulance']],
        ]
        healthcare_table = create_modern_table(healthcare_data, [3*inch, 3.2*inch])
        elements.append(KeepTogether([healthcare_table]))
        elements.append(Spacer(1, 0.15*inch))

        # Medical Cover Assessment
        elements.append(create_subsection_header("Your Medical Cover Assessment"))

        medical_gap = recommended_medical - medical_cover if medical_cover < recommended_medical else 0
        medical_assessment_data = [
            ("Your medical cover", format_currency(medical_cover, 'USD')),
            (f"Recommended minimum for {destination_costs['region']}", format_currency(recommended_medical, 'USD')),
            ("Gap", format_currency(medical_gap, 'USD') if medical_gap > 0 else "None - Adequate"),
        ]
        elements.append(create_info_card(medical_assessment_data, BRAND_PRIMARY))
        elements.append(Spacer(1, 0.1*inch))

        # Medical cover warning if inadequate
        if medical_cover < recommended_medical:
            warning_text = f"""
            <b>Your medical cover may be insufficient for {destination_costs['region']}.</b>

            A serious hospitalization in {destination_costs['region']} can easily exceed ${medical_cover:,}. If your cover is exhausted:
            - Hospital may demand advance payment to continue treatment
            - You may be transferred to a lower-quality facility
            - Remaining bills become your responsibility

            Consider: Is this risk acceptable for a {trip_duration if trip_duration != 'N/A' else 'your'}-day trip?
            """
            elements.append(create_highlight_box(warning_text, WARNING_LIGHT, WARNING_AMBER))
        else:
            success_text = f"Your medical cover of ${medical_cover:,} is adequate for {destination_costs['region']}. You have sufficient protection for most medical emergencies."
            elements.append(create_highlight_box(success_text, SUCCESS_LIGHT, SUCCESS_GREEN))
        elements.append(Spacer(1, 0.15*inch))

        # Emergency Evacuation
        elements.append(create_subsection_header("Emergency Evacuation"))
        evac_data = [
            ("Your evacuation cover", format_currency(evacuation_cover, 'USD')),
            ("Air ambulance to India (estimate)", "$50,000 - $100,000"),
            ("Medical escort flight (estimate)", "$20,000 - $50,000"),
        ]
        elements.append(create_info_card(evac_data, INFO_BLUE))
        elements.append(Spacer(1, 0.1*inch))

        if evacuation_cover < 50000:
            evac_warning = "Your evacuation cover may be insufficient. If you need emergency evacuation to India or to a better hospital, costs can exceed your cover. The difference comes from your pocket."
            elements.append(create_highlight_box(evac_warning, WARNING_LIGHT, WARNING_AMBER))
        elements.append(Spacer(1, 0.2*inch))

        # ==================== SCHENGEN COMPLIANCE (if applicable) ====================
        if is_schengen:
            elements.append(create_section_header("Schengen Visa Compliance", styles))
            elements.append(Spacer(1, 0.1*inch))

            elements.append(Paragraph(
                f"You're traveling to {destination}, which is part of the Schengen area. Your travel insurance must meet specific requirements for visa approval.",
                styles['body']
            ))
            elements.append(Spacer(1, 0.1*inch))

            # Schengen minimum is €30,000 ≈ $33,000
            schengen_min_usd = 33000
            medical_eur = int(medical_cover * 0.92)  # Approximate EUR

            schengen_medical_ok = medical_cover >= schengen_min_usd

            elements.append(create_subsection_header("Schengen Requirements Checklist"))

            schengen_data = [
                ["Requirement", "Your Policy", "Status"],
                ["Min €30,000 medical cover", f"€{medical_eur:,} (${medical_cover:,})", "Compliant" if schengen_medical_ok else "NON-COMPLIANT"],
                ["Covers all Schengen countries", "Yes (typically)", "Check policy"],
                ["Covers emergency repatriation", format_currency(evacuation_cover, 'USD'), "Compliant" if evacuation_cover > 0 else "Check policy"],
                ["Valid for entire trip duration", f"{trip_start} to {trip_end}", "Verify dates match visa"],
            ]
            schengen_table = create_modern_table(schengen_data, [2.5*inch, 2*inch, 1.7*inch])
            elements.append(KeepTogether([schengen_table]))
            elements.append(Spacer(1, 0.1*inch))

            if not schengen_medical_ok:
                schengen_warning = f"""
                <b>Your policy may NOT be Schengen compliant.</b>

                Issue: Medical cover of ${medical_cover:,} (€{medical_eur:,}) is below the Schengen minimum of €30,000.

                This could result in:
                - Visa rejection
                - Entry denial at border
                - Policy not valid for Schengen trip

                Consider upgrading your medical cover before applying for visa.
                """
                elements.append(create_highlight_box(schengen_warning, DANGER_LIGHT, DANGER_RED))
            else:
                schengen_ok = "Your policy appears to meet Schengen visa requirements. Verify that the policy dates cover your entire intended stay."
                elements.append(create_highlight_box(schengen_ok, SUCCESS_LIGHT, SUCCESS_GREEN))
            elements.append(Spacer(1, 0.2*inch))

        # ==================== TRIP PROTECTION COVERAGE ====================
        elements.append(create_section_header("Trip Protection Coverage", styles))
        elements.append(Spacer(1, 0.1*inch))

        # Trip Cancellation
        elements.append(create_subsection_header("Trip Cancellation"))
        cancel_data = [
            ("Cancellation cover", format_currency(trip_cancel_cover)),
            ("Coverage type", "Covered reasons only"),
        ]
        elements.append(create_info_card(cancel_data, BRAND_PRIMARY))
        elements.append(Spacer(1, 0.1*inch))

        elements.append(Paragraph("<b>What's typically covered (cancellation reasons):</b>", styles['body_emphasis']))
        covered_reasons = [
            "Serious illness/death of insured or immediate family",
            "Natural disasters at destination",
            "Visa rejection (if applied through proper channel)",
            "Jury duty / court summons",
        ]
        for reason in covered_reasons:
            elements.append(Paragraph(f"• {reason}", styles['body']))
        elements.append(Spacer(1, 0.1*inch))

        elements.append(Paragraph("<b>What's NOT covered:</b>", styles['body_emphasis']))
        not_covered_reasons = [
            "Change of mind",
            "Work commitments (unless specified)",
            "Fear of travel / terrorism concerns (unless travel advisory issued)",
            "Pre-existing conditions (unless covered)",
            "Pregnancy beyond specified weeks",
        ]
        for reason in not_covered_reasons:
            elements.append(Paragraph(f"• {reason}", styles['body']))
        elements.append(Spacer(1, 0.15*inch))

        # Trip Delay
        elements.append(create_subsection_header("Trip/Flight Delay"))
        delay_data = [
            ("Delay cover", format_currency(trip_delay_cover) if trip_delay_cover > 0 else "Check policy"),
            ("Typical threshold", "6-12 hours delay"),
        ]
        elements.append(create_info_card(delay_data, INFO_BLUE))
        elements.append(Spacer(1, 0.1*inch))

        elements.append(Paragraph(
            "<b>What you can typically claim:</b> Meals during delay, accommodation if overnight, essential purchases, communication costs. Documentation needed: Delay certificate from airline, receipts for expenses.",
            styles['body']
        ))
        elements.append(Spacer(1, 0.2*inch))

        # ==================== BAGGAGE COVERAGE ====================
        elements.append(create_section_header("Baggage Coverage", styles))
        elements.append(Spacer(1, 0.1*inch))

        elements.append(create_subsection_header("Baggage Loss"))
        baggage_data = [
            ("Total baggage cover", format_currency(baggage_loss_cover)),
            ("Per item limit (typical)", format_currency(min(baggage_loss_cover // 10, 20000)) if baggage_loss_cover > 0 else "Check policy"),
        ]
        elements.append(create_info_card(baggage_data, BRAND_PRIMARY))
        elements.append(Spacer(1, 0.1*inch))

        elements.append(Paragraph("<b>What's covered:</b>", styles['body_emphasis']))
        elements.append(Paragraph("• Checked baggage lost by airline", styles['body']))
        elements.append(Paragraph("• Baggage stolen (with police report)", styles['body']))
        elements.append(Paragraph("• Baggage damaged beyond repair", styles['body']))
        elements.append(Spacer(1, 0.05*inch))

        elements.append(Paragraph("<b>What's NOT covered:</b>", styles['body_emphasis']))
        elements.append(Paragraph("• Carry-on items left unattended", styles['body']))
        elements.append(Paragraph("• Valuables not declared", styles['body']))
        elements.append(Paragraph("• Electronics beyond specified limits", styles['body']))
        elements.append(Paragraph("• Cash, credit cards, tickets", styles['body']))
        elements.append(Spacer(1, 0.1*inch))

        if baggage_loss_cover > 0:
            baggage_tip = f"<b>Tip:</b> Your per-item limit may be around {format_currency(min(baggage_loss_cover // 10, 20000))}. If you're carrying expensive items (laptop, camera, jewelry), they may not be fully covered. Consider not carrying high-value items or declaring them for additional cover."
            elements.append(create_highlight_box(baggage_tip, INFO_LIGHT, INFO_BLUE))
        elements.append(Spacer(1, 0.1*inch))

        # Baggage Delay
        elements.append(create_subsection_header("Baggage Delay"))
        elements.append(Paragraph(
            f"Delay cover: {format_currency(baggage_delay_cover) if baggage_delay_cover > 0 else 'Check policy'}. Typical threshold: 12-24 hours. If your baggage is delayed, you can claim for essential purchases (clothes, toiletries). Keep all receipts.",
            styles['body']
        ))
        elements.append(Spacer(1, 0.2*inch))

        # ==================== WHAT'S NOT COVERED ====================
        elements.append(create_section_header("What's NOT Covered - Full Exclusions", styles))
        elements.append(Spacer(1, 0.1*inch))

        elements.append(Paragraph(
            "These are the things your policy explicitly will not pay for:",
            styles['body']
        ))
        elements.append(Spacer(1, 0.1*inch))

        elements.append(create_subsection_header("Medical Exclusions"))
        medical_exclusions = [
            ["Exclusion", "Details"],
            ["Pre-existing conditions", "Unless specifically covered with add-on"],
            ["Pregnancy (after cutoff)", "Routine pregnancy, childbirth, complications after specified weeks"],
            ["Mental health", "Psychiatric treatment, psychological conditions"],
            ["Dental (non-emergency)", "Routine dental work"],
            ["Cosmetic treatment", "Any elective procedures"],
            ["Self-inflicted injuries", "Suicide, self-harm"],
            ["Alcohol/drug related", "Intoxication, substance abuse"],
            ["Elective surgery", "Procedures that could wait until return"],
        ]
        medical_excl_table = create_modern_table(medical_exclusions, [2.5*inch, 3.7*inch])
        elements.append(KeepTogether([medical_excl_table]))
        elements.append(Spacer(1, 0.15*inch))

        elements.append(create_subsection_header("Trip Exclusions"))
        trip_exclusions = [
            ["Exclusion", "Details"],
            ["Change of mind", "Not wanting to travel"],
            ["Work commitments", "Unless specifically covered"],
            ["Missed flights (your fault)", "Late arrival at airport"],
            ["Government travel advisories", "Check specific terms"],
            ["War / civil unrest", "Unless specifically covered"],
            ["Natural disaster (some policies)", "Check specific terms"],
        ]
        trip_excl_table = create_modern_table(trip_exclusions, [2.5*inch, 3.7*inch])
        elements.append(KeepTogether([trip_excl_table]))
        elements.append(Spacer(1, 0.15*inch))

        elements.append(create_subsection_header("Activity Exclusions"))
        activity_exclusions = [
            ["Activity Type", "Status"],
            ["Professional sports", "Typically NOT covered"],
            ["Racing (any kind)", "Typically NOT covered"],
            ["Scuba diving (beyond limits)", "Check depth limits"],
            ["Skiing/snowboarding", "May need add-on"],
            ["Paragliding/parasailing", "Typically NOT covered"],
            ["Bungee jumping", "Typically NOT covered"],
            ["Mountain climbing (high altitude)", "Check altitude limits"],
        ]
        activity_excl_table = create_modern_table(activity_exclusions, [2.5*inch, 3.7*inch])
        elements.append(KeepTogether([activity_excl_table]))
        elements.append(Spacer(1, 0.1*inch))

        adventure_warning = "<b>Important:</b> If you're injured during an excluded activity, medical expenses are 100% out of pocket. A skiing accident can cost Rs.20-50 Lakhs in Europe. Verify your activities are covered before engaging in them."
        elements.append(create_highlight_box(adventure_warning, WARNING_LIGHT, WARNING_AMBER))
        elements.append(Spacer(1, 0.2*inch))

        # ==================== MY ASSESSMENT ====================
        elements.append(create_section_header("My Assessment", styles))
        elements.append(Spacer(1, 0.1*inch))

        # Overall verdict
        if protection_score >= 80:
            verdict_label = "WELL PROTECTED"
            verdict_color = SUCCESS_GREEN
            verdict_bg = SUCCESS_LIGHT
            verdict_text = "Your travel insurance provides comprehensive coverage for this trip. Medical cover is adequate for your destination, and essential protections are in place."
        elif protection_score >= 60:
            verdict_label = "ADEQUATELY COVERED WITH GAPS"
            verdict_color = WARNING_AMBER
            verdict_bg = WARNING_LIGHT
            verdict_text = "Your coverage handles most common scenarios but has some gaps that could be costly in specific situations. Review the concerns below."
        else:
            verdict_label = "ENHANCEMENT RECOMMENDED"
            verdict_color = DANGER_RED
            verdict_bg = DANGER_LIGHT
            verdict_text = "Your coverage has significant gaps that could leave you financially exposed. Strongly consider upgrading before your trip."

        verdict_box = f"<b>{verdict_label}</b><br/><br/>{verdict_text}"
        elements.append(create_highlight_box(verdict_box, verdict_bg, verdict_color))
        elements.append(Spacer(1, 0.15*inch))

        # Strengths
        if policy_strengths:
            elements.append(create_subsection_header("What This Policy Does Well"))
            for strength in policy_strengths[:4]:
                if isinstance(strength, str):
                    elements.append(Paragraph(f"✓ {strength}", styles['success_text']))
            elements.append(Spacer(1, 0.1*inch))

        # Concerns
        if key_concerns:
            elements.append(create_subsection_header("Where This Policy Falls Short"))
            for concern in key_concerns[:4]:
                if isinstance(concern, dict):
                    title = concern.get('title', 'Coverage Gap')
                    brief = concern.get('brief', '')
                    severity = concern.get('severity', 'medium')
                    severity_icon = "●" if severity == 'high' else "◐" if severity == 'medium' else "○"
                    elements.append(Paragraph(f"{severity_icon} <b>{title}:</b> {brief}", styles['body']))
                elif isinstance(concern, str):
                    elements.append(Paragraph(f"• {concern}", styles['body']))
            elements.append(Spacer(1, 0.1*inch))
        elements.append(Spacer(1, 0.2*inch))

        # ==================== WHAT YOU SHOULD DO ====================
        elements.append(create_section_header("What You Should Do", styles))
        elements.append(Spacer(1, 0.1*inch))

        # PRIORITY 1: Use dynamic recommendations from analysis_data if available
        if recommendations:
            # Handle both list and dict formats
            rec_list = recommendations if isinstance(recommendations, list) else recommendations.get('items', recommendations.get('recommendations', []))

            if rec_list and isinstance(rec_list, list):
                # Separate by priority/timeline
                before_travel_recs = [r for r in rec_list if isinstance(r, dict) and r.get('timeline', '').lower() in ['before travel', 'immediate', 'pre-travel']]
                during_travel_recs = [r for r in rec_list if isinstance(r, dict) and r.get('timeline', '').lower() in ['during travel', 'while traveling']]
                other_recs = [r for r in rec_list if isinstance(r, dict) and r not in before_travel_recs and r not in during_travel_recs]

                if before_travel_recs or other_recs:
                    elements.append(create_subsection_header("Before You Travel"))
                    display_recs = before_travel_recs[:5] if before_travel_recs else other_recs[:5]
                    for rec in display_recs:
                        rec_title = rec.get('title', rec.get('suggestion', rec.get('recommendation', '')))
                        elements.append(Paragraph(f"☐ {rec_title}", styles['body']))
                    elements.append(Spacer(1, 0.1*inch))

                if during_travel_recs:
                    elements.append(create_subsection_header("During Your Trip"))
                    for rec in during_travel_recs[:4]:
                        rec_title = rec.get('title', rec.get('suggestion', rec.get('recommendation', '')))
                        elements.append(Paragraph(f"• {rec_title}", styles['body']))
                    elements.append(Spacer(1, 0.1*inch))

        # FALLBACK: Use hardcoded checklists if no dynamic recommendations
        if not recommendations or not isinstance(recommendations, (list, dict)) or (isinstance(recommendations, list) and len(recommendations) == 0):
            elements.append(create_subsection_header("Before You Travel"))

            before_travel_checklist = [
                f"Verify medical cover is adequate for {destination_costs['region']}",
                "Check if any pre-existing conditions are covered",
                "Confirm activities you plan are not excluded",
                "Save emergency helpline number in your phone",
                "Download/print policy document",
            ]
            for item in before_travel_checklist:
                elements.append(Paragraph(f"☐ {item}", styles['body']))
            elements.append(Spacer(1, 0.1*inch))

        elements.append(create_subsection_header("Pack These"))
        pack_list = [
            "Printed policy document",
            "Insurance card (if issued)",
            "Emergency contact card with helpline numbers",
            "Claim form (downloaded)",
        ]
        for item in pack_list:
            elements.append(Paragraph(f"☐ {item}", styles['body']))
        elements.append(Spacer(1, 0.1*inch))

        elements.append(create_subsection_header("Save in Phone"))
        phone_items = [
            f"24/7 Emergency helpline: {emergency_helpline}",
            f"Policy number: {policy_number}",
            f"Claims email: {claims_email}",
        ]
        for item in phone_items:
            elements.append(Paragraph(f"• {item}", styles['body']))
        elements.append(Spacer(1, 0.2*inch))

        # ==================== HOW TO CLAIM - EMERGENCY GUIDE ====================
        elements.append(PageBreak())
        elements.append(create_section_header("How to Claim - Emergency Guide", styles))
        elements.append(Spacer(1, 0.1*inch))

        # Medical Emergency
        elements.append(create_subsection_header("In Case of Medical Emergency"))

        emergency_box = f"""
        <b>24/7 Emergency Helpline: {emergency_helpline}</b><br/><br/>
        <b>Step 1:</b> Call insurer FIRST (if possible) - Before hospital admission, call the 24/7 helpline, get pre-authorization, ask if hospital is in network<br/><br/>
        <b>Step 2:</b> If true emergency (no time to call) - Get treated first, call insurer within 24 hours, keep ALL documents<br/><br/>
        <b>Step 3:</b> Documents to collect - Hospital admission papers, detailed medical reports, itemized bills (in English), prescriptions, discharge summary
        """
        elements.append(create_highlight_box(emergency_box, INFO_LIGHT, INFO_BLUE))
        elements.append(Spacer(1, 0.15*inch))

        # Trip Cancellation Claim
        elements.append(create_subsection_header("In Case of Trip Cancellation"))
        elements.append(Paragraph(
            "<b>Step 1:</b> Document the reason - Medical certificate (if health-related), death certificate (if applicable), visa rejection letter, etc.",
            styles['body']
        ))
        elements.append(Paragraph(
            "<b>Step 2:</b> Notify insurer within 24-48 hours and get claim reference number.",
            styles['body']
        ))
        elements.append(Paragraph(
            "<b>Step 3:</b> Gather documents - Booking confirmations, cancellation proof, refund received (if any).",
            styles['body']
        ))
        elements.append(Spacer(1, 0.1*inch))

        # Baggage Claim
        elements.append(create_subsection_header("In Case of Baggage Loss/Delay"))
        elements.append(Paragraph(
            "<b>At Airport (Immediately):</b> Report to airline's baggage counter, get PIR (Property Irregularity Report) - CRITICAL, note reference number.",
            styles['body']
        ))
        elements.append(Paragraph(
            "<b>If Delayed:</b> Keep receipts for essential purchases, limit to reasonable items (clothes, toiletries).",
            styles['body']
        ))
        elements.append(Paragraph(
            "<b>If Lost (After 21 Days):</b> Get written confirmation from airline, prepare list of contents with values, submit claim with proof of ownership.",
            styles['body']
        ))
        elements.append(Spacer(1, 0.1*inch))

        # Theft Claim
        elements.append(create_subsection_header("In Case of Theft"))
        elements.append(Paragraph(
            "<b>Step 1:</b> File police report immediately at local police station, get copy of FIR.",
            styles['body']
        ))
        elements.append(Paragraph(
            "<b>Step 2:</b> Notify insurer within 24 hours with police report.",
            styles['body']
        ))
        elements.append(Paragraph(
            "<b>Step 3:</b> Document stolen items with values and proof of ownership (photos, receipts, bank statements).",
            styles['body']
        ))
        elements.append(Spacer(1, 0.15*inch))

        # Important Reminders
        elements.append(create_subsection_header("Important Reminders"))
        reminders = [
            "Call BEFORE treatment if possible - Pre-authorization prevents claim disputes later",
            "Keep EVERYTHING - Every receipt, every document, every report",
            "Documents in English - Get translations if needed",
            "Don't delay - Late notification can void your claim",
            "Take photos - Damaged baggage, accident scene, documents",
        ]
        for i, reminder in enumerate(reminders, 1):
            elements.append(Paragraph(f"{i}. {reminder}", styles['body']))
        elements.append(Spacer(1, 0.15*inch))

        # Claim Helplines Summary
        helpline_data = [
            ("24/7 Emergency (Medical)", emergency_helpline),
            ("Claims Email", claims_email),
            ("Policy Number", policy_number),
        ]
        elements.append(create_info_card(helpline_data, DANGER_RED))
        elements.append(Spacer(1, 0.2*inch))

        # ==================== TRAVEL SAFETY TIPS ====================
        elements.append(create_section_header("Travel Safety Tips", styles))
        elements.append(Spacer(1, 0.1*inch))

        elements.append(create_subsection_header("Medical"))
        medical_tips = [
            "Carry copies of prescriptions for regular medications",
            f"Know the location of nearest hospital at {destination}",
            "Carry basic first-aid kit",
            f"Check if any vaccinations required for {destination}",
        ]
        for tip in medical_tips:
            elements.append(Paragraph(f"• {tip}", styles['body']))
        elements.append(Spacer(1, 0.1*inch))

        elements.append(create_subsection_header("Documents"))
        doc_tips = [
            "Keep digital copies of passport, visa, policy in email/cloud",
            "Carry printed copy of policy",
            "Share itinerary with family back home",
        ]
        for tip in doc_tips:
            elements.append(Paragraph(f"• {tip}", styles['body']))
        elements.append(Spacer(1, 0.1*inch))

        elements.append(create_subsection_header("Money"))
        money_tips = [
            "Don't carry large amounts of cash",
            "Inform bank of travel dates (prevent card blocks)",
            "Know your card's international emergency number",
        ]
        for tip in money_tips:
            elements.append(Paragraph(f"• {tip}", styles['body']))
        elements.append(Spacer(1, 0.2*inch))

        # ==================== FOOTER / DISCLAIMER ====================
        elements.append(HRFlowable(width="100%", thickness=1, color=BORDER_LIGHT))
        elements.append(Spacer(1, 0.1*inch))

        disclaimer_text = f"""
        <b>Analysis Version:</b> 9.0 | <b>Generated:</b> {datetime.now().strftime('%d %b %Y %H:%M')} |
        <b>Valid for:</b> Trip from {trip_start} to {trip_end}

        This analysis is based on the policy document provided and standard travel insurance terms.
        It is not a guarantee of claim settlement. Actual coverage depends on specific policy terms,
        circumstances of the claim, and insurer's assessment. Always refer to your policy document for exact terms.
        """
        elements.append(Paragraph(disclaimer_text, ParagraphStyle(
            'disclaimer',
            fontName=FONT_REGULAR,
            fontSize=7,
            textColor=LIGHT_GRAY,
            alignment=TA_CENTER,
            leading=10
        )))
        elements.append(Spacer(1, 0.1*inch))

        elements.append(Paragraph(
            "<b>EAZR Policy Analysis | Clarity Before Crisis</b>",
            ParagraphStyle('footer_brand', fontName=FONT_BOLD, fontSize=8, textColor=BRAND_PRIMARY, alignment=TA_CENTER)
        ))

        # Build PDF
        pdf_doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)

        buffer.seek(0)
        logger.info(f"✅ Travel insurance report generated successfully for policy {policy_number}")
        return buffer

    except Exception as e:
        logger.error(f"❌ Error generating travel insurance report: {str(e)}", exc_info=True)
        raise


# ==================== V10: 6-PAGE TRAVEL INSURANCE REPORT ====================


def _v10_score_color(score: int):
    """Return ReportLab color for V10 score."""
    if score >= 90:
        return SCORE_EXCELLENT
    elif score >= 75:
        return SCORE_STRONG
    elif score >= 60:
        return SCORE_ADEQUATE
    elif score >= 40:
        return SCORE_BASIC
    return SCORE_LOW


def _v10_status_color(status: str):
    """Return color for coverage status."""
    sl = str(status).lower()
    if sl in ("covered", "yes", "active", "above", "meets"):
        return COVERAGE_COVERED_CLR
    elif sl in ("limited", "partial"):
        return COVERAGE_LIMITED_CLR
    return COVERAGE_NOT_COVERED_CLR


class EmergencyPageTemplate:
    """Dark navy header/footer for emergency reference card (Page 6)."""
    @staticmethod
    def draw(canvas, doc_template):
        canvas.saveState()
        # Dark navy header
        canvas.setFillColor(EMERGENCY_BG)
        canvas.rect(0, A4[1] - 0.6 * inch, A4[0], 0.6 * inch, fill=True, stroke=False)
        canvas.setFont(FONT_BOLD, 18)
        canvas.setFillColor(EMERGENCY_TEXT)
        canvas.drawString(0.6 * inch, A4[1] - 0.4 * inch, "EAZR")
        canvas.setFont(FONT_REGULAR, 8)
        canvas.setFillColor(EMERGENCY_ACCENT)
        canvas.drawString(0.6 * inch, A4[1] - 0.52 * inch, "Emergency Reference Card")
        canvas.setFont(FONT_REGULAR, 8)
        canvas.setFillColor(EMERGENCY_TEXT)
        canvas.drawRightString(A4[0] - 0.6 * inch, A4[1] - 0.4 * inch, f"Page {doc_template.page}")
        # Dark footer
        canvas.setStrokeColor(EMERGENCY_ACCENT)
        canvas.setLineWidth(0.5)
        canvas.line(0.6 * inch, 0.5 * inch, A4[0] - 0.6 * inch, 0.5 * inch)
        canvas.setFont(FONT_REGULAR, 7)
        canvas.setFillColor(EMERGENCY_ACCENT)
        canvas.drawString(0.6 * inch, 0.35 * inch, "KEEP THIS PAGE ACCESSIBLE DURING TRAVEL")
        canvas.drawRightString(A4[0] - 0.6 * inch, 0.35 * inch, f"Generated: {datetime.now().strftime('%d %b %Y')}")
        canvas.restoreState()


def _generate_travel_report_v10(policy_data: dict, analysis_data: dict) -> BytesIO:
    """
    Generate 6-page V10 travel insurance analysis report per EAZR_05 spec.
    Pages: 1-Cover+Summary, 2-Score Deep-Dive, 3-Destination Analysis+Coverage Map,
    4-Scenarios (T001-T005), 5-Action Plan, 6-Emergency Reference Card.
    """
    buffer = BytesIO()
    pdf_doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=0.6 * inch, leftMargin=0.6 * inch,
        topMargin=0.85 * inch, bottomMargin=0.7 * inch,
        title="Travel Insurance Policy Analysis V10",
        author="EAZR Insurance Platform"
    )

    elements = []
    styles = create_styles()

    # ---- Extract base data ----
    policy_number = str(policy_data.get('policyNumber', 'N/A'))
    insurer_name = str(policy_data.get('insuranceProvider', 'N/A'))
    policy_holder_name = policy_data.get('policyHolderName', 'Dear Policyholder')
    first_name = policy_holder_name.split()[0] if policy_holder_name and policy_holder_name != 'N/A' else 'there'
    if first_name.lower() in ['mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'shri', 'smt']:
        parts = policy_holder_name.split()
        first_name = parts[1] if len(parts) > 1 else 'there'

    premium = safe_int(policy_data.get('premium', 0))
    start_date = policy_data.get('startDate', 'N/A')
    end_date = policy_data.get('endDate', 'N/A')

    category_data = policy_data.get('categorySpecificData', {})
    trip_details = category_data.get('tripDetails', {})
    traveller_details = category_data.get('travellerDetails', [])
    coverage_summary = category_data.get('coverageSummary', {})
    exclusions_data = category_data.get('exclusions', {})
    emergency_contacts = category_data.get('emergencyContacts', {})

    destination_countries = trip_details.get('destinationCountries', [])
    if isinstance(destination_countries, list) and destination_countries:
        destination = ', '.join(str(c) for c in destination_countries)
    else:
        destination = str(destination_countries) if destination_countries else 'International'

    trip_type = trip_details.get('tripType', 'Single Trip')
    trip_duration = trip_details.get('tripDuration', 'N/A')
    trip_start = trip_details.get('tripStartDate', start_date)
    trip_end = trip_details.get('tripEndDate', end_date)

    # V10 analysis data
    pr = analysis_data.get('protectionReadiness', {})
    composite_score = pr.get('compositeScore', safe_int(analysis_data.get('protectionScore', 0)))
    verdict = pr.get('verdict', {})
    verdict_label = verdict.get('label', analysis_data.get('protectionScoreLabel', ''))
    verdict_summary = verdict.get('summary', '')
    verdict_color_hex = verdict.get('color', '#6B7280')
    scores = pr.get('scores', {})
    s1 = scores.get('s1', {})
    s2 = scores.get('s2', {})

    trip_state = analysis_data.get('tripState', {})
    dest_check = analysis_data.get('destinationCoverageCheck', {})
    emergency_ref = analysis_data.get('emergencyReference', {})

    # Gaps
    gaps_data = analysis_data.get('coverageGaps', {})
    if isinstance(gaps_data, dict):
        gap_summary = gaps_data.get('summary', {})
        gaps_list = gaps_data.get('gaps', [])
    else:
        gap_summary = {}
        gaps_list = gaps_data if isinstance(gaps_data, list) else []

    # Strengths
    strengths = analysis_data.get('coverageStrengths', [])

    # Scenarios
    scenarios_data = analysis_data.get('scenarios', {})
    primary_scenario_id = scenarios_data.get('primaryScenarioId', 'T001') if isinstance(scenarios_data, dict) else 'T001'
    simulations = scenarios_data.get('simulations', []) if isinstance(scenarios_data, dict) else []

    # Recommendations
    recs = analysis_data.get('recommendations', {})
    quick_wins = recs.get('quickWins', []) if isinstance(recs, dict) else []
    priority_upgrades = recs.get('priorityUpgrades', []) if isinstance(recs, dict) else []
    total_upgrade_cost = recs.get('totalUpgradeCost', {}) if isinstance(recs, dict) else {}
    multi_trip = recs.get('multiTripConsideration', None) if isinstance(recs, dict) else None

    # Destination costs
    dest_costs = analysis_data.get('destinationCosts', {})
    destination_region = dest_costs.get('region', 'International')

    # Trip state framing
    action_framing = trip_state.get('actionFraming', 'For Your Next Trip')
    trip_state_label = trip_state.get('state', 'PRE_TRIP')

    # Helper styles
    body_s = styles['body']
    bold_s = styles['body_emphasis']

    def _p(text, style=None):
        return Paragraph(str(text), style or body_s)

    def _pb(text):
        return Paragraph(f"<b>{text}</b>", bold_s)

    # ================================================================
    # PAGE 1: COVER + EXECUTIVE SUMMARY
    # ================================================================
    elements.append(Paragraph(f"{insurer_name}", styles['main_title']))
    elements.append(Paragraph(f"Travel Insurance Analysis for {first_name}", styles['subtitle']))
    elements.append(Spacer(1, 0.1 * inch))

    # Trip context card
    trip_badge_color = TRAVEL_DOMESTIC_BADGE if trip_state.get('state') == 'DOMESTIC' or 'domestic' in str(trip_type).lower() else TRAVEL_INTL_BADGE
    trip_ctx_data = [
        [_pb("Destination"), _p(destination)],
        [_pb("Trip Type"), _p(trip_type)],
        [_pb("Duration"), _p(f"{trip_duration} days" if trip_duration != 'N/A' else 'N/A')],
        [_pb("Travelers"), _p(f"{len(traveller_details)}" if traveller_details else "1")],
        [_pb("Period"), _p(f"{trip_start} to {trip_end}")],
    ]

    # Add countdown if PRE_TRIP
    if trip_state.get('daysToDepart') is not None:
        urgency = trip_state.get('urgency', 'normal')
        days_label = f"{trip_state['daysToDepart']} days to departure"
        if urgency == 'high':
            days_label += " (URGENT)"
        trip_ctx_data.append([_pb("Countdown"), _p(days_label)])
    elif trip_state.get('daysRemaining') is not None:
        trip_ctx_data.append([_pb("Trip Day"), _p(f"Day {trip_state.get('tripDay', '?')} of {trip_state.get('totalDays', '?')}")])

    trip_table = Table(trip_ctx_data, colWidths=[2.0 * inch, 4.3 * inch])
    trip_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), FONT_REGULAR),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('BACKGROUND', (0, 0), (-1, -1), BRAND_LIGHTER),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
    ]))
    elements.append(trip_table)
    elements.append(Spacer(1, 0.15 * inch))

    # Composite score + verdict
    score_color = _v10_score_color(composite_score)
    elements.append(create_section_header("Travel Readiness Verdict", styles))
    elements.append(Spacer(1, 0.05 * inch))

    score_data = [
        [
            Paragraph(f"<font size='28' color='{verdict_color_hex}'><b>{composite_score}</b></font><font size='12' color='#6B7280'>/100</font>", ParagraphStyle('score_big', alignment=TA_CENTER, fontName=FONT_BOLD, fontSize=28, leading=34)),
            Paragraph(f"<b>{verdict_label}</b><br/><font size='9' color='#6B7280'>{verdict_summary}</font>", ParagraphStyle('verdict_text', fontName=FONT_BOLD, fontSize=13, textColor=CHARCOAL, leading=16)),
        ]
    ]
    score_table = Table(score_data, colWidths=[1.8 * inch, 4.5 * inch])
    score_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, -1), WHISPER),
        ('BOX', (0, 0), (-1, -1), 1, score_color),
    ]))
    elements.append(score_table)
    elements.append(Spacer(1, 0.1 * inch))

    # S1 + S2 tiles
    s1_score = s1.get('score', 0)
    s2_score = s2.get('score', 0)
    s1_label = s1.get('label', '')
    s2_label = s2.get('label', '')
    s1_color_hex = s1.get('color', '#6B7280')
    s2_color_hex = s2.get('color', '#6B7280')

    tile_data = [
        [
            Paragraph(f"<b>S1: Medical Emergency Readiness</b><br/><font size='16' color='{s1_color_hex}'><b>{s1_score}</b></font>/100 &nbsp; <font size='9' color='{s1_color_hex}'>{s1_label}</font><br/><font size='8' color='#6B7280'>Weight: 60%</font>", ParagraphStyle('tile', fontName=FONT_REGULAR, fontSize=9, leading=15)),
            Paragraph(f"<b>S2: Trip Protection Score</b><br/><font size='16' color='{s2_color_hex}'><b>{s2_score}</b></font>/100 &nbsp; <font size='9' color='{s2_color_hex}'>{s2_label}</font><br/><font size='8' color='#6B7280'>Weight: 40%</font>", ParagraphStyle('tile2', fontName=FONT_REGULAR, fontSize=9, leading=15)),
        ]
    ]
    tile_table = Table(tile_data, colWidths=[3.15 * inch, 3.15 * inch])
    tile_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (0, 0), WHISPER),
        ('BACKGROUND', (1, 0), (1, 0), WHISPER),
        ('BOX', (0, 0), (0, 0), 0.5, BORDER_LIGHT),
        ('BOX', (1, 0), (1, 0), 0.5, BORDER_LIGHT),
    ]))
    elements.append(tile_table)
    elements.append(Spacer(1, 0.15 * inch))

    # At a Glance card
    elements.append(create_section_header("At a Glance", styles))
    elements.append(Spacer(1, 0.05 * inch))

    med_benchmark = dest_check.get('medicalBenchmark', {})
    per_day = dest_check.get('perDayCost', {})
    schengen_info = dest_check.get('schengenCompliance', {})

    glance_items = [
        ["Medical Cover", med_benchmark.get('yourCoverageFormatted', 'N/A')],
        ["vs Benchmark", f"{med_benchmark.get('percentOfRequired', 0)}% of recommended {med_benchmark.get('requiredFormatted', '')}"],
        ["Total Gaps", f"{gap_summary.get('total', 0)} ({gap_summary.get('high', 0)} high, {gap_summary.get('medium', 0)} medium)"],
    ]
    if schengen_info and schengen_info.get('applicable'):
        glance_items.append(["Schengen", schengen_info.get('badgeLabel', 'N/A')])
    glance_items.append(["Per Day/Person", per_day.get('perPersonPerDayFormatted', 'N/A')])
    if total_upgrade_cost:
        glance_items.append(["Upgrade Cost", total_upgrade_cost.get('monthlyEmiFormatted', total_upgrade_cost.get('annualFormatted', 'N/A'))])

    glance_data = [[_pb(k), _p(v)] for k, v in glance_items]
    glance_table = Table(glance_data, colWidths=[2.2 * inch, 4.1 * inch])
    glance_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('BACKGROUND', (0, 0), (-1, -1), WHISPER),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
    ]))
    elements.append(glance_table)

    # ================================================================
    # PAGE 2: SCORE DEEP-DIVE
    # ================================================================
    elements.append(PageBreak())
    elements.append(create_section_header("Score Deep-Dive", styles))
    elements.append(Spacer(1, 0.1 * inch))

    # S1 Medical Emergency Readiness factors
    elements.append(Paragraph(f"<b>S1: Medical Emergency Readiness</b> — Score: {s1_score}/100 (Weight: 60%)", bold_s))
    elements.append(Spacer(1, 0.05 * inch))

    s1_factors = s1.get('factors', [])
    if s1_factors:
        s1_header = [_pb("Factor"), _pb("Points"), _pb("Max"), _pb("Rating")]
        s1_rows = [s1_header]
        for f in s1_factors:
            if isinstance(f, dict):
                s1_rows.append([
                    _p(f.get('name', '')),
                    _p(str(f.get('points', 0))),
                    _p(str(f.get('maxPoints', 0))),
                    _p(f.get('label', '')),
                ])
        s1_table = Table(s1_rows, colWidths=[2.8 * inch, 1.0 * inch, 1.0 * inch, 1.5 * inch])
        s1_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('BACKGROUND', (0, 0), (-1, 0), BRAND_PRIMARY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ]))
        for i in range(1, len(s1_rows)):
            if i % 2 == 0:
                s1_table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), WHISPER)]))
        elements.append(s1_table)
    else:
        elements.append(_p("No S1 factor data available."))

    elements.append(Spacer(1, 0.1 * inch))
    elements.append(create_highlight_box(
        f"<b>What This Means for {destination}:</b> Your medical emergency readiness score of {s1_score}/100 "
        f"{'meets the recommended threshold for this destination.' if s1_score >= 75 else 'is below the recommended threshold. Consider increasing medical coverage before travel.'}",
        INFO_LIGHT if s1_score >= 75 else WARNING_LIGHT,
        INFO_BLUE if s1_score >= 75 else WARNING_AMBER
    ))
    elements.append(Spacer(1, 0.2 * inch))

    # S2 Trip Protection Score factors
    elements.append(Paragraph(f"<b>S2: Trip Protection Score</b> — Score: {s2_score}/100 (Weight: 40%)", bold_s))
    elements.append(Spacer(1, 0.05 * inch))

    s2_factors = s2.get('factors', [])
    if s2_factors:
        s2_header = [_pb("Factor"), _pb("Points"), _pb("Max"), _pb("Rating")]
        s2_rows = [s2_header]
        for f in s2_factors:
            if isinstance(f, dict):
                s2_rows.append([
                    _p(f.get('name', '')),
                    _p(str(f.get('points', 0))),
                    _p(str(f.get('maxPoints', 0))),
                    _p(f.get('label', '')),
                ])
        s2_table = Table(s2_rows, colWidths=[2.8 * inch, 1.0 * inch, 1.0 * inch, 1.5 * inch])
        s2_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('BACKGROUND', (0, 0), (-1, 0), BRAND_PRIMARY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ]))
        for i in range(1, len(s2_rows)):
            if i % 2 == 0:
                s2_table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), WHISPER)]))
        elements.append(s2_table)
    else:
        elements.append(_p("No S2 factor data available."))

    elements.append(Spacer(1, 0.1 * inch))
    trip_cost_str = format_currency(premium, 'INR')
    elements.append(create_highlight_box(
        f"<b>What This Means for your {trip_cost_str} trip:</b> Your trip protection score of {s2_score}/100 "
        f"{'provides good coverage for trip disruptions.' if s2_score >= 70 else 'suggests gaps in trip disruption coverage. Review cancellation and delay benefits.'}",
        INFO_LIGHT if s2_score >= 70 else WARNING_LIGHT,
        INFO_BLUE if s2_score >= 70 else WARNING_AMBER
    ))

    # ================================================================
    # PAGE 3: DESTINATION ANALYSIS + COVERAGE MAP
    # ================================================================
    elements.append(PageBreak())
    elements.append(create_section_header("Destination Analysis & Coverage Map", styles))
    elements.append(Spacer(1, 0.05 * inch))

    # Medical benchmark
    if med_benchmark:
        bm_status = med_benchmark.get('status', 'below')
        bm_color = COVERAGE_COVERED_CLR if bm_status == 'above' else (COVERAGE_LIMITED_CLR if bm_status == 'meets' else COVERAGE_NOT_COVERED_CLR)
        bm_note = med_benchmark.get('note', '')
        bm_data = [
            [_pb("Your Medical Cover"), _p(med_benchmark.get('yourCoverageFormatted', 'N/A'))],
            [_pb("Recommended for " + destination_region), _p(med_benchmark.get('requiredFormatted', 'N/A'))],
            [_pb("% of Recommended"), _p(f"{med_benchmark.get('percentOfRequired', 0)}%")],
            [_pb("Status"), _p(bm_status.upper())],
        ]
        bm_table = Table(bm_data, colWidths=[3.0 * inch, 3.3 * inch])
        bm_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('BACKGROUND', (0, 0), (-1, -1), WHISPER),
            ('BOX', (0, 0), (-1, -1), 0.5, bm_color),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
        ]))
        elements.append(bm_table)
        if bm_note:
            elements.append(Spacer(1, 0.03 * inch))
            elements.append(_p(bm_note))
        elements.append(Spacer(1, 0.1 * inch))

    # Schengen compliance
    if schengen_info and schengen_info.get('applicable'):
        sc_compliant = schengen_info.get('compliant', False)
        sc_color = SCHENGEN_COMPLIANT_CLR if sc_compliant else SCHENGEN_NONCOMPLIANT_CLR
        sc_label = schengen_info.get('badgeLabel', 'Schengen')
        sc_details = schengen_info.get('details', '')
        elements.append(create_highlight_box(
            f"<b>Schengen Compliance: {sc_label}</b><br/>{sc_details}",
            SUCCESS_LIGHT if sc_compliant else DANGER_LIGHT,
            sc_color
        ))
        elements.append(Spacer(1, 0.1 * inch))

    # Coverage Map Grid (17 coverage types)
    elements.append(Paragraph("<b>Complete Coverage Map</b>", bold_s))
    elements.append(Spacer(1, 0.05 * inch))

    coverage_map_items = [
        ("Medical Expenses", coverage_summary.get("medicalExpenses")),
        ("Emergency Evacuation", coverage_summary.get("emergencyMedicalEvacuation")),
        ("Repatriation", coverage_summary.get("repatriationOfRemains")),
        ("Pre-existing Conditions", None),
        ("COVID Treatment", None),
        ("COVID Quarantine", None),
        ("Trip Cancellation", coverage_summary.get("tripCancellation")),
        ("Trip Curtailment", coverage_summary.get("tripInterruption")),
        ("Trip Delay", coverage_summary.get("flightDelay")),
        ("Missed Connection", None),
        ("Baggage Loss", coverage_summary.get("baggageLoss")),
        ("Baggage Delay", coverage_summary.get("baggageDelay")),
        ("Passport Loss", coverage_summary.get("passportLoss")),
        ("Personal Liability", coverage_summary.get("personalLiability")),
        ("PA - Death", coverage_summary.get("accidentalDeath")),
        ("PA - Disability", coverage_summary.get("permanentDisability")),
        ("Adventure Sports", None),
    ]

    # Enrich from category_data
    med_cov = category_data.get('medicalCoverage', {})
    ped_info = med_cov.get('preExistingConditions', {})
    covid_info = med_cov.get('covidCoverage', {})
    adventure_excl = exclusions_data.get('adventureSportsExclusion', '')

    coverage_map_items[3] = ("Pre-existing Conditions", "Covered" if ped_info.get('covered') else "Not Covered")
    coverage_map_items[4] = ("COVID Treatment", "Covered" if covid_info.get('treatmentCovered') else "Not Covered")
    coverage_map_items[5] = ("COVID Quarantine", covid_info.get('quarantineLimit') if covid_info.get('quarantineCovered') else "Not Covered")
    coverage_map_items[9] = ("Missed Connection", coverage_summary.get("missedConnection", "Not Covered"))
    adventure_status = "Excluded" if ("excluded" in str(adventure_excl).lower() or not adventure_excl) else "Covered"
    coverage_map_items[16] = ("Adventure Sports", adventure_status)

    cm_header = [_pb("Coverage Type"), _pb("Status"), _pb("Amount")]
    cm_rows = [cm_header]
    for cov_name, cov_val in coverage_map_items:
        if cov_val is None or cov_val == '' or cov_val == 'N/A':
            status_text = "Not Found"
            amount_text = "-"
        elif isinstance(cov_val, str) and cov_val.lower() in ('not covered', 'excluded', 'not found'):
            status_text = cov_val
            amount_text = "-"
        elif isinstance(cov_val, str) and cov_val.lower() == 'covered':
            status_text = "Covered"
            amount_text = "See policy"
        else:
            status_text = "Covered"
            amount_text = str(cov_val)
        cm_rows.append([_p(cov_name), _p(status_text), _p(amount_text)])

    cm_table = Table(cm_rows, colWidths=[2.5 * inch, 1.8 * inch, 2.0 * inch])
    cm_style_cmds = [
        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_PRIMARY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
    ]
    # Color-code status column
    for i in range(1, len(cm_rows)):
        status_val = coverage_map_items[i - 1][1]
        if status_val is not None and str(status_val).lower() not in ('not covered', 'excluded', 'not found', '', 'n/a'):
            cm_style_cmds.append(('TEXTCOLOR', (1, i), (1, i), COVERAGE_COVERED_CLR))
        elif status_val is not None:
            cm_style_cmds.append(('TEXTCOLOR', (1, i), (1, i), COVERAGE_NOT_COVERED_CLR))
        if i % 2 == 0:
            cm_style_cmds.append(('BACKGROUND', (0, i), (-1, i), WHISPER))

    cm_table.setStyle(TableStyle(cm_style_cmds))
    elements.append(cm_table)
    elements.append(Spacer(1, 0.1 * inch))

    # Per-day cost
    if per_day:
        elements.append(create_highlight_box(
            f"<b>Cost per Day:</b> {per_day.get('perDayFormatted', 'N/A')} total | "
            f"{per_day.get('perPersonPerDayFormatted', 'N/A')} per person/day | "
            f"Total Premium: {per_day.get('totalPremiumFormatted', 'N/A')} for {per_day.get('tripDays', 0)} days, "
            f"{per_day.get('travelersCount', 1)} traveler(s)",
            INFO_LIGHT, INFO_BLUE
        ))
        elements.append(Spacer(1, 0.1 * inch))

    # Strengths (compact)
    if strengths:
        elements.append(Paragraph("<b>Coverage Strengths</b>", bold_s))
        elements.append(Spacer(1, 0.03 * inch))
        for st in strengths[:5]:
            if isinstance(st, dict):
                elements.append(_p(f"• <b>{st.get('title', '')}</b>: {st.get('reason', '')}"))
            elif isinstance(st, str):
                elements.append(_p(f"• {st}"))
        elements.append(Spacer(1, 0.1 * inch))

    # Gaps (compact)
    if gaps_list:
        elements.append(Paragraph(f"<b>Coverage Gaps</b> ({gap_summary.get('total', len(gaps_list))} identified)", bold_s))
        elements.append(Spacer(1, 0.03 * inch))
        for g in gaps_list[:6]:
            if isinstance(g, dict):
                sev = g.get('severity', 'medium').upper()
                sev_color = '#DC2626' if sev == 'HIGH' else ('#D97706' if sev == 'MEDIUM' else '#6B7280')
                elements.append(_p(f"• <font color='{sev_color}'>[{sev}]</font> <b>{g.get('title', '')}</b>: {g.get('description', '')[:120]}"))

    # ================================================================
    # PAGE 4: SCENARIOS (T001-T005)
    # ================================================================
    elements.append(PageBreak())
    elements.append(create_section_header("What Could Happen — Scenario Simulations", styles))
    elements.append(Spacer(1, 0.05 * inch))
    elements.append(_p(f"Based on your policy coverage and {destination_region} costs. Primary scenario highlighted."))
    elements.append(Spacer(1, 0.1 * inch))

    if simulations:
        for idx, sim in enumerate(simulations):
            if not isinstance(sim, dict):
                continue
            sim_id = sim.get('scenarioId', sim.get('id', f'T{idx + 1:03d}'))
            is_primary = (sim_id == primary_scenario_id)
            sim_title = sim.get('title', sim.get('name', f'Scenario {idx + 1}'))
            sim_desc = sim.get('description', '')[:200]

            # Cost breakdown
            total_cost = safe_int(sim.get('totalCost', sim.get('estimatedCost', 0)))
            covered = safe_int(sim.get('coveredAmount', sim.get('insurancePays', 0)))
            pocket = safe_int(sim.get('outOfPocket', sim.get('youPay', 0)))

            border_color = BRAND_PRIMARY if is_primary else BORDER_LIGHT
            bg = BRAND_LIGHTER if is_primary else WHITE
            primary_badge = " [PRIMARY]" if is_primary else ""

            sim_data = [
                [Paragraph(f"<b>{sim_id}: {sim_title}{primary_badge}</b>", ParagraphStyle('sim_title', fontName=FONT_BOLD, fontSize=10, textColor=BRAND_DARK, leading=14))],
                [_p(sim_desc)] if sim_desc else [],
                [_p(f"Total Cost: {format_currency(total_cost, 'USD')} | Insurance Pays: {format_currency(covered, 'USD')} | You Pay: {format_currency(pocket, 'USD')}")],
            ]
            sim_data = [r for r in sim_data if r]  # Remove empty rows

            sim_table = Table(sim_data, colWidths=[6.3 * inch])
            sim_table.setStyle(TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('BACKGROUND', (0, 0), (-1, -1), bg),
                ('BOX', (0, 0), (-1, -1), 1 if is_primary else 0.5, border_color),
            ]))
            elements.append(KeepTogether([sim_table, Spacer(1, 0.08 * inch)]))
    else:
        elements.append(_p("No scenario simulations available. Scenarios will be generated from your policy data."))
        elements.append(Spacer(1, 0.2 * inch))

    # Destination verdict one-liner
    dest_verdict = dest_check.get('verdictOneLiner', '')
    if dest_verdict:
        elements.append(Spacer(1, 0.05 * inch))
        elements.append(create_highlight_box(
            f"<b>Destination Verdict:</b> {dest_verdict}",
            INFO_LIGHT, INFO_BLUE
        ))

    # ================================================================
    # PAGE 5: ACTION PLAN
    # ================================================================
    elements.append(PageBreak())
    elements.append(create_section_header(action_framing, styles))
    elements.append(Spacer(1, 0.05 * inch))

    # Quick wins
    if quick_wins:
        elements.append(Paragraph("<b>Quick Wins — Easy Improvements</b>", bold_s))
        elements.append(Spacer(1, 0.05 * inch))
        for qw in quick_wins:
            if isinstance(qw, dict):
                elements.append(_p(f"• <b>{qw.get('title', '')}</b>: {qw.get('description', '')}"))
        elements.append(Spacer(1, 0.15 * inch))

    # Priority upgrades
    if priority_upgrades:
        elements.append(Paragraph("<b>Priority Upgrades — Investment Required</b>", bold_s))
        elements.append(Spacer(1, 0.05 * inch))

        pu_header = [_pb("#"), _pb("Upgrade"), _pb("Cost"), _pb("EMI"), _pb("Priority")]
        pu_rows = [pu_header]
        for pu in priority_upgrades:
            if isinstance(pu, dict):
                pu_rows.append([
                    _p(str(pu.get('priority', ''))),
                    _p(pu.get('title', '')),
                    _p(pu.get('estimatedCostFormatted', format_currency(pu.get('estimatedCost', 0), 'INR'))),
                    _p(pu.get('eazrEmiFormatted', format_currency(pu.get('eazrEmi', 0), 'INR'))),
                    _p(pu.get('priorityLabel', '')),
                ])
        pu_table = Table(pu_rows, colWidths=[0.4 * inch, 2.5 * inch, 1.2 * inch, 1.0 * inch, 1.2 * inch])
        pu_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('BACKGROUND', (0, 0), (-1, 0), BRAND_PRIMARY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
        ]))
        for i in range(1, len(pu_rows)):
            if i % 2 == 0:
                pu_table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), WHISPER)]))
        elements.append(pu_table)
        elements.append(Spacer(1, 0.1 * inch))

    # Investment summary
    if total_upgrade_cost:
        inv_data = [
            [_pb("Total Annual Cost"), _p(total_upgrade_cost.get('annualFormatted', 'N/A'))],
            [_pb("Monthly EMI via EAZR"), _p(total_upgrade_cost.get('monthlyEmiFormatted', 'N/A'))],
        ]
        inv_table = Table(inv_data, colWidths=[3.0 * inch, 3.3 * inch])
        inv_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 0), (-1, -1), BRAND_LIGHTER),
            ('BOX', (0, 0), (-1, -1), 1, BRAND_PRIMARY),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
        ]))
        elements.append(inv_table)
        elements.append(Spacer(1, 0.1 * inch))

    # Multi-trip consideration
    if multi_trip and multi_trip.get('applicable'):
        elements.append(create_highlight_box(
            f"<b>Multi-Trip Consideration:</b> {multi_trip.get('note', '')}<br/>"
            f"Potential savings: {multi_trip.get('savingsPercent', '')} | "
            f"Annual multi-trip cost: {multi_trip.get('annualCost', 'N/A')}",
            INFO_LIGHT, INFO_BLUE
        ))
        elements.append(Spacer(1, 0.1 * inch))

    # EAZR CTA
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(create_highlight_box(
        "<b>Need help upgrading?</b> Open EAZR app to compare plans, get instant quotes, "
        "and pay monthly with EAZR EMI — no credit card needed.",
        BRAND_LIGHTER, BRAND_PRIMARY
    ))

    # ================================================================
    # PAGE 6: EMERGENCY REFERENCE CARD
    # ================================================================
    elements.append(PageBreak())

    # Dark navy background section header
    emg_header_style = ParagraphStyle(
        'emg_header', fontName=FONT_BOLD, fontSize=16,
        textColor=WHITE, alignment=TA_CENTER, leading=20
    )
    emg_sub_style = ParagraphStyle(
        'emg_sub', fontName=FONT_BOLD, fontSize=10,
        textColor=CHARCOAL, alignment=TA_LEFT, leading=14
    )
    emg_body_style = ParagraphStyle(
        'emg_body', fontName=FONT_REGULAR, fontSize=9,
        textColor=CHARCOAL, leading=13
    )
    emg_big_style = ParagraphStyle(
        'emg_big', fontName=FONT_BOLD, fontSize=14,
        textColor=BRAND_PRIMARY, alignment=TA_LEFT, leading=18
    )

    # Emergency card title
    emg_title_data = [[Paragraph("EMERGENCY REFERENCE CARD", emg_header_style)]]
    emg_title_table = Table(emg_title_data, colWidths=[6.3 * inch])
    emg_title_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), EMERGENCY_BG),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(emg_title_table)
    elements.append(Spacer(1, 0.05 * inch))
    elements.append(Paragraph("<i>Keep this page accessible during your trip</i>", ParagraphStyle(
        'emg_note', fontName=FONT_ITALIC, fontSize=8, textColor=MEDIUM_GRAY, alignment=TA_CENTER)))
    elements.append(Spacer(1, 0.1 * inch))

    # Policy details
    emg_policy_data = [
        [_pb("Policy Number"), _p(emergency_ref.get('policyNumber', policy_number))],
        [_pb("Valid From"), _p(emergency_ref.get('validFrom', start_date))],
        [_pb("Valid To"), _p(emergency_ref.get('validTo', end_date))],
        [_pb("Destinations"), _p(emergency_ref.get('destinations', destination))],
        [_pb("Medical Cover"), _p(emergency_ref.get('medicalCover', 'See policy'))],
    ]
    emg_pol_table = Table(emg_policy_data, colWidths=[2.0 * inch, 4.3 * inch])
    emg_pol_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('BACKGROUND', (0, 0), (-1, -1), WHISPER),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
    ]))
    elements.append(emg_pol_table)
    elements.append(Spacer(1, 0.15 * inch))

    # Helplines — PROMINENT
    helplines = emergency_ref.get('helplines', {})
    from_india = helplines.get('fromIndia', emergency_contacts.get('emergencyHelpline24x7', 'See policy'))
    from_abroad = helplines.get('fromAbroad', emergency_contacts.get('emergencyHelpline24x7', 'See policy'))
    whatsapp = helplines.get('whatsapp', '')
    email = helplines.get('email', emergency_contacts.get('claimsEmail', 'See policy'))

    elements.append(Paragraph("<b>EMERGENCY HELPLINES</b>", emg_sub_style))
    elements.append(Spacer(1, 0.05 * inch))

    helpline_data = [
        [Paragraph(f"<b>From India:</b>", emg_body_style), Paragraph(f"<b>{from_india}</b>", emg_big_style)],
        [Paragraph(f"<b>From Abroad:</b>", emg_body_style), Paragraph(f"<b>{from_abroad}</b>", emg_big_style)],
    ]
    if whatsapp:
        helpline_data.append([Paragraph("<b>WhatsApp:</b>", emg_body_style), Paragraph(f"<b>{whatsapp}</b>", emg_big_style)])
    helpline_data.append([Paragraph("<b>Claims Email:</b>", emg_body_style), Paragraph(f"<b>{email}</b>", emg_big_style)])

    helpline_table = Table(helpline_data, colWidths=[2.0 * inch, 4.3 * inch])
    helpline_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, -1), EMERGENCY_BG),
        ('TEXTCOLOR', (0, 0), (-1, -1), EMERGENCY_TEXT),
        ('BOX', (0, 0), (-1, -1), 1, EMERGENCY_ACCENT),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, EMERGENCY_ACCENT),
    ]))
    # Override text colors for the dark bg
    for row_data in helpline_data:
        for cell in row_data:
            if hasattr(cell, 'style'):
                cell.style = ParagraphStyle('emg_cell', parent=cell.style, textColor=EMERGENCY_TEXT)

    # Rebuild with white text
    helpline_data_white = []
    wt_style = ParagraphStyle('wt', fontName=FONT_REGULAR, fontSize=9, textColor=EMERGENCY_TEXT, leading=13)
    wt_big = ParagraphStyle('wt_big', fontName=FONT_BOLD, fontSize=14, textColor=EMERGENCY_ACCENT, leading=18)

    helpline_data_white.append([Paragraph("<b>From India:</b>", wt_style), Paragraph(f"<b>{from_india}</b>", wt_big)])
    helpline_data_white.append([Paragraph("<b>From Abroad:</b>", wt_style), Paragraph(f"<b>{from_abroad}</b>", wt_big)])
    if whatsapp:
        helpline_data_white.append([Paragraph("<b>WhatsApp:</b>", wt_style), Paragraph(f"<b>{whatsapp}</b>", wt_big)])
    helpline_data_white.append([Paragraph("<b>Claims Email:</b>", wt_style), Paragraph(f"<b>{email}</b>", wt_big)])

    helpline_table = Table(helpline_data_white, colWidths=[2.0 * inch, 4.3 * inch])
    helpline_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, -1), EMERGENCY_BG),
        ('BOX', (0, 0), (-1, -1), 1, EMERGENCY_ACCENT),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, EMERGENCY_ACCENT),
    ]))
    elements.append(helpline_table)
    elements.append(Spacer(1, 0.15 * inch))

    # Cashless network
    cashless = emergency_ref.get('cashlessNetwork', {})
    if cashless and cashless.get('available'):
        elements.append(Paragraph(f"<b>Cashless Network:</b> {cashless.get('networkName', 'Available')} — "
                                  f"Show your policy at network hospitals for cashless treatment.", emg_body_style))
        elements.append(Spacer(1, 0.1 * inch))

    # 5-Step claim procedure
    claim_steps = emergency_ref.get('claimSteps', [
        "Contact insurer helpline immediately (within 24 hours)",
        "Get a claim reference number and note it down",
        "Visit nearest network hospital or authorized facility",
        "Collect all medical reports, bills, and receipts",
        "Submit claim form with documents within 30 days",
    ])
    elements.append(Paragraph("<b>HOW TO CLAIM — 5 STEPS</b>", emg_sub_style))
    elements.append(Spacer(1, 0.05 * inch))

    for i, step in enumerate(claim_steps[:5]):
        step_text = step if isinstance(step, str) else str(step)
        elements.append(Paragraph(f"<b>Step {i + 1}:</b> {step_text}", emg_body_style))
        elements.append(Spacer(1, 0.02 * inch))

    elements.append(Spacer(1, 0.1 * inch))

    # Travelers
    travelers_list = emergency_ref.get('travelers', [])
    if not travelers_list and traveller_details:
        travelers_list = [
            {"name": t.get("name", "N/A"), "passport": t.get("passportNumber", "N/A")}
            for t in traveller_details if isinstance(t, dict)
        ]

    if travelers_list:
        elements.append(Paragraph("<b>TRAVELERS</b>", emg_sub_style))
        elements.append(Spacer(1, 0.03 * inch))
        tv_header = [_pb("Name"), _pb("Passport")]
        tv_rows = [tv_header]
        for tv in travelers_list:
            if isinstance(tv, dict):
                tv_rows.append([_p(tv.get('name', 'N/A')), _p(tv.get('passport', 'N/A'))])
        tv_table = Table(tv_rows, colWidths=[3.15 * inch, 3.15 * inch])
        tv_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('BACKGROUND', (0, 0), (-1, 0), CHARCOAL),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
        ]))
        elements.append(tv_table)

    # Footer disclaimer
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER_LIGHT))
    elements.append(Spacer(1, 0.05 * inch))
    elements.append(Paragraph(
        f"<b>Analysis Version:</b> 10.0 | <b>Generated:</b> {datetime.now().strftime('%d %b %Y %H:%M')} | "
        f"<b>Valid for:</b> Trip from {trip_start} to {trip_end}<br/>"
        "This analysis is based on the policy document provided. Actual coverage depends on specific policy terms "
        "and insurer's assessment. Always refer to your policy document for exact terms.",
        ParagraphStyle('v10_disclaimer', fontName=FONT_REGULAR, fontSize=7, textColor=LIGHT_GRAY,
                       alignment=TA_CENTER, leading=10)
    ))
    elements.append(Spacer(1, 0.05 * inch))
    elements.append(Paragraph(
        "<b>EAZR Policy Analysis | Clarity Before Crisis</b>",
        ParagraphStyle('v10_footer', fontName=FONT_BOLD, fontSize=8, textColor=BRAND_PRIMARY, alignment=TA_CENTER)
    ))

    # Build PDF
    pdf_doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)

    buffer.seek(0)
    logger.info(f"✅ Travel V10 insurance report generated successfully for policy {policy_number}")
    return buffer