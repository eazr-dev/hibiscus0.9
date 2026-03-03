"""
Health Insurance Policy Analysis Report Generator
Based on EAZR_01_Health_Insurance_PolicyAnalysisTab.md (V10)
8-Page Professional PDF Report

Pages:
1. Cover + Executive Summary (composite score, 4-score tiles, at-a-glance)
2. Score Deep-Dive (S1-S4 factor tables + interpretations)
3. Strengths & Gaps Complete (all strengths + all gaps + severity summary)
4-5. Scenario Simulations (all 10 scenarios + comparison table)
6. Recommendations Action Plan (quick wins + priority upgrades + investment)
7. Policy Reference Snapshot (compact core details)
8. Back Cover (branding + disclaimers)
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

# Import market data service for dynamic healthcare costs
from services.indian_market_data_service import (
    get_city_healthcare_costs,
    get_recommended_sum_insured,
    get_medical_inflation_rate,
    get_health_insurance_market_data
)

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

# V10 Score Colors per spec Section 6.4
SCORE_EXCELLENT = colors.HexColor('#22C55E')
SCORE_STRONG = colors.HexColor('#84CC16')
SCORE_ADEQUATE = colors.HexColor('#EAB308')
SCORE_MODERATE = colors.HexColor('#F97316')
SCORE_ATTENTION = colors.HexColor('#6B7280')
TABLE_HEADER_BG = colors.HexColor('#F9FAFB')
TABLE_BORDER = colors.HexColor('#E5E7EB')

# ==================== FONT CONFIGURATION ====================
FONT_REGULAR = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'
FONT_ITALIC = 'Helvetica-Oblique'
RUPEE_SYMBOL = 'Rs.'

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
            # Keep RUPEE_SYMBOL as 'Rs.' for reliable PDF rendering
            # The ₹ glyph doesn't render reliably across all ReportLab font configs
            break
except Exception as e:
    logger.warning(f"Could not register Unicode font: {e}")


def _sanitize_rupee(text):
    """Replace ₹ symbol with Rs. for reliable PDF rendering"""
    if not isinstance(text, str):
        return text
    return text.replace('₹', 'Rs.')


def format_currency(value, show_symbol=True):
    """Format currency with proper symbol and commas"""
    if value is None or value == 'N/A' or value == '':
        return 'N/A'
    try:
        num = float(value)
        formatted = f"{int(num):,}"
        return f"{RUPEE_SYMBOL}{formatted}" if show_symbol else formatted
    except (ValueError, TypeError):
        return str(value) if value else 'N/A'


def safe_int(value, default=0):
    """Safely convert value to int"""
    if value is None or value == 'N/A' or value == '':
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def safe_str(value, default='N/A'):
    """Safely convert value to string, sanitizing ₹ for PDF rendering"""
    if value is None or value == '' or value == 'N/A':
        return default
    result = str(value)
    return result.replace('₹', 'Rs.')


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


def get_v10_score_color(score):
    """Get V10 spec color for score gauge"""
    if score >= 90:
        return SCORE_EXCELLENT
    elif score >= 75:
        return SCORE_STRONG
    elif score >= 60:
        return SCORE_ADEQUATE
    elif score >= 40:
        return SCORE_MODERATE
    else:
        return SCORE_ATTENTION


def get_severity_color(severity):
    """Get color for gap severity"""
    severity = str(severity).lower()
    if severity == 'high':
        return WARNING_AMBER
    elif severity == 'medium':
        return colors.HexColor('#EAB308')
    else:
        return MEDIUM_GRAY


def get_health_claims_helpline(insurer_name: str) -> str:
    """Get claims helpline number for health insurance providers"""
    if not insurer_name or insurer_name == 'N/A':
        return "See policy document"

    insurer_lower = insurer_name.lower()

    helplines = {
        'star health': '1800-425-2255',
        'star': '1800-425-2255',
        'care health': '1800-102-4488',
        'care': '1800-102-4488',
        'hdfc ergo': '1800-266-0700',
        'hdfc': '1800-266-0700',
        'icici lombard': '1800-266-7766',
        'icici': '1800-266-7766',
        'bajaj allianz': '1800-209-5858',
        'bajaj': '1800-209-5858',
        'max bupa': '1800-102-0011',
        'niva bupa': '1800-102-0011',
        'bupa': '1800-102-0011',
        'aditya birla': '1800-270-7000',
        'birla': '1800-270-7000',
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
        'manipal cigna': '1800-102-4462',
        'cigna': '1800-102-4462',
        'royal sundaram': '1800-568-9999',
        'sundaram': '1800-568-9999',
        'future generali': '1800-220-233',
        'iffco tokio': '1800-103-5499',
        'cholamandalam': '1800-103-6040',
        'chola ms': '1800-103-6040',
        'bharti axa': '1800-102-4444',
        'magma hdi': '1800-102-1700',
        'digit': '1800-258-5956',
        'acko': '1800-266-2256',
        'go digit': '1800-258-5956',
    }

    for key, number in helplines.items():
        if key in insurer_lower:
            return number

    return "See policy document"


# Note: get_city_healthcare_costs is now imported from indian_market_data_service
# This provides dynamic, live market data instead of hardcoded values


class ModernHeader:
    @staticmethod
    def draw(canvas, doc_template):
        canvas.saveState()
        canvas.setFillColor(BRAND_PRIMARY)
        canvas.rect(0, A4[1] - 0.6*inch, A4[0], 0.6*inch, fill=True, stroke=False)

        canvas.setFont(FONT_BOLD, 18)
        canvas.setFillColor(WHITE)
        canvas.drawString(0.6*inch, A4[1] - 0.4*inch, "EAZR")

        canvas.setFont(FONT_REGULAR, 9)
        canvas.setFillColor(colors.HexColor('#B0E0DC'))
        canvas.drawCentredString(A4[0] / 2, A4[1] - 0.4*inch, "Health Insurance Analysis Report")

        canvas.setFont(FONT_REGULAR, 8)
        canvas.setFillColor(WHITE)
        canvas.drawRightString(A4[0] - 0.6*inch, A4[1] - 0.4*inch, f"Page {doc_template.page}")

        canvas.restoreState()


class ModernFooter:
    report_id = ""  # Set before build

    @staticmethod
    def draw(canvas, doc_template):
        canvas.saveState()
        canvas.setStrokeColor(BORDER_LIGHT)
        canvas.setLineWidth(0.5)
        canvas.line(0.6*inch, 0.55*inch, A4[0] - 0.6*inch, 0.55*inch)

        canvas.setFont(FONT_REGULAR, 7)
        canvas.setFillColor(LIGHT_GRAY)
        rid = ModernFooter.report_id or ""
        canvas.drawString(0.6*inch, 0.40*inch, f"EAZR Digipayments Pvt Ltd | Report ID: {rid} | {datetime.now().strftime('%d %b %Y')}")
        canvas.setFont(FONT_REGULAR, 6)
        canvas.drawString(0.6*inch, 0.25*inch, "This is an AI-generated analysis. Not a substitute for professional insurance advice.")

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


def create_score_bar(score, width=4*inch, height=10, color=None):
    """Create a colored score bar using Table cells — renders reliably with any font"""
    pct = min(max(score / 100.0, 0), 1)
    filled_w = max(0.05 * inch, pct * width)
    empty_w = max(0, width - filled_w)
    bar_color = color or get_v10_score_color(score)
    data = [['', '']]
    tbl = Table(data, colWidths=[filled_w, empty_w], rowHeights=[height])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), bar_color),
        ('BACKGROUND', (1, 0), (1, 0), BORDER_LIGHT),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    return tbl


def generate_health_insurance_report(policy_data: dict, analysis_data: dict) -> BytesIO:
    """
    Generate a comprehensive health insurance analysis report based on V10 spec.
    8-page PDF with 4-score system, gap analysis, scenario simulations, and recommendations.
    """
    try:
        buffer = BytesIO()
        pdf_doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=0.6*inch, leftMargin=0.6*inch,
            topMargin=0.85*inch, bottomMargin=0.7*inch,
            title="Health Insurance Policy Analysis",
            author="EAZR Insurance Platform"
        )

        elements = []
        styles = create_styles()

        # ==================== EXTRACT ALL DATA ====================
        policy_number = policy_data.get('policyNumber', 'N/A')
        insurer_name = policy_data.get('insuranceProvider', 'N/A')
        policy_holder_name = policy_data.get('policyHolderName', 'Dear Policyholder')
        _name_parts = policy_holder_name.split() if policy_holder_name and policy_holder_name != 'N/A' else []
        _title_prefixes = {'mr', 'mrs', 'ms', 'miss', 'dr', 'shri', 'smt', 'sri'}
        if len(_name_parts) >= 2 and _name_parts[0].lower().rstrip('.') in _title_prefixes:
            first_name = _name_parts[1]
        elif _name_parts:
            first_name = _name_parts[0]
        else:
            first_name = 'there'
        sum_insured = safe_int(policy_data.get('sumAssured', 0) or policy_data.get('coverageAmount', 0))
        premium = safe_int(policy_data.get('premium', 0))
        premium_frequency = policy_data.get('premiumFrequency', 'yearly')
        start_date = policy_data.get('startDate', 'N/A')
        end_date = policy_data.get('endDate', 'N/A')

        category_data = policy_data.get('categorySpecificData', {})
        policy_identification = category_data.get('policyIdentification', {})
        coverage_details = category_data.get('coverageDetails', {})
        premium_details = category_data.get('premiumDetails', {})
        waiting_periods = category_data.get('waitingPeriods', {})
        room_rent_details = category_data.get('roomRentDetails', {})
        co_payment = category_data.get('copayDetails', category_data.get('coPayment', {}))
        deductibles = category_data.get('deductibles', {})
        sub_limits = category_data.get('subLimits', {})
        network_hospitals = category_data.get('networkHospitals', {})
        exclusions_data = category_data.get('exclusions', {})
        members_covered_raw = category_data.get('membersCovered', []) or category_data.get('insuredMembers', [])
        # Normalize member structure - handle both formats (name/age/relationship and memberName/memberAge/memberRelationship)
        members_covered = []
        for member in members_covered_raw:
            if isinstance(member, dict):
                normalized = {
                    'name': member.get('name') or member.get('memberName') or 'N/A',
                    'age': member.get('age') or member.get('memberAge') or 'N/A',
                    'relationship': member.get('relationship') or member.get('memberRelationship') or 'N/A'
                }
                members_covered.append(normalized)
            elif isinstance(member, str):
                # Handle string format like "Member Name - Relationship"
                parts = member.split(' - ')
                if len(parts) >= 2:
                    members_covered.append({'name': parts[0], 'age': 'N/A', 'relationship': parts[1]})
                else:
                    members_covered.append({'name': member, 'age': 'N/A', 'relationship': 'N/A'})
        pre_existing = category_data.get('preExistingConditions', {})
        benefits_raw = category_data.get('benefits', {})
        accumulated_benefits = category_data.get('accumulatedBenefits', {})
        add_on_policies = category_data.get('addOnPolicies', {})
        policy_history = category_data.get('policyHistory', {})
        network_info = category_data.get('networkInfo', {})
        premium_ncb = category_data.get('premiumNcb', {})

        # Build comprehensive benefits object with fallbacks from multiple sources
        def check_benefit_in_list(benefit_keywords, coverage_details, key_benefits_list):
            """Check if a benefit exists in coverageDetails or keyBenefits list"""
            # Check coverageDetails first
            for key in benefit_keywords:
                if coverage_details.get(key):
                    return True
            # Check keyBenefits list
            if isinstance(key_benefits_list, list):
                for benefit in key_benefits_list:
                    if isinstance(benefit, str):
                        benefit_lower = benefit.lower()
                        for keyword in benefit_keywords:
                            if keyword.lower() in benefit_lower:
                                return True
            return False

        key_benefits_list = analysis_data.get('keyBenefits', []) or policy_data.get('keyBenefitsSummary', [])

        # Build proper benefits structure with fallbacks
        # Check restoration in multiple sources
        restoration_available = False
        restoration_type = 'Up to SI'

        # Check in benefits_raw
        if isinstance(benefits_raw.get('restoration'), dict):
            restoration_available = benefits_raw.get('restoration', {}).get('available', False)
            restoration_type = benefits_raw.get('restoration', {}).get('type', 'Up to SI')
        elif benefits_raw.get('restoration'):
            restoration_available = True
            restoration_type = str(benefits_raw.get('restoration'))

        # Check in coverage_details
        if not restoration_available:
            restoration_val = coverage_details.get('restoration') or coverage_details.get('restorationBenefit')
            if restoration_val and str(restoration_val).lower() not in ['none', 'no', 'n/a', '0', 'false']:
                restoration_available = True
                restoration_type = str(restoration_val) if restoration_val != True else 'Up to SI'

        # Check in keyBenefits list
        if not restoration_available:
            restoration_available = check_benefit_in_list(['restoration', 'recharge', 'automatic recharge', 'restore'], coverage_details, key_benefits_list)

        benefits = {
            'restoration': {
                'available': restoration_available,
                'type': restoration_type if restoration_type and restoration_type.lower() not in ['true', 'yes'] else 'Up to SI'
            },
            'noClaimBonus': {
                'available': (
                    benefits_raw.get('noClaimBonus', {}).get('available', False) if isinstance(benefits_raw.get('noClaimBonus'), dict)
                    else bool(benefits_raw.get('noClaimBonus'))
                    or bool(premium_ncb.get('ncbPercentage'))
                    or check_benefit_in_list(['no claim bonus', 'ncb', 'cumulative bonus'], coverage_details, key_benefits_list)
                ),
                'percentage': (
                    benefits_raw.get('noClaimBonus', {}).get('percentage') if isinstance(benefits_raw.get('noClaimBonus'), dict)
                    else premium_ncb.get('ncbPercentage', '10% per year')
                ),
                'accumulatedAmount': (
                    benefits_raw.get('noClaimBonus', {}).get('accumulatedAmount') if isinstance(benefits_raw.get('noClaimBonus'), dict)
                    else accumulated_benefits.get('accumulatedNcbAmount')
                ),
                'maxPercentage': (
                    benefits_raw.get('noClaimBonus', {}).get('maxPercentage') if isinstance(benefits_raw.get('noClaimBonus'), dict)
                    else '50%'
                )
            },
            'ayushCovered': (
                benefits_raw.get('ayushCovered', False)
                or bool(coverage_details.get('ayushTreatment'))
                or check_benefit_in_list(['ayush', 'ayurveda', 'homeopathy', 'alternative treatment'], coverage_details, key_benefits_list)
            ),
            'ayushLimit': benefits_raw.get('ayushLimit', 'Up to SI'),
            'mentalHealthCovered': (
                benefits_raw.get('mentalHealthCovered', False)
                or bool(coverage_details.get('mentalHealthCover'))
                or check_benefit_in_list(['mental health', 'psychiatric'], coverage_details, key_benefits_list)
            ),
            'dayCareCovered': (
                benefits_raw.get('dayCareCovered', False)
                or bool(coverage_details.get('dayCareProcedures'))
                or check_benefit_in_list(['day care', 'daycare'], coverage_details, key_benefits_list)
            ),
            'dayCareCoverageType': benefits_raw.get('dayCareCoverageType', 'Up to SI') if benefits_raw.get('dayCareCovered') or coverage_details.get('dayCareProcedures') else 'Limited'
        }

        # Add-on policy benefits for display
        add_on_info = {
            'hasAddOn': add_on_policies.get('hasAddOn', False),
            'addOnName': add_on_policies.get('addOnName'),
            'claimShield': add_on_policies.get('claimShield', False),
            'ncbShield': add_on_policies.get('ncbShield', False),
            'inflationShield': add_on_policies.get('inflationShield', False),
            'inflationShieldAmount': accumulated_benefits.get('accumulatedInflationShield')
        }

        # Total effective coverage calculation
        total_effective_coverage = accumulated_benefits.get('totalEffectiveCoverage')
        if not total_effective_coverage and sum_insured > 0:
            ncb_amount = 0
            inflation_amount = 0
            try:
                if accumulated_benefits.get('accumulatedNcbAmount'):
                    ncb_str = str(accumulated_benefits.get('accumulatedNcbAmount', '0'))
                    ncb_amount = safe_int(ncb_str.replace('₹', '').replace(',', '').replace('Rs.', '').strip())
                if accumulated_benefits.get('accumulatedInflationShield'):
                    inf_str = str(accumulated_benefits.get('accumulatedInflationShield', '0'))
                    inflation_amount = safe_int(inf_str.replace('₹', '').replace(',', '').replace('Rs.', '').strip())
            except:
                pass
            total_effective_coverage = sum_insured + ncb_amount + inflation_amount

        protection_score = analysis_data.get('protectionScore', 0)
        protection_label = analysis_data.get('protectionScoreLabel', 'Needs Review')

        # Handle coverageGaps - can be array directly or dict with 'gaps' key
        coverage_gaps_raw = analysis_data.get('coverageGaps', [])
        if isinstance(coverage_gaps_raw, dict):
            coverage_gaps = coverage_gaps_raw.get('gaps', [])
        elif isinstance(coverage_gaps_raw, list):
            coverage_gaps = coverage_gaps_raw
        else:
            coverage_gaps = []

        # Also check keyConcerns as fallback for gaps
        if not coverage_gaps:
            key_concerns = analysis_data.get('keyConcerns', [])
            if isinstance(key_concerns, list) and key_concerns:
                # Convert keyConcerns to coverage_gaps format
                coverage_gaps = []
                for concern in key_concerns:
                    if isinstance(concern, dict):
                        coverage_gaps.append({
                            'title': concern.get('title', ''),
                            'description': concern.get('brief', concern.get('description', '')),
                            'severity': concern.get('severity', 'medium')
                        })

        # Handle keyBenefits with coverageStrengths as fallback
        key_benefits = analysis_data.get('keyBenefits', [])
        if not key_benefits:
            # Use coverageStrengths as fallback
            coverage_strengths = analysis_data.get('coverageStrengths', [])
            if isinstance(coverage_strengths, list):
                key_benefits = []
                for strength in coverage_strengths:
                    if isinstance(strength, dict):
                        # Convert coverageStrengths format to keyBenefits format
                        benefit_text = strength.get('details', strength.get('area', ''))
                        if benefit_text:
                            key_benefits.append(benefit_text)

        recommendations = analysis_data.get('recommendations', []) if isinstance(analysis_data.get('recommendations'), list) else []

        # Fallback: Build recommendations from whatYouShouldDo if recommendations is empty
        if not recommendations:
            what_you_should_do = analysis_data.get('whatYouShouldDo', {})
            if isinstance(what_you_should_do, dict):
                recommendations = []
                # Immediate action = high priority
                immediate = what_you_should_do.get('immediate', {})
                if isinstance(immediate, dict) and immediate.get('action'):
                    recommendations.append({
                        'priority': 'high',
                        'title': immediate.get('action', ''),
                        'description': immediate.get('brief', '')
                    })
                # Short-term action = medium priority
                short_term = what_you_should_do.get('shortTerm', {})
                if isinstance(short_term, dict) and short_term.get('action'):
                    recommendations.append({
                        'priority': 'medium',
                        'title': short_term.get('action', ''),
                        'description': short_term.get('brief', '')
                    })
                # Ongoing action = low priority
                ongoing = what_you_should_do.get('ongoing', {})
                if isinstance(ongoing, dict) and ongoing.get('action'):
                    recommendations.append({
                        'priority': 'low',
                        'title': ongoing.get('action', ''),
                        'description': ongoing.get('brief', '')
                    })

        plan_name = policy_identification.get('productName') or policy_identification.get('planName', 'Health Insurance Plan')
        policy_type = policy_identification.get('policyType', 'Individual')

        # Room rent info
        room_rent_limit = room_rent_details.get('roomRentLimit', 'No Limit')
        room_rent_type = room_rent_details.get('roomRentType', 'Single Private Room')
        room_rent_capping = room_rent_details.get('roomRentCapping', 'None')

        # Co-payment
        co_pay_percentage = safe_int(co_payment.get('generalCopay', co_payment.get('coPaymentPercentage', 0)))
        co_pay_applicable = bool(co_pay_percentage > 0) or co_payment.get('coPaymentApplicable', False)

        # Deductible
        deductible_amount = safe_int(deductibles.get('deductibleAmount', 0))

        # Waiting periods - extract numeric values from strings like "30 days", "48 months"
        def extract_waiting_period_value(value, default, unit='days'):
            """Extract numeric value from waiting period string like '30 days' or '48 months'"""
            if value is None or value == '' or value == 'N/A':
                return default
            if isinstance(value, (int, float)):
                return int(value)
            if isinstance(value, str):
                import re
                # Try to extract number from string like "30 days", "48 months", "36 Months"
                match = re.search(r'(\d+)\s*(days?|months?|years?)?', value, re.IGNORECASE)
                if match:
                    num = int(match.group(1))
                    found_unit = match.group(2).lower() if match.group(2) else unit
                    # Convert years to months if needed
                    if 'year' in found_unit:
                        return num * 12 if 'month' in unit else num
                    return num
            return default

        initial_waiting = extract_waiting_period_value(waiting_periods.get('initialWaitingPeriod'), 30, 'days')
        ped_waiting = extract_waiting_period_value(waiting_periods.get('preExistingDiseaseWaiting'), 48, 'months')
        specific_waiting = extract_waiting_period_value(waiting_periods.get('specificDiseaseWaiting'), 24, 'months')
        maternity_waiting = extract_waiting_period_value(waiting_periods.get('maternityWaiting'), 0, 'months')

        # Override waiting periods if waived via add-ons or portability continuity benefit
        try:
            from services.protection_score_calculator import _detect_waiting_waivers
            _rpt_waivers = _detect_waiting_waivers(category_data)
            _waiting_waived_initial = _rpt_waivers["initial"]
            _waiting_waived_ped = _rpt_waivers["ped"]
            _waiting_waived_specific = _rpt_waivers["specific"]
            if _waiting_waived_initial:
                initial_waiting = 0
            if _waiting_waived_ped:
                ped_waiting = 0
            if _waiting_waived_specific:
                specific_waiting = 0
        except Exception:
            _waiting_waived_initial = False
            _waiting_waived_ped = False
            _waiting_waived_specific = False

        # Network - use network_info for additional data like hospitals count and ambulance cover
        network_count = safe_int(network_hospitals.get('networkCount', 0))
        # Fallback to networkInfo if networkCount is 0
        if network_count == 0 and network_info.get('networkHospitalsCount'):
            network_count_str = str(network_info.get('networkHospitalsCount', '0'))
            # Extract number from string like "16000+" or "16,000"
            import re
            match = re.search(r'(\d[\d,]*)', network_count_str.replace(',', ''))
            if match:
                network_count = safe_int(match.group(1).replace(',', ''))
        # Fallback to insurer database when policy document doesn't specify
        if network_count == 0 and insurer_name:
            try:
                from services.protection_score_calculator import _lookup_network_hospital_count
                network_count = _lookup_network_hospital_count(insurer_name)
            except Exception:
                pass
        tpa_name = (network_hospitals.get('tpaName')
                    or network_info.get('tpaName')
                    or network_info.get('tpa')
                    or category_data.get('claimInfo', {}).get('tpaName')
                    or 'Self (In-house claims)')

        # Ambulance cover - from network_info or sub_limits
        ambulance_cover = network_info.get('ambulanceCover') or sub_limits.get('ambulanceLimit', 'Check policy')
        if ambulance_cover and 'SI' in str(ambulance_cover).upper():
            ambulance_cover = 'Up to SI'

        # City for cost calculations
        city = policy_data.get('city', 'Mumbai')
        city_costs = get_city_healthcare_costs(city)

        # ==================== V10 DATA EXTRACTION ====================
        protection_readiness = analysis_data.get('protectionReadiness', {})
        v10_scores = protection_readiness.get('scores', {})
        v10_verdict = protection_readiness.get('verdict', {})
        composite_score = protection_readiness.get('compositeScore', protection_score)

        v10_strengths = analysis_data.get('coverageStrengths', [])
        if not isinstance(v10_strengths, list):
            v10_strengths = []

        gaps_summary = {}
        if isinstance(coverage_gaps_raw, dict):
            gaps_summary = coverage_gaps_raw.get('summary', {})

        # Recompute gap severity counts from actual gaps if summary is missing/inconsistent
        if coverage_gaps:
            _recomputed_high = sum(1 for g in coverage_gaps if isinstance(g, dict) and str(g.get('severity', '')).lower() == 'high')
            _recomputed_medium = sum(1 for g in coverage_gaps if isinstance(g, dict) and str(g.get('severity', '')).lower() == 'medium')
            _recomputed_low = sum(1 for g in coverage_gaps if isinstance(g, dict) and str(g.get('severity', '')).lower() in ('low', 'info'))
            _recomputed_total = _recomputed_high + _recomputed_medium + _recomputed_low
            # Override if summary was empty or had zero total despite actual gaps existing
            if not gaps_summary or gaps_summary.get('total', 0) == 0:
                gaps_summary = {
                    'high': _recomputed_high,
                    'medium': _recomputed_medium,
                    'info': _recomputed_low,
                    'total': _recomputed_total,
                }

        scenarios_data = analysis_data.get('scenarios', {})
        if isinstance(scenarios_data, dict):
            primary_scenario_id = scenarios_data.get('primaryScenarioId', '')
            simulations = scenarios_data.get('simulations', [])
        elif isinstance(scenarios_data, list):
            primary_scenario_id = ''
            simulations = scenarios_data
        else:
            primary_scenario_id = ''
            simulations = []

        recs_data = analysis_data.get('recommendations', {})
        if isinstance(recs_data, dict):
            quick_wins = recs_data.get('quickWins', [])
            priority_upgrades = recs_data.get('priorityUpgrades', [])
            total_upgrade_cost = recs_data.get('totalUpgradeCost', {})
        else:
            quick_wins = []
            priority_upgrades = recs_data if isinstance(recs_data, list) else []
            total_upgrade_cost = {}

        import hashlib
        report_id_hash = hashlib.md5(f"{policy_number}{datetime.now().isoformat()}".encode()).hexdigest()[:8].upper()
        report_id = f"EAZ-HLT-{datetime.now().strftime('%Y-%m-%d')}-{report_id_hash}"
        ModernFooter.report_id = report_id

        worst_oop = 0
        worst_scenario_name = ''
        for sim in simulations:
            if isinstance(sim, dict):
                sim_oop = safe_int(sim.get('outOfPocket', sim.get('youPay', 0)))
                if sim_oop > worst_oop:
                    worst_oop = sim_oop
                    worst_scenario_name = sim.get('scenarioName', sim.get('name', ''))

        def _color_hex(c):
            """Get hex string from ReportLab color for use in Paragraph HTML"""
            try:
                if hasattr(c, 'hexval'):
                    hv = c.hexval()
                    # hexval() returns '0xRRGGBB', convert to '#RRGGBB' for HTML
                    return '#' + hv[2:] if hv.startswith('0x') else hv
                return '#{:02x}{:02x}{:02x}'.format(int(c.red * 255), int(c.green * 255), int(c.blue * 255))
            except Exception:
                return '#374151'

        # ==================== PAGE 1: COVER + EXECUTIVE SUMMARY ====================
        elements.append(Paragraph("HEALTH INSURANCE ANALYSIS REPORT", styles['main_title']))
        elements.append(Spacer(1, 0.15*inch))
        elements.append(Paragraph(f"Prepared for: <b>{safe_str(policy_holder_name)}</b>", styles['body']))
        elements.append(Paragraph(f"Policy: {safe_str(insurer_name)} — {safe_str(plan_name)}", styles['body']))
        elements.append(Paragraph(f"Policy No: {safe_str(policy_number)}", styles['body']))
        elements.append(Paragraph(f"Valid: {start_date} to {end_date}", styles['body']))
        elements.append(Spacer(1, 0.2*inch))

        elements.append(HRFlowable(width="100%", thickness=2, color=BRAND_PRIMARY, spaceAfter=10))
        elements.append(Spacer(1, 0.1*inch))

        score_color_v10 = get_v10_score_color(composite_score)
        verdict_label = v10_verdict.get('label', protection_label)
        verdict_summary = v10_verdict.get('summary', '')

        score_style = ParagraphStyle('p1_score', fontName=FONT_BOLD, fontSize=14, textColor=CHARCOAL, alignment=TA_CENTER, leading=18, spaceAfter=8)
        elements.append(Paragraph("PROTECTION READINESS SCORE", score_style))
        elements.append(Spacer(1, 0.1*inch))

        score_num_style = ParagraphStyle('p1_score_num', fontName=FONT_BOLD, fontSize=36, textColor=score_color_v10, alignment=TA_CENTER, leading=44, spaceAfter=8)
        elements.append(Paragraph(f"{composite_score}/100", score_num_style))
        elements.append(Spacer(1, 0.05*inch))

        verdict_style = ParagraphStyle('p1_verdict', fontName=FONT_BOLD, fontSize=14, textColor=score_color_v10, alignment=TA_CENTER, leading=18, spaceAfter=8)
        elements.append(Paragraph(verdict_label.upper(), verdict_style))

        if verdict_summary:
            verdict_sum_style = ParagraphStyle('p1_vsum', fontName=FONT_REGULAR, fontSize=10, textColor=SLATE, alignment=TA_CENTER, leading=14, spaceAfter=12)
            elements.append(Paragraph(verdict_summary, verdict_sum_style))
        elements.append(Spacer(1, 0.15*inch))

        # 4-Score Summary Tiles
        s1 = v10_scores.get('s1', {})
        s2 = v10_scores.get('s2', {})
        s3 = v10_scores.get('s3')
        s4 = v10_scores.get('s4', {})

        tile_cells = []
        for label_lines, score_data in [("Emergency\nReadiness", s1), ("Critical\nIllness", s2), ("Family\nProtection", s3), ("Coverage\nStability", s4)]:
            if not score_data or not isinstance(score_data, dict):
                continue
            sv = score_data.get('score', 0)
            sc = _color_hex(get_v10_score_color(sv))
            lbl = label_lines.replace('\n', '<br/>')
            tile_cells.append(Paragraph(
                f'<font size="8" color="{_color_hex(MEDIUM_GRAY)}">{lbl}</font><br/>'
                f'<font size="14" color="{sc}"><b>{sv}/100</b></font>',
                ParagraphStyle(f'tile_{len(tile_cells)}', alignment=TA_CENTER, leading=14)
            ))

        if tile_cells:
            tw = 6.2 * inch / len(tile_cells)
            tile_table = Table([tile_cells], colWidths=[tw] * len(tile_cells), rowHeights=[0.8*inch])
            tile_style_cmds = [
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
                ('BACKGROUND', (0, 0), (-1, -1), WHISPER),
            ]
            tile_table.setStyle(TableStyle(tile_style_cmds))
            elements.append(tile_table)

        elements.append(Spacer(1, 0.2*inch))
        elements.append(HRFlowable(width="100%", thickness=2, color=BRAND_PRIMARY, spaceAfter=10))

        # At a Glance box
        elements.append(create_subsection_header("At a Glance"))
        elements.append(Spacer(1, 0.05*inch))

        effective_coverage = total_effective_coverage or sum_insured
        gap_count_str = ''
        if gaps_summary:
            parts = []
            if gaps_summary.get('high', 0) > 0:
                parts.append(f"{gaps_summary['high']} High")
            if gaps_summary.get('medium', 0) > 0:
                parts.append(f"{gaps_summary['medium']} Medium")
            if gaps_summary.get('info', 0) > 0:
                parts.append(f"{gaps_summary['info']} Info")
            gap_count_str = ' · '.join(parts) if parts else 'None detected'
        else:
            gap_count_str = f"{len(coverage_gaps)} found" if coverage_gaps else 'None detected'

        upgrade_annual = safe_int(total_upgrade_cost.get('annual', 0))
        upgrade_monthly = safe_int(total_upgrade_cost.get('monthlyEmi', 0))
        upgrade_str = f"{format_currency(upgrade_annual)}/yr" if upgrade_annual > 0 else 'No upgrades needed'
        if upgrade_monthly > 0:
            upgrade_str += f" → {format_currency(upgrade_monthly)}/mo with EAZR"

        glance_data = [
            ["Effective Coverage", format_currency(effective_coverage)],
            ["Gaps Found", gap_count_str],
            ["Worst-case OOP", f"{format_currency(worst_oop)} ({worst_scenario_name})" if worst_oop > 0 else 'Minimal'],
            ["Upgrade Cost", upgrade_str],
        ]
        glance_table = create_key_value_table(glance_data, [2.5*inch, 3.7*inch], BRAND_PRIMARY)
        elements.append(glance_table)
        elements.append(Spacer(1, 0.2*inch))

        meta_style = ParagraphStyle('p1_meta', fontName=FONT_REGULAR, fontSize=7, textColor=LIGHT_GRAY, alignment=TA_CENTER)
        elements.append(Paragraph(
            f"Report ID: {report_id} | Generated: {datetime.now().strftime('%d %b %Y %H:%M')} | EAZR Digipayments Pvt Ltd",
            meta_style
        ))
        elements.append(PageBreak())

        # ==================== PAGE 2: SCORE DEEP-DIVE ====================
        elements.append(create_section_header("Protection Readiness Scores — Detailed", styles))
        elements.append(Spacer(1, 0.1*inch))

        def _generate_score_interpretation(score_name, score_val, factors):
            if not factors:
                return ""
            sorted_f = sorted(
                [f for f in factors if isinstance(f, dict) and f.get('pointsMax', 0) > 0],
                key=lambda f: f.get('pointsEarned', 0) / max(f.get('pointsMax', 1), 1)
            )
            weakest = sorted_f[0] if sorted_f else None
            if score_val >= 85:
                text = f"Your {score_name.lower()} coverage is excellent with minimal gaps."
            elif score_val >= 70:
                text = f"Your {score_name.lower()} coverage is generally strong but has room for improvement."
            elif score_val >= 50:
                text = f"Your {score_name.lower()} coverage has notable gaps that could lead to significant out-of-pocket expenses."
            else:
                text = f"Your {score_name.lower()} coverage needs immediate attention — significant vulnerabilities exist."
            if weakest:
                weak_name = weakest.get('name', '')
                weak_pct = int(weakest.get('pointsEarned', 0) / max(weakest.get('pointsMax', 1), 1) * 100)
                text += f" The weakest area is {weak_name} (scoring {weak_pct}% of possible points)."
                if score_val < 85:
                    gain = weakest.get('pointsMax', 0) - weakest.get('pointsEarned', 0)
                    text += f" Addressing this alone could improve your score by up to {gain} points."
            return text

        # Compact styles for score deep-dive to fit 4 scores on 2 pages
        score_body_s = ParagraphStyle('score_body', fontName=FONT_REGULAR, fontSize=7.5, textColor=SLATE, leading=10, spaceAfter=2)
        score_title_s = ParagraphStyle('score_title', fontName=FONT_BOLD, fontSize=9, textColor=CHARCOAL, leading=12, spaceAfter=4)

        def _build_score_block(score_data, score_name, score_num_label):
            if not score_data or not isinstance(score_data, dict):
                return
            sv = score_data.get('score', 0)
            sl = score_data.get('label', '')
            factors = score_data.get('factors', [])
            sc = get_v10_score_color(sv)

            elements.append(Paragraph(
                f"<b>{score_num_label} {score_name}</b> — {sv}/100 ({sl})",
                score_title_s
            ))

            elements.append(create_score_bar(sv, width=5.7*inch, height=10, color=sc))

            if factors:
                _fc_style = ParagraphStyle('FactorCell', fontName=FONT_REGULAR, fontSize=7.5, textColor=CHARCOAL, leading=9)
                _fh_style = ParagraphStyle('FactorHdr', fontName=FONT_BOLD, fontSize=7.5, textColor=WHITE, leading=9)
                factor_data = [[
                    Paragraph("Factor", _fh_style),
                    Paragraph("Your Policy", _fh_style),
                    Paragraph("Benchmark", _fh_style),
                    Paragraph("Points", _fh_style),
                ]]
                for fct in factors:
                    if isinstance(fct, dict):
                        factor_data.append([
                            Paragraph(safe_str(fct.get('name', '')), _fc_style),
                            Paragraph(safe_str(fct.get('yourPolicy', '')), _fc_style),
                            Paragraph(safe_str(fct.get('benchmark', '')), _fc_style),
                            Paragraph(f"{fct.get('pointsEarned', 0)}/{fct.get('pointsMax', 0)}", _fc_style),
                        ])
                if len(factor_data) > 1:
                    tot_e = sum(f.get('pointsEarned', 0) for f in factors if isinstance(f, dict))
                    tot_m = sum(f.get('pointsMax', 0) for f in factors if isinstance(f, dict))
                    factor_data.append(["TOTAL", "", "", f"{tot_e}/{tot_m}"])
                    ft = Table(factor_data, colWidths=[1.9*inch, 1.5*inch, 1.5*inch, 0.8*inch])
                    ft.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
                        ('FONTNAME', (0, 1), (-1, -1), FONT_REGULAR),
                        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
                        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
                        ('TEXTCOLOR', (0, 1), (-1, -1), CHARCOAL),
                        ('BACKGROUND', (0, 0), (-1, 0), BRAND_PRIMARY),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
                        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
                    ] + [('BACKGROUND', (0, i), (-1, i), WHISPER if i % 2 == 0 else WHITE) for i in range(1, len(factor_data))]))
                    elements.append(ft)

            interp = _generate_score_interpretation(score_name, sv, factors)
            if interp:
                elements.append(Paragraph(f"<b>What This Means:</b> {interp}", score_body_s))
            elements.append(Spacer(1, 0.08*inch))

        _build_score_block(s1, "Emergency Hospitalization Readiness", "SCORE 1:")
        _build_score_block(s2, "Critical Illness Preparedness", "SCORE 2:")
        elements.append(PageBreak())

        # ==================== PAGE 3: SCORES CONTINUED ====================
        elements.append(create_section_header("Protection Readiness Scores — Continued", styles))
        elements.append(Spacer(1, 0.1*inch))
        if s3 and isinstance(s3, dict):
            _build_score_block(s3, "Family Protection", "SCORE 3:")
        else:
            elements.append(Paragraph(
                "<i>Score 3: Family Protection — Not applicable (Individual policy)</i>",
                score_body_s
            ))
            elements.append(Spacer(1, 0.05*inch))
        _build_score_block(s4, "Coverage Stability", "SCORE 4:")
        elements.append(PageBreak())

        # ==================== PAGE 3: STRENGTHS & GAPS ====================
        elements.append(create_section_header("What's Working & Where You're Exposed", styles))
        elements.append(Spacer(1, 0.1*inch))

        # Strengths
        elements.append(create_subsection_header("Coverage Strengths"))
        if v10_strengths:
            str_data = [["Strength", "Why It Matters"]]
            for st in v10_strengths:
                if isinstance(st, dict):
                    str_data.append([safe_str(st.get('title', '')), safe_str(st.get('reason', ''))])
            if len(str_data) > 1:
                str_table = create_modern_table(str_data, [2.5*inch, 3.7*inch])
                elements.append(str_table)
        elif key_benefits:
            for i, b in enumerate(key_benefits[:5]):
                b_text = b if isinstance(b, str) else b.get('description', b.get('name', '')) if isinstance(b, dict) else str(b)
                elements.append(Paragraph(f"- {b_text}", styles['body']))
        else:
            elements.append(Paragraph("No specific strengths identified.", styles['body']))
        elements.append(Spacer(1, 0.15*inch))

        # Complete Gap Table — dynamic columns based on available data
        elements.append(create_subsection_header(f"Coverage Gaps ({len(coverage_gaps)} Identified)"))
        if coverage_gaps:
            gap_cell_s = ParagraphStyle('gap_cell', fontName=FONT_REGULAR, fontSize=7.5, textColor=CHARCOAL, leading=10)
            gap_hdr_s = ParagraphStyle('gap_hdr', fontName=FONT_BOLD, fontSize=8, textColor=WHITE, leading=10)

            # Check if any gap has fix or cost data
            _any_fix = any(isinstance(g, dict) and g.get('fix') and safe_str(g.get('fix', '')) != 'N/A' for g in coverage_gaps)
            _any_cost = any(isinstance(g, dict) and g.get('estimatedCost') and (
                (isinstance(g.get('estimatedCost'), (int, float)) and g.get('estimatedCost', 0) > 0) or
                (isinstance(g.get('estimatedCost'), str) and g.get('estimatedCost', '').strip())
            ) for g in coverage_gaps)

            # Build header row based on available columns
            _gap_header = [Paragraph("<b>#</b>", gap_hdr_s),
                           Paragraph("<b>Gap</b>", gap_hdr_s),
                           Paragraph("<b>Severity</b>", gap_hdr_s),
                           Paragraph("<b>Impact</b>", gap_hdr_s)]
            if _any_fix:
                _gap_header.append(Paragraph("<b>Fix</b>", gap_hdr_s))
            if _any_cost:
                _gap_header.append(Paragraph("<b>Cost</b>", gap_hdr_s))
            gap_tbl = [_gap_header]

            for idx_g, gap in enumerate(coverage_gaps):
                if not isinstance(gap, dict):
                    continue
                gid = gap.get('gapId', f'G{idx_g+1:03d}')
                sev = safe_str(gap.get('severity', 'medium')).upper()
                ttl = safe_str(gap.get('title', gap.get('area', gap.get('category', ''))))
                imp = safe_str(gap.get('impact', gap.get('details', gap.get('description', ''))))
                fx = safe_str(gap.get('fix', ''))
                ec = gap.get('estimatedCost', '')
                if isinstance(ec, (int, float)) and ec > 0:
                    ec_s = format_currency(ec) + '/yr'
                elif ec:
                    ec_s = str(ec)
                else:
                    ec_s = '-'
                _gap_row = [
                    Paragraph(gid, gap_cell_s),
                    Paragraph(ttl, gap_cell_s),
                    Paragraph(sev, gap_cell_s),
                    Paragraph(imp, gap_cell_s),
                ]
                if _any_fix:
                    _gap_row.append(Paragraph(fx, gap_cell_s))
                if _any_cost:
                    _gap_row.append(Paragraph(ec_s, gap_cell_s))
                gap_tbl.append(_gap_row)

            if len(gap_tbl) > 1:
                # Adjust column widths based on which columns are shown
                if _any_fix and _any_cost:
                    _gap_widths = [0.45*inch, 1.2*inch, 0.55*inch, 1.6*inch, 1.25*inch, 0.85*inch]
                elif _any_fix:
                    _gap_widths = [0.45*inch, 1.4*inch, 0.6*inch, 2.3*inch, 1.15*inch]
                elif _any_cost:
                    _gap_widths = [0.45*inch, 1.4*inch, 0.6*inch, 2.6*inch, 0.85*inch]
                else:
                    _gap_widths = [0.45*inch, 1.6*inch, 0.7*inch, 3.15*inch]
                gt = Table(gap_tbl, colWidths=_gap_widths)
                gt.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), BRAND_PRIMARY),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
                    ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
                ] + [('BACKGROUND', (0, i), (-1, i), WHISPER if i % 2 == 0 else WHITE) for i in range(1, len(gap_tbl))]))
                elements.append(gt)
        else:
            elements.append(Paragraph("No significant coverage gaps detected.", styles['body']))
        elements.append(Spacer(1, 0.15*inch))

        # Gap Severity Summary
        if gaps_summary:
            elements.append(create_subsection_header("Gap Severity Summary"))
            sev_data = [
                ["Severity", "Count"],
                ["High", str(gaps_summary.get('high', 0))],
                ["Medium", str(gaps_summary.get('medium', 0))],
                ["Info", str(gaps_summary.get('info', 0))],
                ["Total", str(gaps_summary.get('total', 0))],
            ]
            sev_tbl = create_key_value_table(sev_data, [3*inch, 3.2*inch], WARNING_AMBER)
            elements.append(sev_tbl)
            elements.append(Spacer(1, 0.1*inch))

        total_fix_annual = sum(
            safe_int(g.get('estimatedCost', 0)) for g in coverage_gaps
            if isinstance(g, dict) and isinstance(g.get('estimatedCost'), (int, float))
        )
        if total_fix_annual > 0:
            try:
                from services.protection_score_calculator import calculate_ipf_emi
                total_fix_emi = calculate_ipf_emi(total_fix_annual)
            except Exception:
                total_fix_emi = int(total_fix_annual / 12)
            elements.append(create_highlight_box(
                f"<b>Total Annual Fix Cost:</b> {format_currency(total_fix_annual)}/yr → "
                f"<b>{format_currency(total_fix_emi)}/mo with EAZR IPF</b>",
                INFO_LIGHT, INFO_BLUE
            ))
        elements.append(PageBreak())

        # ==================== PAGES 4-5: SCENARIO SIMULATIONS ====================
        elements.append(create_section_header("Real-World Claim Simulations", styles))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph(
            f"We simulated {len(simulations)} common hospitalization scenarios against your policy to show exactly what your insurance will cover.",
            styles['body']
        ))
        elements.append(Spacer(1, 0.1*inch))

        for sim_item in simulations:
            if not isinstance(sim_item, dict):
                continue
            sc_id = sim_item.get('scenarioId', sim_item.get('id', ''))
            sc_name = sim_item.get('scenarioName', sim_item.get('name', ''))
            sc_desc = sim_item.get('situation', sim_item.get('description', ''))
            sc_bill = safe_int(sim_item.get('totalBill', sim_item.get('totalCost', 0)))
            sc_cov = safe_int(sim_item.get('coveredAmount', sim_item.get('insurancePays', 0)))
            sc_oop = safe_int(sim_item.get('outOfPocket', sim_item.get('youPay', 0)))
            sc_pct = safe_int(sim_item.get('coveragePercentage', 0))
            if sc_bill > 0 and sc_pct == 0:
                sc_pct = int(sc_cov / sc_bill * 100) if sc_bill > 0 else 0
            is_primary = sc_id == primary_scenario_id
            primary_tag = " [PRIMARY]" if is_primary else ""

            elements.append(Paragraph(f"<b>{sc_id}: {sc_name}{primary_tag}</b>", styles['body_emphasis']))
            if sc_desc:
                elements.append(Paragraph(f"<i>{sc_desc}</i>", styles['body']))
            elements.append(Spacer(1, 0.05*inch))

            components = sim_item.get('components', sim_item.get('breakdown', []))
            if components and isinstance(components, list):
                comp_rows = [["Component", "Estimated", "Covered", "Gap", ""]]
                for comp in components:
                    if not isinstance(comp, dict):
                        continue
                    c_est = safe_int(comp.get('estimated', comp.get('cost', 0)))
                    c_cov = safe_int(comp.get('covered', comp.get('insurancePays', 0)))
                    c_gap = safe_int(comp.get('gap', comp.get('outOfPocket', max(0, c_est - c_cov))))
                    st_icon = 'OK' if c_gap == 0 else ('X' if c_cov == 0 else '!')
                    comp_rows.append([
                        safe_str(comp.get('name', comp.get('component', '')))[:22],
                        format_currency(c_est), format_currency(c_cov),
                        format_currency(c_gap) if c_gap > 0 else '-', st_icon
                    ])
                if len(comp_rows) > 1:
                    comp_rows.append(["TOTAL", format_currency(sc_bill), format_currency(sc_cov), format_currency(sc_oop), ""])
                    comp_tbl = create_modern_table(comp_rows, [1.4*inch, 1.1*inch, 1.1*inch, 1.1*inch, 0.4*inch])
                    elements.append(KeepTogether([comp_tbl]))
                    elements.append(Spacer(1, 0.05*inch))
            elif sc_bill > 0:
                # Compact financial summary when no component breakdown is available
                _sc_gap = max(0, sc_bill - sc_cov)
                summary_rows = [
                    ["Total Bill", format_currency(sc_bill)],
                    ["Insurance Covers", format_currency(sc_cov)],
                    ["You Pay (OOP)", format_currency(_sc_gap) if _sc_gap > 0 else "Fully Covered"],
                ]
                summary_tbl = Table(summary_rows, colWidths=[1.8*inch, 2*inch])
                summary_tbl.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (0, -1), FONT_REGULAR),
                    ('FONTNAME', (1, 0), (1, -1), FONT_BOLD),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('TEXTCOLOR', (0, 0), (0, -1), MEDIUM_GRAY),
                    ('TEXTCOLOR', (1, 0), (1, -1), CHARCOAL),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('LINEBELOW', (0, -1), (-1, -1), 0.5, BORDER_LIGHT),
                    ('BACKGROUND', (0, 0), (-1, -1), WHISPER),
                ]))
                elements.append(summary_tbl)
                elements.append(Spacer(1, 0.03*inch))

            # Coverage bar — table-based for reliable rendering
            cov_color = SCORE_EXCELLENT if sc_pct >= 80 else (SCORE_ADEQUATE if sc_pct >= 60 else SCORE_MODERATE)
            elements.append(create_score_bar(sc_pct, width=4*inch, height=8, color=cov_color))
            cov_text_s = ParagraphStyle(f'cbar_txt_{sc_id}', fontName=FONT_BOLD, fontSize=8, textColor=cov_color, spaceAfter=2)
            elements.append(Paragraph(f"{sc_pct}% Covered | Out-of-Pocket: {format_currency(sc_oop)}", cov_text_s))

            gaps_triggered = sim_item.get('gapsTriggered', sim_item.get('gaps_triggered', []))
            if gaps_triggered and isinstance(gaps_triggered, list):
                gt_text = ' · '.join(safe_str(g, '') for g in gaps_triggered[:3])
                elements.append(Paragraph(f"<i>Gaps triggered: {gt_text}</i>", styles['body']))
            elements.append(Spacer(1, 0.15*inch))

        # Scenario Comparison Summary Table
        elements.append(create_subsection_header("Scenario Comparison Summary"))
        if simulations:
            cmp_data = [["Scenario", "Total Bill", "Covered", "OOP", "Coverage"]]
            sum_oop = 0
            sum_cpct = 0
            valid_n = 0
            max_oop_val = 0
            max_oop_nm = ''
            for sim_c in simulations:
                if not isinstance(sim_c, dict):
                    continue
                nm = sim_c.get('scenarioName', sim_c.get('name', ''))
                tb = safe_int(sim_c.get('totalBill', sim_c.get('totalCost', 0)))
                cv = safe_int(sim_c.get('coveredAmount', sim_c.get('insurancePays', 0)))
                op = safe_int(sim_c.get('outOfPocket', sim_c.get('youPay', 0)))
                cp = int(cv / tb * 100) if tb > 0 else 0
                cmp_data.append([nm, format_currency(tb), format_currency(cv), format_currency(op), f"{cp}%"])
                sum_oop += op
                sum_cpct += cp
                valid_n += 1
                if op > max_oop_val:
                    max_oop_val = op
                    max_oop_nm = nm
            if valid_n > 0:
                avg_cp = sum_cpct // valid_n
                avg_op = sum_oop // valid_n
                cmp_data.append(["WORST CASE", "", "", format_currency(max_oop_val), ""])
                cmp_data.append(["AVERAGE", "", "", format_currency(avg_op), f"{avg_cp}%"])
            cmp_tbl = create_modern_table(cmp_data, [1.7*inch, 1.1*inch, 1.1*inch, 1.1*inch, 0.8*inch])
            elements.append(cmp_tbl)
        elements.append(Spacer(1, 0.1*inch))
        note_s = ParagraphStyle('sc_note', fontName=FONT_REGULAR, fontSize=7, textColor=LIGHT_GRAY)
        elements.append(Paragraph(f"Costs are metro hospital estimates as of {datetime.now().strftime('%B %Y')}. Actual costs may vary.", note_s))

        # Only force page break before recommendations if there's substantial content
        _total_rec_items = len(quick_wins) + len(priority_upgrades)
        if _total_rec_items > 2:
            elements.append(PageBreak())
        else:
            elements.append(Spacer(1, 0.3*inch))

        # ==================== RECOMMENDATIONS ACTION PLAN ====================
        elements.append(create_section_header("Your Personalized Action Plan", styles))
        elements.append(Spacer(1, 0.1*inch))

        # Quick Wins
        if quick_wins:
            elements.append(create_subsection_header("Quick Wins (No Cost)"))
            for qw in quick_wins:
                if isinstance(qw, dict):
                    qw_title = qw.get('title', '')
                    qw_detail = qw.get('detail', qw.get('description', ''))
                    elements.append(Paragraph(f"<b>{qw_title}</b>", styles['body_emphasis']))
                    if qw_detail:
                        elements.append(Paragraph(f"   {qw_detail}", styles['body']))
                    elements.append(Spacer(1, 0.05*inch))
                elif isinstance(qw, str):
                    elements.append(Paragraph(f"- {qw}", styles['body']))
            elements.append(Spacer(1, 0.15*inch))

        # Priority Upgrades
        if priority_upgrades:
            elements.append(create_subsection_header("Priority Upgrades"))
            for pu_idx, upgrade in enumerate(priority_upgrades):
                if not isinstance(upgrade, dict):
                    continue
                pu_num = pu_idx + 1
                pu_title = safe_str(upgrade.get('title', ''), '')
                pu_priority = upgrade.get('priority', 'medium')
                if isinstance(pu_priority, (int, float)):
                    pu_text = 'HIGH' if pu_priority == 1 else 'MEDIUM' if pu_priority == 2 else 'LOW'
                else:
                    pu_text = str(pu_priority).upper()
                pu_gaps = upgrade.get('gapMapping', [])
                pu_impact = safe_str(upgrade.get('impact', ''), '')
                pu_cost = upgrade.get('estimatedCost', 0)
                pu_emi = upgrade.get('eazrEmi', 0)
                pu_when = upgrade.get('when', '')

                elements.append(Paragraph(
                    f"<b>#{pu_num}  {pu_title}</b>   [{pu_text}]",
                    styles['body_emphasis']
                ))

                detail_parts = []
                if pu_gaps:
                    detail_parts.append(f"Fixes: {', '.join(str(g) for g in pu_gaps)}")
                if pu_impact:
                    detail_parts.append(f"Impact: {pu_impact}")
                cost_parts = []
                if isinstance(pu_cost, (int, float)) and pu_cost > 0:
                    cost_parts.append(f"{format_currency(pu_cost)}/yr")
                if isinstance(pu_emi, (int, float)) and pu_emi > 0:
                    cost_parts.append(f"EAZR EMI: {format_currency(pu_emi)}/mo")
                if cost_parts:
                    detail_parts.append(f"Cost: {' | '.join(cost_parts)}")
                if pu_when:
                    detail_parts.append(f"When: {pu_when}")

                if detail_parts:
                    detail_html = '<br/>'.join(detail_parts)
                    elements.append(create_highlight_box(detail_html, WHISPER, BORDER_LIGHT))
                elements.append(Spacer(1, 0.1*inch))
            elements.append(Spacer(1, 0.1*inch))

        # Investment Summary Table
        if priority_upgrades:
            elements.append(create_subsection_header("Total Upgrade Investment"))
            inv_data = [["Action", "Annual Cost", "EAZR EMI/mo"]]
            inv_total_a = 0
            inv_total_e = 0
            for upg in priority_upgrades:
                if not isinstance(upg, dict):
                    continue
                u_title = upg.get('title', '')[:28]
                u_cost = safe_int(upg.get('estimatedCost', 0))
                u_emi = safe_int(upg.get('eazrEmi', 0))
                inv_data.append([
                    u_title,
                    format_currency(u_cost) if u_cost > 0 else '-',
                    format_currency(u_emi) if u_emi > 0 else '-'
                ])
                inv_total_a += u_cost
                inv_total_e += u_emi
            inv_data.append(["TOTAL", format_currency(inv_total_a), f"{format_currency(inv_total_e)}/mo"])
            inv_tbl = create_modern_table(inv_data, [2.8*inch, 1.5*inch, 1.9*inch])
            elements.append(inv_tbl)
            elements.append(Spacer(1, 0.1*inch))

            if inv_total_e > 0 and worst_oop > 0:
                elements.append(Paragraph(
                    f"For <b>{format_currency(inv_total_e)}/month</b>, your worst-case OOP drops from "
                    f"<b>{format_currency(worst_oop)}</b> significantly.",
                    styles['body']
                ))
            elements.append(Spacer(1, 0.15*inch))
            elements.append(create_highlight_box(
                "<b>Finance your entire protection upgrade with EAZR</b><br/>"
                "Apply at: eazr.in | Download the EAZR app",
                BRAND_LIGHT, BRAND_PRIMARY
            ))
        elif not quick_wins:
            # Fallback for non-V10 recommendations
            elements.append(Paragraph("Based on this analysis, here are recommendations:", styles['body']))
            elements.append(Spacer(1, 0.1*inch))
            if recommendations:
                for rec_item in recommendations[:5]:
                    if isinstance(rec_item, dict):
                        r_title = rec_item.get('title', rec_item.get('suggestion', rec_item.get('recommendation', '')))
                        r_desc = rec_item.get('description', '')
                        elements.append(Paragraph(f"<b>{r_title}</b>{': ' + r_desc if r_desc else ''}", styles['body']))
                    elif isinstance(rec_item, str):
                        elements.append(Paragraph(f"- {rec_item}", styles['body']))

        # When recommendations are sparse, add policy maintenance checklist
        if _total_rec_items <= 2:
            elements.append(Spacer(1, 0.2*inch))
            elements.append(create_subsection_header("Policy Maintenance Checklist"))
            _maint_tips = [
                ["Before Renewal", "Compare your current plan with latest offerings. Check if SI needs an increase based on medical inflation."],
                ["Keep Documents Ready", f"Store your health card, policy number ({policy_number}), and TPA details for quick access during emergencies."],
            ]
            # Only show "Track Waiting Periods" if waiting periods are active (not waived/completed)
            if ped_waiting > 0:
                _maint_tips.append(["Track Waiting Periods", f"Your PED waiting period is {ped_waiting} months. Mark the date when it completes for full coverage eligibility."])
            else:
                _maint_tips.append(["Waiting Periods", "All waiting periods are waived or completed. Your pre-existing conditions are fully covered from day one."])
            _maint_tips.extend([
                ["Review Network Hospitals", "Verify that your preferred hospitals are still in the cashless network before any planned procedures."],
                ["Claim Process", f"For {insurer_name}: Call the claims helpline first, then visit the nearest network hospital with your health card."],
            ])
            for tip_title, tip_desc in _maint_tips:
                elements.append(Paragraph(f"<b>{tip_title}</b>", styles['body_emphasis']))
                elements.append(Paragraph(tip_desc, styles['body']))
                elements.append(Spacer(1, 0.05*inch))

            elements.append(Spacer(1, 0.15*inch))
            elements.append(create_highlight_box(
                f"<b>Your Protection Score: {composite_score}/100</b> — "
                f"{'Your policy provides strong protection. Focus on maintaining continuous coverage.' if composite_score >= 75 else 'Consider the upgrades above to strengthen your coverage.'}",
                BRAND_LIGHT, BRAND_PRIMARY
            ))

        elements.append(PageBreak())

        # ==================== PAGE 8: POLICY REFERENCE SNAPSHOT ====================
        elements.append(create_section_header("Policy Quick Reference", styles))
        elements.append(Spacer(1, 0.05*inch))

        # Use a compact key-value table for policy reference to fit on one page
        def _compact_kv_table(data, accent_color):
            tbl = Table(data, colWidths=[2.3*inch, 3.9*inch])
            tbl.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), FONT_REGULAR),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('TEXTCOLOR', (0, 0), (0, -1), MEDIUM_GRAY),
                ('TEXTCOLOR', (1, 0), (1, -1), CHARCOAL),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LINEABOVE', (0, 0), (-1, 0), 1.5, accent_color),
                ('LINEBELOW', (0, -1), (-1, -1), 0.5, BORDER_LIGHT),
                ('BACKGROUND', (0, 0), (-1, -1), WHISPER),
            ]))
            return tbl

        compact_sub_s = ParagraphStyle('compact_sub', fontName=FONT_BOLD, fontSize=9, textColor=CHARCOAL, spaceBefore=6, spaceAfter=3)

        elements.append(Paragraph("<b>Core Details</b>", compact_sub_s))
        ref_data = [
            ["Insurance Provider", insurer_name],
            ["Product Name", plan_name],
            ["Policy Type", policy_type],
            ["Policy Number", policy_number],
            ["Validity", f"{start_date} to {end_date}"],
            ["Sum Insured", format_currency(sum_insured)],
        ]
        if total_effective_coverage and total_effective_coverage != sum_insured:
            ref_data.append(["Effective Coverage", format_currency(total_effective_coverage)])
        if members_covered:
            m_names = ', '.join(m.get('name', 'N/A') for m in members_covered[:4])
            ref_data.append(["Members Covered", f"{len(members_covered)} ({m_names})"])
        elements.append(_compact_kv_table(ref_data, BRAND_PRIMARY))
        elements.append(Spacer(1, 0.06*inch))

        elements.append(Paragraph("<b>Coverage Limits</b>", compact_sub_s))
        lim_data = [
            ["Room Rent Limit", safe_str(room_rent_limit)],
            ["ICU Limit", safe_str(coverage_details.get('icuLimit', 'Check policy'))],
            ["Co-payment", f"{co_pay_percentage}%" if co_pay_percentage > 0 else "None"],
            ["Deductible", format_currency(deductible_amount) if deductible_amount > 0 else "None"],
            ["Restoration", "Yes" if benefits.get('restoration', {}).get('available') else "No"],
            ["No Claim Bonus", f"Yes ({benefits.get('noClaimBonus', {}).get('percentage', 'N/A')})" if benefits.get('noClaimBonus', {}).get('available') else "No"],
        ]
        elements.append(_compact_kv_table(lim_data, BRAND_SECONDARY))
        elements.append(Spacer(1, 0.06*inch))

        elements.append(Paragraph("<b>Waiting Periods</b>", compact_sub_s))
        wp_data = [
            ["Initial Waiting", "Waived (No Waiting)" if initial_waiting == 0 else f"{initial_waiting} days"],
            ["Pre-existing Disease", "Waived (No Waiting)" if ped_waiting == 0 else f"{ped_waiting} months"],
            ["Specific Diseases", "Waived (No Waiting)" if specific_waiting == 0 else f"{specific_waiting} months"],
        ]
        if maternity_waiting > 0:
            wp_data.append(["Maternity", f"{maternity_waiting} months"])
        elements.append(_compact_kv_table(wp_data, INFO_BLUE))
        elements.append(Spacer(1, 0.06*inch))

        elements.append(Paragraph("<b>Premium Details</b>", compact_sub_s))
        prem_data = [
            ["Annual Premium", format_currency(premium)],
            ["Payment Frequency", premium_frequency.capitalize() if premium_frequency else "Yearly"],
            ["80D Tax Benefit", "Applicable"],
        ]
        elements.append(_compact_kv_table(prem_data, SUCCESS_GREEN))
        elements.append(Spacer(1, 0.06*inch))

        elements.append(Paragraph("<b>Network & Support</b>", compact_sub_s))
        net_data = [
            ["Network Hospitals", f"{network_count}+" if network_count > 0 else "Check with insurer"],
            ["TPA", tpa_name],
            ["Claims Helpline", get_health_claims_helpline(insurer_name)],
        ]
        elements.append(_compact_kv_table(net_data, BRAND_DARK))
        elements.append(PageBreak())

        # ==================== PAGE 8: BACK COVER ====================
        elements.append(Spacer(1, 1.5*inch))
        bc_title_s = ParagraphStyle('bc_title', fontName=FONT_BOLD, fontSize=36, textColor=BRAND_PRIMARY, alignment=TA_CENTER, leading=44, spaceAfter=16)
        elements.append(Paragraph("EAZR", bc_title_s))
        elements.append(Spacer(1, 0.1*inch))
        bc_sub_s = ParagraphStyle('bc_sub', fontName=FONT_REGULAR, fontSize=12, textColor=SLATE, alignment=TA_CENTER, leading=16, spaceAfter=24)
        elements.append(Paragraph("Powered by EAZR Policy Intelligence", bc_sub_s))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(HRFlowable(width="60%", thickness=1, color=BORDER_LIGHT, spaceAfter=20))
        elements.append(Spacer(1, 0.1*inch))
        bc_contact_s = ParagraphStyle('bc_contact', fontName=FONT_REGULAR, fontSize=10, textColor=MEDIUM_GRAY, alignment=TA_CENTER, leading=14, spaceAfter=30)
        elements.append(Paragraph("Contact: support@eazr.in | www.eazr.in", bc_contact_s))

        bc_disc_title_s = ParagraphStyle('bc_disc_title', fontName=FONT_BOLD, fontSize=10, textColor=CHARCOAL, alignment=TA_LEFT, leading=14, spaceAfter=8)
        elements.append(Paragraph("<b>IMPORTANT DISCLAIMERS</b>", bc_disc_title_s))
        disc_items = [
            "1. This report is generated by EAZR's AI-powered Policy Intelligence engine and is intended for informational and educational purposes only.",
            "2. This report does not constitute insurance advice, financial advice, or a recommendation to purchase, modify, or cancel any insurance policy.",
            "3. All cost estimates are based on current metro hospital rate data and may vary significantly based on actual hospital, city, treatment protocols, and individual circumstances.",
            "4. Actual claim settlement is subject to the terms and conditions of your policy document, insurer's underwriting guidelines, and applicable regulations.",
            "5. The scores and ratings in this report are proprietary to EAZR and are computed using publicly available benchmarks and IRDAI regulatory data.",
            "6. EAZR IPF (Insurance Premium Financing) options mentioned in this report are subject to eligibility, credit assessment, and applicable terms. EMI calculations are indicative.",
            "7. For personalized insurance advice, please consult a licensed insurance advisor or your insurer directly.",
        ]
        disc_s = ParagraphStyle('bc_disc', fontName=FONT_REGULAR, fontSize=7.5, textColor=MEDIUM_GRAY, leading=10, spaceAfter=3)
        for d_item in disc_items:
            elements.append(Paragraph(d_item, disc_s))

        elements.append(Spacer(1, 0.3*inch))
        bc_company_s = ParagraphStyle('bc_company', fontName=FONT_BOLD, fontSize=8, textColor=MEDIUM_GRAY, alignment=TA_CENTER, spaceAfter=4)
        elements.append(Paragraph("EAZR Digipayments Private Limited", bc_company_s))
        bc_rid_s = ParagraphStyle('bc_rid', fontName=FONT_REGULAR, fontSize=8, textColor=LIGHT_GRAY, alignment=TA_CENTER, spaceAfter=8)
        elements.append(Paragraph(f"Report ID: {report_id}", bc_rid_s))
        bc_ver_s = ParagraphStyle('bc_ver', fontName=FONT_REGULAR, fontSize=8, textColor=LIGHT_GRAY, alignment=TA_CENTER)
        elements.append(Paragraph(
            f"<b>Analysis Version:</b> 10.0 | <b>Generated:</b> {datetime.now().strftime('%d %B %Y %H:%M')}",
            bc_ver_s
        ))


        # Build PDF
        pdf_doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
        buffer.seek(0)
        logger.info("Health Insurance PDF report generated successfully")
        return buffer

    except Exception as e:
        logger.error(f"Error generating health insurance report: {str(e)}", exc_info=True)
        raise