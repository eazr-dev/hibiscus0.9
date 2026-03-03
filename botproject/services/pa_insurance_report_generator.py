"""
Personal Accident Insurance Policy Analysis Report Generator — V10
Based on EAZR_04_Personal_Accident_PolicyAnalysisTab.md spec
6-page PDF: Cover+Summary, Score Deep-Dive, PPD Schedule+TTD Calculator,
Scenarios (PA001-PA004), Gaps+Actions+Portfolio, Policy Reference+Back Cover.

PA is the simplest PDF in the portfolio — 2 scores (S1 Income Replacement,
S2 Disability Protection), no product split, no SVF.
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
from datetime import datetime
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

# ==================== V10 SCORE & GAP COLORS ====================
SCORE_EXCELLENT = colors.HexColor('#22C55E')
SCORE_STRONG = colors.HexColor('#84CC16')
SCORE_ADEQUATE = colors.HexColor('#EAB308')
SCORE_MODERATE = colors.HexColor('#F97316')
SCORE_ATTENTION = colors.HexColor('#6B7280')

GAP_HIGH = colors.HexColor('#EF4444')
GAP_MEDIUM = colors.HexColor('#F59E0B')
GAP_LOW = colors.HexColor('#6B7280')

# PA-specific badge colors
PA_BADGE_INDIVIDUAL = colors.HexColor('#14B8A6')
PA_BADGE_FAMILY = colors.HexColor('#22C55E')
PA_BADGE_GROUP = colors.HexColor('#6B7280')

# TTD / Income gap bar colors
TTD_ACTIVE = colors.HexColor('#14B8A6')
TTD_WAITING = colors.HexColor('#E5E7EB')
INCOME_GAP_BAR = colors.HexColor('#F97316')

# PPD schedule colors
PPD_FULL_ROW = colors.HexColor('#1F2937')
PPD_PARTIAL_ROW = colors.HexColor('#374151')

# Portfolio matrix colors
PORTFOLIO_COVERED = colors.HexColor('#22C55E')
PORTFOLIO_NOT_COVERED = colors.HexColor('#EF4444')
PORTFOLIO_PARTIAL = colors.HexColor('#EAB308')

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


# ==================== IRDAI STANDARD PPD SCHEDULE ====================
IRDAI_PPD_SCHEDULE = [
    {"disability": "Both hands or both feet", "percentage": 100},
    {"disability": "One hand and one foot", "percentage": 100},
    {"disability": "Total sight loss — both eyes", "percentage": 100},
    {"disability": "Arm at shoulder", "percentage": 70},
    {"disability": "Arm between elbow & shoulder", "percentage": 65},
    {"disability": "Arm at or below elbow", "percentage": 60},
    {"disability": "Hand", "percentage": 55},
    {"disability": "Leg at or above knee", "percentage": 60},
    {"disability": "Leg below knee", "percentage": 50},
    {"disability": "Foot", "percentage": 45},
    {"disability": "Sight of one eye", "percentage": 50},
    {"disability": "Thumb", "percentage": 25},
    {"disability": "Index finger", "percentage": 10},
    {"disability": "Other finger (each)", "percentage": 5},
    {"disability": "Hearing — both ears", "percentage": 50},
    {"disability": "Hearing — one ear", "percentage": 15},
    {"disability": "Speech", "percentage": 50},
]


# ==================== HELPER FUNCTIONS ====================

def format_currency(value, show_symbol=True):
    if value is None or value == 'N/A' or value == '':
        return 'N/A'
    try:
        num = float(value)
        formatted = f"{int(num):,}"
        return f"Rs.{formatted}" if show_symbol else formatted
    except (ValueError, TypeError):
        return str(value) if value else 'N/A'


def safe_int(value, default=0):
    if value is None or value == 'N/A' or value == '':
        return default
    try:
        return int(float(str(value).replace(',', '').replace(RUPEE_SYMBOL, '').replace('Rs.', '').replace('\u20B9', '').strip()))
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    if value is None or value == 'N/A' or value == '':
        return default
    try:
        return float(str(value).replace(',', '').replace('%', '').replace(RUPEE_SYMBOL, '').replace('Rs.', '').replace('\u20B9', '').strip())
    except (ValueError, TypeError):
        return default


def safe_str(value, default='N/A'):
    if value is None or value == '':
        return default
    s = str(value)
    s = s.replace('\u20b9', 'Rs.').replace('\u20B9', 'Rs.').replace('₹', 'Rs.')
    s = s.replace('\u2022', '-').replace('\u2013', '-').replace('\u2014', '-')
    s = s.replace('\u2018', "'").replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
    s = s.replace('\u25a0', '').replace('\u25cf', '-').replace('\u2192', '->')
    return s


def _get_v10_score_color(score):
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
    if score >= 90:
        return SUCCESS_LIGHT
    elif score >= 75:
        return colors.HexColor('#F0FFF4')
    elif score >= 60:
        return WARNING_LIGHT
    elif score >= 40:
        return colors.HexColor('#FFF7ED')
    else:
        return colors.HexColor('#F3F4F6')


def _get_pa_badge_color(policy_sub_type):
    sub = str(policy_sub_type).lower()
    if 'family' in sub or 'floater' in sub:
        return PA_BADGE_FAMILY
    elif 'group' in sub or 'corporate' in sub:
        return PA_BADGE_GROUP
    return PA_BADGE_INDIVIDUAL


def _get_pa_badge_label(policy_sub_type):
    sub = str(policy_sub_type).lower()
    if 'family' in sub or 'floater' in sub:
        return "Family PA"
    elif 'group' in sub or 'corporate' in sub:
        return "Group PA"
    return "Individual PA"


def get_claims_helpline(insurer_name):
    insurer_lower = str(insurer_name).lower()
    helplines = {
        'icici lombard': '1800-266-9725',
        'bajaj allianz': '1800-209-5858',
        'hdfc ergo': '1800-266-0700',
        'new india': '1800-209-1415',
        'united india': '1800-4253-3333',
        'national insurance': '1800-345-0330',
        'oriental insurance': '1800-118-485',
        'tata aig': '1800-266-7780',
        'reliance general': '1800-102-4088',
        'sbi general': '1800-102-1111',
        'iffco tokio': '1800-103-5499',
        'star health': '1800-425-2255',
        'niva bupa': '1800-200-7788',
        'care health': '1800-102-4488',
        'chola ms': '1800-208-5544',
        'future generali': '1800-220-233',
        'kotak': '1800-266-4545',
        'liberty': '1800-266-5844',
        'royal sundaram': '1800-568-9999',
        'acko': '1800-266-2256',
        'digit': '1800-258-4242',
        'go digit': '1800-258-4242',
        'magma': '1800-200-3344',
    }
    for key, number in helplines.items():
        if key in insurer_lower:
            return number
    return "See policy document"


# ==================== REUSABLE UI COMPONENTS ====================

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
        canvas.drawCentredString(A4[0] / 2, A4[1] - 0.4*inch, "Personal Accident Analysis Report")
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
    styles = {
        'cover_main_title': ParagraphStyle(
            'CoverMainTitle', fontName=FONT_BOLD, fontSize=22, textColor=CHARCOAL,
            alignment=TA_CENTER, spaceAfter=4, leading=28
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
        'scenario_title': ParagraphStyle(
            'ScenarioTitle', fontName=FONT_BOLD, fontSize=10, textColor=BRAND_DARK,
            spaceBefore=10, spaceAfter=4
        ),
    }
    return styles


def create_section_header(title, styles):
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
    return Paragraph(
        f"<font color='#{BRAND_DARK.hexval()[2:]}'><b>{title}</b></font>",
        ParagraphStyle('SubsectionHeader', fontName=FONT_BOLD, fontSize=11,
                      textColor=BRAND_DARK, spaceBefore=12, spaceAfter=6)
    )


def create_score_visual(score, protection_label, score_color_override=None):
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
    tile = Table([[para]], colWidths=[2.6*inch])
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
    if not factors:
        return []
    sc_color = colors.HexColor(score_color_hex) if score_color_hex else BRAND_PRIMARY
    elems = []

    bar_text = f"<b>{score_name}</b>  <font color='{score_color_hex}'><b>{score_val}/100 — {score_label}</b></font>"
    elems.append(Paragraph(bar_text, ParagraphStyle('ScoreBarH', fontName=FONT_BOLD, fontSize=11, textColor=CHARCOAL, spaceAfter=6)))

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
# MAIN REPORT GENERATOR — V10 (6-page PDF)
# ==============================================================================

def generate_pa_insurance_report(policy_data: dict, analysis_data: dict) -> BytesIO:
    """
    Generate V10 Personal Accident insurance analysis report.
    Pages: Cover+Summary, Score Deep-Dive, PPD Schedule+TTD Calculator,
    Scenarios (PA001-PA004), Gaps+Actions+Portfolio, Policy Reference+Back Cover.
    """
    try:
        buffer = BytesIO()
        pdf_doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=0.6*inch, leftMargin=0.6*inch,
            topMargin=0.85*inch, bottomMargin=0.7*inch,
            title="Personal Accident Insurance Policy Analysis",
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
        start_date = str(policy_data.get('startDate', 'N/A'))
        end_date = str(policy_data.get('endDate', 'N/A'))

        category_data = policy_data.get('categorySpecificData', {})
        if not isinstance(category_data, dict):
            category_data = {}
        policy_basics = category_data.get('policyBasics', category_data.get('policyIdentification', {}))
        coverage_details = category_data.get('coverageDetails', {})
        additional_benefits = category_data.get('additionalBenefits', {})
        exclusions_data = category_data.get('exclusions', {})
        premium_details = category_data.get('premiumDetails', {})
        insured_members = category_data.get('insuredMembers', [])
        nomination = category_data.get('nomination', {})
        claims_info = category_data.get('claimsInfo', {})

        product_name = safe_str(policy_basics.get('productName') or 'Personal Accident Insurance')
        policy_sub_type = safe_str(policy_basics.get('policyType', 'Individual'))
        total_premium = safe_int(premium_details.get('totalPremium') or premium)

        # Coverage sub-objects
        ad = coverage_details.get('accidentalDeath', {}) if isinstance(coverage_details.get('accidentalDeath'), dict) else {}
        ptd = coverage_details.get('permanentTotalDisability', {}) if isinstance(coverage_details.get('permanentTotalDisability'), dict) else {}
        ppd = coverage_details.get('permanentPartialDisability', {}) if isinstance(coverage_details.get('permanentPartialDisability'), dict) else {}
        ttd = coverage_details.get('temporaryTotalDisability', {}) if isinstance(coverage_details.get('temporaryTotalDisability'), dict) else {}
        medical = coverage_details.get('medicalExpenses', {}) if isinstance(coverage_details.get('medicalExpenses'), dict) else {}

        ad_benefit = safe_int(ad.get('benefitAmount'), sum_assured)
        ptd_benefit = safe_int(ptd.get('benefitAmount'), sum_assured)
        ttd_benefit = safe_int(ttd.get('benefitAmount') or ttd.get('weeklyBenefit'), 0)
        ttd_covered = ttd.get('covered', False)
        ttd_max_weeks = safe_int(ttd.get('maximumWeeks'), 52)
        ttd_waiting = safe_int(ttd.get('waitingPeriodDays'), 7)
        double_indemnity_applicable = ad.get('doubleIndemnity', {}).get('applicable', False)

        # Claims helpline
        claims_helpline = get_claims_helpline(insurer_name)

        # ==================== EXTRACT V10 DATA ====================
        protection_readiness = analysis_data.get('protectionReadiness', {})
        if not isinstance(protection_readiness, dict):
            protection_readiness = {}
        v10_scores = protection_readiness.get('scores', {})

        composite_score = safe_int(protection_readiness.get('compositeScore', analysis_data.get('protectionScore', 0)))
        verdict = protection_readiness.get('verdict', {})
        verdict_label = verdict.get('label', analysis_data.get('protectionScoreLabel', 'Needs Review'))
        verdict_summary = verdict.get('summary', '')
        verdict_color_hex = verdict.get('color', '#6B7280')

        s1_data = v10_scores.get('s1', {})
        s2_data = v10_scores.get('s2', {})

        # Income Gap Check
        income_gap_check = analysis_data.get('incomeGapCheck', {})
        if not isinstance(income_gap_check, dict):
            income_gap_check = {}

        # Portfolio View
        portfolio_view = analysis_data.get('portfolioView', {})
        if not isinstance(portfolio_view, dict):
            portfolio_view = {}

        # Strengths
        v10_strengths = analysis_data.get('coverageStrengths', [])
        if not isinstance(v10_strengths, list):
            v10_strengths = []

        # Gaps
        v10_gaps_data = analysis_data.get('coverageGaps', {})
        if isinstance(v10_gaps_data, dict):
            v10_gap_list = v10_gaps_data.get('gaps', [])
            v10_gap_summary = v10_gaps_data.get('summary', {})
        else:
            v10_gap_list = v10_gaps_data if isinstance(v10_gaps_data, list) else []
            v10_gap_summary = {}

        # Recommendations
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

        # Scenarios
        v10_scenarios = analysis_data.get('scenarios', {})
        if isinstance(v10_scenarios, dict):
            primary_scenario_id = v10_scenarios.get('primaryScenarioId', 'PA001')
            scenario_list = v10_scenarios.get('simulations', [])
        elif isinstance(v10_scenarios, list):
            primary_scenario_id = 'PA001'
            scenario_list = v10_scenarios
        else:
            primary_scenario_id = 'PA001'
            scenario_list = analysis_data.get('scenarioSimulations', [])
            if not isinstance(scenario_list, list):
                scenario_list = []

        # Income data from income gap check
        _recommended_db = safe_int(income_gap_check.get('deathBenefit', {}).get('recommended', 0))
        annual_income = _recommended_db // 10 if _recommended_db > 0 else safe_int(income_gap_check.get('annualIncome', 0))
        if annual_income <= 0:
            # Fallback: derive from sum assured (assume 10x income multiple)
            annual_income = sum_assured // 10 if sum_assured > 0 else 0
        weekly_income = annual_income // 52
        death_benefit_data = income_gap_check.get('deathBenefit', {})
        ttd_benefit_data = income_gap_check.get('ttdBenefit', {})
        income_multiple = safe_float(death_benefit_data.get('incomeMultiple', 0))
        ttd_coverage_pct = safe_float(ttd_benefit_data.get('coveragePct', 0))

        # At a Glance data
        gap_high = safe_int(v10_gap_summary.get('high', 0))
        gap_medium = safe_int(v10_gap_summary.get('medium', 0))
        gap_low = safe_int(v10_gap_summary.get('low', 0))
        upgrade_annual = safe_int(total_upgrade_cost.get('annual', 0))
        upgrade_monthly = safe_int(total_upgrade_cost.get('monthlyEmi', 0))

        # Generate report ID
        report_id = f"EAZ-PA-{datetime.now().strftime('%Y-%m-%d')}-{abs(hash(policy_number)) % 0xFFFF:04X}"
        ModernFooter.report_id = report_id

        # ==================================================================
        # PAGE 1: COVER + EXECUTIVE SUMMARY
        # ==================================================================
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph("PERSONAL ACCIDENT ANALYSIS REPORT", styles['cover_main_title']))
        elements.append(HRFlowable(width="30%", thickness=2, color=BRAND_PRIMARY, spaceAfter=12, hAlign='CENTER'))
        elements.append(Spacer(1, 0.1*inch))

        # Policy info card
        cover_items = [
            ("Prepared for", policy_holder_name),
            ("Policy", product_name),
            ("Policy Number", policy_number),
            ("Status", f"Active | {start_date[:10] if start_date != 'N/A' else 'N/A'} to {end_date[:10] if end_date != 'N/A' else 'N/A'}"),
        ]
        cover_card = create_info_card(cover_items)
        card_wrapper = Table([[cover_card]], colWidths=[6.2*inch])
        card_wrapper.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
        elements.append(card_wrapper)
        elements.append(Spacer(1, 0.08*inch))

        # PA type badge
        badge_color = _get_pa_badge_color(policy_sub_type)
        badge_label = _get_pa_badge_label(policy_sub_type)
        badge_para = Paragraph(f"<font color='#FFFFFF'><b>{badge_label}</b></font>",
                              ParagraphStyle('Badge', fontName=FONT_BOLD, fontSize=9, alignment=TA_CENTER))
        badge_tbl = Table([[badge_para]], colWidths=[1.6*inch])
        badge_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), badge_color),
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
        elements.append(Paragraph("<b>ACCIDENT PROTECTION SCORE</b>", ParagraphStyle(
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

        # Verdict summary
        if verdict_summary:
            elements.append(Paragraph(f"<i>{verdict_summary}</i>", styles['advisory_intro']))

        # S1 + S2 Score Tiles (side by side)
        s1_tile = _create_score_tile(s1_data, "Weight: 60%")
        s2_tile = _create_score_tile(s2_data, "Weight: 40%")
        if s1_tile and s2_tile:
            tiles_row = Table([[s1_tile, s2_tile]], colWidths=[3.1*inch, 3.1*inch])
            tiles_row.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(tiles_row)
            elements.append(Spacer(1, 0.12*inch))

        # At a Glance table
        elements.append(create_subsection_header("AT A GLANCE"))
        glance_data = [
            ["Metric", "Value"],
            ["Sum Insured", format_currency(sum_assured)],
        ]
        if income_multiple > 0:
            rec_text = f"{income_multiple:.1f}x (Recommended: 10x)" if income_multiple < 10 else f"{income_multiple:.1f}x annual income"
            glance_data.append(["Income Multiple", rec_text])
        if ttd_covered and ttd_benefit > 0:
            ttd_text = f"{format_currency(ttd_benefit)}/wk"
            if ttd_coverage_pct > 0:
                ttd_text += f" ({ttd_coverage_pct:.0f}% of income)"
            glance_data.append(["TTD Weekly Benefit", ttd_text])
        elif not ttd_covered:
            glance_data.append(["TTD Weekly Benefit", "Not Covered"])
        gap_text = f"{gap_high} High"
        if gap_medium > 0:
            gap_text += f" | {gap_medium} Medium"
        if gap_low > 0:
            gap_text += f" | {gap_low} Low"
        glance_data.append(["Gaps Found", gap_text])
        if upgrade_annual > 0:
            upgrade_text = f"{format_currency(upgrade_annual)}/yr"
            if upgrade_monthly > 0:
                upgrade_text += f" = {format_currency(upgrade_monthly)}/mo with EAZR"
            glance_data.append(["Recommended Upgrade", upgrade_text])

        glance_table = create_modern_table(glance_data, [2.5*inch, 3.7*inch], header_bg=BRAND_DARK)
        elements.append(glance_table)
        elements.append(Spacer(1, 0.08*inch))

        # Report ID footer
        elements.append(Paragraph(
            f"<font size='7' color='#{LIGHT_GRAY.hexval()[2:]}'>Report ID: {report_id} | Generated: {datetime.now().strftime('%d %b %Y')}</font>",
            ParagraphStyle('ReportId', fontName=FONT_REGULAR, fontSize=7, textColor=LIGHT_GRAY, alignment=TA_CENTER)
        ))

        # ==================================================================
        # PAGE 2: SCORE DEEP-DIVE
        # ==================================================================
        elements.append(PageBreak())
        elements.append(create_section_header("Score Deep-Dive", styles))
        elements.append(Spacer(1, 0.08*inch))
        elements.append(Paragraph(
            f"Hi {first_name}, here's a detailed breakdown of how your PA policy scored across the two evaluation dimensions.",
            styles['body_text']
        ))

        # S1: Income Replacement Adequacy
        if s1_data and s1_data.get('factors'):
            elements.append(Spacer(1, 0.08*inch))
            s1_factors = s1_data.get('factors', [])
            s1_elems = _create_factor_table(
                s1_factors,
                s1_data.get('name', 'Income Replacement Adequacy'),
                safe_int(s1_data.get('score', 0)),
                s1_data.get('label', ''),
                s1_data.get('color', '#6B7280')
            )
            for e in s1_elems:
                elements.append(e)
            elements.append(Spacer(1, 0.06*inch))

            # What This Means for S1
            s1_score = safe_int(s1_data.get('score', 0))
            if s1_score >= 80:
                s1_insight = "Your death benefit and PTD coverage provide strong income replacement. Your family would be well-protected financially in case of an accidental death or permanent disability."
            elif s1_score >= 60:
                s1_insight = "Your income replacement coverage is adequate but could be improved. Consider increasing your sum insured to at least 10x annual income for comprehensive protection."
            else:
                s1_insight = "Your income replacement coverage has significant gaps. The current sum insured may not adequately support your family's financial needs. Increasing coverage should be a priority."
            elements.append(create_highlight_box(
                f"<b>What This Means:</b> {s1_insight}",
                BRAND_LIGHTER, BRAND_PRIMARY
            ))

        # S2: Disability Protection Depth
        if s2_data and s2_data.get('factors'):
            elements.append(Spacer(1, 0.12*inch))
            s2_factors = s2_data.get('factors', [])
            s2_elems = _create_factor_table(
                s2_factors,
                s2_data.get('name', 'Disability Protection Depth'),
                safe_int(s2_data.get('score', 0)),
                s2_data.get('label', ''),
                s2_data.get('color', '#6B7280')
            )
            for e in s2_elems:
                elements.append(e)
            elements.append(Spacer(1, 0.06*inch))

            # What This Means for S2
            s2_score = safe_int(s2_data.get('score', 0))
            if s2_score >= 80:
                s2_insight = "Comprehensive disability protection with good PPD schedule coverage, TTD benefits, and support features like home/vehicle modifications."
            elif s2_score >= 60:
                s2_insight = "Your disability coverage is reasonable but has room for improvement. Adding TTD coverage or extending its duration would significantly improve protection."
            else:
                s2_insight = "Your disability protection has critical gaps. Key features like TTD (income during recovery) or modification benefits may be missing. These gaps leave you financially vulnerable during disability."
            elements.append(create_highlight_box(
                f"<b>What This Means:</b> {s2_insight}",
                BRAND_LIGHTER, BRAND_PRIMARY
            ))

        # ==================================================================
        # PAGE 3: PPD SCHEDULE + TTD CALCULATOR (PA-unique)
        # ==================================================================
        elements.append(PageBreak())
        elements.append(create_section_header("Your Disability Benefits — Calculated", styles))
        elements.append(Spacer(1, 0.04*inch))
        elements.append(Paragraph(
            f"Based on your Sum Insured of {format_currency(sum_assured)}, here are the calculated benefit amounts for each disability type.",
            styles['body_text']
        ))

        # PPD Schedule
        elements.append(create_subsection_header("Permanent Partial Disability — Benefit Schedule"))
        ppd_schedule = ppd.get('schedule', [])
        if not ppd_schedule:
            ppd_schedule = IRDAI_PPD_SCHEDULE

        ppd_table_data = [["Disability", "% of SI", "Benefit Amount"]]
        for item in ppd_schedule:
            pct = safe_float(item.get('percentage', 0))
            amount = int(sum_assured * pct / 100)
            disability_name = safe_str(item.get('disability', item.get('condition', '')))
            is_full = pct >= 100

            ppd_table_data.append([
                disability_name,
                f"{pct:.0f}%",
                format_currency(amount)
            ])
        ppd_table_data.append(["Note: Multiple disabilities claimable, capped at 100% total. Percentages per IRDAI standard schedule.", "", ""])

        ppd_table = Table(ppd_table_data, colWidths=[3.2*inch, 1.0*inch, 2.0*inch])
        ppd_style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), BRAND_DARK),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (2, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('BOX', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
            # Note row styling
            ('SPAN', (0, -1), (-1, -1)),
            ('FONTNAME', (0, -1), (-1, -1), FONT_ITALIC),
            ('TEXTCOLOR', (0, -1), (-1, -1), MEDIUM_GRAY),
            ('FONTSIZE', (0, -1), (-1, -1), 7),
            ('BACKGROUND', (0, -1), (-1, -1), WHISPER),
            ('ALIGN', (0, -1), (-1, -1), 'LEFT'),
        ]
        # Alternate row colors and bold 100% rows
        for i in range(1, len(ppd_table_data) - 1):
            pct_val = safe_float(ppd_schedule[i-1].get('percentage', 0)) if i-1 < len(ppd_schedule) else 0
            if pct_val >= 100:
                ppd_style_cmds.append(('FONTNAME', (0, i), (-1, i), FONT_BOLD))
                ppd_style_cmds.append(('TEXTCOLOR', (0, i), (-1, i), PPD_FULL_ROW))
            elif i % 2 == 0:
                ppd_style_cmds.append(('BACKGROUND', (0, i), (-1, i), WHISPER))

        ppd_table.setStyle(TableStyle(ppd_style_cmds))
        elements.append(ppd_table)
        elements.append(Spacer(1, 0.15*inch))

        # TTD Calculator — Income Timeline
        elements.append(create_subsection_header("Temporary Total Disability — Income Timeline"))

        if ttd_covered and ttd_benefit > 0:
            elements.append(Paragraph(
                f"Your TTD: {format_currency(ttd_benefit)}/week | Max: {ttd_max_weeks} weeks | Waiting: {ttd_waiting} days",
                styles['body_emphasis']
            ))
            if weekly_income > 0:
                elements.append(Paragraph(
                    f"Your weekly income: {format_currency(weekly_income)} | TTD covers: {ttd_coverage_pct:.0f}%",
                    styles['body_text']
                ))

            # TTD timeline table
            _waiting_weeks = max(0, ttd_waiting // 7) if ttd_waiting > 0 else 0
            ttd_periods = [
                ("2 weeks", 2),
                ("1 month", 4),
                ("3 months", 13),
                ("6 months", 26),
                (f"1 year (max {ttd_max_weeks}wk)", min(ttd_max_weeks, 52)),
            ]

            timeline_data = [["Duration Off Work", "TTD Benefit", "Income Lost", "Gap"]]
            for label, total_weeks in ttd_periods:
                benefit_weeks = max(0, total_weeks - _waiting_weeks)
                ttd_payout = ttd_benefit * benefit_weeks
                income_lost = weekly_income * total_weeks
                gap = max(0, income_lost - ttd_payout)
                timeline_data.append([
                    label,
                    format_currency(ttd_payout),
                    format_currency(income_lost),
                    format_currency(gap)
                ])

            timeline_table = create_modern_table(
                timeline_data,
                [1.8*inch, 1.3*inch, 1.3*inch, 1.8*inch],
                header_bg=TTD_ACTIVE
            )
            elements.append(Spacer(1, 0.04*inch))
            elements.append(timeline_table)
            elements.append(Spacer(1, 0.08*inch))

            # Visual coverage bar
            covered_pct = min(100, max(0, int(ttd_coverage_pct)))
            gap_pct = 100 - covered_pct
            bar_content = f"""<font color="#{TTD_ACTIVE.hexval()[2:]}"><b>{'|' * max(1, covered_pct // 3)} TTD Covers {covered_pct}%</b></font>  |  <font color="#{INCOME_GAP_BAR.hexval()[2:]}"><b>{'|' * max(1, gap_pct // 3)} Gap {gap_pct}%</b></font>"""
            elements.append(create_highlight_box(bar_content, WHISPER, TTD_ACTIVE))
            elements.append(Spacer(1, 0.06*inch))

            # TTD insight
            if ttd_coverage_pct < 50:
                ttd_insight = f"The longer you're disabled, the wider the gap. After 6 months, your shortfall could be significant. Increasing your SI would proportionally increase weekly TTD benefits."
            else:
                ttd_insight = f"Your TTD covers a reasonable portion of your income. However, long-term disability can still create financial pressure — consider whether the coverage duration is sufficient for your needs."
            elements.append(Paragraph(ttd_insight, styles['muted_text']))

        else:
            # TTD NOT covered
            elements.append(create_highlight_box(
                "<b>TTD is NOT COVERED in your current policy.</b><br/><br/>"
                "If you cannot work due to an accident (fracture, surgery recovery, etc.), you will have zero income replacement. "
                "This is a critical gap — consider adding TTD cover if your income depends on your ability to work. "
                "TTD typically adds 10-15% to the base premium.",
                DANGER_LIGHT, DANGER_RED
            ))

        # ==================================================================
        # PAGE 4: SCENARIOS (PA001-PA004)
        # ==================================================================
        elements.append(PageBreak())
        elements.append(create_section_header("What Happens In Each Scenario", styles))
        elements.append(Spacer(1, 0.04*inch))
        elements.append(Paragraph(
            f"Based on your Sum Insured of {format_currency(sum_assured)}, here's what happens in four real-world accident scenarios.",
            styles['body_text']
        ))

        # Build scenarios from scenario_list or from raw data
        scenario_colors = {
            'PA001': DANGER_RED,
            'PA002': WARNING_AMBER,
            'PA003': TTD_ACTIVE,
            'PA004': INFO_BLUE,
        }
        scenario_labels = {
            'PA001': 'SCENARIO 1: ACCIDENTAL DEATH',
            'PA002': 'SCENARIO 2: PERMANENT TOTAL DISABILITY (PTD)',
            'PA003': 'SCENARIO 3: TEMPORARY DISABILITY — 6 MONTHS',
            'PA004': 'SCENARIO 4: PARTIAL DISABILITY — PPD EXAMPLE',
        }

        if scenario_list:
            # Use V10 scenario data (PA scenarios have analysis/output/recommendation structure)
            for sim in scenario_list:
                if not isinstance(sim, dict):
                    continue
                sim_id = sim.get('scenarioId', sim.get('id', ''))
                sim_title = sim.get('name', sim.get('title', scenario_labels.get(sim_id, f'Scenario {sim_id}')))
                sim_color = scenario_colors.get(sim_id, MEDIUM_GRAY)
                is_primary = (sim_id == primary_scenario_id)

                # Scenario header
                header_text = sim_title.upper()
                if is_primary:
                    header_text += "  [PRIMARY]"

                # Build key-value data from PA V10 structure
                kv_data = []
                analysis = sim.get('analysis', {})
                output = sim.get('output', {})
                recommendation = sim.get('recommendation', '')
                description = sim.get('description', '')

                if description:
                    kv_data.append(["Scenario", safe_str(description)])

                if sim_id == 'PA001':
                    # Accidental Death — show needs vs coverage vs gap
                    imm = analysis.get('immediateNeeds', {})
                    ong = analysis.get('ongoingNeeds', {})
                    if imm.get('totalFormatted'):
                        kv_data.append(["Immediate Needs", safe_str(imm.get('totalFormatted'))])
                    if ong.get('totalFormatted'):
                        kv_data.append(["Ongoing Needs", safe_str(ong.get('totalFormatted'))])
                    if analysis.get('totalNeedFormatted'):
                        kv_data.append(["Total Need", safe_str(analysis.get('totalNeedFormatted'))])
                    if analysis.get('paBenefitFormatted'):
                        kv_data.append(["PA Benefit", safe_str(analysis.get('paBenefitFormatted'))])
                    if analysis.get('totalCoverageFormatted'):
                        kv_data.append(["Total Coverage (PA + Life)", safe_str(analysis.get('totalCoverageFormatted'))])
                    gap_val = analysis.get('gap', 0)
                    if gap_val and safe_int(gap_val) > 0:
                        kv_data.append(["Gap", safe_str(analysis.get('gapFormatted', format_currency(safe_int(gap_val))))])
                    elif output.get('gapToTotalNeed'):
                        kv_data.append(["Gap", safe_str(output.get('gapToTotalNeed'))])

                elif sim_id == 'PA002':
                    # PTD — show needs, benefit, modification support
                    needs = analysis.get('totalNeeds', {})
                    if needs.get('items'):
                        for item in needs.get('items', []):
                            if isinstance(item, dict) and item.get('label'):
                                kv_data.append([safe_str(item['label']), format_currency(safe_int(item.get('amount', 0)))])
                    if needs.get('totalFormatted'):
                        kv_data.append(["Total Need", safe_str(needs.get('totalFormatted'))])
                    if analysis.get('ptdBenefitFormatted'):
                        kv_data.append(["PTD Benefit", safe_str(analysis.get('ptdBenefitFormatted'))])
                    if output.get('modificationSupport'):
                        kv_data.append(["Modification Support", safe_str(output.get('modificationSupport'))])
                    ptd_gap = analysis.get('gap', 0)
                    if ptd_gap and safe_int(ptd_gap) > 0:
                        kv_data.append(["Gap", safe_str(analysis.get('gapFormatted', format_currency(safe_int(ptd_gap))))])

                elif sim_id == 'PA003':
                    # TTD 6-month — show income loss, TTD benefit, gap
                    inc_loss = analysis.get('incomeLoss', {})
                    if inc_loss.get('totalIncomeLostFormatted'):
                        kv_data.append(["Income Lost (6 months)", safe_str(inc_loss.get('totalIncomeLostFormatted'))])
                    fixed = analysis.get('fixedExpensesContinue', {})
                    if fixed.get('totalNeededFormatted'):
                        kv_data.append(["Fixed Expenses Continue", safe_str(fixed.get('totalNeededFormatted'))])
                    ttd_ben = analysis.get('ttdBenefit', {})
                    if ttd_ben.get('covered'):
                        kv_data.append(["TTD Benefit", safe_str(ttd_ben.get('totalBenefitFormatted', 'N/A'))])
                        if ttd_ben.get('afterWaitingPeriod'):
                            kv_data.append(["Starts After", safe_str(ttd_ben.get('afterWaitingPeriod'))])
                    else:
                        kv_data.append(["TTD Benefit", "NOT COVERED — zero income replacement"])
                    ttd_gap = analysis.get('gap', 0)
                    if ttd_gap and safe_int(ttd_gap) > 0:
                        kv_data.append(["Shortfall", safe_str(analysis.get('gapFormatted', format_currency(safe_int(ttd_gap))))])
                    elif output.get('shortfall'):
                        kv_data.append(["Shortfall", safe_str(output.get('shortfall'))])

                elif sim_id == 'PA004':
                    # PPD example — show lookup, examples
                    lookup = analysis.get('ppdLookup', {})
                    if lookup.get('disability'):
                        kv_data.append(["Example", safe_str(lookup.get('disability'))])
                    if lookup.get('calculation'):
                        kv_data.append(["Calculation", safe_str(lookup.get('calculation'))])
                    if lookup.get('benefitFormatted'):
                        kv_data.append(["Benefit", safe_str(lookup.get('benefitFormatted'))])
                    examples = analysis.get('commonExamples', [])
                    for ex in examples[:3]:
                        if isinstance(ex, dict) and ex.get('disability'):
                            kv_data.append([safe_str(ex['disability']), f"{safe_int(ex.get('percentage', 0))}% = {safe_str(ex.get('benefitFormatted', ''))}"])

                else:
                    # Generic fallback for unknown scenario IDs
                    if output:
                        for k, v in output.items():
                            if isinstance(v, str) and v:
                                kv_data.append([k.replace('_', ' ').title(), safe_str(v)])

                # Add recommendation as last row
                if recommendation:
                    _rec_style = ParagraphStyle('RecCell', fontName=FONT_REGULAR, fontSize=8, textColor=SLATE, leading=10)
                    kv_data.append(["Recommendation", Paragraph(safe_str(recommendation), _rec_style)])

                # Build scenario table
                scenario_header_data = [[header_text, '']]
                if kv_data:
                    scenario_header_data.extend(kv_data)
                else:
                    scenario_header_data.append(['No detailed data available', ''])

                s_table = Table(scenario_header_data, colWidths=[2.5*inch, 3.7*inch])
                s_style = [
                    ('BACKGROUND', (0, 0), (-1, 0), sim_color),
                    ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
                    ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
                    ('SPAN', (0, 0), (-1, 0)),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('FONTNAME', (0, 1), (0, -1), FONT_BOLD),
                    ('TEXTCOLOR', (0, 1), (0, -1), SLATE),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
                    ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ]
                for i in range(1, len(scenario_header_data)):
                    if i % 2 == 0:
                        s_style.append(('BACKGROUND', (0, i), (-1, i), WHISPER))
                s_table.setStyle(TableStyle(s_style))
                elements.append(Spacer(1, 0.06*inch))
                elements.append(KeepTogether([s_table]))
        else:
            # Fallback: Build scenarios from raw category data
            # Scenario 1: Accidental Death
            double_payout = ad_benefit * 2 if double_indemnity_applicable else 0
            s1_kv = [
                ["Event", "Death due to accident (road, workplace, or other covered accident)"],
                ["Base Benefit", format_currency(ad_benefit)],
            ]
            if double_indemnity_applicable:
                s1_kv.append(["Double Indemnity", f"{format_currency(double_payout)} (public transport)"])
            s1_kv.append(["Claim Process", "Nominee submits death certificate + FIR + policy copy"])

            s1_data_rows = [["SCENARIO 1: ACCIDENTAL DEATH", ""]] + s1_kv
            s1_table = Table(s1_data_rows, colWidths=[2.5*inch, 3.7*inch])
            s1_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), DANGER_RED), ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
                ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD), ('SPAN', (0, 0), (-1, 0)),
                ('FONTSIZE', (0, 0), (-1, -1), 8), ('FONTNAME', (0, 1), (0, -1), FONT_BOLD),
                ('TEXTCOLOR', (0, 1), (0, -1), SLATE), ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
                ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
                ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(Spacer(1, 0.06*inch))
            elements.append(KeepTogether([s1_table]))

            # Scenario 2: PTD
            s2_kv = [
                ["Event", "Complete loss of both eyes, both hands/feet, or paralysis"],
                ["Benefit Amount", format_currency(ptd_benefit)],
                ["Additional", "Home/Vehicle modification benefits may apply" if additional_benefits.get('homeModification', {}).get('covered') else "Consider adding PTD support riders"],
            ]
            s2_data_rows = [["SCENARIO 2: PERMANENT TOTAL DISABILITY (PTD)", ""]] + s2_kv
            s2_table = Table(s2_data_rows, colWidths=[2.5*inch, 3.7*inch])
            s2_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), WARNING_AMBER), ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
                ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD), ('SPAN', (0, 0), (-1, 0)),
                ('FONTSIZE', (0, 0), (-1, -1), 8), ('FONTNAME', (0, 1), (0, -1), FONT_BOLD),
                ('TEXTCOLOR', (0, 1), (0, -1), SLATE), ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
                ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
                ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(Spacer(1, 0.06*inch))
            elements.append(KeepTogether([s2_table]))

            # Scenario 3: TTD 6-Month
            if ttd_covered:
                ttd_6mo = ttd_benefit * 26
                s3_kv = [
                    ["Event", "6-month recovery from accident (fracture, surgery, etc.)"],
                    ["TTD Benefit (26 weeks)", format_currency(ttd_6mo)],
                    ["Income Lost (6 months)", format_currency(weekly_income * 26)],
                    ["Gap", format_currency(max(0, weekly_income * 26 - ttd_6mo))],
                ]
            else:
                s3_kv = [
                    ["Event", "6-month recovery from accident"],
                    ["Status", "TTD NOT COVERED — zero income replacement"],
                    ["Impact", f"You lose {format_currency(weekly_income * 26)} over 6 months with no coverage"],
                ]
            s3_data_rows = [["SCENARIO 3: TEMPORARY DISABILITY — 6 MONTHS", ""]] + s3_kv
            s3_table = Table(s3_data_rows, colWidths=[2.5*inch, 3.7*inch])
            s3_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), TTD_ACTIVE), ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
                ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD), ('SPAN', (0, 0), (-1, 0)),
                ('FONTSIZE', (0, 0), (-1, -1), 8), ('FONTNAME', (0, 1), (0, -1), FONT_BOLD),
                ('TEXTCOLOR', (0, 1), (0, -1), SLATE), ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
                ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
                ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(Spacer(1, 0.06*inch))
            elements.append(KeepTogether([s3_table]))

            # Scenario 4: PPD Example
            ppd_example_amount = int(sum_assured * 0.10)
            s4_kv = [
                ["Event", "Loss of index finger in workplace accident"],
                ["PPD Calculation", f"SI ({format_currency(sum_assured)}) x 10% = {format_currency(ppd_example_amount)}"],
                ["Context", f"Thumb = 25% ({format_currency(int(sum_assured * 0.25))}), Hand = 55% ({format_currency(int(sum_assured * 0.55))})"],
                ["How It Works", "Payout based on IRDAI schedule. Multiple disabilities claimable up to 100%"],
            ]
            s4_data_rows = [["SCENARIO 4: PARTIAL DISABILITY — PPD EXAMPLE", ""]] + s4_kv
            s4_table = Table(s4_data_rows, colWidths=[2.5*inch, 3.7*inch])
            s4_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), INFO_BLUE), ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
                ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD), ('SPAN', (0, 0), (-1, 0)),
                ('FONTSIZE', (0, 0), (-1, -1), 8), ('FONTNAME', (0, 1), (0, -1), FONT_BOLD),
                ('TEXTCOLOR', (0, 1), (0, -1), SLATE), ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
                ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
                ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(Spacer(1, 0.06*inch))
            elements.append(KeepTogether([s4_table]))

        # ==================================================================
        # PAGE 5: GAPS + ACTIONS + PORTFOLIO VIEW
        # ==================================================================
        elements.append(PageBreak())
        elements.append(create_section_header("Gaps & Your Action Plan", styles))
        elements.append(Spacer(1, 0.06*inch))

        # Coverage Strengths
        if v10_strengths:
            elements.append(create_subsection_header("Coverage Strengths"))
            strength_data = [["#", "Strength"]]
            for i, s in enumerate(v10_strengths[:5], 1):
                if isinstance(s, dict):
                    title = safe_str(s.get('title', s.get('label', str(s))))
                else:
                    title = safe_str(s)
                strength_data.append([str(i), title])

            strength_table = create_modern_table(strength_data, [0.5*inch, 5.7*inch], header_bg=SUCCESS_GREEN)
            elements.append(strength_table)
            elements.append(Spacer(1, 0.1*inch))

        # Gap Analysis Table
        # Filter to only dict gaps
        _valid_gaps = [g for g in v10_gap_list if isinstance(g, dict)] if v10_gap_list else []
        if _valid_gaps:
            gap_count = len(_valid_gaps)
            elements.append(create_subsection_header(f"Coverage Gaps ({gap_count} Found)"))

            _gap_cell_style = ParagraphStyle('GapCell', fontName=FONT_REGULAR, fontSize=7, textColor=SLATE, leading=9)
            gap_table_data = [["ID", "Severity", "Gap", "Impact", "Fix"]]
            for gap in _valid_gaps:
                gap_table_data.append([
                    safe_str(gap.get('gapId', '')),
                    safe_str(gap.get('severity', '')).upper(),
                    Paragraph(safe_str(gap.get('title', '')), _gap_cell_style),
                    Paragraph(safe_str(gap.get('impact', '')), _gap_cell_style),
                    Paragraph(safe_str(gap.get('solution', gap.get('fix', ''))), _gap_cell_style)
                ])

            gap_table = Table(gap_table_data, colWidths=[0.5*inch, 0.65*inch, 1.25*inch, 1.9*inch, 1.9*inch])
            gap_style_cmds = [
                ('BACKGROUND', (0, 0), (-1, 0), BRAND_DARK),
                ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
                ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('ALIGN', (0, 0), (1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
                ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ]
            for row_idx, gap in enumerate(_valid_gaps, 1):
                sev = gap.get('severity', 'low').lower()
                if sev == 'high':
                    gap_style_cmds.append(('TEXTCOLOR', (1, row_idx), (1, row_idx), GAP_HIGH))
                elif sev == 'medium':
                    gap_style_cmds.append(('TEXTCOLOR', (1, row_idx), (1, row_idx), GAP_MEDIUM))
                if row_idx % 2 == 0:
                    gap_style_cmds.append(('BACKGROUND', (0, row_idx), (-1, row_idx), WHISPER))
            gap_table.setStyle(TableStyle(gap_style_cmds))
            elements.append(gap_table)
            elements.append(Spacer(1, 0.1*inch))

        # Portfolio View (Health/Life/PA comparison matrix)
        portfolio_matrix = portfolio_view.get('matrix', [])
        if portfolio_matrix:
            elements.append(create_subsection_header("Portfolio View — Where PA Fits"))
            port_data = [["Risk", "Health", "Life", "PA"]]

            status_symbols = {
                'covered': 'Yes',
                'not_covered': 'No',
                'partial': 'Partial',
                'conditional': 'Conditional',
            }

            for row in portfolio_matrix:
                if not isinstance(row, dict):
                    continue
                port_data.append([
                    row.get('risk', ''),
                    status_symbols.get(row.get('health', ''), str(row.get('health', ''))),
                    status_symbols.get(row.get('life', ''), str(row.get('life', ''))),
                    status_symbols.get(row.get('pa', ''), str(row.get('pa', ''))),
                ])

            port_table = Table(port_data, colWidths=[2.0*inch, 1.2*inch, 1.2*inch, 1.8*inch])
            port_style_cmds = [
                ('BACKGROUND', (0, 0), (-1, 0), BRAND_PRIMARY),
                ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
                ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOX', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
                ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]
            # Color code cells
            for i in range(1, len(port_data)):
                for j in range(1, 4):
                    val = port_data[i][j].lower() if isinstance(port_data[i][j], str) else ''
                    if val == 'yes':
                        port_style_cmds.append(('TEXTCOLOR', (j, i), (j, i), PORTFOLIO_COVERED))
                        port_style_cmds.append(('FONTNAME', (j, i), (j, i), FONT_BOLD))
                    elif val == 'no':
                        port_style_cmds.append(('TEXTCOLOR', (j, i), (j, i), PORTFOLIO_NOT_COVERED))
                    elif val in ('partial', 'conditional'):
                        port_style_cmds.append(('TEXTCOLOR', (j, i), (j, i), PORTFOLIO_PARTIAL))
                if i % 2 == 0:
                    port_style_cmds.append(('BACKGROUND', (0, i), (-1, i), WHISPER))
            port_table.setStyle(TableStyle(port_style_cmds))
            elements.append(port_table)

            footer_note = portfolio_view.get('footerNote', '')
            if footer_note:
                elements.append(Spacer(1, 0.04*inch))
                elements.append(Paragraph(safe_str(footer_note), styles['muted_text']))
            elements.append(Spacer(1, 0.1*inch))

        # Priority Actions
        all_recs = quick_wins + priority_upgrades
        if all_recs:
            elements.append(create_subsection_header("Priority Actions"))

            rec_table_data = [["#", "Action", "Category", "Est. Cost", "EAZR EMI"]]
            for i, rec in enumerate(all_recs[:6], 1):
                if not isinstance(rec, dict):
                    continue
                est_cost = rec.get('estimatedCost', rec.get('annualCost', ''))
                if isinstance(est_cost, (int, float)) and est_cost > 0:
                    est_cost_str = format_currency(est_cost)
                else:
                    est_cost_str = safe_str(est_cost)
                emi = rec.get('monthlyEmi', '')
                if isinstance(emi, (int, float)) and emi > 0:
                    emi_str = f"{format_currency(emi)}/mo"
                elif rec.get('ipfEligible'):
                    emi_str = "Yes"
                else:
                    emi_str = "N/A"
                rec_table_data.append([
                    str(i),
                    safe_str(rec.get('title', '')),
                    safe_str(rec.get('category', '')).title(),
                    est_cost_str,
                    emi_str,
                ])

            rec_table = create_modern_table(
                rec_table_data,
                [0.4*inch, 2.4*inch, 1.0*inch, 1.2*inch, 1.2*inch],
                header_bg=BRAND_PRIMARY
            )
            elements.append(rec_table)

            # Investment summary
            if upgrade_annual > 0:
                elements.append(Spacer(1, 0.06*inch))
                inv_data = [
                    ["Total Annual Upgrade Cost", format_currency(upgrade_annual)],
                    ["EAZR EMI (Monthly)", format_currency(upgrade_monthly) + "/mo" if upgrade_monthly > 0 else "N/A"],
                ]
                inv_table = create_key_value_table(inv_data, [3.5*inch, 2.7*inch], accent_color=BRAND_PRIMARY)
                elements.append(inv_table)

            elements.append(Spacer(1, 0.06*inch))
            elements.append(Paragraph(
                "Finance your PA upgrade with EAZR IPF — pay in easy monthly EMIs.",
                styles['muted_text']
            ))

        # ==================================================================
        # PAGE 6: POLICY REFERENCE + BACK COVER
        # ==================================================================
        elements.append(PageBreak())
        elements.append(create_section_header("Policy Reference Snapshot", styles))
        elements.append(Spacer(1, 0.06*inch))

        # Core policy details
        ref_data = [
            ["Detail", "Value"],
            ["Insurer", insurer_name],
            ["Product", product_name],
            ["Policy Type", policy_sub_type],
            ["Policy Number", policy_number],
            ["Validity", f"{start_date[:10] if start_date != 'N/A' else 'N/A'} to {end_date[:10] if end_date != 'N/A' else 'N/A'}"],
            ["Sum Insured", format_currency(sum_assured)],
            ["AD Benefit", f"{format_currency(ad_benefit)} ({safe_int(ad.get('benefitPercentage'), 100)}% of SI)" + (" + Double Indemnity" if double_indemnity_applicable else "")],
            ["PTD Benefit", f"{format_currency(ptd_benefit)} ({safe_int(ptd.get('benefitPercentage'), 100)}% of SI)"],
            ["PPD", f"As per IRDAI schedule ({len(ppd.get('schedule', IRDAI_PPD_SCHEDULE))} conditions)"],
        ]

        if ttd_covered:
            ref_data.append(["TTD", f"{format_currency(ttd_benefit)}/wk | Max {ttd_max_weeks} weeks | {ttd_waiting}-day wait"])
        else:
            ref_data.append(["TTD", "Not Covered"])

        medical_covered = medical.get('covered', False)
        if medical_covered:
            ref_data.append(["Medical Expenses", f"{medical.get('limitPercentage', 0)}% of SI ({safe_str(medical.get('perAccidentOrAnnual', 'per_accident')).replace('_', ' ').title()})"])
        else:
            ref_data.append(["Medical Expenses", "Not Covered"])

        # Additional benefits
        benefit_labels = {
            'educationBenefit': 'Education Benefit',
            'loanEmiCover': 'Loan EMI Cover',
            'ambulanceCharges': 'Ambulance Charges',
            'homeModification': 'Home Modification',
            'vehicleModification': 'Vehicle Modification',
        }
        active_benefits = []
        for key, label in benefit_labels.items():
            ben = additional_benefits.get(key, {})
            if isinstance(ben, dict) and ben.get('covered'):
                active_benefits.append(label)
        if active_benefits:
            ref_data.append(["Additional Benefits", ", ".join(active_benefits)])

        # Premium
        base_prem = safe_int(premium_details.get('basePremium', 0))
        gst_amt = safe_int(premium_details.get('gstAmount') or premium_details.get('gst', 0))
        ref_data.append(["Premium", f"{format_currency(total_premium)} (Base: {format_currency(base_prem)} + GST: {format_currency(gst_amt)})"])

        # Exclusions summary
        std_exclusions = exclusions_data.get('standardExclusions', [])
        if std_exclusions:
            exc_preview = ", ".join(safe_str(str(e)[:80]) for e in std_exclusions[:2])
            if len(std_exclusions) > 2:
                exc_preview += f" + {len(std_exclusions) - 2} more"
            ref_data.append(["Key Exclusions", Paragraph(exc_preview, ParagraphStyle('ExcCell', fontName=FONT_REGULAR, fontSize=8, textColor=SLATE, leading=11))])

        ref_data.append(["Claim Helpline", claims_helpline])

        ref_table = create_modern_table(ref_data, [2.0*inch, 4.2*inch], header_bg=BRAND_PRIMARY)
        elements.append(ref_table)
        elements.append(Spacer(1, 0.2*inch))

        # EAZR Branding
        elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_PRIMARY, spaceAfter=8))
        elements.append(Paragraph(
            "<b>Finance your PA with EAZR IPF</b> — Split your premium into easy monthly EMIs.",
            ParagraphStyle('CTAText', fontName=FONT_BOLD, fontSize=10, textColor=BRAND_PRIMARY, alignment=TA_CENTER, spaceAfter=6)
        ))
        elements.append(Paragraph(
            "Contact: support@eazr.in | www.eazr.in",
            ParagraphStyle('ContactText', fontName=FONT_REGULAR, fontSize=9, textColor=MEDIUM_GRAY, alignment=TA_CENTER, spaceAfter=12)
        ))

        # Disclaimers
        elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_LIGHT, spaceAfter=8))
        elements.append(Paragraph(
            "<b>IMPORTANT DISCLAIMERS</b>",
            ParagraphStyle('DisclaimerTitle', fontName=FONT_BOLD, fontSize=8, textColor=SLATE, alignment=TA_CENTER, spaceAfter=6)
        ))

        disclaimers = [
            "This report is generated by EAZR's AI-powered Policy Intelligence engine for informational and educational purposes only.",
            "PPD (Permanent Partial Disability) percentages shown are per the IRDAI standard disability schedule. Actual disability assessment and percentage determination is done by the insurer's medical board at the time of claim. Actual payouts may differ.",
            "TTD (Temporary Total Disability) benefit calculations assume continuous disability for the stated duration. Actual benefit depends on medical certification of total disability and is subject to policy terms, waiting periods, and insurer approval.",
            "Income replacement calculations use user-provided annual income data. Actual income loss and financial needs vary by individual circumstances.",
            "Family financial need estimates in death scenarios use standard assumptions (6% inflation, 8% discount rate) and may not reflect actual requirements.",
            "The scores and ratings are proprietary to EAZR and do not represent any insurer's official assessment.",
            "EAZR IPF (Insurance Premium Financing) is subject to eligibility, minimum premium thresholds (Rs.5,000+), and applicable terms.",
            "For personalized insurance advice, consult a licensed insurance advisor or financial planner.",
        ]

        disc_style = ParagraphStyle(
            'DisclaimerItem', fontName=FONT_REGULAR, fontSize=6.5, textColor=LIGHT_GRAY,
            alignment=TA_JUSTIFY, leading=9, spaceBefore=2, spaceAfter=2
        )
        for i, disc in enumerate(disclaimers, 1):
            elements.append(Paragraph(f"{i}. {disc}", disc_style))

        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph(
            f"EAZR Digipayments Private Limited | Report ID: {report_id}",
            ParagraphStyle('Footer', fontName=FONT_REGULAR, fontSize=7, textColor=LIGHT_GRAY, alignment=TA_CENTER)
        ))

        # ==================== BUILD PDF ====================
        def on_first_page(canvas, doc):
            pass  # No header on cover page

        def on_later_pages(canvas, doc):
            ModernHeader.draw(canvas, doc)
            ModernFooter.draw(canvas, doc)

        pdf_doc.build(elements, onFirstPage=on_first_page, onLaterPages=on_later_pages)
        buffer.seek(0)
        return buffer

    except Exception as e:
        logger.error(f"Error generating PA V10 PDF report: {e}", exc_info=True)
        # Fallback: minimal report
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=50)
        styles_fallback = getSampleStyleSheet()
        elements_fallback = [
            Paragraph("EAZR Personal Accident Insurance Analysis", styles_fallback['Title']),
            Spacer(1, 12),
            Paragraph(f"Policy: {safe_str(str(policy_data.get('policyNumber', 'N/A')))} | Insurer: {safe_str(str(policy_data.get('insuranceProvider', 'N/A')))}", styles_fallback['Normal']),
            Paragraph(f"Sum Insured: {format_currency(policy_data.get('coverageAmount', 0))}", styles_fallback['Normal']),
            Paragraph(f"Protection Score: {analysis_data.get('protectionScore', 0)}/100", styles_fallback['Normal']),
            Spacer(1, 12),
            Paragraph("Full report could not be generated. Please contact support@eazr.in.", styles_fallback['Normal']),
        ]
        doc.build(elements_fallback)
        buffer.seek(0)
        return buffer
