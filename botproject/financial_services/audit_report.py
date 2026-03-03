import sys
import os
from io import BytesIO
from datetime import datetime
import json
import logging

# Error handling for missing dependencies
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.graphics.shapes import Drawing, Rect, Circle
    from reportlab.graphics.charts.piecharts import Pie
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics import renderPDF
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Please install required packages: pip install reportlab matplotlib")
    sys.exit(1)

logger = logging.getLogger(__name__)

def create_insurance_analysis_pdf(analysis_data: dict) -> BytesIO:
    """
    Create a professionally designed PDF report from insurance analysis data
    
    Args:
        analysis_data (dict): The analysis response from the insurance analyzer
        
    Returns:
        BytesIO: PDF file buffer ready for download
    """
    
    # Create PDF buffer
    buffer = BytesIO()
    
    # Create document with custom page size and margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=1*inch,
        title=f"Insurance Policy Analysis Report"
    )
    
    # Get styles and create custom styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#3b82f6'),
        spaceAfter=20,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=12,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#374151'),
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )
    
    highlight_style = ParagraphStyle(
        'Highlight',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#059669'),
        spaceAfter=10,
        fontName='Helvetica-Bold',
        backColor=colors.HexColor('#ecfdf5'),
        borderColor=colors.HexColor('#10b981'),
        borderWidth=1,
        borderPadding=8
    )
    
    # Story container for all elements
    story = []
    
    # ==================== HEADER SECTION ====================
    
    # Main title
    insurance_type = analysis_data.get('insurance_type', 'unknown').lower()
    insurance_type_display = insurance_type.title()

    framework_map = {
        'auto': 'AIPS - Auto Insurance Protection Score',
        'health': 'HIPS - Health Insurance Protection Score',
        'life': 'LIPS - Life Insurance Protection Score'
    }
    framework_name = framework_map.get(insurance_type, 'Insurance Protection Score')

    story.append(Paragraph(f"{framework_name}", title_style))
    story.append(Paragraph("Comprehensive Policy Analysis Report", subtitle_style))

    # Report metadata table
    extraction_confidence = analysis_data.get('extraction_confidence',
                                             analysis_data.get('extraction_info', {}).get('confidence', 85))

    metadata_data = [
        ['Report Generated', datetime.now().strftime('%B %d, %Y at %I:%M %p')],
        ['Analysis Framework', framework_name],
        ['Extraction Confidence', f"{extraction_confidence}%"],
        ['Insurance Type', insurance_type_display + ' Insurance']
    ]
    
    metadata_table = Table(metadata_data, colWidths=[2.5*inch, 3.5*inch])
    metadata_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1f2937')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#059669')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
    ]))
    
    story.append(metadata_table)
    story.append(Spacer(1, 20))
    
    # ==================== SCORE OVERVIEW SECTION ====================
    
    story.append(Paragraph(" Overall Protection Score", subtitle_style))
    
    # Score highlight box
    total_score = analysis_data.get('total_score', 0)
    protection_level = analysis_data.get('protection_level', 'Unknown')
    
    score_color = colors.HexColor('#dc2626')  # Red
    if total_score >= 90:
        score_color = colors.HexColor('#059669')  # Green
    elif total_score >= 75:
        score_color = colors.HexColor('#0891b2')  # Blue
    elif total_score >= 60:
        score_color = colors.HexColor('#ca8a04')  # Yellow
    elif total_score >= 45:
        score_color = colors.HexColor('#ea580c')  # Orange
    
    score_text = f"""
    <para alignment="center" spaceBefore="10" spaceAfter="15">
        <font size="36" color="{score_color.hexval()}"><b>{total_score}/100</b></font><br/><br/><br/>
        <font size="16" color="#1f2937"><b>{protection_level}</b></font><br/><br/><br/>
        <font size="12" color="#6b7280">{analysis_data.get('general_recommendation', '')}</font>
    </para>
    """
    
    story.append(Paragraph(score_text, body_style))
    story.append(Spacer(1, 20))
    
    # ==================== CATEGORY BREAKDOWN ====================
    
    story.append(Paragraph(" Category-wise Score Breakdown", subtitle_style))
    
    # Category scores table
    category_scores = analysis_data.get('category_scores', {})
    category_data = [['Category', 'Score', 'Performance', 'Status']]
    
    for category, score in category_scores.items():
        # Format category name
        formatted_category = category.replace('_', ' ').title()
        
        # Determine performance level
        if score >= 90:
            performance = "Excellent"
            status_color = colors.HexColor('#059669')
            status = " Strong"
        elif score >= 75:
            performance = "Very Good"
            status_color = colors.HexColor('#0891b2')
            status = " Good"
        elif score >= 60:
            performance = "Good"
            status_color = colors.HexColor('#ca8a04')
            status = " Fair"
        elif score >= 45:
            performance = "Fair"
            status_color = colors.HexColor('#ea580c')
            status = " Weak"
        else:
            performance = "Poor"
            status_color = colors.HexColor('#dc2626')
            status = " Poor"
        
        category_data.append([
            formatted_category,
            f"{score}",
            performance,
            status
        ])
    
    category_table = Table(category_data, colWidths=[2.2*inch, 0.8*inch, 1.2*inch, 1.2*inch])
    category_table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        
        # Data rows styling
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1f2937')),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        
        # Grid and borders
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
    ]))
    
    story.append(category_table)
    story.append(Spacer(1, 25))
    
    # ==================== POLICY INFORMATION ====================
    
    story.append(Paragraph(" Policy Information", subtitle_style))
    
    policy_info = analysis_data.get('policy_info', {})
    user_info = analysis_data.get('user_info', {})
    
    # Policy details table
    if insurance_type.lower() == 'health':
        policy_details = [
            ['Policy Details', 'Value'],
            ['Insurance Company', policy_info.get('insurer_name', 'N/A')],
            ['Sum Insured', f"{policy_info.get('sum_insured', 0):,.0f}" if policy_info.get('sum_insured') else 'N/A'],
            ['Annual Premium', f"{policy_info.get('annual_premium', 0):,.0f}" if policy_info.get('annual_premium') else 'N/A'],
            ['Room Rent Limit', policy_info.get('room_rent_limit', 'Not specified') or 'Not specified'],
            ['Daycare Procedures', str(policy_info.get('daycare_procedures', 0)) if policy_info.get('daycare_procedures') else 'Not covered'],
            ['Waiting Period', f"{policy_info.get('waiting_period', 'N/A')} years" if policy_info.get('waiting_period', 0) > 0 else 'No waiting period'],
            ['Co-payment', f"{policy_info.get('copayment', 0)}%" if policy_info.get('copayment') else 'No co-payment'],
            ['Ambulance Coverage', f"{policy_info.get('ambulance_coverage', 0):,.0f}" if policy_info.get('ambulance_coverage') else 'Not covered']
        ]
    elif insurance_type.lower() == 'auto':
        policy_details = [
            ['Policy Details', 'Value'],
            ['Insurance Company', policy_info.get('insurer_name', 'N/A')],
            ['IDV Amount', f"{policy_info.get('idv_amount', 0):,.0f}" if policy_info.get('idv_amount') else 'N/A'],
            ['Annual Premium', f"{policy_info.get('annual_premium', 0):,.0f}" if policy_info.get('annual_premium') else 'N/A'],
            ['Vehicle Make & Model', f"{policy_info.get('vehicle_make', '')} {policy_info.get('vehicle_model', '')}".strip() or 'N/A'],
            ['Vehicle Age', f"{policy_info.get('vehicle_age', 0)} years" if policy_info.get('vehicle_age') else 'N/A'],
            ['Registration Number', policy_info.get('registration_number', 'N/A')],
            ['Zero Depreciation', policy_info.get('zero_depreciation', 'Not available') or 'Not available'],
            ['Engine Protection', policy_info.get('engine_protection', 'Not available') or 'Not available'],
            ['PA Coverage', f"{policy_info.get('pa_coverage', 0)*100000:,.0f}" if policy_info.get('pa_coverage') else 'Not covered'],
            ['Roadside Assistance', policy_info.get('roadside_assistance', 'Not available') or 'Not available'],
            ['NCB Protection', policy_info.get('ncb_protection', 'Not available') or 'Not available']
        ]
    elif insurance_type.lower() == 'life':
        policy_details = [
            ['Policy Details', 'Value'],
            ['Insurance Company', policy_info.get('insurer_name', 'N/A')],
            ['Sum Assured', f"{policy_info.get('sum_assured', 0):,.0f}" if policy_info.get('sum_assured') else 'N/A'],
            ['Annual Income', f"{policy_info.get('annual_income', 0):,.0f}" if policy_info.get('annual_income') else 'N/A'],
            ['Income Multiple', f"{policy_info.get('income_multiple', 0)}x" if policy_info.get('income_multiple') else 'N/A'],
            ['Policy Type', policy_info.get('policy_type', 'N/A').title()],
            ['Coverage Duration', policy_info.get('coverage_duration', 'N/A').replace('_', ' ').title()],
            ['Accidental Death Benefit', f"{policy_info.get('accidental_death_multiplier', 0)}x base cover" if policy_info.get('accidental_death_multiplier') else 'Not available'],
            ['Critical Illness Rider', policy_info.get('critical_illness_rider', 'Not available').replace('_', ' ').title()],
            ['Terminal Illness Coverage', policy_info.get('terminal_illness_coverage', 'Not available').replace('_', ' ').title()],
            ['Disability Coverage', policy_info.get('disability_coverage', 'Not available').replace('_', ' ').title()],
            ['Waiver of Premium', policy_info.get('waiver_of_premium', 'Not available').replace('_', ' ').title()]
        ]
    else:
        # Default policy details for unknown types
        policy_details = [
            ['Policy Details', 'Value'],
            ['Insurance Company', policy_info.get('insurer_name', 'N/A')],
            ['Policy Number', policy_info.get('policy_number', 'N/A')],
            ['Premium Amount', f"{policy_info.get('annual_premium', 0):,.0f}" if policy_info.get('annual_premium') else 'N/A']
        ]
    
    policy_table = Table(policy_details, colWidths=[2.5*inch, 3.5*inch])
    policy_table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        
        # Data rows
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f1f5f9')),
        ('BACKGROUND', (1, 1), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor('#1f2937')),
        ('TEXTCOLOR', (1, 1), (1, -1), colors.HexColor('#059669')),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    
    story.append(policy_table)
    story.append(Spacer(1, 25))
    
    # ==================== USER INFORMATION ====================
    
    story.append(Paragraph(" Policyholder Information", subtitle_style))
    
    user_details = [
        ['Personal Details', 'Information'],
        ['Name', user_info.get('name', 'N/A')],
        ['Age', f"{user_info.get('age', 'N/A')} years" if user_info.get('age') else 'N/A'],
        ['Date of Birth', user_info.get('date_of_birth', 'N/A')],
        ['Policy Number', user_info.get('policy_number', 'N/A')],
        ['Mobile Number', user_info.get('mobile_number', 'N/A')],
        ['Email ID', user_info.get('email_id', 'N/A')]
    ]
    
    # Add insurance-specific fields
    if insurance_type.lower() == 'health':
        user_details.append(['Family Size', f"{user_info.get('family_count', 1)} member(s)"])
        if user_info.get('aadhar_number'):
            user_details.append(['Aadhar Number', user_info.get('aadhar_number')])
        if user_info.get('pan_number'):
            user_details.append(['PAN Number', user_info.get('pan_number')])
    elif insurance_type.lower() == 'auto':
        if user_info.get('manufacturing_year'):
            user_details.append(['Vehicle Year', str(user_info.get('manufacturing_year'))])
        if user_info.get('fuel_type'):
            user_details.append(['Fuel Type', user_info.get('fuel_type').title()])
        if user_info.get('license_number'):
            user_details.append(['License Number', user_info.get('license_number')])
        if user_info.get('aadhar_number'):
            user_details.append(['Aadhar Number', user_info.get('aadhar_number')])
        if user_info.get('pan_number'):
            user_details.append(['PAN Number', user_info.get('pan_number')])
    elif insurance_type.lower() == 'life':
        if user_info.get('gender'):
            user_details.append(['Gender', user_info.get('gender').title()])
        if user_info.get('life_stage'):
            user_details.append(['Life Stage', user_info.get('life_stage', '').replace('_', ' ').title()])
        if user_info.get('smoking_status'):
            user_details.append(['Smoking Status', user_info.get('smoking_status').title()])
        if user_info.get('occupation'):
            user_details.append(['Occupation', user_info.get('occupation').title()])
        if user_info.get('annual_income'):
            user_details.append(['Annual Income', f"{user_info.get('annual_income', 0):,.0f}"])
        if user_info.get('nominee_details'):
            nominee = user_info.get('nominee_details', {})
            if isinstance(nominee, dict) and nominee.get('name'):
                user_details.append(['Nominee', nominee.get('name')])
            elif isinstance(nominee, str):
                user_details.append(['Nominee', nominee])
    
    user_table = Table(user_details, colWidths=[2.5*inch, 3.5*inch])
    user_table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        
        # Data rows
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#ecfdf5')),
        ('BACKGROUND', (1, 1), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1f2937')),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#a7f3d0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')])
    ]))
    
    story.append(user_table)
    story.append(Spacer(1, 25))
    
    # ==================== DETAILED ANALYSIS ====================
    
    story.append(Paragraph(" Detailed Score Analysis", subtitle_style))
    
    # Create detailed breakdown
    max_scores_map = {
        'auto': {
            'vehicle_protection': 40,
            'personal_protection': 15,
            'third_party_coverage': 20,
            'additional_benefits': 15,
            'cost_efficiency': 10
        },
        'health': {
            'coverage_adequacy': 35,
            'waiting_periods': 20,
            'additional_benefits': 20,
            'service_quality': 15,
            'cost_efficiency': 10
        },
        'life': {
            'coverage_adequacy': 40,
            'policy_structure': 25,
            'riders_addons': 20,
            'financial_returns': 10,
            'service_quality': 5
        }
    }
    
    max_scores = max_scores_map.get(insurance_type.lower(), {})
    
    detailed_data = [['Category', 'Score', 'Max Points', 'Percentage', 'Grade']]
    
    for category, score in category_scores.items():
        max_score = max_scores.get(category, 100)
        percentage = (score / max_score) * 100 if max_score > 0 else 0
        
        # Grade assignment
        if percentage >= 90:
            grade = "A+"
            grade_color = colors.HexColor('#059669')
        elif percentage >= 80:
            grade = "A"
            grade_color = colors.HexColor('#0891b2')
        elif percentage >= 70:
            grade = "B+"
            grade_color = colors.HexColor('#ca8a04')
        elif percentage >= 60:
            grade = "B"
            grade_color = colors.HexColor('#ea580c')
        elif percentage >= 50:
            grade = "C"
            grade_color = colors.HexColor('#dc2626')
        else:
            grade = "D"
            grade_color = colors.HexColor('#991b1b')
        
        detailed_data.append([
            category.replace('_', ' ').title(),
            f"{score:.1f}",
            str(max_score),
            f"{percentage:.1f}%",
            grade
        ])
    
    detailed_table = Table(detailed_data, colWidths=[2*inch, 0.8*inch, 0.8*inch, 1*inch, 0.8*inch])
    detailed_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        
        # Data rows
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1f2937')),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
    ]))
    
    story.append(detailed_table)
    story.append(Spacer(1, 25))
    
    # ==================== RECOMMENDATIONS ====================
    
    story.append(Paragraph(" Personalized Recommendations", subtitle_style))
    
    recommendations = analysis_data.get('personalized_recommendations', [])
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            priority = rec.get('priority', 'Medium')
            category = rec.get('category', 'General')
            recommendation = rec.get('recommendation', '')
            
            # Priority styling
            if priority == 'Critical':
                priority_color = colors.HexColor('#dc2626')
                priority_icon = ""
            elif priority == 'High':
                priority_color = colors.HexColor('#ea580c')
                priority_icon = ""
            elif priority == 'Medium':
                priority_color = colors.HexColor('#ca8a04')
                priority_icon = ""
            else:
                priority_color = colors.HexColor('#059669')
                priority_icon = ""
            
            # Recommendation box
            rec_text = f"""
            <para>
                <font color="{priority_color.hexval()}"><b>{priority_icon} {priority} Priority - {category}</b></font><br/>
                <font color="#374151">{recommendation}</font>
            </para>
            """
            
            rec_style = ParagraphStyle(
                f'Recommendation{i}',
                parent=body_style,
                backColor=colors.HexColor('#f8fafc'),
                borderColor=priority_color,
                borderWidth=2,
                borderPadding=10,
                spaceAfter=12
            )
            
            story.append(Paragraph(rec_text, rec_style))
    else:
        story.append(Paragraph("No specific recommendations at this time. Your policy appears well-structured.", body_style))
    
    story.append(Spacer(1, 20))
    
    # ==================== SUMMARY INSIGHTS ====================
    
    story.append(Paragraph(" Key Insights & Summary", subtitle_style))
    
    # Generate insights based on scores
    insights = []
    
    # Overall performance insight
    if total_score >= 80:
        insights.append(" Your policy demonstrates strong overall protection with comprehensive coverage.")
    elif total_score >= 60:
        insights.append(" Your policy provides adequate protection but has room for improvement in key areas.")
    else:
        insights.append(" Your policy shows significant gaps that need immediate attention.")
    
    # Category-specific insights
    if category_scores:
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        best_category = sorted_categories[0][0].replace('_', ' ').title()
        worst_category = sorted_categories[-1][0].replace('_', ' ').title()
        
        insights.append(f" Strongest area: {best_category} ({sorted_categories[0][1]:.1f} points)")
        insights.append(f" Focus area: {worst_category} ({sorted_categories[-1][1]:.1f} points)")
    
    # Insurance-specific insights
    if insurance_type.lower() == 'health':
        if policy_info.get('sum_insured', 0) >= 1000000:
            insights.append(" Good sum insured amount that should cover most medical emergencies.")
        if policy_info.get('waiting_period', 4) <= 1:
            insights.append(" Excellent waiting period terms for faster claim processing.")
    
    elif insurance_type.lower() == 'auto':
        if policy_info.get('vehicle_age', 0) <= 3:
            insights.append(" New vehicle - excellent time to maximize comprehensive coverage benefits.")
        if policy_info.get('idv_amount', 0) >= 500000:
            insights.append(" Good IDV coverage that reflects current market value.")
        if policy_info.get('zero_depreciation', '') != 'none':
            insights.append(" Zero depreciation coverage protects against out-of-pocket repair costs.")
    
    elif insurance_type.lower() == 'life':
        income_multiple = policy_info.get('income_multiple', 0)
        if income_multiple >= 10:
            insights.append(" Excellent income replacement ratio ensuring family financial security.")
        elif income_multiple < 5:
            insights.append(" Consider increasing coverage to achieve 10-15x income replacement ratio.")
        
        if policy_info.get('critical_illness_rider', 'none') != 'none':
            insights.append(" Critical illness rider provides additional protection against major diseases.")
    
    # Add extraction confidence insight
    extraction_confidence = analysis_data.get('extraction_confidence', 0)
    if extraction_confidence >= 80:
        insights.append(f" High data extraction confidence ({extraction_confidence}%) ensures accurate analysis.")
    elif extraction_confidence >= 60:
        insights.append(f" Good data extraction ({extraction_confidence}%) with reliable analysis results.")
    else:
        insights.append(f" Moderate extraction confidence ({extraction_confidence}%) - some manual verification recommended.")
    
    for insight in insights:
        story.append(Paragraph(insight, body_style))
        story.append(Spacer(1, 6))
    
    story.append(Spacer(1, 20))
    
    # ==================== SCORE VISUALIZATION ====================
    
    story.append(Paragraph(" Visual Score Breakdown", subtitle_style))
    
    # Create a simple bar chart using reportlab graphics
    drawing = Drawing(400, 200)
    
    # Chart dimensions
    chart_x, chart_y = 50, 50
    chart_width, chart_height = 300, 120
    
    if category_scores:
        bar_width = chart_width / len(category_scores)
        
        # Find max score for scaling
        max_scores = max_scores_map.get(insurance_type.lower(), {})
        
        # Draw bars
        x_pos = chart_x
        for i, (category, score) in enumerate(category_scores.items()):
            # Calculate bar height
            max_score_for_category = max_scores.get(category, 100)
            bar_height = (score / max_score_for_category) * chart_height if max_score_for_category > 0 else 0
            
            # Color based on performance
            if score >= 90:
                bar_color = colors.HexColor('#059669')
            elif score >= 75:
                bar_color = colors.HexColor('#0891b2')
            elif score >= 60:
                bar_color = colors.HexColor('#ca8a04')
            elif score >= 45:
                bar_color = colors.HexColor('#ea580c')
            else:
                bar_color = colors.HexColor('#dc2626')
            
            # Draw bar
            bar = Rect(x_pos + 5, chart_y, bar_width - 10, bar_height)
            bar.fillColor = bar_color
            bar.strokeColor = colors.HexColor('#374151')
            bar.strokeWidth = 1
            drawing.add(bar)
            
            x_pos += bar_width
    
    story.append(drawing)
    story.append(Spacer(1, 20))
    
    # ==================== IMPROVEMENT SUGGESTIONS ====================
    
    if total_score < 80:  # Only show improvement section for scores below 80
        story.append(Paragraph(" Improvement Roadmap", subtitle_style))
        
        improvement_suggestions = []
        
        # Score-based improvements
        if total_score < 50:
            improvement_suggestions.append("Consider switching to a more comprehensive policy with better coverage terms.")
        elif total_score < 70:
            improvement_suggestions.append("Focus on adding essential riders and improving coverage gaps.")
        
        # Category-specific improvements
        if category_scores:
            lowest_category = min(category_scores.items(), key=lambda x: x[1])
            lowest_cat_name = lowest_category[0].replace('_', ' ').title()
            lowest_score = lowest_category[1]
            
            if lowest_score < 15:
                improvement_suggestions.append(f"Priority: Strengthen {lowest_cat_name} - this is your weakest coverage area.")
        
        # Insurance-specific improvements
        if insurance_type.lower() == 'health':
            if policy_info.get('sum_insured', 0) < 500000:
                improvement_suggestions.append("Increase sum insured to at least 5 lakhs for adequate healthcare coverage.")
            if policy_info.get('waiting_period', 0) > 2:
                improvement_suggestions.append("Look for policies with shorter waiting periods for pre-existing diseases.")
        
        elif insurance_type.lower() == 'auto':
            if policy_info.get('zero_depreciation', 'none') == 'none':
                improvement_suggestions.append("Add zero depreciation coverage to avoid depreciation deductions during claims.")
            if policy_info.get('engine_protection', 'none') == 'none':
                improvement_suggestions.append("Engine protection is essential, especially during monsoon season.")
        
        elif insurance_type.lower() == 'life':
            income_multiple = policy_info.get('income_multiple', 0)
            if income_multiple < 10:
                improvement_suggestions.append("Increase life coverage to 10-15 times your annual income for adequate protection.")
        
        for suggestion in improvement_suggestions:
            story.append(Paragraph(f" {suggestion}", body_style))
        
        story.append(Spacer(1, 20))
    
    # ==================== POLICY COMPARISON INSIGHTS ====================
    
    if analysis_data.get('comparison_summary'):  # If this is a comparison report
        story.append(Paragraph(" Policy Comparison Summary", subtitle_style))
        
        comparison = analysis_data.get('comparison_summary', {})
        best_policy = comparison.get('best_policy', {})
        score_range = comparison.get('score_range', {})
        
        comparison_text = f"""
        Best Performing Policy: {best_policy.get('file_name', 'N/A')} (Score: {best_policy.get('score', 0)})
        Score Range: {score_range.get('lowest', 0)} - {score_range.get('highest', 0)} points
        Performance Spread: {score_range.get('spread', 0)} points difference
        """
        
        story.append(Paragraph(comparison_text, body_style))
        story.append(Spacer(1, 15))
    
    # ==================== FOOTER ====================
    
    # Add a separator line
    story.append(Spacer(1, 20))
    
    footer_text = f"""
    <para alignment="center">
        <font size="8" color="#6b7280">
            Report generated by AI-Powered Insurance Analyzer  {datetime.now().strftime('%B %d, %Y')}  
            For questions or policy optimization, consult with your insurance advisor
        </font>
    </para>
    """
    
    story.append(Paragraph(footer_text, body_style))
    
    # ==================== DISCLAIMER ====================
    
    disclaimer_text = f"""
    <para alignment="center">
        <font size="7" color="#9ca3af">
            Disclaimer: This analysis is based on automated extraction and may not capture all policy nuances. 
            Please verify critical details with your insurance provider. This report is for informational purposes only 
            and does not constitute financial or legal advice.
        </font>
    </para>
    """
    
    story.append(Spacer(1, 10))
    story.append(Paragraph(disclaimer_text, body_style))
    
    # ==================== BUILD PDF ====================
    
    try:
        doc.build(story)
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise Exception(f"Failed to generate PDF: {str(e)}")


def create_comparison_pdf(comparison_data: dict) -> BytesIO:
    """
    Create a PDF report for policy comparison
    
    Args:
        comparison_data (dict): The comparison response from the analyzer
        
    Returns:
        BytesIO: PDF file buffer ready for download
    """
    
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=1*inch,
        title="Insurance Policy Comparison Report"
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'ComparisonTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=25,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'ComparisonSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#3b82f6'),
        spaceAfter=15,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'ComparisonBody',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#374151'),
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )
    
    story = []
    
    # Title
    story.append(Paragraph("Insurance Policy Comparison Report", title_style))
    
    # Summary
    comparison_summary = comparison_data.get('comparison_summary', {})
    individual_results = comparison_data.get('individual_results', [])
    total_policies = comparison_data.get('total_policies', 0)
    
    # Metadata
    metadata_data = [
        ['Report Generated', datetime.now().strftime('%B %d, %Y at %I:%M %p')],
        ['Total Policies Compared', str(total_policies)],
        ['Insurance Type', comparison_summary.get('insurance_type', 'Unknown').title()],
        ['Best Policy', comparison_summary.get('best_policy', {}).get('file_name', 'N/A')]
    ]
    
    metadata_table = Table(metadata_data, colWidths=[2.5*inch, 3.5*inch])
    metadata_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1f2937')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#059669')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
    ]))
    
    story.append(metadata_table)
    story.append(Spacer(1, 25))
    
    # Policy ranking table
    story.append(Paragraph(" Policy Ranking", subtitle_style))
    
    ranking_data = [['Rank', 'Policy File', 'Score', 'Protection Level', 'Insurer']]
    
    for i, result in enumerate(individual_results, 1):
        ranking_data.append([
            str(i),
            result.get('file_name', 'N/A'),
            f"{result.get('total_score', 0):.1f}",
            result.get('protection_level', 'Unknown'),
            result.get('policy_info', {}).get('insurer_name', 'N/A')
        ])
    
    ranking_table = Table(ranking_data, colWidths=[0.8*inch, 2*inch, 1*inch, 1.5*inch, 1.5*inch])
    ranking_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        
        # First row (winner) highlight
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#ecfdf5')),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#059669')),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        
        # Other data rows
        ('TEXTCOLOR', (0, 2), (-1, -1), colors.HexColor('#1f2937')),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 2), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 2), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
    ]))
    
    story.append(ranking_table)
    story.append(Spacer(1, 25))
    
    # Category leaders
    if comparison_summary.get('category_leaders'):
        story.append(Paragraph(" Category Leaders", subtitle_style))
        
        leaders_data = [['Category', 'Best Policy', 'Score']]
        category_leaders = comparison_summary.get('category_leaders', {})
        
        for category, leader_info in category_leaders.items():
            leaders_data.append([
                category.replace('_', ' ').title(),
                leader_info.get('policy', 'N/A'),
                f"{leader_info.get('score', 0):.1f}"
            ])
        
        leaders_table = Table(leaders_data, colWidths=[2.5*inch, 2.5*inch, 1*inch])
        leaders_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1f2937')),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#a7f3d0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')])
        ]))
        
        story.append(leaders_table)
        story.append(Spacer(1, 25))
    
    # Footer
    footer_text = f"""
    <para alignment="center">
        <font size="8" color="#6b7280">
            Policy Comparison Report  Generated on {datetime.now().strftime('%B %d, %Y')}  
            AI-Powered Insurance Analysis Platform
        </font>
    </para>
    """
    
    story.append(Paragraph(footer_text, body_style))
    
    try:
        doc.build(story)
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        logger.error(f"Comparison PDF generation failed: {e}")
        raise Exception(f"Failed to generate comparison PDF: {str(e)}")


def format_currency(amount: float) -> str:
    """Format currency amounts in Indian format"""
    if amount >= 10000000:  # 1 crore
        return f"{amount/10000000:.1f} Cr"
    elif amount >= 100000:  # 1 lakh
        return f"{amount/100000:.1f} L"
    else:
        return f"{amount:,.0f}"


def get_risk_color(score: float) -> colors.Color:
    """Get color based on risk score"""
    if score >= 90:
        return colors.HexColor('#059669')  # Green
    elif score >= 75:
        return colors.HexColor('#0891b2')  # Blue
    elif score >= 60:
        return colors.HexColor('#ca8a04')  # Yellow
    elif score >= 45:
        return colors.HexColor('#ea580c')  # Orange
    else:
        return colors.HexColor('#dc2626')  # Red


def create_enhanced_analysis_pdf(analysis_data: dict, include_charts: bool = True) -> BytesIO:
    """
    Enhanced PDF creation with additional visual elements
    
    Args:
        analysis_data (dict): Analysis data
        include_charts (bool): Whether to include visual charts
        
    Returns:
        BytesIO: Enhanced PDF buffer
    """
    
    # Use the main function and add enhancements
    buffer = create_insurance_analysis_pdf(analysis_data)
    
    # Additional enhancements can be added here
    # For now, return the standard PDF
    return buffer


# Utility functions for integration
def validate_analysis_data(analysis_data: dict) -> bool:
    """
    Validate that analysis data contains required fields for PDF generation

    Args:
        analysis_data (dict): Analysis data to validate

    Returns:
        bool: True if data is valid for PDF generation
    """
    # Check if analysis_data is None or empty
    if not analysis_data or not isinstance(analysis_data, dict):
        logger.error(f"Analysis data is invalid: {type(analysis_data)}")
        return False

    # Check for error in analysis results
    if 'error' in analysis_data:
        logger.error(f"Analysis contains error: {analysis_data.get('error')}")
        return False

    required_fields = ['insurance_type', 'total_score', 'category_scores']

    missing_fields = []
    for field in required_fields:
        if field not in analysis_data:
            missing_fields.append(field)

    if missing_fields:
        logger.warning(f"Missing required fields for PDF generation: {', '.join(missing_fields)}")
        logger.warning(f"Available fields: {', '.join(analysis_data.keys())}")
        return False

    # Check if category_scores is not empty
    if not analysis_data.get('category_scores'):
        logger.warning("Category scores are empty")
        return False

    logger.info(f"Analysis data validation passed for {analysis_data.get('insurance_type')} insurance")
    return True


def get_pdf_filename(analysis_data: dict) -> str:
    """
    Generate appropriate filename for the PDF report
    
    Args:
        analysis_data (dict): Analysis data
        
    Returns:
        str: Formatted filename
    """
    insurance_type = analysis_data.get('insurance_type', 'insurance')
    user_name = analysis_data.get('user_info', {}).get('name', 'policy')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Clean filename
    clean_name = user_name.replace(' ', '_').replace('.', '') if user_name else 'policy'
    filename = f"{insurance_type}_{clean_name}_{timestamp}_analysis.pdf"
    
    return filename


# Main function for external usage
def generate_pdf_report(analysis_data: dict) -> BytesIO:
    """
    Main function to generate PDF report from analysis data
    
    Args:
        analysis_data (dict): Complete analysis data from insurance analyzer
        
    Returns:
        BytesIO: PDF file buffer
        
    Raises:
        ValueError: If analysis data is invalid
        Exception: If PDF generation fails
    """
    try:
        # Validate input data
        if not validate_analysis_data(analysis_data):
            raise ValueError("Invalid analysis data for PDF generation")
        
        # Generate PDF
        pdf_buffer = create_insurance_analysis_pdf(analysis_data)
        
        logger.info(f"Successfully generated PDF report for {analysis_data.get('insurance_type', 'unknown')} insurance")
        return pdf_buffer
        
    except Exception as e:
        logger.error(f"PDF report generation failed: {e}")
        raise Exception(f"Failed to generate PDF report: {str(e)}")
    






