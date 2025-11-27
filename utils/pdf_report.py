from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
import plotly.io as pio
from io import BytesIO
from datetime import datetime

def generate_pdf_report(farm_data, farmer_name, year, insights_list, gauge_fig, pie_fig, donut_fig, bar_fig, line_fig=None):
    """
    Generate a comprehensive PDF report with all charts and metrics.
    Returns BytesIO object ready for download.
    """
    
    # Create PDF buffer
    pdf_buffer = BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Container for PDF elements
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#2d5016'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#5d4037'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold',
        borderPadding=10
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        textColor=colors.HexColor('#5d4037')
    )
    
    # === HEADER ===
    elements.append(Paragraph(f"🌾 SFI & Scope 3 ESG Report", title_style))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph(f"<b>Farm:</b> {farm_data['farm_name']}", normal_style))
    elements.append(Paragraph(f"<b>Farmer:</b> {farmer_name}", normal_style))
    elements.append(Paragraph(f"<b>Year:</b> {year}", normal_style))
    elements.append(Paragraph(f"<b>Report Generated:</b> {datetime.now().strftime('%d %B %Y')}", normal_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # === OVERALL SCORE SECTION ===
    elements.append(Paragraph("Your Farm's ESG Score", heading_style))
    
    esg_score = farm_data['esg_score']
    if esg_score >= 70:
        message = "Excellent! You're a leader in sustainable farming."
        color = "#2d5016"
    elif esg_score >= 50:
        message = "Good work! A few improvements will boost your score."
        color = "#f9a825"
    else:
        message = "There's room for improvement in your farming practices."
        color = "#c62828"
    
    elements.append(Paragraph(f"<b>Overall ESG Score: {esg_score:.0f}/100</b>", 
                             ParagraphStyle('ScoreStyle', parent=normal_style, fontSize=14, 
                                          textColor=colors.HexColor(color))))
    elements.append(Paragraph(message, normal_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Add gauge chart image
    try:
        gauge_img_buffer = BytesIO()
        gauge_fig.write_image(gauge_img_buffer, format='png', width=400, height=300)
        gauge_img_buffer.seek(0)
        gauge_img = Image(gauge_img_buffer, width=3*inch, height=2.25*inch)
        elements.append(gauge_img)
    except:
        elements.append(Paragraph("(Gauge chart unavailable)", normal_style))
    
    elements.append(Spacer(1, 0.3*inch))
    
    # === ESG COMPONENTS ===
    elements.append(Paragraph("ESG Components Breakdown", heading_style))
    
    e_score = farm_data['e_score']
    s_score = farm_data['s_score']
    g_score = farm_data['g_score']
    
    score_data = [
        ['Component', 'Score', 'Assessment'],
        ['Environment (50%)', f"{e_score:.0f}/100", 'Excellent' if e_score >= 70 else 'Good' if e_score >= 50 else 'Needs Work'],
        ['Social (30%)', f"{s_score:.0f}/100", 'Excellent' if s_score >= 70 else 'Good' if s_score >= 50 else 'Needs Work'],
        ['Governance (20%)', f"{g_score:.0f}/100", 'Excellent' if g_score >= 70 else 'Good' if g_score >= 50 else 'Needs Work'],
    ]
    
    score_table = Table(score_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a7c29')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
    ]))
    elements.append(score_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Add pie chart
    try:
        pie_img_buffer = BytesIO()
        pie_fig.write_image(pie_img_buffer, format='png', width=500, height=400)
        pie_img_buffer.seek(0)
        pie_img = Image(pie_img_buffer, width=3.5*inch, height=2.8*inch)
        elements.append(pie_img)
    except:
        elements.append(Paragraph("(Pie chart unavailable)", normal_style))
    
    elements.append(PageBreak())
    
    # === KEY METRICS ===
    elements.append(Paragraph("Key Sustainability Metrics", heading_style))
    
    metrics_data = [
        ['Metric', 'Value', 'Status'],
        ['Total Farm Area', f"{farm_data['total_farm_area_ha']:.1f} ha", '✓ Tracked'],
        ['Emissions Intensity', f"{farm_data['emissions_per_ha']:.0f} kg/ha", 'Excellent' if farm_data['emissions_per_ha'] < 30 else 'Good' if farm_data['emissions_per_ha'] < 50 else 'Needs Work'],
        ['Nitrogen Use', f"{farm_data['n_per_ha']:.0f} kg/ha", 'Excellent' if farm_data['n_per_ha'] < 50 else 'Good' if farm_data['n_per_ha'] < 100 else 'Needs Work'],
        ['SFI Compliance', f"{((farm_data['sfi_soil_compliance_rate'] + farm_data['sfi_nutrient_compliance_rate'] + farm_data['sfi_hedgerow_compliance_rate']) / 3 * 100):.0f}%", '✓ Compliant'],
    ]
    
    metrics_table = Table(metrics_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a7c29')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    elements.append(metrics_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Add donut chart
    try:
        donut_img_buffer = BytesIO()
        donut_fig.write_image(donut_img_buffer, format='png', width=500, height=400)
        donut_img_buffer.seek(0)
        donut_img = Image(donut_img_buffer, width=3.5*inch, height=2.8*inch)
        elements.append(donut_img)
    except:
        elements.append(Paragraph("(Donut chart unavailable)", normal_style))
    
    elements.append(PageBreak())
    
    # === RECOMMENDATIONS ===
    elements.append(Paragraph("What You Can Do This Season", heading_style))
    
    for i, insight in enumerate(insights_list, 1):
        elements.append(Paragraph(f"<b>{i}.</b> {insight}", normal_style))
    
    elements.append(Spacer(1, 0.3*inch))
    
    # === COMPARISON ===
    elements.append(Paragraph("Your Farm vs. Other Farms", heading_style))
    
    try:
        bar_img_buffer = BytesIO()
        bar_fig.write_image(bar_img_buffer, format='png', width=600, height=400)
        bar_img_buffer.seek(0)
        bar_img = Image(bar_img_buffer, width=5*inch, height=3.33*inch)
        elements.append(bar_img)
    except:
        elements.append(Paragraph("(Comparison chart unavailable)", normal_style))
    
    # Add multi-year progress if available
    if line_fig:
        elements.append(PageBreak())
        elements.append(Paragraph("Your Progress Over Time", heading_style))
        try:
            line_img_buffer = BytesIO()
            line_fig.write_image(line_img_buffer, format='png', width=600, height=400)
            line_img_buffer.seek(0)
            line_img = Image(line_img_buffer, width=5*inch, height=3.33*inch)
            elements.append(line_img)
        except:
            elements.append(Paragraph("(Progress chart unavailable)", normal_style))
    
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(
        "<i>This report was generated by the AgriESG Dashboard. For more information, visit your dashboard to explore your farm's data in detail.</i>",
        ParagraphStyle('Footer', parent=normal_style, fontSize=9, textColor=colors.grey)
    ))
    
    # Build PDF
    doc.build(elements)
    pdf_buffer.seek(0)
    
    return pdf_buffer
