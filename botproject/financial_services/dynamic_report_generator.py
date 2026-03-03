import os
from io import BytesIO
from datetime import datetime
import logging
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, PageBreak, KeepTogether, Flowable, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.colors import HexColor
from reportlab.graphics.shapes import Drawing, Rect, Circle, Line, Path, Polygon, String
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)

# Modern color palette
COLORS = {
    'primary': HexColor('#6366F1'),       # Indigo
    'primary_light': HexColor('#A5B4FC'),   
    'primary_dark': HexColor('#4F46E5'),   
    'secondary': HexColor('#8B5CF6'),     # Purple
    'success': HexColor('#10B981'),       # Emerald
    'success_light': HexColor('#6EE7B7'),
    'warning': HexColor('#F59E0B'),       # Amber
    'warning_light': HexColor('#FCD34D'),
    'danger': HexColor('#EF4444'),        # Red
    'danger_light': HexColor('#FCA5A5'),
    'info': HexColor('#06B6D4'),          # Cyan
    'info_light': HexColor('#67E8F9'),
    'dark': HexColor('#111827'),          # Gray 900
    'gray': HexColor('#6B7280'),          # Gray 500
    'light': HexColor('#F3F4F6'),         # Gray 100
    'white': HexColor('#FFFFFF'),
    'bg_card': HexColor('#FAFAFA'),
    'border': HexColor('#E5E7EB')
}

class ModernHeader(Flowable):
    """Custom header with gradient effect"""
    def __init__(self, width, height, title, subtitle):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.title = title
        self.subtitle = subtitle
    
    def draw(self):
        # Draw gradient background
        steps = 30
        for i in range(steps):
            ratio = i / steps
            # Interpolate between primary and secondary colors
            r = int(0.39 + (0.55 - 0.39) * ratio)
            g = int(0.40 + (0.36 - 0.40) * ratio) 
            b = int(0.95 + (0.96 - 0.95) * ratio)
            
            y_pos = self.height * (1 - i/steps)
            self.canv.setFillColorRGB(r, g, b)
            self.canv.rect(0, y_pos, self.width, self.height/steps + 1, stroke=0, fill=1)
        
        # Add decorative circles
        self.canv.setFillColor(COLORS['white'])
        self.canv.setFillAlpha(0.1)
        self.canv.circle(self.width * 0.1, self.height * 0.7, 40, stroke=0, fill=1)
        self.canv.circle(self.width * 0.85, self.height * 0.3, 60, stroke=0, fill=1)
        self.canv.setFillAlpha(1)
        
        # Draw title
        self.canv.setFont("Helvetica-Bold", 28)
        self.canv.setFillColor(COLORS['white'])
        self.canv.drawCentredString(self.width/2, self.height - 35, self.title)
        
        # Draw subtitle
        self.canv.setFont("Helvetica", 14)
        self.canv.drawCentredString(self.width/2, self.height - 55, self.subtitle)

class ScoreCard(Flowable):
    """Modern score card with circular progress"""
    def __init__(self, width, height, score, verdict, color):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.score = score
        self.verdict = verdict
        self.color = color
    
    def draw(self):
        # Draw card background
        self.canv.setFillColor(COLORS['white'])
        self.canv.setStrokeColor(COLORS['border'])
        self.canv.roundRect(0, 0, self.width, self.height, 10, stroke=1, fill=1)
        
        # Draw shadow
        self.canv.setFillColor(COLORS['gray'])
        self.canv.setFillAlpha(0.1)
        self.canv.roundRect(2, -2, self.width, self.height, 10, stroke=0, fill=1)
        self.canv.setFillAlpha(1)
        
        # Circular progress
        cx = self.width * 0.3
        cy = self.height * 0.5
        radius = min(self.width, self.height) * 0.25
        
        # Background circle
        self.canv.setStrokeColor(COLORS['light'])
        self.canv.setLineWidth(12)
        self.canv.circle(cx, cy, radius, stroke=1, fill=0)
        
        # Progress arc
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(12)
        self.canv.setLineCap(1)  # Round line caps
        
        # Calculate angle for score
        angle = 360 * (self.score / 100)
        path = self.canv.beginPath()
        path.arc(cx - radius, cy - radius, cx + radius, cy + radius, 90, 90 - angle)
        self.canv.drawPath(path, stroke=1, fill=0)
        
        # Score text in center
        self.canv.setFont("Helvetica-Bold", 24)
        self.canv.setFillColor(COLORS['dark'])
        self.canv.drawCentredString(cx, cy - 8, f"{int(self.score)}")
        self.canv.setFont("Helvetica", 10)
        self.canv.setFillColor(COLORS['gray'])
        self.canv.drawCentredString(cx, cy - 25, "SCORE")
        
        # Verdict text
        self.canv.setFont("Helvetica-Bold", 22)
        self.canv.setFillColor(self.color)
        self.canv.drawString(self.width * 0.55, cy + 15, self.verdict)
        
        # Rating stars
        star_y = cy - 10
        for i in range(5):
            star_x = self.width * 0.55 + (i * 20)
            if i < int(self.score / 20):
                self.canv.setFillColor(COLORS['warning'])
                star = ''
            else:
                self.canv.setFillColor(COLORS['light'])
                star = ''
            self.canv.setFont("Helvetica", 16)
            self.canv.drawString(star_x, star_y, star)

def get_rating_text(score):
    """Get rating text based on score"""
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Fair"
    else:
        return "Poor"

def get_rating_color(score):
    """Get color based on score"""
    if score >= 80:
        return COLORS['success']
    elif score >= 60:
        return COLORS['primary']
    elif score >= 40:
        return COLORS['warning']
    else:
        return COLORS['danger']

def create_styles():
    """Create custom paragraph styles"""
    styles = {}
    base_styles = getSampleStyleSheet()
    
    styles['title'] = ParagraphStyle(
        'ModernTitle',
        parent=base_styles['Heading1'],
        fontSize=28,
        textColor=COLORS['dark'],
        spaceAfter=15,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    styles['subtitle'] = ParagraphStyle(
        'ModernSubtitle',
        parent=base_styles['Normal'],
        fontSize=14,
        textColor=COLORS['gray'],
        spaceAfter=25,
        alignment=TA_LEFT
    )
    
    styles['section'] = ParagraphStyle(
        'SectionHeader',
        parent=base_styles['Heading2'],
        fontSize=18,
        textColor=COLORS['primary'],
        spaceAfter=15,
        spaceBefore=25,
        fontName='Helvetica-Bold',
        borderColor=COLORS['primary'],
        borderWidth=0,
        borderPadding=0,
        leftIndent=0
    )
    
    styles['body'] = ParagraphStyle(
        'BodyText',
        parent=base_styles['Normal'],
        fontSize=11,
        textColor=COLORS['dark'],
        spaceAfter=10,
        alignment=TA_LEFT,
        leading=16
    )
    
    styles['card_text'] = ParagraphStyle(
        'CardText',
        parent=base_styles['Normal'],
        fontSize=12,
        textColor=COLORS['dark'],
        alignment=TA_LEFT
    )
    
    styles['footer'] = ParagraphStyle(
        'FooterStyle',
        parent=base_styles['Normal'],
        fontSize=9,
        textColor=COLORS['gray'],
        alignment=TA_CENTER,
        spaceBefore=30
    )
    
    return styles

def create_score_bars_chart(scores):
    """Create horizontal bar chart for scores"""
    drawing = Drawing(450, 200)
    
    # Add background
    bg = Rect(0, 0, 450, 200,
             fillColor=COLORS['bg_card'],
             strokeColor=None,
             rx=5, ry=5)
    drawing.add(bg)
    
    categories = [
        ('Coverage Adequacy', scores.get('coverage_adequacy', 0)),
        ('Pricing Value', scores.get('pricing', 0)),
        ('Benefits Quality', scores.get('benefits', 0)),
        ('Company Rating', scores.get('company', 0))
    ]
    
    y_pos = 150
    bar_height = 25
    
    for cat, score in categories:
        # Category label
        label = String(10, y_pos + 8, cat,
                      fontSize=11,
                      fontName='Helvetica',
                      fillColor=COLORS['dark'])
        drawing.add(label)
        
        # Background bar
        bg_bar = Rect(150, y_pos, 250, bar_height,
                     fillColor=COLORS['light'],
                     strokeColor=None,
                     rx=3, ry=3)
        drawing.add(bg_bar)
        
        # Score bar
        bar_width = (score / 100) * 250
        bar_color = get_rating_color(score)
        score_bar = Rect(150, y_pos, bar_width, bar_height,
                        fillColor=bar_color,
                        strokeColor=None,
                        rx=3, ry=3)
        drawing.add(score_bar)
        
        # Score text
        score_text = String(410, y_pos + 8, f"{score:.0f}%",
                          fontSize=11,
                          fontName='Helvetica-Bold',
                          fillColor=bar_color)
        drawing.add(score_text)
        
        y_pos -= 40
    
    return drawing

def create_premium_comparison(your_premium, market_avg):
    """Create premium comparison visualization"""
    drawing = Drawing(450, 180)
    
    # Background
    bg = Rect(0, 0, 450, 180,
             fillColor=COLORS['white'],
             strokeColor=COLORS['border'],
             rx=5, ry=5)
    drawing.add(bg)
    
    max_val = max(your_premium, market_avg) * 1.1
    if max_val == 0:
        max_val = 1
    
    # Your premium
    bar1_height = (your_premium / max_val) * 120
    bar1_color = COLORS['danger'] if your_premium > market_avg else COLORS['success']
    
    bar1 = Rect(120, 30, 80, bar1_height,
               fillColor=bar1_color,
               strokeColor=None,
               rx=3, ry=3)
    drawing.add(bar1)
    
    # Market average
    bar2_height = (market_avg / max_val) * 120
    bar2 = Rect(250, 30, 80, bar2_height,
               fillColor=COLORS['primary'],
               strokeColor=None,
               rx=3, ry=3)
    drawing.add(bar2)
    
    # Labels
    label1 = String(160, 15, 'Your Premium',
                   textAnchor='middle',
                   fontSize=11,
                   fontName='Helvetica')
    drawing.add(label1)
    
    label2 = String(290, 15, 'Market Average',
                   textAnchor='middle',
                   fontSize=11,
                   fontName='Helvetica')
    drawing.add(label2)
    
    # Values
    val1 = String(160, 35 + bar1_height + 5, f'{your_premium:,.0f}',
                 textAnchor='middle',
                 fontSize=13,
                 fontName='Helvetica-Bold',
                 fillColor=bar1_color)
    drawing.add(val1)
    
    val2 = String(290, 35 + bar2_height + 5, f'{market_avg:,.0f}',
                 textAnchor='middle',
                 fontSize=13,
                 fontName='Helvetica-Bold',
                 fillColor=COLORS['primary'])
    drawing.add(val2)
    
    # Difference indicator
    if your_premium != market_avg:
        diff = abs(your_premium - market_avg)
        diff_text = f"{'Saving' if your_premium < market_avg else 'Overpaying'}: {diff:,.0f}"
        diff_color = COLORS['success'] if your_premium < market_avg else COLORS['danger']
        
        diff_label = String(225, 160, diff_text,
                          textAnchor='middle',
                          fontSize=12,
                          fontName='Helvetica-Bold',
                          fillColor=diff_color)
        drawing.add(diff_label)
    
    return drawing

def create_info_card(title, items, icon=""):
    """Create an information card table"""
    # Prepare data with icon in header
    data = [[f'{icon} {title}']]
    
    for key, value in items:
        data.append([key, value])
    
    table = Table(data, colWidths=[3*inch, 3.5*inch])
    
    style = TableStyle([
        # Header
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary']),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLORS['white']),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Body
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('TEXTCOLOR', (0, 1), (0, -1), COLORS['gray']),
        ('TEXTCOLOR', (1, 1), (1, -1), COLORS['dark']),
        ('BACKGROUND', (0, 1), (-1, -1), COLORS['white']),
        ('GRID', (0, 1), (-1, -1), 0.5, COLORS['border']),
        ('LEFTPADDING', (0, 1), (-1, -1), 12),
        ('RIGHTPADDING', (0, 1), (-1, -1), 12),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
        
        # Outer border
        ('BOX', (0, 0), (-1, -1), 1, COLORS['border']),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ])
    
    table.setStyle(style)
    return table

def generate_health_insurance_section(data, story, styles):
    """Generate health insurance specific sections"""
    
    # Members Section
    members = data.get('analysis_data', {}).get('members', [])
    if members:
        member_items = []
        total_coverage = data.get('coverage_amount', 1000000)
        per_person = total_coverage / len(members) if members else total_coverage
        
        for member in members:
            member_items.append([
                member.get('name', 'N/A'),
                f"{member.get('age', 'N/A')} yrs  {per_person:,.0f} coverage"
            ])
        
        members_card = create_info_card("Insured Members", member_items, "")
        story.append(members_card)
        story.append(Spacer(1, 20))
    
    # Coverage Analysis
    coverage_amt = data.get('coverage_amount', 1000000)
    member_count = len(members) if members else 1
    per_person_coverage = coverage_amt / member_count
    
    if per_person_coverage < 500000:
        status = " Inadequate"
        color = COLORS['danger']
    elif per_person_coverage < 1000000:
        status = " Basic"
        color = COLORS['warning']
    else:
        status = " Good"
        color = COLORS['success']
    
    coverage_items = [
        ['Total Sum Insured', f"{coverage_amt:,.0f}"],
        ['Per Person Coverage', f"{per_person_coverage:,.0f}"],
        ['Coverage Status', status]
    ]
    
    coverage_card = create_info_card("Coverage Analysis", coverage_items, "")
    story.append(coverage_card)
    story.append(Spacer(1, 20))

def generate_auto_insurance_section(data, story, styles):
    """Generate auto insurance specific sections"""
    
    analysis_data = data.get('analysis_data', {})
    
    vehicle_items = [
        ['Registration', analysis_data.get('registration', 'N/A')],
        ['Make & Model', analysis_data.get('vehicle_make_model', 'N/A')],
        ['IDV Value', f"{analysis_data.get('idv', 0):,.0f}"],
        ['NCB Discount', f"{analysis_data.get('ncb_percentage', 0)}%"]
    ]
    
    vehicle_card = create_info_card("Vehicle Information", vehicle_items, "")
    story.append(vehicle_card)
    story.append(Spacer(1, 20))

def generate_life_insurance_section(data, story, styles):
    """Generate life insurance specific sections"""
    
    analysis_data = data.get('analysis_data', {})
    
    policy_items = [
        ['Sum Assured', f"{analysis_data.get('sum_assured', 0):,.0f}"],
        ['Policy Term', f"{analysis_data.get('policy_term', 'N/A')} years"],
        ['Premium Term', f"{analysis_data.get('premium_paying_term', 'N/A')} years"],
        ['Nominee', analysis_data.get('nominee', 'N/A')]
    ]
    
    policy_card = create_info_card("Policy Details", policy_items, "")
    story.append(policy_card)
    story.append(Spacer(1, 20))

def generate_modern_insurance_report(analysis_data):
    """Main function to generate PDF report"""
    
    try:
        buffer = BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Get custom styles
        styles = create_styles()
        
        story = []
        
        # Modern header
        insurance_type = analysis_data.get('insurance_type', 'Insurance').title()
        header = ModernHeader(7*inch, 1.2*inch, 
                             f"{insurance_type} Insurance Analysis",
                             "AI-Powered Policy Evaluation Report")
        story.append(header)
        story.append(Spacer(1, 30))
        
        # Score card
        score = analysis_data.get('recommendation_score', 0)
        verdict = analysis_data.get('verdict', 'UNKNOWN')
        verdict_color = get_rating_color(score)
        
        score_card = ScoreCard(7*inch, 2*inch, score, verdict, verdict_color)
        story.append(score_card)
        story.append(Spacer(1, 15))
        
        # Verdict explanation
        if analysis_data.get('verdict_explanation'):
            exp_text = f'<para alignment="center"><font color="{COLORS["gray"].hexval()}">{analysis_data["verdict_explanation"]}</font></para>'
            story.append(Paragraph(exp_text, styles['body']))
            story.append(Spacer(1, 25))
        
        # Policy Overview
        overview_items = [
            ['Company', analysis_data.get('company_name', 'Unknown')],
            ['Policy Number', analysis_data.get('policy_number', 'N/A')],
            ['Annual Premium', f"{analysis_data.get('premium_amount', 0):,.0f}"],
            ['Coverage Amount', f"{analysis_data.get('coverage_amount', 0):,.0f}"]
        ]
        
        overview_card = create_info_card("Policy Overview", overview_items, "")
        story.append(overview_card)
        story.append(Spacer(1, 25))
        
        # Premium Analysis
        story.append(Paragraph('<b>Premium Analysis</b>', styles['section']))
        
        market_comp = analysis_data.get('market_comparison', {})
        your_premium = market_comp.get('your_premium', 0)
        market_avg = market_comp.get('market_average', 0)
        
        premium_chart = create_premium_comparison(your_premium, market_avg)
        story.append(premium_chart)
        story.append(Spacer(1, 20))
        
        # Alert if overpriced
        is_overpriced = analysis_data.get('is_overpriced', False)
        if is_overpriced:
            alert_text = f'<para alignment="center"><font color="{COLORS["danger"].hexval()}" size="12"><b> Alert: You are overpaying by {abs(market_comp.get("difference", 0)):,.0f} annually!</b></font></para>'
            
            alert_data = [[Paragraph(alert_text, styles['body'])]]
            alert_table = Table(alert_data, colWidths=[6.5*inch])
            alert_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor('#FEF2F2')),
                ('BOX', (0, 0), (-1, -1), 2, COLORS['danger']),
                ('TOPPADDING', (0, 0), (-1, -1), 15),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER')
            ]))
            story.append(alert_table)
            story.append(Spacer(1, 20))
        
        # Detailed Scores
        story.append(Paragraph('<b>Detailed Assessment</b>', styles['section']))
        
        scores = analysis_data.get('detailed_scores', {})
        score_chart = create_score_bars_chart(scores)
        story.append(score_chart)
        story.append(Spacer(1, 25))
        
        # Type-specific sections
        insurance_type_lower = analysis_data.get('insurance_type', '').lower()
        if insurance_type_lower == 'health':
            generate_health_insurance_section(analysis_data, story, styles)
        elif insurance_type_lower == 'auto':
            generate_auto_insurance_section(analysis_data, story, styles)
        elif insurance_type_lower == 'life':
            generate_life_insurance_section(analysis_data, story, styles)
        
        # Key Findings & Issues
        key_findings = analysis_data.get('key_findings', [])
        issues = analysis_data.get('issues', [])
        
        if key_findings or issues:
            story.append(Paragraph('<b>Key Insights</b>', styles['section']))
            
            insights_data = []
            for finding in key_findings:
                insights_data.append([Paragraph(f'<font color="{COLORS["success"].hexval()}">{finding}</font>', styles['body'])])
            for issue in issues:
                insights_data.append([Paragraph(f'<font color="{COLORS["warning"].hexval()}">{issue}</font>', styles['body'])])
            
            if insights_data:
                insights_table = Table(insights_data, colWidths=[6.5*inch])
                insights_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), COLORS['bg_card']),
                    ('BOX', (0, 0), (-1, -1), 0.5, COLORS['border']),
                    ('LEFTPADDING', (0, 0), (-1, -1), 15),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
                ]))
                story.append(insights_table)
                story.append(Spacer(1, 20))
        
        # Recommendations
        suggestions = analysis_data.get('suggestions', [])
        if suggestions:
            story.append(Paragraph('<b>Recommendations</b>', styles['section']))
            
            for i, suggestion in enumerate(suggestions, 1):
                rec_text = f'<para><b>{i}.</b> {suggestion}</para>'
                rec_data = [[Paragraph(rec_text, styles['body'])]]
                
                rec_table = Table(rec_data, colWidths=[6.5*inch])
                rec_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#EFF6FF')),
                    ('BOX', (0, 0), (-1, -1), 1, COLORS['primary_light']),
                    ('LEFTPADDING', (0, 0), (-1, -1), 15),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10)
                ]))
                story.append(rec_table)
                story.append(Spacer(1, 8))
            
            story.append(Spacer(1, 15))
        
        # Better Alternatives
        alternatives = analysis_data.get('alternatives', [])
        if alternatives:
            story.append(Paragraph('<b>Better Alternatives</b>', styles['section']))
            
            alt_data = [['Provider', 'Premium', 'Key Benefits', 'Savings']]
            for alt in alternatives[:3]:
                benefits = alt.get('benefits', 'N/A')
                if len(benefits) > 40:
                    benefits = benefits[:40] + '...'
                
                alt_data.append([
                    alt.get('provider', 'N/A'),
                    f"{alt.get('premium', 0):,.0f}",
                    benefits,
                    f"{alt.get('annual_savings', 0):,.0f}/yr"
                ])
            
            alt_table = Table(alt_data, colWidths=[1.8*inch, 1.2*inch, 2.3*inch, 1.2*inch])
            alt_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), COLORS['info']),
                ('TEXTCOLOR', (0, 0), (-1, 0), COLORS['white']),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, COLORS['border']),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLORS['white'], COLORS['bg_card']]),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ('ALIGN', (3, 0), (3, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10)
            ]))
            story.append(alt_table)
            story.append(Spacer(1, 20))
        
        # Footer
        story.append(Spacer(1, 30))
        
        # Decorative line
        line_drawing = Drawing(500, 10)
        decorative_line = Line(0, 5, 500, 5,
                              strokeColor=COLORS['primary'],
                              strokeWidth=1,
                              strokeDashArray=[3, 3])
        line_drawing.add(decorative_line)
        story.append(line_drawing)
        
        footer_text = f'''
        <para alignment="center">
            <font size="9" color="{COLORS['gray'].hexval()}">
            Report Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>
            <font size="8">This AI-powered analysis is for informational purposes only.
            Please consult with a qualified insurance advisor before making any decisions.</font>
            </font>
        </para>
        '''
        story.append(Paragraph(footer_text, styles['footer']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        logger.info("Modern PDF generated successfully")
        return buffer
        
    except Exception as e:
        logger.error(f"PDF generation error: {str(e)}")
        raise Exception(f"Failed to generate PDF: {str(e)}")

# Wrapper function for compatibility
def generate_universal_insurance_report(analysis_data):
    """Wrapper function for API compatibility"""
    return generate_modern_insurance_report(analysis_data)