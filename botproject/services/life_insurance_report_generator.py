"""
Life Insurance Policy Analysis Report Generator — V10
Based on EAZR_02_Life_Insurance_PolicyAnalysisTab.md spec
7-page PDF: Cover+Summary, Score Deep-Dive, Strengths & Gaps,
Scenarios, Recommendations+SVF, Policy Reference, Back Cover.

Term policies: ~6 pages (S1 only, L001 only, no SVF).
Savings policies: 7 pages (S1+S2+S3, L001-L004, SVF section).
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

# Import market data service for dynamic rates
from services.indian_market_data_service import (
    get_ppf_rate,
    get_bank_fd_rate,
    get_survival_benefit_rate,
    get_life_insurance_market_data
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

# ==================== V10 SCORE & GAP COLORS ====================
SCORE_EXCELLENT = colors.HexColor('#22C55E')
SCORE_STRONG = colors.HexColor('#84CC16')
SCORE_ADEQUATE = colors.HexColor('#EAB308')
SCORE_MODERATE = colors.HexColor('#F97316')
SCORE_ATTENTION = colors.HexColor('#6B7280')

GAP_HIGH = colors.HexColor('#F97316')
GAP_MEDIUM = colors.HexColor('#EAB308')
GAP_LOW = colors.HexColor('#6B7280')
GAP_OPPORTUNITY = colors.HexColor('#8B5CF6')

SVF_ACCENT = colors.HexColor('#8B5CF6')
SVF_BG = colors.HexColor('#F5F3FF')
SVF_LIGHT = colors.HexColor('#EDE9FE')

BADGE_COLORS = {
    'term': colors.HexColor('#3B82F6'),
    'endowment': colors.HexColor('#22C55E'),
    'ulip': colors.HexColor('#8B5CF6'),
    'whole_life': colors.HexColor('#F59E0B'),
    'money_back': colors.HexColor('#EC4899'),
    'pension': colors.HexColor('#6B7280'),
    'child_plan': colors.HexColor('#14B8A6'),
}

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
        return int(float(value))
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    """Safely convert value to float"""
    if value is None or value == 'N/A' or value == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_str(value, default=''):
    """Safely convert value to string, sanitizing Unicode for PDF rendering"""
    if value is None:
        return default
    s = str(value)
    s = s.replace('\u20b9', 'Rs.').replace('₹', 'Rs.')
    s = s.replace('\u2022', '-').replace('\u2013', '-').replace('\u2014', '-')
    s = s.replace('\u2018', "'").replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
    return s


def _get_v10_score_color(score):
    """Get V10 score color based on tier thresholds."""
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


def _get_v10_score_bg(score):
    """Get light background color for V10 score tier."""
    if score >= 90:
        return SUCCESS_LIGHT
    elif score >= 75:
        return colors.HexColor('#ECFCCB')
    elif score >= 60:
        return WARNING_LIGHT
    elif score >= 40:
        return colors.HexColor('#FFEDD5')
    else:
        return WHISPER


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


def _get_gap_color(severity):
    """Get gap color by severity string."""
    sev = str(severity).lower()
    if sev == 'high':
        return GAP_HIGH
    elif sev == 'medium':
        return GAP_MEDIUM
    elif sev == 'opportunity':
        return GAP_OPPORTUNITY
    return GAP_LOW


def _get_gap_bg(severity):
    """Get light background for gap severity."""
    sev = str(severity).lower()
    if sev == 'high':
        return colors.HexColor('#FFEDD5')
    elif sev == 'medium':
        return WARNING_LIGHT
    elif sev == 'opportunity':
        return SVF_LIGHT
    return WHISPER


def get_claims_helpline(insurer_name: str) -> str:
    """Get claims helpline number based on insurance provider name"""
    if not insurer_name or insurer_name == 'N/A':
        return "See policy document"

    insurer_lower = insurer_name.lower()

    helplines = {
        'lic': '022-68276827',
        'life insurance corporation': '022-68276827',
        'hdfc life': '1800-266-9777',
        'hdfc': '1800-266-9777',
        'icici prudential': '1860-266-7766',
        'icici pru': '1860-266-7766',
        'sbi life': '1800-267-9090',
        'max life': '1860-120-5577',
        'bajaj allianz life': '1800-209-5858',
        'bajaj': '1800-209-5858',
        'kotak life': '1800-209-8800',
        'kotak': '1800-209-8800',
        'tata aia': '1800-266-9966',
        'tata': '1800-266-9966',
        'birla sun life': '1800-270-7000',
        'aditya birla': '1800-270-7000',
        'reliance nippon': '1800-102-1010',
        'reliance': '1800-102-1010',
        'pnb metlife': '1800-425-6969',
        'metlife': '1800-425-6969',
        'aviva': '1800-103-7766',
        'aegon': '1800-209-9090',
        'exide life': '1800-419-8228',
        'canara hsbc': '1800-103-0003',
        'star union': '1800-266-8833',
        'india first': '1800-209-7225',
        'sahara': '1800-180-1111',
        'shriram': '1800-103-0123',
        'edelweiss': '1800-419-5999',
        'future generali': '1800-220-233',
        'pramerica': '1800-102-4444',
        'bharti axa': '1800-102-4444',
    }

    for key, number in helplines.items():
        if key in insurer_lower:
            return number

    return "See policy document"


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
        canvas.drawCentredString(A4[0] / 2, A4[1] - 0.4*inch, "Life Insurance Analysis Report")

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
        canvas.setFont(FONT_REGULAR, 6.5)
        canvas.setFillColor(LIGHT_GRAY)
        rid = ModernFooter.report_id or ""
        canvas.drawString(0.6*inch, 0.38*inch,
                         f"EAZR Digipayments Pvt Ltd | Report ID: {rid} | {datetime.now().strftime('%d %B %Y')}")
        canvas.drawRightString(A4[0] - 0.6*inch, 0.38*inch,
                              "AI-generated analysis. Not a substitute for professional advice.")
        canvas.restoreState()


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


def create_score_visual(score, protection_label, score_color_override=None):
    """Create a modern protection score visual"""
    score_color = score_color_override or _get_v10_score_color(score)
    bg_color = _get_v10_score_bg(score)

    score_content = f"""
    <font size="32" color="#{score_color.hexval()[2:]}"><b>{score}</b></font><font size="12" color="#{MEDIUM_GRAY.hexval()[2:]}">/100</font>
    <br/><br/>
    <font size="10" color="#{score_color.hexval()[2:]}"><b>{protection_label}</b></font>
    """
    score_para = Paragraph(score_content, ParagraphStyle('ScoreDisplay', fontName=FONT_BOLD, alignment=TA_CENTER, leading=18))
    score_table = Table([[score_para]], colWidths=[2.2*inch])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_color),
        ('BOX', (0, 0), (-1, -1), 2, score_color),
        ('TOPPADDING', (0, 0), (-1, -1), 18),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 18),
        ('LEFTPADDING', (0, 0), (-1, -1), 18),
        ('RIGHTPADDING', (0, 0), (-1, -1), 18),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    return score_table


def create_info_card(items, accent_color=BRAND_PRIMARY):
    """Create a modern info card"""
    card_data = []
    for key, value in items:
        card_data.append([
            Paragraph(f"<b>{key}</b>", ParagraphStyle('CardKey', fontName=FONT_BOLD, fontSize=8, textColor=MEDIUM_GRAY)),
            Paragraph(str(value), ParagraphStyle('CardValue', fontName=FONT_REGULAR, fontSize=9, textColor=CHARCOAL))
        ])
    card = Table(card_data, colWidths=[1.8*inch, 2.8*inch])
    card.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), WHISPER),
        ('LINEABOVE', (0, 0), (-1, 0), 3, accent_color),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return card


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
    """Create a key-value style table for scenarios"""
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


def _create_score_tile(score_data, weight_label):
    """Create a single score tile for the executive summary."""
    if not score_data:
        return None
    sc = safe_int(score_data.get('score', 0))
    label = score_data.get('label', '')
    name = score_data.get('name', '')
    color_hex = score_data.get('color', '#6B7280')
    sc_color = colors.HexColor(color_hex)
    bg = _get_v10_score_bg(sc)

    content = f"""<font size="18" color="{color_hex}"><b>{sc}</b></font><font size="8" color="#{MEDIUM_GRAY.hexval()[2:]}">/100</font>
<br/><font size="7" color="#{SLATE.hexval()[2:]}">{name}</font>
<br/><font size="6" color="#{LIGHT_GRAY.hexval()[2:]}">{weight_label}</font>"""
    para = Paragraph(content, ParagraphStyle('TileScore', fontName=FONT_BOLD, alignment=TA_CENTER, leading=13))
    tile = Table([[para]], colWidths=[1.9*inch])
    tile.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('BOX', (0, 0), (-1, -1), 1.5, sc_color),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    return tile


def _create_factor_table(factors, score_name, score_val, score_label, score_color_hex):
    """Create a factor-level breakdown table for score deep-dive."""
    if not factors:
        return []

    sc_color = colors.HexColor(score_color_hex) if score_color_hex else BRAND_PRIMARY
    elems = []

    # Score bar header
    bar_text = f"<b>{score_name}</b>  <font color='{score_color_hex}'><b>{score_val}/100 — {score_label}</b></font>"
    elems.append(Paragraph(bar_text, ParagraphStyle('ScoreBarH', fontName=FONT_BOLD, fontSize=11, textColor=CHARCOAL, spaceAfter=6)))

    # Factor table — use Paragraph for text wrapping
    _fc_s = ParagraphStyle('FactorCell', fontName=FONT_REGULAR, fontSize=8, textColor=SLATE, leading=10)
    _fh_s = ParagraphStyle('FactorHdr', fontName=FONT_BOLD, fontSize=8, textColor=WHITE, leading=10)
    table_data = [[
        Paragraph("Factor", _fh_s),
        Paragraph("Your Policy", _fh_s),
        Paragraph("Benchmark", _fh_s),
        Paragraph("Pts/Max", _fh_s),
    ]]
    for f in factors:
        fname = safe_str(f.get('name', ''))
        your_val = safe_str(f.get('yourPolicy', ''))
        bench = safe_str(f.get('benchmark', ''))
        earned = safe_int(f.get('pointsEarned', 0))
        max_pts = safe_int(f.get('pointsMax', 0))
        table_data.append([
            Paragraph(fname, _fc_s),
            Paragraph(your_val, _fc_s),
            Paragraph(bench, _fc_s),
            Paragraph(f"{earned}/{max_pts}", _fc_s),
        ])

    # Total row
    _ft_s = ParagraphStyle('FactorTotal', fontName=FONT_BOLD, fontSize=8, textColor=CHARCOAL, leading=10)
    total_earned = sum(safe_int(f.get('pointsEarned', 0)) for f in factors)
    total_max = sum(safe_int(f.get('pointsMax', 0)) for f in factors)
    table_data.append([Paragraph("TOTAL", _ft_s), "", "", Paragraph(f"{total_earned}/{total_max}", _ft_s)])

    ft = Table(table_data, colWidths=[2.0*inch, 1.5*inch, 1.3*inch, 1.4*inch])
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), sc_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('FONTNAME', (0, 1), (-1, -1), FONT_REGULAR),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TEXTCOLOR', (0, 1), (-1, -2), SLATE),
        ('FONTNAME', (0, -1), (-1, -1), FONT_BOLD),
        ('TEXTCOLOR', (0, -1), (-1, -1), CHARCOAL),
        ('BACKGROUND', (0, -1), (-1, -1), BRAND_LIGHTER),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
    ]
    for i in range(1, len(table_data) - 1):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), WHISPER))
    ft.setStyle(TableStyle(style_cmds))
    elems.append(ft)
    return elems


# ==============================================================================
# MAIN REPORT GENERATOR — V10 (7-page PDF)
# ==============================================================================

def generate_life_insurance_report(policy_data: dict, analysis_data: dict) -> BytesIO:
    """
    Generate V10 life insurance analysis report.
    Pages: Cover+Summary, Score Deep-Dive, Strengths & Gaps,
    Scenarios, Recommendations+SVF, Policy Reference, Back Cover.
    """
    try:
        buffer = BytesIO()
        pdf_doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=0.6*inch, leftMargin=0.6*inch,
            topMargin=0.85*inch, bottomMargin=0.7*inch,
            title="Life Insurance Policy Analysis",
            author="EAZR Insurance Platform"
        )

        elements = []
        styles = create_styles()

        # ==================== EXTRACT BASE DATA ====================
        policy_number = str(policy_data.get('policyNumber', 'N/A'))
        insurer_name = str(policy_data.get('insuranceProvider', 'N/A'))
        policy_holder_name = policy_data.get('policyHolderName', 'Dear Policyholder')
        _name_parts = policy_holder_name.split() if policy_holder_name and policy_holder_name != 'N/A' else []
        _title_prefixes = {'mr', 'mrs', 'ms', 'miss', 'dr', 'shri', 'smt', 'sri'}
        if len(_name_parts) >= 2 and _name_parts[0].lower().rstrip('.') in _title_prefixes:
            first_name = _name_parts[1]
        elif _name_parts:
            first_name = _name_parts[0]
        else:
            first_name = 'there'
        sum_assured = safe_int(policy_data.get('sumAssured', 0) or policy_data.get('coverageAmount', 0))
        premium = safe_int(policy_data.get('premium', 0))
        premium_frequency = str(policy_data.get('premiumFrequency', 'annual')).lower()
        start_date = str(policy_data.get('startDate', 'N/A'))
        end_date = str(policy_data.get('endDate', 'N/A'))

        category_data = policy_data.get('categorySpecificData', {})
        if not isinstance(category_data, dict):
            category_data = {}
        policy_identification = category_data.get('policyIdentification', {})
        policyholder_life_assured = category_data.get('policyholderLifeAssured', {})
        coverage_details = category_data.get('coverageDetails', {})
        premium_details = category_data.get('premiumDetails', {})
        riders = category_data.get('riders', [])
        bonus_value = category_data.get('bonusValue', {})
        nomination = category_data.get('nomination', {})
        key_terms = category_data.get('keyTerms', {})

        plan_name = policy_identification.get('productName') or policy_identification.get('policyType', 'Life Insurance Plan')
        policy_type_display = str(policy_identification.get('policyType', 'Endowment')).title()
        policy_term_raw = coverage_details.get('policyTerm', 'N/A')
        premium_paying_term = coverage_details.get('premiumPayingTerm', 'N/A')
        maturity_date = coverage_details.get('maturityDate', end_date)

        life_assured_dob = policyholder_life_assured.get('lifeAssuredDob') or policyholder_life_assured.get('policyholderDob', 'N/A')
        life_assured_age = safe_int(policyholder_life_assured.get('lifeAssuredAge') or policyholder_life_assured.get('policyholderAge', 0))

        policy_term_years = 0
        if policy_term_raw and str(policy_term_raw) != 'N/A':
            try:
                term_str = str(policy_term_raw).lower().replace('years', '').replace('year', '').strip()
                policy_term_years = int(float(term_str))
            except (ValueError, TypeError):
                policy_term_years = 0

        maturity_age = 0
        if life_assured_age > 0 and policy_term_years > 0:
            maturity_age = life_assured_age + policy_term_years
        elif life_assured_dob and str(life_assured_dob) != 'N/A' and maturity_date and str(maturity_date) != 'N/A':
            try:
                dob_dt = datetime.strptime(str(life_assured_dob)[:10], '%Y-%m-%d')
                mat_dt = datetime.strptime(str(maturity_date)[:10], '%Y-%m-%d')
                maturity_age = (mat_dt - dob_dt).days // 365
            except Exception:
                pass

        policy_term = f"{policy_term_years} years" if policy_term_years > 0 else str(policy_term_raw)

        nominees = nomination.get('nominees', []) if isinstance(nomination, dict) else []
        nominee_name = nominees[0].get('nomineeName', 'Not specified') if nominees else 'Not specified'
        nominee_relationship = nominees[0].get('nomineeRelationship', '') if nominees else ''

        accrued_bonus = safe_int(bonus_value.get('accruedBonus', 0))
        surrender_value = safe_int(bonus_value.get('surrenderValue', 0))
        guaranteed_maturity = safe_int(bonus_value.get('guaranteedMaturity', 0))
        projected_maturity = safe_int(bonus_value.get('projectedMaturity', 0))
        policy_loan = safe_int(bonus_value.get('policyLoan', 0))

        annual_premium = premium
        freq_display = premium_frequency.title()
        if premium_frequency == 'monthly':
            annual_premium = premium * 12
        elif premium_frequency == 'quarterly':
            annual_premium = premium * 4
        elif premium_frequency == 'half-yearly':
            annual_premium = premium * 2

        rider_sum = 0
        adb_amount = 0
        ci_amount = 0
        rider_list = []
        for rider in riders:
            if isinstance(rider, dict):
                r_sum = safe_int(rider.get('riderSumAssured', 0))
                rider_sum += r_sum
                rider_list.append(rider)
                r_name = str(rider.get('riderName', '')).lower()
                if 'accident' in r_name or 'adb' in r_name or 'addb' in r_name:
                    adb_amount += r_sum
                if 'critical' in r_name or 'illness' in r_name or 'ci ' in r_name:
                    ci_amount += r_sum

        net_death_benefit = sum_assured + accrued_bonus
        total_death_with_riders = net_death_benefit + rider_sum

        policy_age_years = 0
        try:
            if start_date and start_date != 'N/A':
                start_dt = datetime.strptime(str(start_date)[:10], '%Y-%m-%d')
                policy_age_years = (datetime.now() - start_dt).days // 365
        except Exception:
            pass
        total_premiums_paid = annual_premium * policy_age_years

        surrender_percentage = 0
        if total_premiums_paid > 0 and surrender_value > 0:
            surrender_percentage = round((surrender_value / total_premiums_paid) * 100, 1)

        ppt_years = safe_int(str(premium_paying_term).replace(' years', '').replace(' year', '').replace('years', '').replace('year', ''))
        total_premium_payable = annual_premium * ppt_years if ppt_years > 0 else 0
        grace_period = key_terms.get('gracePeriod', '30 days') if isinstance(key_terms, dict) else '30 days'
        next_premium_due = premium_details.get('premiumDueDate', premium_details.get('nextPremiumDueDate', 'N/A')) if isinstance(premium_details, dict) else 'N/A'
        claims_helpline = get_claims_helpline(insurer_name)

        # ==================== EXTRACT V10 DATA ====================
        protection_readiness = analysis_data.get('protectionReadiness', {})
        if not isinstance(protection_readiness, dict):
            protection_readiness = {}
        v10_scores = protection_readiness.get('scores', {})
        render_mode = protection_readiness.get('renderMode', {})
        product_type = str(protection_readiness.get('productType', '')).lower()
        is_term = render_mode.get('mode') == 'PROTECTION_ONLY'
        is_savings = not is_term and bool(protection_readiness)
        composite_score = safe_int(protection_readiness.get('compositeScore', analysis_data.get('protectionScore', 0)))
        verdict = protection_readiness.get('verdict', {})
        verdict_label = verdict.get('label', analysis_data.get('protectionScoreLabel', 'Needs Review'))
        verdict_summary = verdict.get('summary', '')
        verdict_color_hex = verdict.get('color', '#6B7280')

        s1_data = v10_scores.get('s1', {})
        s2_data = v10_scores.get('s2')
        s3_data = v10_scores.get('s3')

        badge_label = render_mode.get('badgeLabel', policy_type_display)
        badge_color_hex = render_mode.get('badgeColor', '#3B82F6')

        v10_strengths = analysis_data.get('coverageStrengths', [])
        if not isinstance(v10_strengths, list):
            v10_strengths = []

        v10_gaps_data = analysis_data.get('coverageGaps', {})
        if isinstance(v10_gaps_data, dict):
            v10_gap_list = v10_gaps_data.get('gaps', [])
            v10_gap_summary = v10_gaps_data.get('summary', {})
        else:
            v10_gap_list = v10_gaps_data if isinstance(v10_gaps_data, list) else []
            v10_gap_summary = {}

        v10_recs = analysis_data.get('recommendations', {})
        if isinstance(v10_recs, dict):
            quick_wins = v10_recs.get('quickWins', [])
            priority_upgrades = v10_recs.get('priorityUpgrades', [])
            total_upgrade_cost = v10_recs.get('totalUpgradeCost', {})
        elif isinstance(v10_recs, list):
            quick_wins = []
            priority_upgrades = v10_recs
            total_upgrade_cost = {}
        else:
            quick_wins = []
            priority_upgrades = []
            total_upgrade_cost = {}

        v10_scenarios = analysis_data.get('scenarios', {})
        if isinstance(v10_scenarios, dict):
            primary_scenario_id = v10_scenarios.get('primaryScenarioId', 'L001')
            scenario_list = v10_scenarios.get('simulations', [])
        elif isinstance(v10_scenarios, list):
            primary_scenario_id = 'L001'
            scenario_list = v10_scenarios
        else:
            primary_scenario_id = 'L001'
            scenario_list = []

        svf_opportunity = analysis_data.get('svfOpportunity', None)

        # Generate report ID
        report_id = f"EAZ-LIF-{datetime.now().strftime('%Y-%m-%d')}-{abs(hash(policy_number)) % 0xFFFF:04X}"
        ModernFooter.report_id = report_id

        # ==================== PAGE 1: COVER + EXECUTIVE SUMMARY ====================
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph("LIFE INSURANCE ANALYSIS REPORT", ParagraphStyle(
            'CoverTitle', fontName=FONT_BOLD, fontSize=22, textColor=CHARCOAL,
            alignment=TA_CENTER, spaceAfter=4, leading=28
        )))
        elements.append(HRFlowable(width="30%", thickness=2, color=BRAND_PRIMARY, spaceAfter=12, hAlign='CENTER'))
        elements.append(Spacer(1, 0.1*inch))

        # Policy info + product badge
        cover_items = [
            ("Prepared for", safe_str(policy_holder_name)),
            ("Policy", safe_str(plan_name)),
            ("Policy Number", safe_str(policy_number)),
            ("Status", f"Active | Start: {start_date[:10] if start_date != 'N/A' else 'N/A'} | Maturity: {str(maturity_date)[:10] if str(maturity_date) != 'N/A' else 'N/A'}"),
        ]
        cover_card = create_info_card(cover_items)
        card_wrapper = Table([[cover_card]], colWidths=[6.2*inch])
        card_wrapper.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
        elements.append(card_wrapper)
        elements.append(Spacer(1, 0.08*inch))

        # Product type badge
        try:
            b_color = colors.HexColor(badge_color_hex)
        except Exception:
            b_color = BADGE_COLORS.get(product_type, INFO_BLUE)
        badge_para = Paragraph(f"<font color='#FFFFFF'><b>{badge_label}</b></font>",
                              ParagraphStyle('Badge', fontName=FONT_BOLD, fontSize=9, alignment=TA_CENTER))
        badge_tbl = Table([[badge_para]], colWidths=[1.6*inch])
        badge_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), b_color),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        badge_wrapper = Table([[badge_tbl]], colWidths=[6.2*inch])
        badge_wrapper.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
        elements.append(badge_wrapper)
        elements.append(Spacer(1, 0.15*inch))

        # Composite score visual
        elements.append(Paragraph("<b>POLICY READINESS SCORE</b>", ParagraphStyle(
            'ScoreHeading', fontName=FONT_BOLD, fontSize=10, textColor=SLATE, alignment=TA_CENTER, spaceAfter=6)))
        try:
            v_color = colors.HexColor(verdict_color_hex)
        except Exception:
            v_color = _get_v10_score_color(composite_score)
        score_visual = create_score_visual(composite_score, verdict_label, v_color)
        score_wrapper = Table([[score_visual]], colWidths=[6.2*inch])
        score_wrapper.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
        elements.append(score_wrapper)
        elements.append(Spacer(1, 0.06*inch))

        if verdict_summary:
            elements.append(Paragraph(f"<i>{verdict_summary}</i>", ParagraphStyle(
                'VerdictSummary', fontName=FONT_ITALIC, fontSize=9, textColor=SLATE, alignment=TA_CENTER, spaceAfter=8)))

        # Score tiles
        if is_savings and s2_data and s3_data:
            s1_tile = _create_score_tile(s1_data, f"Weight: {s1_data.get('weight', '45%')}")
            s2_tile = _create_score_tile(s2_data, f"Weight: {s2_data.get('weight', '30%')}")
            s3_tile = _create_score_tile(s3_data, f"Weight: {s3_data.get('weight', '25%')}")
            if s1_tile and s2_tile and s3_tile:
                tiles_row = Table([[s1_tile, s2_tile, s3_tile]], colWidths=[2.07*inch, 2.07*inch, 2.07*inch])
                tiles_row.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                elements.append(tiles_row)
        elif s1_data:
            s1_tile = _create_score_tile(s1_data, f"Weight: {s1_data.get('weight', '100%')}")
            if s1_tile:
                tile_wrapper = Table([[s1_tile]], colWidths=[6.2*inch])
                tile_wrapper.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
                elements.append(tile_wrapper)

        elements.append(Spacer(1, 0.12*inch))

        # At A Glance table
        elements.append(create_subsection_header("At A Glance"))
        glance_data = [["Metric", "Value"]]
        glance_data.append(["Death Benefit", format_currency(max(0, total_death_with_riders - policy_loan)) + " (SA + Bonuses)"])

        gap_high = safe_int(v10_gap_summary.get('high', 0))
        gap_med = safe_int(v10_gap_summary.get('medium', 0))
        gap_opp = safe_int(v10_gap_summary.get('opportunity', 0))
        gap_low = safe_int(v10_gap_summary.get('low', 0))
        gap_summary_str = ""
        parts = []
        if gap_high:
            parts.append(f"{gap_high} High")
        if gap_med:
            parts.append(f"{gap_med} Medium")
        if gap_low:
            parts.append(f"{gap_low} Low")
        if gap_opp:
            parts.append(f"{gap_opp} Opportunity")
        gap_summary_str = " | ".join(parts) if parts else "None identified"
        glance_data.append(["Gaps Found", gap_summary_str])

        # Family gap from L001 scenario
        family_gap = 0
        for sc in scenario_list:
            if isinstance(sc, dict) and sc.get('scenarioId') == 'L001':
                # V10 format: gap is a dict with 'amount' key
                _l001_gap = sc.get('gap', {})
                if isinstance(_l001_gap, dict):
                    family_gap = safe_int(_l001_gap.get('amount', 0))
                else:
                    family_gap = safe_int(_l001_gap)
                # Fallback to financialImpact (legacy)
                if family_gap <= 0:
                    fi = sc.get('financialImpact', {})
                    if isinstance(fi, dict):
                        family_gap = safe_int(fi.get('totalShortfall', 0)) or safe_int(fi.get('gap', 0))
                break
        if family_gap > 0:
            glance_data.append(["Family Gap", f"{format_currency(family_gap)} shortfall (if death today)"])

        if is_savings:
            glance_data.append(["Surrender Value", format_currency(surrender_value) if surrender_value > 0 else "Not yet available"])
            if svf_opportunity and svf_opportunity.get('eligible'):
                svf_max = svf_opportunity.get('maxSvfFormatted', format_currency(int(surrender_value * 0.9)))
                glance_data.append(["SVF Available", f"Up to {svf_max} via EAZR"])
        else:
            glance_data.append(["Annual Premium", format_currency(annual_premium)])
            years_remaining = policy_term_years - policy_age_years if policy_term_years > 0 else 0
            if years_remaining > 0:
                glance_data.append(["Years Remaining", f"{years_remaining} years"])

        glance_table = create_modern_table(glance_data, [2.5*inch, 3.7*inch], CHARCOAL)
        elements.append(glance_table)
        elements.append(Spacer(1, 0.1*inch))

        elements.append(Paragraph(
            f"<b>Report ID:</b> {report_id} | <b>Generated:</b> {datetime.now().strftime('%d %B %Y')}",
            styles['muted_text']))
        elements.append(PageBreak())

        # ==================== PAGE 2: SCORE DEEP-DIVE ====================
        elements.append(create_section_header("Score Deep-Dive", styles))
        elements.append(Spacer(1, 0.1*inch))

        # S1 Factor Table (always shown)
        if s1_data and s1_data.get('factors'):
            s1_elems = _create_factor_table(
                s1_data['factors'],
                f"SCORE 1: {s1_data.get('name', 'Family Financial Security').upper()}",
                safe_int(s1_data.get('score', 0)),
                s1_data.get('label', ''),
                s1_data.get('color', '#6B7280')
            )
            elements.append(KeepTogether(s1_elems))
            elements.append(Spacer(1, 0.08*inch))

            # What This Means for S1
            s1_score = safe_int(s1_data.get('score', 0))
            if s1_score >= 75:
                s1_meaning = f"Your family receives {format_currency(max(0, total_death_with_riders - policy_loan))} if something happens today — a strong financial safety net."
            elif s1_score >= 60:
                s1_meaning = f"Your family receives {format_currency(max(0, total_death_with_riders - policy_loan))} — adequate for immediate needs but may fall short for long-term income replacement."
            else:
                s1_meaning = f"Your family receives {format_currency(max(0, total_death_with_riders - policy_loan))} — this is likely insufficient for their long-term financial needs. Additional term cover is recommended."
            elements.append(create_highlight_box(
                f"<b>What This Means:</b> {s1_meaning}",
                BRAND_LIGHTER, BRAND_PRIMARY
            ))
            elements.append(Spacer(1, 0.15*inch))

        # S2 Factor Table (savings only)
        if is_savings and s2_data and s2_data.get('factors'):
            s2_elems = _create_factor_table(
                s2_data['factors'],
                f"SCORE 2: {s2_data.get('name', 'Policy Value Score').upper()}",
                safe_int(s2_data.get('score', 0)),
                s2_data.get('label', ''),
                s2_data.get('color', '#6B7280')
            )
            elements.append(KeepTogether(s2_elems))
            elements.append(Spacer(1, 0.08*inch))

            s2_score = safe_int(s2_data.get('score', 0))
            if surrender_percentage > 0:
                sv_text = f"Surrender value has recovered to {surrender_percentage}% of premiums paid."
            else:
                sv_text = "Surrender value data not yet available."
            if s2_score >= 70:
                s2_meaning = f"Your policy is past the early-year penalty zone. {sv_text} Continuing to maturity is significantly more valuable than surrendering now."
            else:
                s2_meaning = f"{sv_text} The policy value is still building — surrendering now would result in a significant loss."
            elements.append(create_highlight_box(
                f"<b>What This Means:</b> {s2_meaning}",
                BRAND_LIGHTER, BRAND_PRIMARY
            ))
            elements.append(Spacer(1, 0.15*inch))

        # S3 Factor Table (savings only)
        if is_savings and s3_data and s3_data.get('factors'):
            s3_elems = _create_factor_table(
                s3_data['factors'],
                f"SCORE 3: {s3_data.get('name', 'SVF Eligibility Score').upper()}",
                safe_int(s3_data.get('score', 0)),
                s3_data.get('label', ''),
                s3_data.get('color', '#6B7280')
            )
            elements.append(KeepTogether(s3_elems))
            elements.append(Spacer(1, 0.08*inch))

            svf_max_amt = int(surrender_value * 0.9) if surrender_value > 0 else 0
            s3_score = safe_int(s3_data.get('score', 0))
            if s3_score >= 70 and svf_max_amt > 0:
                s3_meaning = f"Your policy is well-qualified for EAZR Surrender Value Financing. You can access up to {format_currency(svf_max_amt)} (90% of SV) without surrendering. Your life protection, bonuses, and maturity benefit remain intact."
            elif svf_max_amt > 0:
                s3_meaning = f"You may be eligible for up to {format_currency(svf_max_amt)} via EAZR SVF. This is significantly better than surrendering as your policy benefits remain intact."
            else:
                s3_meaning = "SVF eligibility requires a surrender value. As your policy builds value over time, this option will become available."
            elements.append(create_highlight_box(
                f"<b>What This Means for Accessing Funds:</b> {s3_meaning}",
                SVF_BG, SVF_ACCENT
            ))

        elements.append(PageBreak())

        # ==================== PAGE 3: STRENGTHS & GAPS ====================
        elements.append(create_section_header("What's Working & Where You're Exposed", styles))
        elements.append(Spacer(1, 0.1*inch))

        # Strengths table
        elements.append(create_subsection_header("Coverage Strengths"))
        if v10_strengths:
            str_data = [["Strength", "Why It Matters"]]
            for st in v10_strengths[:8]:
                if isinstance(st, dict):
                    str_data.append([safe_str(st.get('title', '')), safe_str(st.get('reason', st.get('description', '')))])
                elif isinstance(st, str):
                    str_data.append([st, ""])
            str_table = create_modern_table(str_data, [3.0*inch, 3.2*inch], SUCCESS_GREEN)
            elements.append(str_table)
        else:
            elements.append(Paragraph("No specific strengths identified based on available data.", styles['body_text']))
        elements.append(Spacer(1, 0.15*inch))

        # Complete gap table
        elements.append(create_subsection_header("Coverage Gaps"))
        if v10_gap_list:
            gap_table_data = [["#", "Gap", "Severity", "Est. Cost"]]
            for idx, gap in enumerate(v10_gap_list, 1):
                if isinstance(gap, dict):
                    gap_id = gap.get('gapId', f'G{idx:03d}')
                    title = safe_str(gap.get('title', gap.get('category', gap.get('description', 'Coverage Gap'))))
                    severity = str(gap.get('severity', 'medium')).upper()
                    est_cost = safe_int(gap.get('estimatedCost', 0))
                    cost_str = format_currency(est_cost) + "/yr" if est_cost > 0 else "—"
                    gap_table_data.append([gap_id, title, severity, cost_str])
                elif isinstance(gap, str) and gap.strip():
                    gap_table_data.append([f"G{idx:03d}", gap, "MEDIUM", "—"])

            if len(gap_table_data) > 1:
                gap_tbl = Table(gap_table_data, colWidths=[0.6*inch, 2.8*inch, 1.0*inch, 1.8*inch])
                g_style = [
                    ('BACKGROUND', (0, 0), (-1, 0), CHARCOAL),
                    ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
                    ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
                    ('FONTNAME', (0, 1), (-1, -1), FONT_REGULAR),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('TEXTCOLOR', (0, 1), (-1, -1), SLATE),
                    ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                    ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                    ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
                    ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
                ]
                # Color severity cells
                for i in range(1, len(gap_table_data)):
                    sev_val = gap_table_data[i][2]
                    if sev_val == 'HIGH':
                        g_style.append(('TEXTCOLOR', (2, i), (2, i), GAP_HIGH))
                    elif sev_val == 'MEDIUM':
                        g_style.append(('TEXTCOLOR', (2, i), (2, i), GAP_MEDIUM))
                    elif sev_val == 'OPPORTUNITY':
                        g_style.append(('TEXTCOLOR', (2, i), (2, i), GAP_OPPORTUNITY))
                    else:
                        g_style.append(('TEXTCOLOR', (2, i), (2, i), GAP_LOW))
                    if i % 2 == 0:
                        g_style.append(('BACKGROUND', (0, i), (-1, i), WHISPER))

                gap_tbl.setStyle(TableStyle(g_style))
                elements.append(gap_tbl)
                elements.append(Spacer(1, 0.08*inch))

                # Gap severity summary box
                summary_parts = []
                if gap_high:
                    summary_parts.append(f"<b><font color='#{GAP_HIGH.hexval()[2:]}'>High: {gap_high}</font></b>")
                if gap_med:
                    summary_parts.append(f"<b><font color='#{GAP_MEDIUM.hexval()[2:]}'>Medium: {gap_med}</font></b>")
                if gap_low:
                    summary_parts.append(f"<b>Low: {gap_low}</b>")
                if gap_opp:
                    summary_parts.append(f"<b><font color='#{GAP_OPPORTUNITY.hexval()[2:]}'>Opportunity: {gap_opp}</font></b>")

                total_fix = safe_int(total_upgrade_cost.get('annual', 0))
                monthly_emi = safe_int(total_upgrade_cost.get('monthlyEmi', 0))
                cost_line = ""
                if total_fix > 0:
                    cost_line = f"<br/>Total Fix Cost: {format_currency(total_fix)}/year"
                    if monthly_emi > 0:
                        cost_line += f" | EAZR EMI: {format_currency(monthly_emi)}/month"

                if summary_parts:
                    elements.append(create_highlight_box(
                        f"<b>Gap Summary:</b> {' | '.join(summary_parts)}{cost_line}",
                        INFO_LIGHT, INFO_BLUE
                    ))
        else:
            elements.append(create_highlight_box(
                "<b>No significant coverage gaps identified.</b> Your policy appears to provide adequate protection.",
                SUCCESS_LIGHT, SUCCESS_GREEN
            ))

        elements.append(PageBreak())

        # ==================== PAGE 4: SCENARIOS ====================
        elements.append(create_section_header("Life Decisions — Impact Analysis", styles))
        elements.append(Spacer(1, 0.1*inch))

        scenarios_by_id = {}
        for sc in scenario_list:
            if isinstance(sc, dict):
                scenarios_by_id[sc.get('scenarioId', '')] = sc

        # L001: Premature Death Impact (all policies)
        l001 = scenarios_by_id.get('L001', {})
        if l001:
            l001_section = []
            l001_section.append(create_subsection_header("Scenario L001: Premature Death — Family Financial Impact"))
            l001_desc = l001.get('description', 'What happens to your family if you pass away today')
            l001_section.append(Paragraph(f"<i>{l001_desc}</i>", styles['muted_text']))
            l001_section.append(Spacer(1, 0.05*inch))

            # V10 format: familyReceives, familyNeeds, gap directly on scenario
            _l001_receives = l001.get('familyReceives', {})
            _l001_needs = l001.get('familyNeeds', {})
            _l001_gap = l001.get('gap', {})
            _l001_has_v10 = isinstance(_l001_receives, dict) and _l001_receives.get('items')

            if _l001_has_v10:
                # Family Receives table
                recv_items = _l001_receives.get('items', [])
                if recv_items:
                    recv_data = [["Your Family Receives", "Amount"]]
                    for item in recv_items:
                        if isinstance(item, dict):
                            recv_data.append([item.get('label', ''), item.get('formatted', format_currency(safe_int(item.get('amount', 0))))])
                    total_payout = _l001_receives.get('totalFormatted', format_currency(safe_int(_l001_receives.get('totalPayout', 0))))
                    recv_data.append(["TOTAL PAYOUT", total_payout])
                    if len(recv_data) > 2:
                        l001_section.append(create_modern_table(recv_data, [3.5*inch, 2.7*inch], SUCCESS_GREEN))
                        l001_section.append(Spacer(1, 0.08*inch))

                # Family Needs table
                needs_items = _l001_needs.get('items', []) if isinstance(_l001_needs, dict) else []
                if needs_items:
                    needs_data = [["Your Family Actually Needs", "Amount"]]
                    for item in needs_items:
                        if isinstance(item, dict):
                            needs_data.append([item.get('label', ''), item.get('formatted', format_currency(safe_int(item.get('amount', 0))))])
                    total_need = _l001_needs.get('totalFormatted', format_currency(safe_int(_l001_needs.get('totalNeed', 0))))
                    needs_data.append(["TOTAL FAMILY NEED", total_need])
                    if len(needs_data) > 2:
                        l001_section.append(create_modern_table(needs_data, [3.5*inch, 2.7*inch], DANGER_RED))
                        l001_section.append(Spacer(1, 0.08*inch))

                # Gap callout
                gap_amount = safe_int(_l001_gap.get('amount', 0)) if isinstance(_l001_gap, dict) else safe_int(_l001_gap)
                has_gap = _l001_gap.get('hasGap', gap_amount > 0) if isinstance(_l001_gap, dict) else gap_amount > 0
                gap_desc = _l001_gap.get('description', '') if isinstance(_l001_gap, dict) else ''
                if has_gap and gap_amount > 0:
                    l001_section.append(create_highlight_box(
                        f"<b>FAMILY FINANCIAL GAP: {format_currency(gap_amount)}</b><br/>{gap_desc or 'Your family faces a shortfall that needs to be addressed through additional life cover.'}",
                        DANGER_LIGHT, DANGER_RED
                    ))
                else:
                    l001_section.append(create_highlight_box(
                        "<b>Coverage appears adequate</b> based on available data. Review annually or when circumstances change.",
                        SUCCESS_LIGHT, SUCCESS_GREEN
                    ))

                # Recommendation
                _l001_rec = l001.get('recommendation', {})
                if isinstance(_l001_rec, dict) and _l001_rec.get('action'):
                    l001_section.append(Spacer(1, 0.04*inch))
                    l001_section.append(Paragraph(
                        f"<i>{safe_str(_l001_rec['action'])}</i>",
                        styles['insight_text']
                    ))

            else:
                # Legacy financialImpact format
                fi = l001.get('financialImpact', {})
                if isinstance(fi, dict) and fi:
                    needs = fi.get('familyNeeds', fi.get('needs', {}))
                    if isinstance(needs, dict):
                        needs_data = [["Category", "Amount"]]
                        for k, v in needs.items():
                            if k not in ('total', 'totalNeeded'):
                                label = k.replace('_', ' ').replace('camelCase', '').title()
                                needs_data.append([label, format_currency(safe_int(v))])
                        total_need = safe_int(needs.get('total', needs.get('totalNeeded', fi.get('totalNeed', 0))))
                        if total_need > 0:
                            needs_data.append(["TOTAL FAMILY NEED", format_currency(total_need)])
                        if len(needs_data) > 1:
                            l001_section.append(create_modern_table(needs_data, [3.5*inch, 2.7*inch], BRAND_PRIMARY))
                            l001_section.append(Spacer(1, 0.08*inch))

                    shortfall = safe_int(fi.get('totalShortfall', fi.get('gap', family_gap)))
                    if shortfall > 0:
                        l001_section.append(create_highlight_box(
                            f"<b>FAMILY FINANCIAL GAP: {format_currency(shortfall)}</b><br/>Your family faces a shortfall that needs to be addressed through additional life cover.",
                            DANGER_LIGHT, DANGER_RED
                        ))
                    else:
                        l001_section.append(create_highlight_box(
                            "<b>Coverage appears adequate</b> based on available data. Review annually or when circumstances change.",
                            SUCCESS_LIGHT, SUCCESS_GREEN
                        ))
                elif family_gap > 0:
                    l001_section.append(create_highlight_box(
                        f"<b>FAMILY FINANCIAL GAP: {format_currency(family_gap)}</b><br/>Your family faces a shortfall that needs to be addressed through additional life cover.",
                        DANGER_LIGHT, DANGER_RED
                    ))
                else:
                    l001_section.append(create_highlight_box(
                        "<b>Coverage appears adequate</b> based on available data. Review annually or when circumstances change.",
                        SUCCESS_LIGHT, SUCCESS_GREEN
                    ))

            elements.append(KeepTogether(l001_section))
            elements.append(Spacer(1, 0.15*inch))

        # L002: Surrender Analysis (savings only)
        l002 = scenarios_by_id.get('L002', {})
        if is_savings and l002:
            l002_section = []
            l002_section.append(create_subsection_header("Scenario L002: Surrender Now — Complete Impact"))
            l002_section.append(Spacer(1, 0.05*inch))

            # V10 format: whatYouGet, whatYouLose directly on scenario
            _l002_get = l002.get('whatYouGet', {})
            _l002_lose = l002.get('whatYouLose', {})
            _l002_has_v10 = isinstance(_l002_get, dict) and 'items' in _l002_get

            if _l002_has_v10:
                get_val = safe_int(_l002_get.get('netAmount', surrender_value))
                lose_items = _l002_lose.get('items', []) if isinstance(_l002_lose, dict) else []
                lose_protection = sum_assured
                lose_bonuses = accrued_bonus
                lose_maturity = projected_maturity
                for item in lose_items:
                    if isinstance(item, dict):
                        lbl = (item.get('label', '') or '').lower()
                        amt = safe_int(item.get('amount', 0))
                        if 'protection' in lbl:
                            lose_protection = amt
                        elif 'bonus' in lbl and 'future' not in lbl:
                            lose_bonuses = amt
                        elif 'maturity' in lbl:
                            lose_maturity = amt
                total_lost = safe_int(_l002_lose.get('totalValueForegone', lose_protection + lose_bonuses + lose_maturity)) if isinstance(_l002_lose, dict) else (lose_protection + lose_bonuses + lose_maturity)
            else:
                fi = l002.get('financialImpact', {})
                get_val = safe_int(fi.get('surrenderValue', surrender_value)) if isinstance(fi, dict) else surrender_value
                lose_protection = safe_int(fi.get('lostProtection', sum_assured)) if isinstance(fi, dict) else sum_assured
                lose_bonuses = safe_int(fi.get('lostBonuses', accrued_bonus)) if isinstance(fi, dict) else accrued_bonus
                lose_maturity = safe_int(fi.get('lostMaturity', projected_maturity)) if isinstance(fi, dict) else projected_maturity
                total_lost = safe_int(fi.get('totalLost', lose_protection + lose_bonuses + lose_maturity)) if isinstance(fi, dict) else (lose_protection + lose_bonuses + lose_maturity)

            if True:

                surr_data = [
                    ["What You Get", "What You Lose"],
                    [f"Surrender Value: {format_currency(get_val)}", f"Life Protection: {format_currency(lose_protection)}"],
                    ["", f"Accrued Bonuses: {format_currency(lose_bonuses)}"],
                    ["", f"Maturity Benefit: {format_currency(lose_maturity)}"],
                    [f"NET: {format_currency(get_val)}", f"TOTAL LOST: {format_currency(total_lost)}"],
                ]
                surr_tbl = Table(surr_data, colWidths=[3.1*inch, 3.1*inch])
                surr_tbl.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), CHARCOAL),
                    ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
                    ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
                    ('FONTNAME', (0, 1), (-1, -1), FONT_REGULAR),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('TEXTCOLOR', (0, 1), (0, -1), SUCCESS_GREEN),
                    ('TEXTCOLOR', (1, 1), (1, -1), DANGER_RED),
                    ('FONTNAME', (0, -1), (-1, -1), FONT_BOLD),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
                    ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
                    ('LINEBETWEEN', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
                ]))
                l002_section.append(surr_tbl)
                l002_section.append(Spacer(1, 0.06*inch))

                # SVF alternative callout
                svf_max = int(surrender_value * 0.9) if surrender_value > 0 else 0
                if svf_max > 0:
                    l002_section.append(create_highlight_box(
                        f"<b>ALTERNATIVE: EAZR SVF</b><br/>Access up to {format_currency(svf_max)} — AND keep your {format_currency(sum_assured)} life protection, "
                        f"{format_currency(projected_maturity)} maturity benefit, and tax benefits intact.",
                        SVF_BG, SVF_ACCENT
                    ))

            elements.append(KeepTogether(l002_section))
            elements.append(Spacer(1, 0.15*inch))

        # L003: Loan Comparison (savings only)
        l003 = scenarios_by_id.get('L003', {})
        if is_savings and l003:
            l003_section = []
            l003_section.append(create_subsection_header("Scenario L003: Loan Options Comparison"))
            l003_section.append(Spacer(1, 0.05*inch))

            fi = l003.get('financialImpact', {})
            loan_max = int(surrender_value * 0.9) if surrender_value > 0 else 0

            loan_data = [
                ["Parameter", "Policy Loan", "Personal Loan", "EAZR SVF"],
                ["Interest Rate", "9-12% p.a.", "12-18% p.a.", "10-14%"],
                ["Max Amount", format_currency(loan_max), "Income-based", format_currency(loan_max)],
                ["Impact on Policy", "Reduces DB", "None", "Assigned"],
                ["Death Benefit Safe", "Reduced", "No impact", "Intact"],
                ["Credit Score Impact", "None", "Yes", "None"],
                ["Processing", "3-7 days", "1-7 days", "24-72 hrs"],
                ["Repayment", "Flexible", "Fixed EMI", "Flexible"],
            ]

            loan_tbl = Table(loan_data, colWidths=[1.5*inch, 1.5*inch, 1.6*inch, 1.6*inch])
            loan_style = [
                ('BACKGROUND', (0, 0), (-1, 0), CHARCOAL),
                ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
                ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
                ('FONTNAME', (0, 1), (-1, -1), FONT_REGULAR),
                ('FONTSIZE', (0, 0), (-1, -1), 7.5),
                ('TEXTCOLOR', (0, 1), (0, -1), MEDIUM_GRAY),
                ('TEXTCOLOR', (1, 1), (-1, -1), SLATE),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
                ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
                ('LINEBETWEEN', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
                # Highlight SVF column
                ('BACKGROUND', (3, 1), (3, -1), SVF_BG),
            ]
            for i in range(1, len(loan_data)):
                if i % 2 == 0:
                    loan_style.append(('BACKGROUND', (0, i), (2, i), WHISPER))
            loan_tbl.setStyle(TableStyle(loan_style))
            l003_section.append(loan_tbl)
            l003_section.append(Spacer(1, 0.06*inch))
            l003_section.append(create_highlight_box(
                "<b>VERDICT:</b> EAZR SVF offers the best balance — competitive rates, fast processing, no credit score impact, and full death benefit protection.",
                SVF_BG, SVF_ACCENT
            ))
            elements.append(KeepTogether(l003_section))
            elements.append(Spacer(1, 0.15*inch))

        # L004: Continue vs Paid-Up (savings only)
        l004 = scenarios_by_id.get('L004', {})
        if is_savings and l004:
            l004_section = []
            l004_section.append(create_subsection_header("Scenario L004: Continue Premiums vs Paid-Up"))
            l004_section.append(Spacer(1, 0.05*inch))

            # V10 format: continueScenario, paidUpScenario, verdict directly on scenario
            _l004_cont = l004.get('continueScenario', {})
            _l004_paid = l004.get('paidUpScenario', {})
            _l004_has_v10 = isinstance(_l004_cont, dict) and 'remainingAmount' in _l004_cont

            if _l004_has_v10:
                future_premiums = safe_int(_l004_cont.get('remainingAmount', _l004_cont.get('totalInvestment', 0)))
                cont_sa = safe_int(_l004_cont.get('deathBenefit', sum_assured))
                cont_maturity = _l004_cont.get('maturityFormatted', format_currency(safe_int(_l004_cont.get('projectedMaturity', projected_maturity))))
                paid_sa = safe_int(_l004_paid.get('paidUpSA', int(sum_assured * 0.6)))
                paid_maturity = _l004_paid.get('paidUpMaturityFormatted', format_currency(safe_int(_l004_paid.get('paidUpMaturity', 0))))
            else:
                fi = l004.get('financialImpact', {})
                if isinstance(fi, dict):
                    future_premiums = safe_int(fi.get('futurePremiums', total_premium_payable - total_premiums_paid))
                    paid_sa = safe_int(fi.get('reducedSA', int(sum_assured * 0.6)))
                else:
                    remaining_years = max(ppt_years - policy_age_years, 0)
                    future_premiums = annual_premium * remaining_years
                    paid_sa = int(sum_assured * 0.6)
                cont_sa = sum_assured
                cont_maturity = format_currency(projected_maturity) if projected_maturity > 0 else "As per terms"
                paid_maturity = format_currency(int(projected_maturity * 0.6)) if projected_maturity > 0 else "Reduced"

            cont_data = [
                ["", "CONTINUE", "PAID-UP"],
                ["Future Premiums", format_currency(future_premiums), "N/A"],
                ["Sum Assured", format_currency(cont_sa), format_currency(paid_sa) + " (reduced)" if paid_sa > 0 else "N/A"],
                ["Projected Maturity", cont_maturity if isinstance(cont_maturity, str) else format_currency(cont_maturity), paid_maturity if isinstance(paid_maturity, str) else format_currency(paid_maturity)],
                ["Bonuses Continue", "Full rate", "Reduced rate"],
                ["Tax Benefits", "Continue", "Stop"],
            ]
            cont_tbl = Table(cont_data, colWidths=[2.0*inch, 2.1*inch, 2.1*inch])
            cont_style = [
                ('BACKGROUND', (0, 0), (-1, 0), CHARCOAL),
                ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
                ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
                ('FONTNAME', (0, 1), (-1, -1), FONT_REGULAR),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('TEXTCOLOR', (0, 1), (0, -1), MEDIUM_GRAY),
                ('TEXTCOLOR', (1, 1), (-1, -1), SLATE),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
                ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
                ('LINEBETWEEN', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
                ('BACKGROUND', (1, 1), (1, -1), SUCCESS_LIGHT),
            ]
            cont_tbl.setStyle(TableStyle(cont_style))
            l004_section.append(cont_tbl)
            l004_section.append(Spacer(1, 0.06*inch))

            # Use API verdict if available, otherwise compute locally
            _l004_verdict = l004.get('verdict', {})
            if isinstance(_l004_verdict, dict) and _l004_verdict.get('recommendation'):
                verdict_rec = safe_str(_l004_verdict.get('recommendation', ''))
                verdict_reason = safe_str(_l004_verdict.get('reason', ''))
                verdict_text = f"<b>VERDICT: {verdict_rec}</b>"
                if verdict_reason:
                    verdict_text += f"<br/>{verdict_reason}"
                # Add IPF suggestion if present
                _ipf_sug = _l004_verdict.get('ipfSuggestion', {})
                if isinstance(_ipf_sug, dict) and _ipf_sug.get('applicable'):
                    ipf_desc = safe_str(_ipf_sug.get('description', ''))
                    if ipf_desc:
                        verdict_text += f"<br/><i>{ipf_desc}</i>"
            else:
                verdict_text = "<b>VERDICT:</b> Continuing is generally recommended to maximize your maturity benefit and maintain full death benefit cover."
            l004_section.append(create_highlight_box(verdict_text, INFO_LIGHT, INFO_BLUE))
            elements.append(KeepTogether(l004_section))

        elements.append(PageBreak())

        # ==================== PAGE 5: RECOMMENDATIONS + SVF ====================
        elements.append(create_section_header("Your Personalized Action Plan", styles))
        elements.append(Spacer(1, 0.1*inch))

        # Quick Wins
        if quick_wins:
            elements.append(create_subsection_header("Quick Wins (No Cost)"))
            for qw in quick_wins[:4]:
                if isinstance(qw, dict):
                    qw_title = qw.get('title', qw.get('suggestion', ''))
                    qw_detail = qw.get('description', qw.get('action', ''))
                    qw_text = f"<b>{qw_title}</b>"
                    if qw_detail:
                        qw_text += f" — {qw_detail}"
                    elements.append(Paragraph(f"  {qw_text}", styles['bullet_point']))
                elif isinstance(qw, str):
                    elements.append(Paragraph(f"  {qw}", styles['bullet_point']))
            elements.append(Spacer(1, 0.1*inch))

        # Priority Upgrades
        if priority_upgrades:
            elements.append(create_subsection_header("Priority Actions"))
            for idx, pu in enumerate(priority_upgrades[:4], 1):
                if isinstance(pu, dict):
                    pu_title = safe_str(pu.get('title', pu.get('suggestion', pu.get('recommendation', ''))))
                    pu_severity = str(pu.get('priority', pu.get('severity', ''))).upper()
                    pu_fixes = pu.get('fixes', pu.get('gapId', ''))
                    pu_impact = safe_str(pu.get('impact', pu.get('description', '')))
                    pu_cost = safe_int(pu.get('estimatedCost', pu.get('annualCost', 0)))
                    pu_emi = safe_int(pu.get('eazrEmi', pu.get('monthlyEmi', 0)))
                    pu_when = pu.get('when', pu.get('timeline', ''))

                    pu_content = f"<b>#{idx}  {pu_title}</b>"
                    if pu_severity:
                        pu_content += f"  [{pu_severity}]"
                    pu_lines = []
                    if pu_fixes:
                        pu_lines.append(f"Fixes: {pu_fixes}")
                    if pu_impact:
                        pu_lines.append(f"Impact: {pu_impact}")
                    if pu_cost > 0:
                        cost_text = f"Cost: ~{format_currency(pu_cost)}/yr"
                        if pu_emi > 0:
                            cost_text += f" | EAZR IPF: {format_currency(pu_emi)}/mo"
                        pu_lines.append(cost_text)
                    if pu_when:
                        pu_lines.append(f"When: {pu_when}")

                    if pu_lines:
                        pu_content += "<br/>" + "<br/>".join(pu_lines)

                    elements.append(KeepTogether([create_highlight_box(pu_content, WHISPER, BRAND_PRIMARY)]))
                    elements.append(Spacer(1, 0.06*inch))
                elif isinstance(pu, str):
                    elements.append(Paragraph(f"<b>#{idx}</b>  {pu}", styles['numbered_item']))
            elements.append(Spacer(1, 0.1*inch))

        # Investment summary table
        total_annual = safe_int(total_upgrade_cost.get('annual', 0))
        total_monthly = safe_int(total_upgrade_cost.get('monthlyEmi', 0))
        if total_annual > 0 or priority_upgrades:
            elements.append(create_subsection_header("Investment Summary"))
            _inv_cell = ParagraphStyle('InvCell', fontName=FONT_REGULAR, fontSize=8, textColor=SLATE, leading=10)
            inv_data = [["Action", "Annual Cost", "EAZR EMI/mo"]]
            for pu in priority_upgrades[:4]:
                if isinstance(pu, dict):
                    pu_title = safe_str(pu.get('title', pu.get('suggestion', '')))
                    pu_cost = safe_int(pu.get('estimatedCost', pu.get('annualCost', 0)))
                    pu_emi = safe_int(pu.get('eazrEmi', pu.get('monthlyEmi', 0)))
                    if pu_cost > 0:
                        inv_data.append([Paragraph(pu_title, _inv_cell), format_currency(pu_cost), format_currency(pu_emi) if pu_emi > 0 else "—"])
            if total_annual > 0:
                inv_data.append(["TOTAL", format_currency(total_annual), format_currency(total_monthly) + "/mo" if total_monthly > 0 else "—"])
            if len(inv_data) > 1:
                inv_tbl = create_modern_table(inv_data, [3.0*inch, 1.6*inch, 1.6*inch], BRAND_DARK)
                elements.append(inv_tbl)
                elements.append(Spacer(1, 0.06*inch))
                if total_monthly > 0:
                    elements.append(Paragraph(
                        f"For {format_currency(total_monthly)}/month, you can significantly strengthen your family's financial protection.",
                        styles['insight_text']
                    ))
            elements.append(Spacer(1, 0.12*inch))

        # SVF Section (savings only)
        if is_savings and svf_opportunity and svf_opportunity.get('eligible'):
            elements.append(create_subsection_header("EAZR Surrender Value Financing (SVF)"))
            svf_sv = svf_opportunity.get('surrenderValueFormatted', format_currency(surrender_value))
            svf_max = svf_opportunity.get('maxSvfFormatted', format_currency(int(surrender_value * 0.9)))

            svf_info_data = [
                ["SVF Detail", "Value"],
                ["Surrender Value", svf_sv],
                ["Max SVF Amount", svf_max],
                ["Your Life Cover", "Remains intact"],
                ["Maturity Benefit", "Remains intact"],
                ["Bonuses", "Continue accruing"],
                ["Processing", "24-72 hours"],
            ]
            svf_tbl = create_modern_table(svf_info_data, [3.0*inch, 3.2*inch], SVF_ACCENT)
            elements.append(svf_tbl)
            elements.append(Spacer(1, 0.06*inch))

            # SVF vs Surrender comparison
            comparison = svf_opportunity.get('comparison', [])
            if comparison:
                comp_data = [["Feature", "Surrender", "EAZR SVF"]]
                for c in comparison:
                    if isinstance(c, dict):
                        feature = c.get('feature', '')
                        surr_val = "Yes" if c.get('surrender') else "No"
                        svf_val = "Yes" if c.get('svf') else "No"
                        comp_data.append([feature, surr_val, svf_val])

                if len(comp_data) > 1:
                    comp_tbl = Table(comp_data, colWidths=[2.8*inch, 1.7*inch, 1.7*inch])
                    comp_style = [
                        ('BACKGROUND', (0, 0), (-1, 0), SVF_ACCENT),
                        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
                        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
                        ('FONTNAME', (0, 1), (-1, -1), FONT_REGULAR),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
                        ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
                        ('BACKGROUND', (2, 1), (2, -1), SVF_BG),
                    ]
                    comp_tbl.setStyle(TableStyle(comp_style))
                    elements.append(comp_tbl)

            elements.append(Spacer(1, 0.06*inch))
            elements.append(create_highlight_box(
                "<b>Need funds from your policy?</b> Check your SVF eligibility at eazr.in — 24-72 hour processing, no credit score impact.",
                SVF_BG, SVF_ACCENT
            ))

        elements.append(PageBreak())

        # ==================== PAGE 6: POLICY REFERENCE ====================
        elements.append(create_section_header("Policy Quick Reference", styles))
        elements.append(Spacer(1, 0.1*inch))

        # Core details table
        elements.append(create_subsection_header("Core Details"))
        uin = policy_identification.get('uin', 'N/A')
        death_benefit_formula = f"SA ({format_currency(sum_assured)}) + Accrued Bonus ({format_currency(accrued_bonus)})"
        premiums_paid_count = policy_age_years
        premiums_remaining = max(ppt_years - policy_age_years, 0) if ppt_years > 0 else 0

        core_data = [
            ["Field", "Value"],
            ["Insurance Provider", str(insurer_name)],
            ["Product Name", str(plan_name)],
            ["Policy Type", str(policy_type_display)],
            ["UIN", str(uin)],
            ["Policy Number", str(policy_number)],
            ["Sum Assured", format_currency(sum_assured)],
            ["Current Death Benefit", format_currency(max(0, total_death_with_riders - policy_loan))],
            ["Death Benefit Formula", death_benefit_formula],
            ["Policy Term", str(policy_term)],
            ["Premium Paying Term", str(premium_paying_term)],
            ["Premiums Paid", f"{premiums_paid_count} years" if premiums_paid_count > 0 else "N/A"],
            ["Premiums Remaining", f"{premiums_remaining} years" if premiums_remaining > 0 else "Completed" if ppt_years > 0 and premiums_remaining <= 0 else "N/A"],
            ["Maturity Date", str(maturity_date)[:10] if str(maturity_date) != 'N/A' else 'N/A'],
        ]

        if guaranteed_maturity > 0 or projected_maturity > 0:
            core_data.append(["Guaranteed Maturity", format_currency(guaranteed_maturity) if guaranteed_maturity > 0 else "As per terms"])
            core_data.append(["Projected Maturity", format_currency(projected_maturity) if projected_maturity > 0 else "Depends on bonus"])

        if surrender_value > 0:
            core_data.append(["Surrender Value", format_currency(surrender_value)])
        if accrued_bonus > 0:
            core_data.append(["Accrued Bonus", format_currency(accrued_bonus)])
        if policy_loan > 0:
            core_data.append(["Outstanding Loan", format_currency(policy_loan)])

        core_data.append(["Premium", f"{format_currency(premium)} ({freq_display})"])
        core_data.append(["Annual Premium", format_currency(annual_premium)])
        core_data.append(["Next Due Date", str(next_premium_due) if str(next_premium_due) != 'N/A' else "Check policy"])
        core_data.append(["Grace Period", str(grace_period)])

        core_tbl = create_modern_table(core_data, [2.8*inch, 3.4*inch], BRAND_DARK)
        elements.append(core_tbl)
        elements.append(Spacer(1, 0.12*inch))

        # Riders table
        elements.append(create_subsection_header("Riders"))
        if rider_list:
            rider_data = [["Rider Name", "Sum Assured", "Premium", "Status"]]
            for rider in rider_list:
                r_name = str(rider.get('riderName', 'N/A'))
                r_sum = format_currency(rider.get('riderSumAssured', 0))
                r_prem = format_currency(rider.get('riderPremium', 0))
                r_status = str(rider.get('riderStatus', 'Active')).title()
                rider_data.append([r_name, r_sum, r_prem, r_status])
            rider_tbl = create_modern_table(rider_data, [2.4*inch, 1.4*inch, 1.2*inch, 1.2*inch], BRAND_PRIMARY)
            elements.append(rider_tbl)
        else:
            elements.append(Paragraph("No riders attached to this policy.", styles['body_text']))
        elements.append(Spacer(1, 0.1*inch))

        # Nominee table
        elements.append(create_subsection_header("Nominees"))
        if nominees:
            nom_data = [["Name", "Relationship", "Allocation %"]]
            for nom in nominees:
                n_name = safe_str(str(nom.get('nomineeName', 'N/A')))
                n_rel = safe_str(str(nom.get('nomineeRelationship', 'N/A')))
                _n_pct_raw = str(nom.get('nomineeShare', nom.get('allocation', nom.get('nomineePercentage', '100')))).rstrip('%')
                n_pct = f"{_n_pct_raw}%"
                nom_data.append([n_name, n_rel, n_pct])
            nom_tbl = create_modern_table(nom_data, [2.5*inch, 2.0*inch, 1.7*inch], BRAND_PRIMARY)
            elements.append(nom_tbl)
        else:
            elements.append(Paragraph("Nominee details not available.", styles['body_text']))
        elements.append(Spacer(1, 0.1*inch))

        # Tax benefits
        elements.append(create_subsection_header("Tax Benefits"))
        tax_80c = "Eligible" if annual_premium > 0 else "N/A"
        tax_10d = "Eligible (if premium < 10% of SA)" if (annual_premium > 0 and sum_assured > 0 and annual_premium <= sum_assured * 0.1) else "Check conditions"
        elements.append(Paragraph(f"<b>Section 80C:</b> {tax_80c} — Premium deduction up to {RUPEE_SYMBOL}1,50,000/year", styles['body_text']))
        elements.append(Paragraph(f"<b>Section 10(10D):</b> {tax_10d} — Maturity/death benefit tax-free", styles['body_text']))
        elements.append(Spacer(1, 0.1*inch))

        # Helpline
        elements.append(create_subsection_header("Claims Helpline"))
        elements.append(Paragraph(f"<b>{safe_str(insurer_name)}:</b> {safe_str(claims_helpline)}", styles['body_text']))

        elements.append(PageBreak())

        # ==================== PAGE 7: BACK COVER ====================
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph("<b>EAZR</b>", ParagraphStyle(
            'BackLogo', fontName=FONT_BOLD, fontSize=36, textColor=BRAND_PRIMARY,
            alignment=TA_CENTER, leading=44, spaceAfter=8
        )))
        elements.append(Paragraph("Powered by EAZR Policy Intelligence", ParagraphStyle(
            'BackTag', fontName=FONT_REGULAR, fontSize=10, textColor=MEDIUM_GRAY,
            alignment=TA_CENTER, leading=14, spaceAfter=20
        )))
        elements.append(HRFlowable(width="50%", thickness=1, color=BORDER_LIGHT, spaceAfter=15, hAlign='CENTER'))

        # Dual CTA
        cta_data = [[
            Paragraph("<b>Need premium financing?</b><br/>EAZR IPF", ParagraphStyle(
                'CTA1', fontName=FONT_REGULAR, fontSize=9, textColor=BRAND_DARK, alignment=TA_CENTER, leading=13)),
            Paragraph("<b>Need funds from your policy?</b><br/>EAZR SVF", ParagraphStyle(
                'CTA2', fontName=FONT_REGULAR, fontSize=9, textColor=SVF_ACCENT, alignment=TA_CENTER, leading=13)),
        ]]
        cta_tbl = Table(cta_data, colWidths=[3.1*inch, 3.1*inch])
        cta_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), BRAND_LIGHTER),
            ('BACKGROUND', (1, 0), (1, 0), SVF_BG),
            ('BOX', (0, 0), (0, 0), 1, BRAND_PRIMARY),
            ('BOX', (1, 0), (1, 0), 1, SVF_ACCENT),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(cta_tbl)
        elements.append(Spacer(1, 0.15*inch))

        elements.append(Paragraph("support@eazr.in  |  eazr.in", ParagraphStyle(
            'ContactLine', fontName=FONT_REGULAR, fontSize=9, textColor=MEDIUM_GRAY, alignment=TA_CENTER, spaceAfter=15
        )))

        elements.append(HRFlowable(width="80%", thickness=0.5, color=BORDER_LIGHT, spaceAfter=12, hAlign='CENTER'))

        # 9 Disclaimers
        elements.append(Paragraph("<b>IMPORTANT DISCLAIMERS</b>", ParagraphStyle(
            'DisclaimerTitle', fontName=FONT_BOLD, fontSize=9, textColor=CHARCOAL, alignment=TA_CENTER, spaceAfter=8
        )))

        disclaimers = [
            "This report is generated by EAZR's AI-powered Policy Intelligence engine and is intended for informational and educational purposes only.",
            "This report does not constitute insurance advice, financial advice, investment advice, or a recommendation to purchase, modify, surrender, or cancel any insurance policy.",
            "All projected values (maturity benefits, bonuses, fund values) are illustrations based on current rates and assumed growth scenarios. Actual values may differ materially. Past performance does not guarantee future results.",
            "Family financial need calculations are estimates based on user-provided inputs and standard assumptions (6% inflation, 8% discount rate). Actual needs may vary significantly based on individual circumstances.",
            "Surrender value, loan eligibility, and bonus amounts are as extracted from your policy document. For exact current values, contact your insurer directly.",
            "The scores and ratings in this report are proprietary to EAZR and are computed using industry benchmarks and IRDAI data. They do not represent any insurer's official assessment.",
            "EAZR SVF (Surrender Value Financing) and IPF (Insurance Premium Financing) options are subject to eligibility, credit assessment, and applicable terms and conditions. EMI calculations are indicative.",
            "For personalized insurance or financial advice, please consult a licensed insurance advisor or SEBI-registered financial planner.",
            "IRDAI does not endorse, approve, or guarantee any analysis, score, or recommendation in this report.",
        ]
        disc_style = ParagraphStyle('DisclaimerItem', fontName=FONT_REGULAR, fontSize=6.5,
                                    textColor=LIGHT_GRAY, leading=9, alignment=TA_JUSTIFY,
                                    spaceAfter=3, leftIndent=15, rightIndent=15)
        for i, d in enumerate(disclaimers, 1):
            elements.append(Paragraph(f"{i}. {d}", disc_style))

        elements.append(Spacer(1, 0.15*inch))
        elements.append(Paragraph("EAZR Digipayments Private Limited", ParagraphStyle(
            'CompanyName', fontName=FONT_BOLD, fontSize=7, textColor=MEDIUM_GRAY, alignment=TA_CENTER, spaceAfter=3
        )))
        elements.append(Paragraph(f"Report ID: {report_id}", ParagraphStyle(
            'ReportId', fontName=FONT_REGULAR, fontSize=7, textColor=LIGHT_GRAY, alignment=TA_CENTER, spaceAfter=3
        )))
        elements.append(Paragraph(
            f"<b>Version:</b> V10.0 | <b>Generated:</b> {datetime.now().strftime('%d %B %Y at %I:%M %p')}",
            styles['muted_text']))

        # ==================== BUILD PDF ====================
        def on_page(canvas, doc_template):
            ModernHeader.draw(canvas, doc_template)
            ModernFooter.draw(canvas, doc_template)

        pdf_doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
        buffer.seek(0)
        logger.info("Life Insurance PDF report generated successfully (V10)")
        return buffer

    except Exception as e:
        logger.error(f"Error generating Life Insurance PDF report: {str(e)}", exc_info=True)
        raise
