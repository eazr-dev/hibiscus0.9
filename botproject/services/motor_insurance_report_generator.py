"""
Motor Insurance Policy Analysis Report Generator
Based on EAZR_03_Motor_Insurance_PolicyAnalysisTab.md — V10
8-Page PDF Report: Cover, Scores, IDV+NCB, Gaps+Add-ons, Scenarios, Renewal, Reference, Back Cover

Features:
- KeepTogether to prevent table splitting across pages
- Modern UI with better spacing and visual hierarchy
- 3-score system (S1/S2/S3) per product type
- Product-type adaptation (Comprehensive/TP-Only/SAOD)
- IDV analysis, NCB tracker, depreciation schedule
- 15-addon map with relevance tags
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
import hashlib

# Import market data service for dynamic rates
from services.indian_market_data_service import (
    get_motor_insurance_market_data,
    get_metal_depreciation_rate,
    get_parts_breakdown,
    get_compulsory_deductible,
    get_pa_cover_amount,
    get_tp_property_damage_limit,
    get_driving_fine_details
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

# V10 Score tier colors
SCORE_EXCELLENT = colors.HexColor('#22C55E')
SCORE_STRONG = colors.HexColor('#84CC16')
SCORE_ADEQUATE = colors.HexColor('#EAB308')
SCORE_BASIC = colors.HexColor('#F97316')
SCORE_MINIMAL = colors.HexColor('#6B7280')

# V10 Policy type badge colors
BADGE_COMP = colors.HexColor('#22C55E')
BADGE_TP = colors.HexColor('#F97316')
BADGE_SAOD = colors.HexColor('#3B82F6')

# V10 Add-on relevance colors
ADDON_ESSENTIAL = colors.HexColor('#F97316')
ADDON_RECOMMENDED = colors.HexColor('#EAB308')
ADDON_OPTIONAL = colors.HexColor('#6B7280')
ADDON_ACTIVE = colors.HexColor('#22C55E')
ADDON_MISSING = colors.HexColor('#EF4444')

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
            # RUPEE_SYMBOL stays as 'Rs.' — Unicode ₹ renders as ■ in some PDF contexts
            break
except Exception as e:
    logger.warning(f"Could not register Unicode font: {e}")


def safe_str(value, default=''):
    """Safely convert value to string, sanitizing Unicode for PDF rendering"""
    if value is None:
        return default
    s = str(value)
    # Replace Unicode rupee with safe ASCII "Rs."
    s = s.replace('\u20b9', 'Rs.').replace('₹', 'Rs.')
    # Replace other problematic Unicode
    s = s.replace('\u2022', '-').replace('\u2013', '-').replace('\u2014', '-')
    s = s.replace('\u2018', "'").replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
    return s


def format_currency(value, show_symbol=True):
    """Format currency with proper symbol and commas"""
    if value is None or value == 'N/A' or value == '':
        return 'N/A'
    try:
        num = float(value)
        formatted = f"{int(num):,}"
        return f"Rs.{formatted}" if show_symbol else formatted
    except (ValueError, TypeError):
        return str(value) if value else 'N/A'


def safe_int(value, default=0):
    """Safely convert value to int"""
    if value is None or value == 'N/A' or value == '':
        return default
    try:
        return int(float(str(value).replace(',', '').replace(RUPEE_SYMBOL, '').replace('Rs.', '').replace('\u20b9', '').strip()))
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    """Safely convert value to float"""
    if value is None or value == 'N/A' or value == '':
        return default
    try:
        return float(str(value).replace(',', '').replace('%', '').replace(RUPEE_SYMBOL, '').replace('Rs.', '').replace('\u20b9', '').strip())
    except (ValueError, TypeError):
        return default


def get_v10_score_color(score):
    """Get V10 tier color for a score"""
    if score >= 90:
        return SCORE_EXCELLENT
    elif score >= 75:
        return SCORE_STRONG
    elif score >= 60:
        return SCORE_ADEQUATE
    elif score >= 40:
        return SCORE_BASIC
    else:
        return SCORE_MINIMAL


def get_v10_score_bg(score):
    """Get light background for a score"""
    if score >= 75:
        return SUCCESS_LIGHT
    elif score >= 60:
        return WARNING_LIGHT
    elif score >= 40:
        return colors.HexColor('#FEF3C7')
    else:
        return DANGER_LIGHT


def get_v10_score_label(score):
    """Get V10 verdict label for a score"""
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Strong"
    elif score >= 60:
        return "Adequate"
    elif score >= 40:
        return "Basic"
    else:
        return "Minimal"


def get_motor_claims_helpline(insurer_name: str) -> str:
    """Get claims helpline number based on motor insurance provider name"""
    if not insurer_name or insurer_name == 'N/A':
        return "See policy document"

    insurer_lower = insurer_name.lower()

    helplines = {
        'icici lombard': '1800-266-9725',
        'icici': '1800-266-9725',
        'hdfc ergo': '1800-266-0700',
        'hdfc': '1800-266-0700',
        'bajaj allianz': '1800-209-5858',
        'bajaj': '1800-209-5858',
        'tata aig': '1800-266-7780',
        'tata': '1800-266-7780',
        'reliance general': '1800-102-5678',
        'reliance': '1800-102-5678',
        'new india assurance': '1800-209-1415',
        'new india': '1800-209-1415',
        'oriental insurance': '1800-118-485',
        'oriental': '1800-118-485',
        'united india': '1800-425-3333',
        'united': '1800-425-3333',
        'national insurance': '1800-345-0330',
        'national': '1800-345-0330',
        'iffco tokio': '1800-103-5499',
        'iffco': '1800-103-5499',
        'sbi general': '1800-102-1111',
        'sbi': '1800-102-1111',
        'cholamandalam': '1800-208-9898',
        'chola': '1800-208-9898',
        'bharti axa': '1800-103-4141',
        'bharti': '1800-103-4141',
        'future generali': '1800-220-233',
        'future': '1800-220-233',
        'royal sundaram': '1800-568-9999',
        'royal': '1800-568-9999',
        'shriram general': '1800-103-3009',
        'shriram': '1800-103-3009',
        'acko': '1800-266-2256',
        'digit': '1800-258-5956',
        'go digit': '1800-258-5956',
        'kotak mahindra': '1800-266-4545',
        'kotak': '1800-266-4545',
        'magma hdi': '1800-200-3881',
        'magma': '1800-200-3881',
        'liberty': '1800-266-5844',
        'raheja qbe': '1800-102-8922',
        'raheja': '1800-102-8922',
        'navi': '1800-123-0004',
        'zuno': '1800-266-5844',
    }

    for key, number in helplines.items():
        if key in insurer_lower:
            return number

    return "See policy document"


def get_depreciation_rate(vehicle_age):
    """Get metal depreciation rate based on vehicle age"""
    return get_metal_depreciation_rate(vehicle_age)


def calculate_claim_scenario(repair_bill, vehicle_age, has_zero_dep, compulsory_deductible, voluntary_deductible, smart_saver_deductible=0):
    """Calculate what insurance pays vs what you pay for a repair claim"""
    metal_depreciation_rate = get_depreciation_rate(vehicle_age)
    parts_breakdown = get_parts_breakdown()
    plastic_pct = parts_breakdown.get("plastic_percentage", 30) / 100
    metal_pct = parts_breakdown.get("metal_percentage", 50) / 100
    paint_pct = parts_breakdown.get("paint_percentage", 15) / 100

    plastic_cost = repair_bill * plastic_pct
    metal_cost = repair_bill * metal_pct
    paint_cost = repair_bill * paint_pct

    market_data = get_motor_insurance_market_data()
    plastic_dep_rate = market_data.get("depreciation_rates", {}).get("plastic_rubber_fibre", 50) / 100
    paint_dep_rate = market_data.get("depreciation_rates", {}).get("paint", 30) / 100

    if has_zero_dep:
        depreciation_deduction = 0
    else:
        plastic_depreciation = plastic_cost * plastic_dep_rate
        metal_depreciation = metal_cost * (metal_depreciation_rate / 100)
        paint_depreciation = paint_cost * paint_dep_rate
        depreciation_deduction = plastic_depreciation + metal_depreciation + paint_depreciation

    total_deductible = compulsory_deductible + voluntary_deductible + smart_saver_deductible
    insurance_pays = repair_bill - depreciation_deduction - total_deductible
    you_pay = depreciation_deduction + total_deductible

    return {
        'repair_bill': repair_bill,
        'depreciation': depreciation_deduction,
        'deductible': total_deductible,
        'compulsory_deductible': compulsory_deductible,
        'voluntary_deductible': voluntary_deductible,
        'smart_saver_deductible': smart_saver_deductible,
        'insurance_pays': max(0, insurance_pays),
        'you_pay': you_pay
    }


# ==================== PDF LAYOUT HELPERS ====================

class ModernHeader:
    @staticmethod
    def draw(canvas, doc_template):
        canvas.saveState()
        canvas.setFillColor(BRAND_PRIMARY)
        canvas.rect(0, A4[1] - 0.6*inch, A4[0], 0.6*inch, fill=True, stroke=False)

        canvas.setFont(FONT_BOLD, 20)
        canvas.setFillColor(WHITE)
        canvas.drawString(0.6*inch, A4[1] - 0.4*inch, "EAZR")

        canvas.setFont(FONT_REGULAR, 8)
        canvas.setFillColor(colors.HexColor('#B0E0DC'))
        canvas.drawCentredString(A4[0] / 2, A4[1] - 0.38*inch, "Motor Insurance Analysis Report")

        canvas.setFont(FONT_REGULAR, 9)
        canvas.setFillColor(WHITE)
        canvas.drawRightString(A4[0] - 0.6*inch, A4[1] - 0.38*inch, f"Page {doc_template.page}")

        canvas.restoreState()


class ModernFooter:
    report_id = ""

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
    styles = {
        'cover_main_title': ParagraphStyle(
            'CoverMainTitle', fontName=FONT_BOLD, fontSize=28, textColor=CHARCOAL,
            alignment=TA_CENTER, spaceAfter=6, leading=34
        ),
        'cover_subtitle': ParagraphStyle(
            'CoverSubtitle', fontName=FONT_REGULAR, fontSize=12, textColor=MEDIUM_GRAY,
            alignment=TA_CENTER, spaceAfter=20
        ),
        'section_title': ParagraphStyle(
            'SectionTitle', fontName=FONT_BOLD, fontSize=16, textColor=BRAND_DARK,
            spaceBefore=20, spaceAfter=10, leading=20
        ),
        'section_subtitle': ParagraphStyle(
            'SectionSubtitle', fontName=FONT_BOLD, fontSize=11, textColor=CHARCOAL,
            spaceBefore=14, spaceAfter=6, leading=14
        ),
        'advisory_intro': ParagraphStyle(
            'AdvisoryIntro', fontName=FONT_ITALIC, fontSize=10, textColor=SLATE,
            alignment=TA_JUSTIFY, spaceBefore=6, spaceAfter=12, leading=15,
            leftIndent=15, rightIndent=15
        ),
        'body_text': ParagraphStyle(
            'BodyText', fontName=FONT_REGULAR, fontSize=9, textColor=SLATE,
            alignment=TA_JUSTIFY, spaceAfter=6, leading=14
        ),
        'body_emphasis': ParagraphStyle(
            'BodyEmphasis', fontName=FONT_BOLD, fontSize=9, textColor=CHARCOAL,
            spaceAfter=4, leading=13
        ),
        'insight_text': ParagraphStyle(
            'InsightText', fontName=FONT_REGULAR, fontSize=9, textColor=BRAND_DARK,
            leftIndent=10, rightIndent=10, spaceAfter=10, leading=14
        ),
        'warning_text': ParagraphStyle(
            'WarningText', fontName=FONT_REGULAR, fontSize=9, textColor=DANGER_RED,
            leftIndent=8, spaceAfter=6, leading=13
        ),
        'muted_text': ParagraphStyle(
            'MutedText', fontName=FONT_REGULAR, fontSize=8, textColor=MEDIUM_GRAY,
            spaceAfter=4, leading=12
        ),
        'bullet_point': ParagraphStyle(
            'BulletPoint', fontName=FONT_REGULAR, fontSize=9, textColor=SLATE,
            leftIndent=15, spaceAfter=3, leading=13
        ),
        'numbered_item': ParagraphStyle(
            'NumberedItem', fontName=FONT_REGULAR, fontSize=9, textColor=SLATE,
            leftIndent=20, spaceAfter=4, leading=13
        ),
        'scenario_title': ParagraphStyle(
            'ScenarioTitle', fontName=FONT_BOLD, fontSize=10, textColor=BRAND_DARK,
            spaceBefore=10, spaceAfter=4
        ),
    }
    return styles


def create_section_header(title, styles):
    """Create a modern section header with accent bar"""
    header_content = [
        [Paragraph(f"<b>{title}</b>", ParagraphStyle(
            'SectionHeader', fontName=FONT_BOLD, fontSize=14, textColor=BRAND_DARK,
            leading=18
        ))]
    ]
    header_table = Table(header_content, colWidths=[6.2*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BRAND_LIGHTER),
        ('LINEBEFORE', (0, 0), (0, -1), 4, BRAND_PRIMARY),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    return header_table


def create_subsection_header(title):
    """Create a subsection header"""
    return Paragraph(
        f"<font color='#{BRAND_DARK.hexval()[2:]}'><b>{title}</b></font>",
        ParagraphStyle('SubsectionHeader', fontName=FONT_BOLD, fontSize=11,
                      textColor=BRAND_DARK, spaceBefore=12, spaceAfter=6)
    )


def create_highlight_box(content, bg_color, border_color):
    """Create a highlighted callout box"""
    para = Paragraph(content, ParagraphStyle('HighlightContent', fontName=FONT_REGULAR, fontSize=9, textColor=CHARCOAL, leading=14, alignment=TA_LEFT))
    box = Table([[para]], colWidths=[6.2*inch])
    box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_color),
        ('LINEBEFORE', (0, 0), (0, -1), 3, border_color),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    return box


def create_modern_table(data, col_widths, header_bg=BRAND_PRIMARY, alt_rows=True):
    """Create a modern styled table with alternating rows"""
    table = Table(data, colWidths=col_widths)
    style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), header_bg),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('FONTNAME', (0, 1), (-1, -1), FONT_REGULAR),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), SLATE),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
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


def create_score_tile(score, name, weight_str, max_width=1.8*inch):
    """Create a single score tile for the 3-score bar"""
    sc = get_v10_score_color(score)
    bg = get_v10_score_bg(score)
    label = get_v10_score_label(score)
    content = (
        f"<font size='18' color='#{sc.hexval()[2:]}'><b>{score}</b></font>"
        f"<font size='8' color='#{MEDIUM_GRAY.hexval()[2:]}'>/100</font><br/>"
        f"<font size='8' color='#{sc.hexval()[2:]}'><b>{label}</b></font><br/>"
        f"<font size='7' color='#{MEDIUM_GRAY.hexval()[2:]}'>{name}</font><br/>"
        f"<font size='6' color='#{LIGHT_GRAY.hexval()[2:]}'>{weight_str}</font>"
    )
    para = Paragraph(content, ParagraphStyle('ScoreTile', fontName=FONT_BOLD, alignment=TA_CENTER, leading=14))
    tile = Table([[para]], colWidths=[max_width])
    tile.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('BOX', (0, 0), (-1, -1), 1.5, sc),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return tile


def create_score_bar(elements, score_data, product_type):
    """Add the score bar visualization for V10 factor tables"""

    # Inline helper to build a score table
    def _build_score_section(score_key, elements_list, styles_dict):
        sd = score_data.get(score_key)
        if not sd:
            return
        score = sd.get("score", 0)
        name = sd.get("name", score_key.upper())
        label = sd.get("label", get_v10_score_label(score))
        sc = get_v10_score_color(score)

        # Score header
        bar_fill = min(30, int(score * 30 / 100))
        bar_visual = "=" * bar_fill + "-" * (30 - bar_fill)

        header_text = (
            f"<font size='11' color='#{BRAND_DARK.hexval()[2:]}'><b>{name} — {score}/100 ({label})</b></font><br/>"
            f"<font size='8' color='#{sc.hexval()[2:]}'>{bar_visual}</font>"
        )
        elements_list.append(Paragraph(header_text, ParagraphStyle(
            'ScoreHeader', fontName=FONT_BOLD, fontSize=11, textColor=BRAND_DARK,
            spaceBefore=12, spaceAfter=6, leading=16
        )))

        # Factor table — use Paragraph for text wrapping instead of truncation
        factors = sd.get("factors", [])
        if factors:
            _cell_style = ParagraphStyle('FactorCell', fontName=FONT_REGULAR, fontSize=8, textColor=SLATE, leading=10)
            _hdr_style = ParagraphStyle('FactorHdr', fontName=FONT_BOLD, fontSize=8, textColor=WHITE, leading=10)
            table_data = [[
                Paragraph("Factor", _hdr_style),
                Paragraph("Your Policy", _hdr_style),
                Paragraph("Benchmark", _hdr_style),
                Paragraph("Points", _hdr_style),
            ]]
            for f in factors:
                pts = f"{f.get('pointsEarned', 0)}/{f.get('pointsMax', 0)}"
                table_data.append([
                    Paragraph(safe_str(f.get("name", "")), _cell_style),
                    Paragraph(safe_str(f.get("yourPolicy", "")), _cell_style),
                    Paragraph(safe_str(f.get("benchmark", "")), _cell_style),
                    Paragraph(pts, _cell_style),
                ])
            ft = create_modern_table(table_data, [2.0*inch, 1.6*inch, 1.6*inch, 1.0*inch])
            elements_list.append(KeepTogether([ft, Spacer(1, 0.08*inch)]))

        # What this means
        weakest = None
        lowest_pct = 1.0
        for f in factors:
            mx = f.get("pointsMax", 1)
            if mx > 0:
                pct = f.get("pointsEarned", 0) / mx
                if pct < lowest_pct:
                    lowest_pct = pct
                    weakest = f.get("name", "")
        weakest_max = 20
        for f in factors:
            mx = f.get("pointsMax", 1)
            if mx > 0 and f.get("name", "") == weakest:
                weakest_max = mx
                break
        if weakest:
            improvement = int((1 - lowest_pct) * weakest_max) if factors else 0
            meaning = (
                f"Your {name.lower()} is <b>{label.lower()}</b>. "
                f"The weakest area is <b>{weakest}</b> (scoring {int(lowest_pct*100)}% of possible points)."
            )
            if improvement > 5:
                meaning += f" Addressing this alone could improve your score by up to {improvement} points."
            elements_list.append(Paragraph(meaning, styles_dict['body_text']))

    styles = create_styles()
    pt = product_type.upper() if product_type else "COMP_CAR"

    _build_score_section("s1", elements, styles)

    if not pt.startswith("TP"):
        _build_score_section("s2", elements, styles)

    if not pt.startswith("TP"):
        _build_score_section("s3", elements, styles)


# ==================== MAIN REPORT GENERATOR ====================

def generate_motor_insurance_report(policy_data: dict, analysis_data: dict) -> BytesIO:
    """
    Generate V10 motor insurance analysis report — 8-page PDF.
    Pages: Cover, Scores, IDV+NCB+Depreciation, Gaps+Add-ons, Scenarios, Renewal, Reference, Back Cover.
    """
    try:
        buffer = BytesIO()
        pdf_doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=0.6*inch, leftMargin=0.6*inch,
            topMargin=0.85*inch, bottomMargin=0.7*inch,
            title="Motor Insurance Policy Analysis",
            author="EAZR Digipayments Pvt Ltd"
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
        start_date = policy_data.get('startDate', 'N/A')
        end_date = policy_data.get('endDate', 'N/A')

        category_data = policy_data.get('categorySpecificData', {})
        vehicle_details = category_data.get('vehicleDetails', {})
        coverage_details = category_data.get('coverageDetails', {})
        ncb_data = category_data.get('ncb', {})
        add_on_covers = category_data.get('addOnCovers', {})
        premium_breakdown = category_data.get('premiumBreakdown', {})

        # Vehicle Information
        vehicle_make = vehicle_details.get('vehicleMake', 'N/A')
        vehicle_model = vehicle_details.get('vehicleModel', 'N/A')
        vehicle_variant = vehicle_details.get('vehicleVariant', '')
        registration_number = vehicle_details.get('registrationNumber', 'N/A')
        manufacturing_year = safe_int(vehicle_details.get('manufacturingYear', 0))
        registration_date = vehicle_details.get('registrationDate', 'N/A')
        fuel_type = vehicle_details.get('fuelType', 'N/A')
        engine_number = vehicle_details.get('engineNumber', 'N/A')
        chassis_number = vehicle_details.get('chassisNumber', 'N/A')
        engine_cc = vehicle_details.get('engineCapacity', vehicle_details.get('cubicCapacity', 'N/A'))

        current_year = datetime.now().year
        vehicle_age = current_year - manufacturing_year if manufacturing_year > 0 else 0

        # Coverage Details
        idv = safe_int(coverage_details.get('idv', 0) or policy_data.get('coverageAmount', 0))
        od_premium = safe_int(coverage_details.get('odPremium', 0))
        tp_premium = safe_int(coverage_details.get('tpPremium', 0))
        total_premium = safe_int(premium_breakdown.get('totalPremium', 0) or policy_data.get('premium', 0))

        # Policy Type
        policy_identification = category_data.get('policyIdentification', {})
        policy_type = policy_identification.get('productType', 'Comprehensive')
        if not policy_type or policy_type == 'N/A':
            policy_type = 'Comprehensive' if od_premium > 0 else 'Third Party Only'

        is_tp_only = 'third party' in policy_type.lower()
        is_saod = any(k in policy_type.lower() for k in ['standalone', 'stand-alone', 'saod'])
        is_comprehensive = not is_tp_only and not is_saod

        # Product type for V10
        if is_tp_only:
            product_type_key = "TP_ONLY"
            badge_color = BADGE_TP
            badge_text = "Third Party Only"
        elif is_saod:
            product_type_key = "SAOD"
            badge_color = BADGE_SAOD
            badge_text = "Standalone OD"
        else:
            product_type_key = "COMP_CAR"
            badge_color = BADGE_COMP
            badge_text = "Comprehensive"

        # NCB Data
        ncb_percentage = safe_float(ncb_data.get('ncbPercentage', 0))
        ncb_protection = add_on_covers.get('ncbProtect', False) or ncb_data.get('ncbProtection', False)

        # Add-on Covers
        has_zero_dep = bool(add_on_covers.get('zeroDepreciation', False))
        has_engine_protection = bool(add_on_covers.get('engineProtection', False))
        has_rti = bool(add_on_covers.get('returnToInvoice', False))
        has_rsa = bool(add_on_covers.get('roadsideAssistance', False))
        has_consumables = bool(add_on_covers.get('consumables', False))
        has_tyre_cover = bool(add_on_covers.get('tyreCover', False))
        has_key_cover = bool(add_on_covers.get('keyCover', False))
        has_passenger_cover = bool(add_on_covers.get('passengerCover', False))

        # Deductibles
        live_compulsory_deductible = get_compulsory_deductible()
        compulsory_deductible = safe_int(coverage_details.get('compulsoryDeductible', live_compulsory_deductible))
        voluntary_deductible = safe_int(coverage_details.get('voluntaryDeductible', 0))
        smart_saver_deductible = safe_int(coverage_details.get('smartSaverDeductible', 0) or
                                          coverage_details.get('planDeductible', 0) or
                                          coverage_details.get('additionalDeductible', 0))
        total_deductible = compulsory_deductible + voluntary_deductible + smart_saver_deductible

        # IDV calculations — prefer V10 idvSnapshot from analysis_data for consistency
        # (will be populated after V10 data extraction below, defaulting to local calc for now)
        market_value = int(idv * 1.15) if idv else 0
        current_on_road_estimate = int(idv * 1.35) if idv else 0
        replacement_gap = current_on_road_estimate - idv if current_on_road_estimate > idv else 0
        idv_ratio = idv / market_value if market_value > 0 else 1.0
        idv_gap = max(0, market_value - idv)

        # NCB calculations
        basic_od_premium = safe_int(premium_breakdown.get('basicOdPremium', od_premium))
        ncb_savings = int(basic_od_premium * ncb_percentage / 100) if basic_od_premium else 0
        ncb_years = {20: 1, 25: 2, 35: 3, 45: 4, 50: 5}.get(int(ncb_percentage), 0)
        ncb_claim_threshold = int(basic_od_premium * ncb_percentage / 100) if ncb_percentage > 0 and basic_od_premium > 0 and not ncb_protection else 0

        # Loan information
        hypothecation_details = coverage_details.get('hypothecation', {})
        financier_name = hypothecation_details.get('financierName', '') or coverage_details.get('financier', '')
        outstanding_loan = safe_int(hypothecation_details.get('outstandingAmount', 0) or coverage_details.get('loanOutstanding', 0))

        # Metal depreciation
        metal_depreciation_rate = get_depreciation_rate(vehicle_age)

        # PA cover
        live_pa_cover = get_pa_cover_amount()
        pa_cover_amount = safe_int(coverage_details.get('personalAccidentCover', live_pa_cover) or
                                   coverage_details.get('paCover', live_pa_cover))

        # TP coverage
        live_tp_property_limit = get_tp_property_damage_limit()
        tp_coverage = coverage_details.get('thirdPartyCoverage', {})
        tp_bodily_injury = tp_coverage.get('bodilyInjury', 'Unlimited')
        tp_property_damage = safe_int(tp_coverage.get('propertyDamage', live_tp_property_limit))
        if is_saod:
            tp_property_damage = 0

        # Claims helpline
        claims_helpline = get_motor_claims_helpline(insurer_name)

        # V10 Analysis Data
        protection_readiness = analysis_data.get('protectionReadiness', {})
        composite_score = protection_readiness.get('compositeScore', analysis_data.get('protectionScore', 0))
        verdict = protection_readiness.get('verdict', {})
        verdict_label = verdict.get('label', analysis_data.get('protectionScoreLabel', 'Needs Review'))
        verdict_summary = verdict.get('summary', '')
        scores_data = protection_readiness.get('scores', {})

        # V10 IDV/NCB snapshots — override local IDV calculations for consistency
        idv_snapshot = analysis_data.get('idvSnapshot', {})
        ncb_snapshot = analysis_data.get('ncbSnapshot', {})

        # Override IDV values from V10 snapshot if available
        if idv_snapshot:
            _snap_mv = safe_int(idv_snapshot.get('marketValue', 0))
            _snap_orp = safe_int(idv_snapshot.get('onRoadPrice', 0))
            _snap_gap = safe_int(idv_snapshot.get('gap', 0))
            _snap_ratio = idv_snapshot.get('idvRatio', 0)
            if _snap_mv > 0:
                market_value = _snap_mv
            if _snap_orp > 0:
                current_on_road_estimate = _snap_orp
            if _snap_gap > 0:
                idv_gap = _snap_gap
                replacement_gap = _snap_gap
            if _snap_ratio > 0:
                idv_ratio = _snap_ratio

        # V10 Gaps & Strengths
        coverage_strengths = analysis_data.get('coverageStrengths', [])
        coverage_gaps_obj = analysis_data.get('coverageGaps', {})
        if isinstance(coverage_gaps_obj, dict):
            dynamic_gaps = coverage_gaps_obj.get('gaps', [])
            gap_summary = coverage_gaps_obj.get('summary', {})
        elif isinstance(coverage_gaps_obj, list):
            dynamic_gaps = coverage_gaps_obj
            gap_summary = {}
        else:
            dynamic_gaps = []
            gap_summary = {}

        # Also check gapAnalysis (moved from policyDetailsUI)
        gap_analysis_obj = analysis_data.get('gapAnalysis', {})
        if isinstance(gap_analysis_obj, dict) and gap_analysis_obj.get('gaps'):
            gap_analysis_gaps = gap_analysis_obj.get('gaps', [])
            if isinstance(gap_analysis_gaps, list) and len(gap_analysis_gaps) > len(dynamic_gaps):
                dynamic_gaps = gap_analysis_gaps
                # Recompute gap_summary to match the new source
                _ga_summary = gap_analysis_obj.get('summary', {})
                if isinstance(_ga_summary, dict) and _ga_summary:
                    gap_summary = _ga_summary
                else:
                    # Recount from the actual gaps list
                    gap_summary = {'high': 0, 'medium': 0, 'low': 0, 'total': len(dynamic_gaps)}
                    for _g in dynamic_gaps:
                        if isinstance(_g, dict):
                            _sev = str(_g.get('severity', 'low')).lower()
                            if _sev in gap_summary:
                                gap_summary[_sev] += 1

        # V10 Scenarios
        scenarios_obj = analysis_data.get('scenarios', {})
        if isinstance(scenarios_obj, dict) and scenarios_obj.get('simulations'):
            simulations = scenarios_obj.get('simulations', [])
            primary_scenario_id = scenarios_obj.get('primaryScenarioId', 'M001')
        else:
            simulations = analysis_data.get('scenarioSimulations', [])
            primary_scenario_id = scenarios_obj.get('primaryScenarioId', 'M001') if isinstance(scenarios_obj, dict) else 'M001'

        # V10 Recommendations
        recommendations_obj = analysis_data.get('recommendations', {})
        if isinstance(recommendations_obj, dict):
            priority_upgrades = recommendations_obj.get('priorityUpgrades', recommendations_obj.get('recommendations', []))
            total_upgrade_cost = recommendations_obj.get('totalUpgradeCost', {})
        elif isinstance(recommendations_obj, list):
            priority_upgrades = recommendations_obj
            total_upgrade_cost = {}
        else:
            priority_upgrades = []
            total_upgrade_cost = {}

        if not isinstance(priority_upgrades, list):
            priority_upgrades = []

        # Key concerns fallback
        key_concerns = analysis_data.get('keyConcerns', [])

        # Policy strengths fallback
        policy_strengths = analysis_data.get('policyStrengths', [])

        # Report ID
        report_id_hash = hashlib.md5(f"{policy_number}{datetime.now().isoformat()}".encode()).hexdigest()[:8].upper()
        report_id = f"EAZ-MTR-{datetime.now().strftime('%Y-%m-%d')}-{report_id_hash}"
        ModernFooter.report_id = report_id

        # Days to renewal
        days_to_renewal = 0
        try:
            from datetime import datetime as dt
            end_date_parsed = None
            for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%B %d, %Y', '%d %B %Y']:
                try:
                    end_date_parsed = dt.strptime(end_date, fmt)
                    break
                except ValueError:
                    continue
            if end_date_parsed:
                days_to_renewal = (end_date_parsed - dt.now()).days
        except Exception:
            pass

        is_expired = days_to_renewal < 0

        # ==================== PAGE 1: COVER + EXECUTIVE SUMMARY ====================
        elements.append(Spacer(1, 0.3*inch))

        # Title
        elements.append(Paragraph("Motor Insurance", styles['cover_main_title']))
        elements.append(Paragraph("Analysis Report", styles['cover_main_title']))
        elements.append(Spacer(1, 0.12*inch))

        # Vehicle info
        vehicle_display = f"{vehicle_make} {vehicle_model}"
        if vehicle_variant:
            vehicle_display += f" {vehicle_variant}"
        if manufacturing_year:
            vehicle_display += f" ({manufacturing_year})"
        elements.append(Paragraph(f"Prepared for: <b>{safe_str(policy_holder_name)}</b>", styles['cover_subtitle']))

        # Vehicle + policy type badge
        vehicle_line = f"Vehicle: {safe_str(vehicle_display)} | {safe_str(fuel_type)}, {safe_str(engine_cc)}cc"
        elements.append(Paragraph(vehicle_line, ParagraphStyle('VehicleLine', fontName=FONT_REGULAR, fontSize=10, textColor=SLATE, alignment=TA_CENTER, spaceAfter=4)))
        elements.append(Paragraph(f"Registration: {safe_str(registration_number)}", ParagraphStyle('RegLine', fontName=FONT_REGULAR, fontSize=10, textColor=SLATE, alignment=TA_CENTER, spaceAfter=8)))

        # Policy info with badge
        policy_badge = Paragraph(
            f"<font color='#{WHITE.hexval()[2:]}'><b> {badge_text} </b></font>",
            ParagraphStyle('Badge', fontName=FONT_BOLD, fontSize=8, textColor=WHITE, alignment=TA_CENTER)
        )
        badge_table = Table([[policy_badge]], colWidths=[1.5*inch])
        badge_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), badge_color),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))

        policy_line = Paragraph(
            f"Policy: {insurer_name} | {policy_number}",
            ParagraphStyle('PolicyLine', fontName=FONT_REGULAR, fontSize=9, textColor=MEDIUM_GRAY, alignment=TA_CENTER)
        )
        validity_text = f"Valid: {start_date} to {end_date}"
        if days_to_renewal > 0:
            validity_text += f" ({days_to_renewal} days to renewal)"
        elif is_expired:
            validity_text += " (EXPIRED)"
        validity_line = Paragraph(validity_text, ParagraphStyle('ValidityLine', fontName=FONT_REGULAR, fontSize=9, textColor=MEDIUM_GRAY, alignment=TA_CENTER))

        # Center badge
        badge_wrapper = Table([[badge_table]], colWidths=[6.2*inch])
        badge_wrapper.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
        elements.append(badge_wrapper)
        elements.append(Spacer(1, 0.06*inch))
        elements.append(policy_line)
        elements.append(validity_line)
        elements.append(Spacer(1, 0.2*inch))

        # Expired alert
        if is_expired:
            fine_details = get_driving_fine_details()
            fine_amount = fine_details.get("fine", 2000)
            expired_text = f"<font color='#DC2626'><b>POLICY EXPIRED</b></font> — Driving without insurance: Fine up to Rs.{fine_amount:,}, imprisonment. Renew immediately."
            elements.append(create_highlight_box(expired_text, DANGER_LIGHT, DANGER_RED))
            elements.append(Spacer(1, 0.1*inch))

        # Composite Score
        score_color = get_v10_score_color(composite_score)
        score_bg = get_v10_score_bg(composite_score)
        score_content = (
            f"<font size='9' color='#{MEDIUM_GRAY.hexval()[2:]}'>COVERAGE READINESS SCORE</font><br/><br/>"
            f"<font size='32' color='#{score_color.hexval()[2:]}'><b>{composite_score}</b></font>"
            f"<font size='12' color='#{MEDIUM_GRAY.hexval()[2:]}'>/100</font><br/><br/>"
            f"<font size='11' color='#{score_color.hexval()[2:]}'><b>{verdict_label.upper()}</b></font>"
        )
        if verdict_summary:
            score_content += f"<br/><font size='8' color='#{SLATE.hexval()[2:]}'>{verdict_summary}</font>"
        score_para = Paragraph(score_content, ParagraphStyle('CoverScore', fontName=FONT_BOLD, alignment=TA_CENTER, leading=16))
        score_box = Table([[score_para]], colWidths=[3*inch])
        score_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), score_bg),
            ('BOX', (0, 0), (-1, -1), 2, score_color),
            ('TOPPADDING', (0, 0), (-1, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        score_wrapper = Table([[score_box]], colWidths=[6.2*inch])
        score_wrapper.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
        elements.append(score_wrapper)
        elements.append(Spacer(1, 0.15*inch))

        # 3-Score Bar
        s1 = scores_data.get("s1", {})
        s2 = scores_data.get("s2")
        s3 = scores_data.get("s3")

        tiles = []
        if s1:
            tiles.append(create_score_tile(s1.get("score", 0), "Coverage\nAdequacy", "40%" if is_comprehensive else ("50%" if is_saod else "100%")))
        if s2 and not is_tp_only:
            tiles.append(create_score_tile(s2.get("score", 0), "Claim\nReadiness", "35%"))
        if s3 and not is_tp_only:
            tiles.append(create_score_tile(s3.get("score", 0), "Value for\nMoney", "25%" if is_comprehensive else "50%"))

        if tiles:
            tile_row = Table([tiles], colWidths=[2.0*inch] * len(tiles))
            tile_row.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ]))
            tile_wrapper = Table([[tile_row]], colWidths=[6.2*inch])
            tile_wrapper.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
            elements.append(tile_wrapper)
            elements.append(Spacer(1, 0.15*inch))

        # At a Glance box
        idv_display_ratio = f"{round(idv_ratio * 100)}%"
        if idv_ratio >= 0.95:
            idv_indicator_txt = "OK"
        elif idv_ratio >= 0.90:
            idv_indicator_txt = "Slight gap"
        else:
            idv_indicator_txt = "Gap"

        high_gaps = gap_summary.get('high', 0)
        med_gaps = gap_summary.get('medium', 0)
        low_gaps = gap_summary.get('low', 0)
        total_gaps = gap_summary.get('total', len(dynamic_gaps))
        gap_display = ""
        parts = []
        if high_gaps:
            parts.append(f"{high_gaps} High")
        if med_gaps:
            parts.append(f"{med_gaps} Medium")
        if low_gaps:
            parts.append(f"{low_gaps} Low")
        gap_display = " | ".join(parts) if parts else f"{total_gaps} identified"

        # Worst OOP from scenarios — handle motor-specific format
        worst_oop = 0
        worst_scenario_name = ""
        if isinstance(simulations, list):
            for sim in simulations:
                if isinstance(sim, dict):
                    # Try standard keys first
                    oop = safe_int(sim.get('outOfPocket', sim.get('youPay', 0)))
                    # Motor-specific: check withoutAddon for OOP
                    if oop == 0:
                        wa = sim.get('withoutAddon', {})
                        if isinstance(wa, dict):
                            oop = safe_int(wa.get('outOfPocket', wa.get('gap', wa.get('depreciationDeducted', 0))))
                    if oop > worst_oop:
                        worst_oop = oop
                        worst_scenario_name = sim.get('name', sim.get('title', sim.get('scenarioId', '')))

        total_addon_cost_annual = safe_int(total_upgrade_cost.get('annual', 0))
        total_addon_cost_emi = safe_int(total_upgrade_cost.get('monthlyEmi', 0))

        glance_data = [
            ["At a Glance", ""],
            ["IDV vs Market Value", f"{format_currency(idv)} / {format_currency(market_value)} ({idv_display_ratio}) {idv_indicator_txt}"],
            ["NCB", f"{int(ncb_percentage)}% — saving {format_currency(ncb_savings)}/yr" if ncb_savings else f"{int(ncb_percentage)}%"],
            ["Gaps Found", gap_display],
        ]
        if worst_oop > 0:
            glance_data.append(["Worst-case OOP", f"{format_currency(worst_oop)} ({worst_scenario_name[:30]})"])
        if total_addon_cost_annual > 0:
            emi_text = f" = {format_currency(total_addon_cost_emi)}/mo with EAZR" if total_addon_cost_emi else ""
            glance_data.append(["Recommended Add-ons", f"{format_currency(total_addon_cost_annual)}/yr{emi_text}"])

        glance_table = create_modern_table(glance_data, [2.4*inch, 3.8*inch])
        elements.append(glance_table)

        elements.append(PageBreak())

        # ==================== PAGE 2: SCORE DEEP-DIVE ====================
        elements.append(create_section_header("Protection Readiness Scores — Detailed", styles))
        elements.append(Spacer(1, 0.1*inch))

        if scores_data:
            create_score_bar(elements, scores_data, product_type_key)
        else:
            # Fallback if no V10 scores
            elements.append(Paragraph(
                f"Overall Protection Score: <b>{composite_score}/100 — {verdict_label}</b>",
                styles['body_emphasis']
            ))
            elements.append(Spacer(1, 0.1*inch))
            if is_tp_only:
                elements.append(Paragraph("Third Party Only policy — limited scoring (no OD, no add-ons).", styles['body_text']))
            elif is_saod:
                elements.append(Paragraph("Standalone OD policy — no Third Party component scored.", styles['body_text']))

        elements.append(PageBreak())

        # ==================== PAGE 3: IDV ANALYSIS + NCB TRACKER + DEPRECIATION ====================
        if not is_tp_only:
            # IDV Section
            elements.append(create_section_header("IDV (Insured Declared Value) Analysis", styles))
            elements.append(Spacer(1, 0.1*inch))

            idv_intro = (
                f"Your IDV is <b>{format_currency(idv)}</b> — this is the maximum your insurer pays in total loss or theft. "
                f"It should be as close to market value as possible."
            )
            elements.append(Paragraph(idv_intro, styles['body_text']))
            elements.append(Spacer(1, 0.1*inch))

            idv_data = [
                ["", ""],
                ["On-Road Price (approx.)", format_currency(current_on_road_estimate)],
                ["Current Market Value (est.)", format_currency(market_value)],
                ["Your IDV", format_currency(idv)],
                ["Gap in Total Loss", format_currency(idv_gap)],
                ["IDV Adequacy", f"{round(idv_ratio * 100)}%"],
            ]
            idv_table = create_key_value_table(idv_data, [3*inch, 3*inch])
            elements.append(KeepTogether([idv_table, Spacer(1, 0.1*inch)]))

            # IDV indicator box
            if idv_ratio >= 0.95:
                idv_box_text = f"IDV is aligned with market value. Adequate for replacement."
                elements.append(create_highlight_box(idv_box_text, SUCCESS_LIGHT, SUCCESS_GREEN))
            elif idv_ratio >= 0.90:
                idv_box_text = f"Slight gap of {format_currency(idv_gap)}. Consider requesting higher IDV at renewal."
                elements.append(create_highlight_box(idv_box_text, WARNING_LIGHT, WARNING_AMBER))
            else:
                rti_note = " With RTI add-on, you'd get full on-road price." if not has_rti else " Your RTI cover bridges this gap."
                idv_box_text = f"<b>Gap of {format_currency(idv_gap)}</b> — you'll receive less than your vehicle is worth in total loss.{rti_note}"
                elements.append(create_highlight_box(idv_box_text, DANGER_LIGHT, DANGER_RED))

            elements.append(Spacer(1, 0.15*inch))

            # NCB Section
            elements.append(create_section_header("NCB (No Claim Bonus) Tracker", styles))
            elements.append(Spacer(1, 0.1*inch))

            # NCB Progression
            ncb_progression_data = [
                ["Claim-Free Years", "NCB", "Status"],
                ["Year 0", "0%", "<<" if ncb_percentage == 0 else ""],
                ["Year 1", "20%", "<<" if ncb_percentage == 20 else ""],
                ["Year 2", "25%", "<<" if ncb_percentage == 25 else ""],
                ["Year 3", "35%", "<<" if ncb_percentage == 35 else ""],
                ["Year 4", "45%", "<<" if ncb_percentage == 45 else ""],
                ["Year 5+", "50%", "<<" if ncb_percentage >= 50 else ""],
            ]
            ncb_prog_table = create_modern_table(ncb_progression_data, [2*inch, 2*inch, 2*inch])
            elements.append(KeepTogether([ncb_prog_table, Spacer(1, 0.1*inch)]))

            ncb_status_data = [
                ["", ""],
                ["Current NCB", f"{int(ncb_percentage)}%"],
                ["Annual Savings", format_currency(ncb_savings)],
                ["Claim-Free Years", str(ncb_years)],
                ["NCB Protect", "Active" if ncb_protection else "Not Active"],
            ]
            ncb_status_table = create_key_value_table(ncb_status_data, [3*inch, 3*inch])
            elements.append(KeepTogether([ncb_status_table, Spacer(1, 0.1*inch)]))

            # Claim Decision Threshold
            if ncb_claim_threshold > 0:
                threshold_text = (
                    f"<b>YOUR CLAIM DECISION THRESHOLD</b><br/><br/>"
                    f"Your NCB value: {format_currency(ncb_savings)}/year<br/>"
                    f"<b>RULE:</b> Claim only if repair cost exceeds {format_currency(ncb_claim_threshold)}.<br/>"
                    f"Below {format_currency(ncb_claim_threshold)} — pay from pocket — save your NCB.<br/><br/>"
                    f"<b>If you claim:</b> NCB drops from {int(ncb_percentage)}% to 0% (per IRDAI rules). "
                    f"Next year premium increase: +{format_currency(ncb_savings)}. "
                    f"Takes {ncb_years} claim-free years to rebuild."
                )
                elements.append(create_highlight_box(threshold_text, WARNING_LIGHT, WARNING_AMBER))
            elif ncb_protection:
                elements.append(create_highlight_box(
                    "<b>NCB Protect Active</b> — Claim any amount without losing your NCB discount.",
                    SUCCESS_LIGHT, SUCCESS_GREEN
                ))

            elements.append(Spacer(1, 0.15*inch))

            # Depreciation Schedule
            elements.append(create_subsection_header(f"Depreciation Schedule (Your Vehicle: {vehicle_age} years old)"))

            dep_parts_data = [
                ["Part Type", "Depreciation", f"On {RUPEE_SYMBOL}10K Part"],
                ["Rubber/Plastic", "50%", f"{RUPEE_SYMBOL}5,000"],
                ["Fiberglass", "30%", f"{RUPEE_SYMBOL}3,000"],
                [f"Metal (body)", f"{metal_depreciation_rate}%", format_currency(int(10000 * metal_depreciation_rate / 100))],
                ["Glass", "0%", f"{RUPEE_SYMBOL}0"],
                ["Batteries", "50%", f"{RUPEE_SYMBOL}5,000"],
                ["Paint", "30-50%", f"{RUPEE_SYMBOL}3,000-5,000"],
            ]
            dep_table = create_modern_table(dep_parts_data, [2.2*inch, 1.5*inch, 2.5*inch])
            elements.append(KeepTogether([dep_table, Spacer(1, 0.08*inch)]))

            if has_zero_dep:
                elements.append(Paragraph(
                    f"<b>Your Zero Dep eliminates ALL of the above deductions.</b>",
                    styles['insight_text']
                ))
            else:
                elements.append(Paragraph(
                    f"<b>Without Zero Dep, you pay depreciation on every claim. Vehicle age {vehicle_age}yr = {metal_depreciation_rate}% on metal parts.</b>",
                    styles['warning_text']
                ))

        else:
            # TP-Only: minimal IDV section
            elements.append(create_section_header("Third Party Only Policy — No OD Coverage", styles))
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph(
                "Your policy is <b>Third Party Only</b>. It covers only damage you cause to others — "
                "not your own vehicle. If your car is damaged, stolen, or totaled, you receive nothing from insurance.",
                styles['body_text']
            ))
            elements.append(Spacer(1, 0.1*inch))

            tp_data = [
                ["", ""],
                ["Third-party injury/death", str(tp_bodily_injury) if tp_bodily_injury else "Unlimited"],
                ["Third-party property damage", format_currency(tp_property_damage) if tp_property_damage else "Up to Rs.7,50,000"],
                ["Personal Accident (Owner-Driver)", format_currency(pa_cover_amount)],
                ["Own Damage", "NOT COVERED"],
            ]
            tp_table = create_key_value_table(tp_data, [3*inch, 3*inch])
            elements.append(KeepTogether([tp_table, Spacer(1, 0.1*inch)]))

            elements.append(create_highlight_box(
                "<b>Recommendation:</b> At renewal, consider upgrading to a Comprehensive policy to protect your vehicle against "
                "accidents, theft, natural disasters, and fire.",
                WARNING_LIGHT, WARNING_AMBER
            ))

        elements.append(PageBreak())

        # ==================== PAGE 4: COVERAGE GAPS + ADD-ON MAP ====================
        elements.append(create_section_header("What's Covered & What's Missing", styles))
        elements.append(Spacer(1, 0.1*inch))

        # Coverage Strengths
        elements.append(create_subsection_header("Coverage Strengths"))

        if coverage_strengths and isinstance(coverage_strengths, list):
            for s in coverage_strengths[:6]:
                if isinstance(s, dict):
                    title = safe_str(s.get('title', s.get('area', '')))
                    reason = safe_str(s.get('reason', s.get('details', '')))
                    elements.append(Paragraph(f"<b>{title}</b> — {reason}" if reason else f"<b>{title}</b>", styles['bullet_point']))
                elif isinstance(s, str):
                    elements.append(Paragraph(f"  {safe_str(s)}", styles['bullet_point']))
        elif policy_strengths:
            for s in policy_strengths[:4]:
                if isinstance(s, str):
                    elements.append(Paragraph(f"  {safe_str(s)}", styles['bullet_point']))
        else:
            # Fallback
            if is_comprehensive:
                elements.append(Paragraph("  Comprehensive coverage protects both your vehicle and third-party liability", styles['bullet_point']))
            if has_zero_dep:
                elements.append(Paragraph("  Zero Depreciation eliminates hidden deductions on claims", styles['bullet_point']))
            if has_engine_protection:
                elements.append(Paragraph("  Engine Protection covers water damage — critical in monsoon", styles['bullet_point']))
            if ncb_percentage >= 35:
                elements.append(Paragraph(f"  Strong NCB of {int(ncb_percentage)}% providing significant premium savings", styles['bullet_point']))

        elements.append(Spacer(1, 0.1*inch))

        # Coverage Gaps Table
        elements.append(create_subsection_header("Coverage Gaps"))

        if dynamic_gaps:
            _gap_cell = ParagraphStyle('GapCell', fontName=FONT_REGULAR, fontSize=7, textColor=SLATE, leading=9)
            gap_table_data = [["#", "Gap", "Severity", "Impact", "Fix", "Est. Cost"]]
            for i, gap in enumerate(dynamic_gaps[:12], 1):
                if not isinstance(gap, dict):
                    continue
                gap_id = gap.get('gapId', f'G{i:03d}')
                gap_title = safe_str(gap.get('title', gap.get('area', gap.get('gap', ''))))
                severity = safe_str(gap.get('severity', gap.get('statusType', 'medium'))).upper()
                impact = safe_str(gap.get('impact', gap.get('description', gap.get('details', ''))))
                fix = safe_str(gap.get('solution', gap.get('recommendation', '')))
                cost = safe_str(gap.get('estimatedCost', ''))
                gap_table_data.append([gap_id, Paragraph(gap_title, _gap_cell), severity, Paragraph(impact, _gap_cell), Paragraph(fix, _gap_cell), cost])

            gap_table = Table(gap_table_data, colWidths=[0.5*inch, 1.2*inch, 0.6*inch, 1.5*inch, 1.3*inch, 1.1*inch])
            gap_style = [
                ('BACKGROUND', (0, 0), (-1, 0), BRAND_PRIMARY),
                ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
                ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
                ('FONTNAME', (0, 1), (-1, -1), FONT_REGULAR),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('TEXTCOLOR', (0, 1), (-1, -1), SLATE),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
                ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
            ]
            # Color-code severity column
            for i in range(1, len(gap_table_data)):
                sev = str(gap_table_data[i][2]).lower()
                if 'high' in sev:
                    gap_style.append(('TEXTCOLOR', (2, i), (2, i), DANGER_RED))
                elif 'med' in sev:
                    gap_style.append(('TEXTCOLOR', (2, i), (2, i), WARNING_AMBER))
                if i % 2 == 0:
                    gap_style.append(('BACKGROUND', (0, i), (-1, i), WHISPER))
            gap_table.setStyle(TableStyle(gap_style))
            elements.append(KeepTogether([gap_table, Spacer(1, 0.1*inch)]))

            # Gap severity summary
            if gap_summary:
                summary_text = f"Gap Summary: {gap_summary.get('high', 0)} High | {gap_summary.get('medium', 0)} Medium | {gap_summary.get('low', 0)} Low | Total: {gap_summary.get('total', len(dynamic_gaps))}"
                elements.append(Paragraph(f"<b>{summary_text}</b>", styles['muted_text']))
        else:
            elements.append(create_highlight_box(
                "<b>No significant coverage gaps identified.</b> Your policy has essential add-ons in place.",
                SUCCESS_LIGHT, SUCCESS_GREEN
            ))

        elements.append(Spacer(1, 0.12*inch))

        # Add-on Map (15 add-ons)
        if not is_tp_only:
            elements.append(create_subsection_header("Add-On Map"))

            # Determine relevance based on vehicle age and city
            def _addon_relevance(addon_key):
                essential_young = ['zeroDepreciation', 'engineProtection', 'returnToInvoice']
                recommended = ['ncbProtect', 'roadsideAssistance', 'consumables']
                if vehicle_age <= 3 and addon_key in essential_young:
                    return ("Essential", ADDON_ESSENTIAL)
                if vehicle_age <= 5 and addon_key in ['zeroDepreciation', 'engineProtection']:
                    return ("Essential", ADDON_ESSENTIAL)
                if addon_key in recommended:
                    return ("Recommended", ADDON_RECOMMENDED)
                return ("Optional", ADDON_OPTIONAL)

            addon_map_data = [["Add-on", "Status", "Relevance", "Est. Cost/yr"]]
            addon_list = [
                ("zeroDepreciation", "Zero Depreciation", has_zero_dep, f"{RUPEE_SYMBOL}5,000-8,000"),
                ("engineProtection", "Engine Protect", has_engine_protection, f"{RUPEE_SYMBOL}1,000-2,500"),
                ("returnToInvoice", "Return to Invoice", has_rti, f"{RUPEE_SYMBOL}2,000-4,000"),
                ("ncbProtect", "NCB Protect", ncb_protection, f"{RUPEE_SYMBOL}300-1,500"),
                ("roadsideAssistance", "Roadside Assistance", has_rsa, f"{RUPEE_SYMBOL}500-1,500"),
                ("consumables", "Consumables Cover", has_consumables, f"{RUPEE_SYMBOL}300-800"),
                ("keyCover", "Key Replacement", has_key_cover, f"{RUPEE_SYMBOL}500-1,000"),
                ("tyreCover", "Tyre Protect", has_tyre_cover, f"{RUPEE_SYMBOL}800-2,000"),
                ("passengerCover", "Passenger Cover", has_passenger_cover, f"{RUPEE_SYMBOL}300-600"),
                ("personalBaggage", "Personal Baggage", False, f"{RUPEE_SYMBOL}300-600"),
                ("emiProtect", "EMI Protect", False, f"{RUPEE_SYMBOL}500-1,500"),
                ("dailyAllowance", "Daily Allowance", False, f"{RUPEE_SYMBOL}300-800"),
                ("windshieldCover", "Windshield Cover", False, f"{RUPEE_SYMBOL}300-500"),
            ]

            # Add EV-specific if fuel type suggests EV
            is_ev = fuel_type and any(k in fuel_type.lower() for k in ['electric', 'ev', 'battery'])
            if is_ev:
                addon_list.append(("evCover", "EV Battery Cover", False, f"{RUPEE_SYMBOL}2,000-5,000"))
            else:
                addon_list.append(("evCover", "EV Battery Cover", False, "N/A"))

            for addon_key, addon_name, is_active, est_cost in addon_list:
                if is_active:
                    status_text = "Active"
                elif addon_key == "evCover" and not is_ev:
                    status_text = "N/A"
                else:
                    status_text = "Missing"

                if addon_key == "evCover" and not is_ev:
                    relevance_text = "N/A"
                else:
                    rel, _ = _addon_relevance(addon_key)
                    relevance_text = rel

                cost_text = est_cost if not is_active else "Included"
                addon_map_data.append([addon_name, status_text, relevance_text, cost_text])

            addon_map_table = Table(addon_map_data, colWidths=[1.8*inch, 0.9*inch, 1.2*inch, 1.4*inch])
            addon_style = [
                ('BACKGROUND', (0, 0), (-1, 0), BRAND_PRIMARY),
                ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
                ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
                ('FONTNAME', (0, 1), (-1, -1), FONT_REGULAR),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('TEXTCOLOR', (0, 1), (-1, -1), SLATE),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
                ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
            ]
            # Color code status and relevance
            for i in range(1, len(addon_map_data)):
                status = addon_map_data[i][1]
                if status == "Active":
                    addon_style.append(('TEXTCOLOR', (1, i), (1, i), ADDON_ACTIVE))
                elif status == "Missing":
                    addon_style.append(('TEXTCOLOR', (1, i), (1, i), ADDON_MISSING))

                rel = addon_map_data[i][2]
                if rel == "Essential":
                    addon_style.append(('TEXTCOLOR', (2, i), (2, i), ADDON_ESSENTIAL))
                elif rel == "Recommended":
                    addon_style.append(('TEXTCOLOR', (2, i), (2, i), ADDON_RECOMMENDED))

                if i % 2 == 0:
                    addon_style.append(('BACKGROUND', (0, i), (-1, i), WHISPER))
            addon_map_table.setStyle(TableStyle(addon_style))
            elements.append(KeepTogether([addon_map_table, Spacer(1, 0.08*inch)]))

            # Legend
            elements.append(Paragraph(
                "<b>Essential:</b> Based on vehicle age + city | "
                "<b>Recommended:</b> Based on NCB level + usage | "
                "<b>Optional:</b> Nice-to-have",
                styles['muted_text']
            ))

        elements.append(PageBreak())

        # ==================== PAGE 5: SCENARIO SIMULATIONS ====================
        elements.append(create_section_header("Real-World Claim Simulations", styles))
        elements.append(Spacer(1, 0.1*inch))

        elements.append(Paragraph(
            "We simulated common scenarios against your policy to show exactly what your insurance will cover.",
            styles['body_text']
        ))
        elements.append(Spacer(1, 0.1*inch))

        # Helper: extract financial data from motor-specific scenario format
        def _extract_motor_scenario_financials(sim):
            """Extract totalCost, insurancePays, outOfPocket from motor scenario format."""
            sim_id = sim.get('scenarioId', '')

            # Check for motor-specific withoutAddon/withAddon format
            without_addon = sim.get('withoutAddon', {})
            with_addon = sim.get('withAddon', {})
            repair_breakdown = sim.get('repairBreakdown', {})
            if_claim = sim.get('ifClaim', {})
            if_no_claim = sim.get('ifNoClaim', {})
            coverage_info = sim.get('coverage', {})
            typical_claims = sim.get('typicalClaims', [])
            your_status = sim.get('yourStatus', '')

            # M001: Total Loss / Theft
            if sim_id == 'M001' and without_addon:
                claim_amt = safe_int(without_addon.get('claimAmount', 0))
                gap = safe_int(without_addon.get('gap', 0))
                total = claim_amt + gap if gap > 0 else claim_amt
                return {
                    'format': 'comparison',
                    'totalCost': total,
                    'rows': [
                        ["On-Road Value (est.)", format_currency(total)],
                        ["You Receive (IDV)", format_currency(claim_amt)],
                        ["Gap (Out of Pocket)", format_currency(gap)],
                    ],
                    'with_label': with_addon.get('label', 'With RTI'),
                    'with_desc': safe_str(with_addon.get('description', '')),
                    'without_label': without_addon.get('label', 'Without RTI'),
                    'without_desc': safe_str(without_addon.get('description', '')),
                    'oop': gap,
                    'status': your_status,
                    'recommendation': safe_str(sim.get('recommendation', '')),
                }

            # M002: Major Accident - Parts Replacement
            if sim_id == 'M002' and repair_breakdown:
                total_repair = safe_int(repair_breakdown.get('totalRepairCost', 0))
                dep_deducted = safe_int(without_addon.get('depreciationDeducted', 0))
                claim_payable = safe_int(without_addon.get('claimPayable', 0))
                oop = safe_int(without_addon.get('outOfPocket', dep_deducted))
                parts = repair_breakdown.get('parts', [])
                rows = []
                for part in parts:
                    if isinstance(part, dict):
                        rows.append([safe_str(part.get('name', '')), format_currency(part.get('cost', 0))])
                labor = safe_int(repair_breakdown.get('labor', 0))
                painting = safe_int(repair_breakdown.get('painting', 0))
                if labor:
                    rows.append(["Labor", format_currency(labor)])
                if painting:
                    rows.append(["Painting", format_currency(painting)])
                rows.append(["Total Repair Cost", format_currency(total_repair)])
                rows.append(["Depreciation Deducted", format_currency(dep_deducted)])
                rows.append(["Insurance Pays", format_currency(claim_payable)])
                rows.append(["You Pay (OOP)", format_currency(oop)])
                coverage_pct = int(claim_payable / total_repair * 100) if total_repair > 0 else 0
                return {
                    'format': 'breakdown',
                    'totalCost': total_repair,
                    'rows': rows,
                    'oop': oop,
                    'coveragePct': coverage_pct,
                    'with_label': with_addon.get('label', 'With Zero Dep'),
                    'with_desc': safe_str(with_addon.get('description', '')),
                    'without_label': without_addon.get('label', 'Without Zero Dep'),
                    'without_desc': safe_str(without_addon.get('description', '')),
                    'status': your_status,
                    'recommendation': safe_str(sim.get('recommendation', '')),
                }

            # M003: Engine Damage
            if sim_id == 'M003' and without_addon:
                engine_cost = safe_int(without_addon.get('outOfPocket', 0))
                covered_flag = without_addon.get('covered', False)
                with_covered = with_addon.get('covered', True)
                with_payout = safe_int(with_addon.get('claimPayable', engine_cost))
                oop = engine_cost if not covered_flag else 0
                return {
                    'format': 'comparison',
                    'totalCost': engine_cost,
                    'rows': [
                        ["Engine Repair Cost", format_currency(engine_cost)],
                        ["Without Engine Protect", format_currency(engine_cost) + " (OOP)"],
                        ["With Engine Protect", format_currency(0) + " (Fully Covered)"],
                    ],
                    'oop': oop,
                    'status': your_status,
                    'recommendation': safe_str(sim.get('recommendation', '')),
                }

            # M004: Third Party Accident
            if sim_id == 'M004' and (coverage_info or typical_claims):
                rows = []
                if coverage_info:
                    rows.append(["Death/Bodily Injury", safe_str(coverage_info.get('deathBodilyInjury', 'Unlimited'))])
                    rows.append(["Property Damage", safe_str(coverage_info.get('propertyDamage', ''))])
                for tc in typical_claims[:4]:
                    if isinstance(tc, dict):
                        rows.append([safe_str(tc.get('type', '')), safe_str(tc.get('range', ''))])
                return {
                    'format': 'info',
                    'totalCost': 0,
                    'rows': rows,
                    'oop': 0,
                    'status': your_status,
                    'recommendation': safe_str(sim.get('recommendation', '')),
                }

            # M005: Minor Accident - Claim Decision
            if sim_id == 'M005' and (if_claim or if_no_claim):
                inputs = sim.get('inputs', {})
                repair_cost = safe_int(inputs.get('repairCost', 0))
                rows = [
                    ["Repair Cost", format_currency(repair_cost)],
                    ["Current NCB", safe_str(inputs.get('currentNcb', ''))],
                ]
                if if_claim:
                    rows.append(["If You Claim", f"Get {format_currency(safe_int(if_claim.get('claimAmount', 0)))}, NCB drops {safe_str(if_claim.get('ncbImpact', ''))}"])
                if if_no_claim:
                    rows.append(["If You Don't Claim", f"Pay {format_currency(safe_int(if_no_claim.get('outOfPocket', 0)))}, retain NCB"])
                threshold = sim.get('claimThreshold', {})
                if threshold:
                    rows.append(["Claim Threshold", safe_str(threshold.get('message', ''))])
                return {
                    'format': 'decision',
                    'totalCost': repair_cost,
                    'rows': rows,
                    'oop': safe_int(if_no_claim.get('outOfPocket', repair_cost)),
                    'status': your_status,
                    'recommendation': safe_str(sim.get('recommendation', '')),
                }

            # Generic fallback — try standard keys
            total_cost = safe_int(sim.get('totalCost', sim.get('repairCost', 0)))
            covered_amt = safe_int(sim.get('insurancePays', sim.get('covered', 0)))
            oop_amt = safe_int(sim.get('outOfPocket', sim.get('youPay', 0)))
            cov_pct = sim.get('coveragePercentage', sim.get('coveragePct', 0))
            return {
                'format': 'generic',
                'totalCost': total_cost,
                'rows': [
                    ["Total Cost", format_currency(total_cost)],
                    ["Insurance Pays", format_currency(covered_amt)],
                    ["You Pay (OOP)", format_currency(oop_amt)],
                    ["Coverage", f"{int(cov_pct)}%"],
                ],
                'oop': oop_amt,
                'coveragePct': cov_pct,
                'status': '',
                'recommendation': '',
            }

        # Use dynamic simulations if available
        if simulations and isinstance(simulations, list):
            for sim in simulations:
                if not isinstance(sim, dict):
                    continue

                sim_id = sim.get('scenarioId', sim.get('id', ''))
                sim_title = sim.get('name', sim.get('title', sim.get('scenarioTitle', sim_id)))
                is_primary = (sim_id == primary_scenario_id)
                primary_marker = " [PRIMARY]" if is_primary else ""
                description = safe_str(sim.get('description', sim.get('subtitle', '')))

                # Section header
                header = f"{sim_id}: {sim_title}{primary_marker}"
                elements.append(create_subsection_header(header))

                if description:
                    elements.append(Paragraph(description[:150], styles['body_text']))

                # Extract financial data using motor-aware helper
                fin = _extract_motor_scenario_financials(sim)
                rows = fin.get('rows', [])

                if rows:
                    sim_data = [["", "Amount"]] + rows
                    oop_val = fin.get('oop', 0)
                    sim_table = create_key_value_table(sim_data, [3*inch, 3*inch],
                                                        accent_color=DANGER_RED if oop_val > 0 else SUCCESS_GREEN)
                    elements.append(KeepTogether([sim_table, Spacer(1, 0.06*inch)]))

                # Status and recommendation
                status = fin.get('status', '')
                rec_text = fin.get('recommendation', '')
                if status == 'at_risk' and rec_text:
                    elements.append(Paragraph(
                        f"<font color='#DC2626'><b>AT RISK</b></font> — {rec_text[:120]}",
                        styles['body_text']
                    ))
                elif status == 'protected' and rec_text:
                    elements.append(Paragraph(
                        f"<font color='#059669'><b>PROTECTED</b></font> — {rec_text[:120]}",
                        styles['body_text']
                    ))
                elif status == 'covered' and rec_text:
                    elements.append(Paragraph(
                        f"<font color='#059669'><b>COVERED</b></font> — {rec_text[:120]}",
                        styles['body_text']
                    ))
                elif rec_text:
                    elements.append(Paragraph(f"<i>{rec_text[:120]}</i>", styles['body_text']))

                elements.append(Spacer(1, 0.08*inch))

        else:
            # Fallback: generate hardcoded scenarios
            scenario_50k = calculate_claim_scenario(50000, vehicle_age, has_zero_dep, compulsory_deductible, voluntary_deductible, smart_saver_deductible)
            scenario_2l = calculate_claim_scenario(200000, vehicle_age, has_zero_dep, compulsory_deductible, voluntary_deductible, smart_saver_deductible)

            elements.append(create_subsection_header("M001: Total Loss / Theft"))
            loss_data = [
                ["", "Your Policy"],
                ["You Receive", format_currency(idv)],
                ["Replacement Cost", format_currency(current_on_road_estimate)],
                ["Gap (OOP)", format_currency(replacement_gap)],
            ]
            elements.append(KeepTogether([create_key_value_table(loss_data, [3*inch, 3*inch]), Spacer(1, 0.1*inch)]))

            elements.append(create_subsection_header("M002: Major Accident (Rs.2,00,000 repair)"))
            major_data = [
                ["", "Amount"],
                ["Repair Bill", format_currency(200000)],
                ["Depreciation Deducted", format_currency(scenario_2l['depreciation'])],
                ["Deductibles", format_currency(total_deductible)],
                ["Insurance Pays", format_currency(scenario_2l['insurance_pays'])],
                ["You Pay", format_currency(scenario_2l['you_pay'])],
            ]
            elements.append(KeepTogether([create_key_value_table(major_data, [3*inch, 3*inch]), Spacer(1, 0.1*inch)]))

            elements.append(create_subsection_header("M005: Minor Accident (Rs.50,000 repair)"))
            minor_data = [
                ["", "Amount"],
                ["Repair Bill", format_currency(50000)],
                ["Depreciation Deducted", format_currency(scenario_50k['depreciation'])],
                ["Deductibles", format_currency(total_deductible)],
                ["Insurance Pays", format_currency(scenario_50k['insurance_pays'])],
                ["You Pay", format_currency(scenario_50k['you_pay'])],
            ]
            elements.append(KeepTogether([create_key_value_table(minor_data, [3*inch, 3*inch]), Spacer(1, 0.1*inch)]))

        # Scenario Comparison Summary Table
        if simulations and isinstance(simulations, list) and len(simulations) >= 2:
            elements.append(Spacer(1, 0.08*inch))
            elements.append(create_subsection_header("Scenario Comparison Summary"))

            comp_data = [["Scenario", "Total Cost", "Your OOP", "Status"]]
            worst_case_oop = 0
            for sim in simulations:
                if not isinstance(sim, dict):
                    continue
                sim_name = str(sim.get('name', sim.get('title', sim.get('scenarioId', ''))))
                fin = _extract_motor_scenario_financials(sim)
                tc = fin.get('totalCost', 0)
                oop = fin.get('oop', 0)
                status = fin.get('status', '')
                status_display = 'Protected' if status == 'protected' else ('At Risk' if status == 'at_risk' else ('Covered' if status == 'covered' else '-'))
                comp_data.append([sim_name, format_currency(tc), format_currency(oop), status_display])
                worst_case_oop = max(worst_case_oop, oop)

            comp_data.append(["WORST CASE", "", format_currency(worst_case_oop), ""])

            comp_table = create_modern_table(comp_data, [2.2*inch, 1.4*inch, 1.4*inch, 1.2*inch])
            elements.append(KeepTogether([comp_table]))

        elements.append(PageBreak())

        # ==================== PAGE 6: RENEWAL CHECKLIST ====================
        elements.append(create_section_header("Your Renewal Checklist", styles))
        elements.append(Spacer(1, 0.1*inch))

        if days_to_renewal > 0:
            elements.append(Paragraph(
                f"Renewal Date: <b>{end_date}</b> ({days_to_renewal} days away)",
                styles['body_emphasis']
            ))
        elif is_expired:
            elements.append(Paragraph(
                f"<font color='#DC2626'><b>POLICY EXPIRED on {end_date}. Renew immediately.</b></font>",
                styles['body_emphasis']
            ))
        elements.append(Spacer(1, 0.1*inch))

        # Priority Upgrades
        elements.append(create_subsection_header("Priority Upgrades"))

        if priority_upgrades:
            for i, rec in enumerate(priority_upgrades[:6], 1):
                if not isinstance(rec, dict):
                    continue
                rec_title = safe_str(rec.get('title', rec.get('category', f'Recommendation {i}')))
                rec_desc = safe_str(rec.get('description', rec.get('suggestion', rec.get('impact', ''))))
                rec_cost = safe_str(rec.get('estimatedCost', ''))
                rec_fixes = safe_str(rec.get('fixes', ''))
                rec_priority = rec.get('priority', 'medium')

                card_content = f"<b>#{i} {rec_title}</b>"
                if rec_fixes:
                    card_content += f" <font color='#{MEDIUM_GRAY.hexval()[2:]}' size='7'>[Fixes: {rec_fixes}]</font>"
                card_content += f"<br/>"
                if rec_desc:
                    card_content += f"<font size='9' color='#{SLATE.hexval()[2:]}'>{str(rec_desc)[:150]}</font><br/>"
                if rec_cost:
                    card_content += f"<font size='8' color='#{BRAND_PRIMARY.hexval()[2:]}'>Cost: <b>{rec_cost}</b></font>"

                pri_str = str(rec_priority).lower()
                if pri_str in ('high', 'immediate', '1', '2'):
                    border = DANGER_RED
                    bg = DANGER_LIGHT
                elif pri_str in ('medium', 'renewal', '3', '4'):
                    border = WARNING_AMBER
                    bg = WARNING_LIGHT
                else:
                    border = INFO_BLUE
                    bg = INFO_LIGHT

                elements.append(create_highlight_box(card_content, bg, border))
                elements.append(Spacer(1, 0.06*inch))
        else:
            # Fallback recommendations
            what_you_should_do = analysis_data.get('whatYouShouldDo', {})
            if isinstance(what_you_should_do, dict):
                for key in ['immediate', 'renewal', 'ongoing']:
                    action = what_you_should_do.get(key, {})
                    if isinstance(action, dict) and action.get('action'):
                        elements.append(Paragraph(
                            f"<b>{key.title()}:</b> {action.get('action', '')} — {action.get('brief', '')}",
                            styles['bullet_point']
                        ))
            else:
                # Basic hardcoded fallback
                if not has_zero_dep and vehicle_age < 5:
                    elements.append(Paragraph("  Add Zero Depreciation at renewal", styles['bullet_point']))
                if not has_engine_protection:
                    elements.append(Paragraph("  Add Engine Protection for monsoon coverage", styles['bullet_point']))
                if not ncb_protection and ncb_percentage >= 35:
                    elements.append(Paragraph(f"  Add NCB Protection to preserve your {int(ncb_percentage)}% NCB", styles['bullet_point']))

        elements.append(Spacer(1, 0.12*inch))

        # Investment Summary Table
        if total_upgrade_cost and (total_upgrade_cost.get('annual') or total_upgrade_cost.get('monthlyEmi')):
            elements.append(create_subsection_header("Total Upgrade Investment"))

            inv_data = [
                ["", ""],
                ["Total Annual Cost", format_currency(total_upgrade_cost.get('annual', 0))],
                ["EAZR EMI/month", format_currency(total_upgrade_cost.get('monthlyEmi', 0))],
            ]
            inv_table = create_key_value_table(inv_data, [3*inch, 3*inch], accent_color=BRAND_PRIMARY)
            elements.append(KeepTogether([inv_table, Spacer(1, 0.08*inch)]))

            if worst_oop > 0:
                elements.append(Paragraph(
                    f"For {format_currency(total_upgrade_cost.get('monthlyEmi', 0))}/month, "
                    f"your worst-case OOP drops from {format_currency(worst_oop)} significantly.",
                    styles['insight_text']
                ))

        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph(
            f"<b>Finance your entire protection upgrade with EAZR</b><br/>"
            f"Apply at: eazr.in | Download the EAZR app",
            ParagraphStyle('CTA', fontName=FONT_BOLD, fontSize=10, textColor=BRAND_PRIMARY, alignment=TA_CENTER, leading=14)
        ))

        elements.append(PageBreak())

        # ==================== PAGE 7: VEHICLE & POLICY REFERENCE ====================
        elements.append(create_section_header("Vehicle & Policy Reference", styles))
        elements.append(Spacer(1, 0.1*inch))

        # Vehicle Details
        elements.append(create_subsection_header("Vehicle Details"))
        vehicle_ref_data = [
            ["Make", vehicle_make],
            ["Model", f"{vehicle_model} {vehicle_variant}".strip()],
            ["Manufacturing Year", str(manufacturing_year) if manufacturing_year else "N/A"],
            ["Fuel Type", fuel_type],
            ["Engine Capacity", f"{engine_cc}cc" if engine_cc and engine_cc != 'N/A' else "N/A"],
            ["Registration", registration_number],
            ["Registration Date", registration_date],
            ["Engine Number", engine_number],
            ["Chassis Number", chassis_number],
        ]
        vr_data = [["", ""]] + vehicle_ref_data
        vr_table = create_key_value_table(vr_data, [2.5*inch, 3.5*inch])
        elements.append(KeepTogether([vr_table, Spacer(1, 0.1*inch)]))

        # Policy Details
        elements.append(create_subsection_header("Policy Details"))
        policy_ref_data = [
            ["", ""],
            ["Insurer", insurer_name],
            ["Policy Number", policy_number],
            ["Policy Type", badge_text],
            ["Validity", f"{start_date} to {end_date}"],
        ]
        pr_table = create_key_value_table(policy_ref_data, [2.5*inch, 3.5*inch])
        elements.append(KeepTogether([pr_table, Spacer(1, 0.1*inch)]))

        # Coverage
        elements.append(create_subsection_header("Coverage"))
        coverage_ref_data = [
            ["Coverage", "Amount"],
            ["IDV (Own Damage)", format_currency(idv)],
            ["OD Premium", format_currency(od_premium)],
            ["TP Premium", format_currency(tp_premium)],
            ["PA Cover (Owner-Driver)", format_currency(pa_cover_amount)],
            ["Compulsory Deductible", format_currency(compulsory_deductible)],
        ]
        if voluntary_deductible > 0:
            coverage_ref_data.append(["Voluntary Deductible", format_currency(voluntary_deductible)])
        if smart_saver_deductible > 0:
            coverage_ref_data.append(["Plan Deductible", format_currency(smart_saver_deductible)])
        cr_table = create_modern_table(coverage_ref_data, [3*inch, 3*inch])
        elements.append(KeepTogether([cr_table, Spacer(1, 0.1*inch)]))

        # Active Add-ons
        elements.append(create_subsection_header("Active Add-ons"))
        active_addons = []
        addon_checks = [
            (has_zero_dep, "Zero Depreciation"),
            (has_engine_protection, "Engine Protection"),
            (has_rti, "Return to Invoice"),
            (ncb_protection, "NCB Protection"),
            (has_rsa, "Roadside Assistance"),
            (has_consumables, "Consumables Cover"),
            (has_tyre_cover, "Tyre Cover"),
            (has_key_cover, "Key Replacement"),
            (has_passenger_cover, "Passenger Cover"),
        ]
        for is_active, name in addon_checks:
            if is_active:
                active_addons.append(name)

        if active_addons:
            for addon in active_addons:
                elements.append(Paragraph(f"  {addon}", styles['bullet_point']))
        else:
            elements.append(Paragraph("  No add-on covers detected", styles['muted_text']))

        elements.append(Spacer(1, 0.08*inch))

        # NCB & Premium
        elements.append(create_subsection_header("NCB & Premium"))
        ncb_prem_data = [
            ["", ""],
            ["NCB Percentage", f"{int(ncb_percentage)}%"],
            ["NCB Savings", format_currency(ncb_savings)],
            ["Total Premium Paid", format_currency(total_premium)],
        ]
        np_table = create_key_value_table(ncb_prem_data, [3*inch, 3*inch])
        elements.append(KeepTogether([np_table, Spacer(1, 0.08*inch)]))

        # Network & Support
        elements.append(create_subsection_header("Network & Support"))
        support_data = [
            ["", ""],
            ["Claims Helpline", claims_helpline],
            ["IRDAI Toll-Free", "155255 / 1800-4254-732"],
        ]
        if financier_name:
            support_data.append(["Hypothecation", financier_name])
            if outstanding_loan > 0:
                support_data.append(["Outstanding Loan", format_currency(outstanding_loan)])
        sp_table = create_key_value_table(support_data, [2.5*inch, 3.5*inch])
        elements.append(KeepTogether([sp_table]))

        elements.append(PageBreak())

        # ==================== PAGE 8: BACK COVER — DISCLAIMERS ====================
        elements.append(Spacer(1, 1.5*inch))

        # EAZR Branding
        elements.append(Paragraph("EAZR", ParagraphStyle(
            'BrandName', fontName=FONT_BOLD, fontSize=36, textColor=BRAND_PRIMARY, alignment=TA_CENTER, leading=44, spaceAfter=8
        )))
        elements.append(Paragraph("Powered by EAZR Policy Intelligence", ParagraphStyle(
            'Powered', fontName=FONT_REGULAR, fontSize=12, textColor=MEDIUM_GRAY, alignment=TA_CENTER, leading=16, spaceAfter=6
        )))
        elements.append(Paragraph("Finance your next renewal with EAZR IPF", ParagraphStyle(
            'CTA2', fontName=FONT_ITALIC, fontSize=10, textColor=BRAND_SECONDARY, alignment=TA_CENTER, leading=14, spaceAfter=6
        )))
        elements.append(Paragraph("Contact: support@eazr.in | www.eazr.in", ParagraphStyle(
            'Contact', fontName=FONT_REGULAR, fontSize=9, textColor=MEDIUM_GRAY, alignment=TA_CENTER, leading=12, spaceAfter=24
        )))

        elements.append(Spacer(1, 0.3*inch))

        # Disclaimers
        disclaimer_title = Paragraph(
            "<b>IMPORTANT DISCLAIMERS</b>",
            ParagraphStyle('DisclaimerTitle', fontName=FONT_BOLD, fontSize=10, textColor=CHARCOAL, spaceBefore=10, spaceAfter=8)
        )
        elements.append(disclaimer_title)

        disclaimers = [
            "This report is generated by EAZR's AI-powered Policy Intelligence engine for informational and educational purposes only.",
            "IDV (Insured Declared Value) and market value estimates are based on standard depreciation schedules and publicly available market data. Actual IDV is set by the insurer at renewal.",
            "Add-on costs mentioned are indicative ranges based on market data. Actual premiums will be quoted by your insurer at renewal.",
            "NCB (No Claim Bonus) percentages and rules are per IRDAI standard guidelines. Specific terms may vary by insurer.",
            "Depreciation rates used are per IRDAI standard depreciation schedule. Actual claim depreciation may vary by insurer's interpretation.",
            "Scenario simulations use estimated repair and replacement costs for metro cities. Actual costs vary by city, garage, and parts availability.",
            "EAZR IPF (Insurance Premium Financing) is subject to eligibility, minimum premium thresholds, and applicable terms.",
            "For personalized insurance advice, consult your insurer or a licensed insurance advisor.",
        ]

        for i, disc in enumerate(disclaimers, 1):
            elements.append(Paragraph(
                f"{i}. {disc}",
                ParagraphStyle('Disclaimer', fontName=FONT_REGULAR, fontSize=7, textColor=MEDIUM_GRAY, leading=10, spaceAfter=3, leftIndent=10)
            ))

        elements.append(Spacer(1, 0.2*inch))

        # Report footer
        elements.append(Paragraph(
            f"EAZR Digipayments Private Limited",
            ParagraphStyle('CompanyName', fontName=FONT_BOLD, fontSize=8, textColor=MEDIUM_GRAY, alignment=TA_CENTER, spaceAfter=4)
        ))
        elements.append(Paragraph(
            f"Report ID: {report_id}",
            ParagraphStyle('ReportId', fontName=FONT_REGULAR, fontSize=8, textColor=MEDIUM_GRAY, alignment=TA_CENTER, spaceAfter=2)
        ))
        elements.append(Paragraph(
            f"Analysis Version: 10.0 | Generated: {datetime.now().strftime('%d %B %Y %H:%M')}",
            ParagraphStyle('Version', fontName=FONT_REGULAR, fontSize=7, textColor=LIGHT_GRAY, alignment=TA_CENTER)
        ))

        # ==================== BUILD PDF ====================
        pdf_doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
        buffer.seek(0)

        logger.info(f"V10 Motor insurance report generated successfully for policy {policy_number}")
        return buffer

    except Exception as e:
        logger.error(f"Error generating motor insurance report: {str(e)}", exc_info=True)
        raise
