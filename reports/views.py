from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db.models import Count, Avg, Q
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO

from complaints.models import Complaint, ComplaintFeedback
from schemes.models import Scheme
from accounts.models import User, Ward

# ReportLab imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER


def is_admin(user):
    return user.is_authenticated and (user.role == 'panchayath_admin' or user.is_superuser)


@login_required
@user_passes_test(is_admin)
def export_complaints_excel(request):
    """Export all complaints to Excel with comprehensive details."""
    status_filter = request.GET.get('status')
    ward_filter = request.GET.get('ward')
    priority_filter = request.GET.get('priority')
    
    complaints = Complaint.objects.select_related('user', 'ward', 'assigned_worker').all()
    
    if status_filter:
        complaints = complaints.filter(status=status_filter)
    if ward_filter:
        complaints = complaints.filter(ward_id=ward_filter)
    if priority_filter:
        complaints = complaints.filter(priority=priority_filter)
    
    data = []
    for complaint in complaints:
        data.append({
            'ID': complaint.id,
            'Title': complaint.title,
            'Description': complaint.description,
            'Category': complaint.category or 'N/A',
            'Priority': complaint.get_priority_display(),
            'Status': complaint.get_status_display(),
            'Ward': f"Ward {complaint.ward.ward_number}" if complaint.ward else 'N/A',
            'Citizen': complaint.user.get_full_name() or complaint.user.username,
            'Assigned Worker': complaint.assigned_worker.username if complaint.assigned_worker else 'Unassigned',
            'Rating': complaint.citizen_rating if complaint.citizen_rating else 'N/A',
            'Is Duplicate': 'Yes' if complaint.is_duplicate else 'No',
            'Created Date': complaint.created_at.strftime('%Y-%m-%d %H:%M'),
            'Updated Date': complaint.updated_at.strftime('%Y-%m-%d %H:%M'),
            'Address': complaint.address_extra or 'N/A',
        })
    
    df = pd.DataFrame(data)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Complaints', index=False)
        
        worksheet = writer.sheets['Complaints']
        for idx, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).apply(len).max(), len(col)) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
    
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f'complaints_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
@user_passes_test(is_admin)
def export_schemes_excel(request):
    """Export scheme beneficiaries to Excel."""
    schemes = Scheme.objects.all()
    
    data = []
    for scheme in schemes:
        data.append({
            'Scheme Name': scheme.name,
            'Description': scheme.description,
            'Benefits': scheme.benefits,
            'Min Age': scheme.min_age,
            'Max Age': scheme.max_age,
            'Max Income': str(scheme.max_income),
            'Gender Target': scheme.get_gender_target_display(),
            'Target Occupation': scheme.target_occupation or 'All',
            'Is Active': 'Yes' if scheme.is_active else 'No',
            'Application Link': scheme.application_link or 'N/A',
            'Created Date': scheme.created_at.strftime('%Y-%m-%d'),
        })
    
    df = pd.DataFrame(data)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Schemes', index=False)
        
        worksheet = writer.sheets['Schemes']
        for idx, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).apply(len).max(), len(col)) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
    
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f'schemes_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
@user_passes_test(is_admin)
def export_monthly_report_pdf(request):
    """Generate comprehensive monthly report in PDF format."""
    month = request.GET.get('month')
    if month:
        report_date = datetime.strptime(month, '%Y-%m')
    else:
        report_date = timezone.now()
    
    start_date = report_date.replace(day=1)
    if start_date.month == 12:
        end_date = start_date.replace(year=start_date.year + 1, month=1)
    else:
        end_date = start_date.replace(month=start_date.month + 1)
    
    complaints = Complaint.objects.filter(created_at__gte=start_date, created_at__lt=end_date)
    
    total_complaints = complaints.count()
    resolved_complaints = complaints.filter(status='resolved').count()
    pending_complaints = complaints.filter(status='pending').count()
    high_priority = complaints.filter(priority='high').count()
    
    category_stats = complaints.values('category').annotate(count=Count('id')).order_by('-count')[:5]
    ward_stats = complaints.values('ward__ward_number', 'ward__ward_name').annotate(count=Count('id')).order_by('-count')[:5]
    
    feedbacks = ComplaintFeedback.objects.filter(created_at__gte=start_date, created_at__lt=end_date)
    avg_rating = feedbacks.aggregate(Avg('rating'))['rating__avg'] or 0
    total_feedbacks = feedbacks.count()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2563eb'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    title = Paragraph(f"Monthly Report - {report_date.strftime('%B %Y')}", title_style)
    elements.append(title)
    
    subtitle = Paragraph(
        f"Smart Ward Management System<br/>Generated on: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}",
        styles['Normal']
    )
    elements.append(subtitle)
    elements.append(Spacer(1, 0.3*inch))
    
    elements.append(Paragraph("Executive Summary", heading_style))
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Complaints', str(total_complaints)],
        ['Resolved Complaints', str(resolved_complaints)],
        ['Pending Complaints', str(pending_complaints)],
        ['High Priority Issues', str(high_priority)],
        ['Resolution Rate', f"{(resolved_complaints/total_complaints*100):.1f}%" if total_complaints > 0 else "0%"],
        ['Average Citizen Rating', f"{avg_rating:.2f}/5.0"],
        ['Total Feedbacks', str(total_feedbacks)],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))
    
    if category_stats:
        elements.append(Paragraph("Top 5 Complaint Categories", heading_style))
        
        category_data = [['Category', 'Count', 'Percentage']]
        for cat in category_stats:
            percentage = (cat['count'] / total_complaints * 100) if total_complaints > 0 else 0
            category_data.append([
                cat['category'] or 'Uncategorized',
                str(cat['count']),
                f"{percentage:.1f}%"
            ])
        
        category_table = Table(category_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        category_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elements.append(category_table)
        elements.append(Spacer(1, 0.3*inch))
    
    if ward_stats:
        elements.append(Paragraph("Top 5 Wards by Complaint Volume", heading_style))
        
        ward_data = [['Ward', 'Complaints']]
        for ward in ward_stats:
            ward_data.append([
                f"Ward {ward['ward__ward_number']} - {ward['ward__ward_name']}",
                str(ward['count'])
            ])
        
        ward_table = Table(ward_data, colWidths=[3.5*inch, 2*inch])
        ward_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f59e0b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elements.append(ward_table)
    
    elements.append(Spacer(1, 0.5*inch))
    footer_text = Paragraph(
        "<i>This report is auto-generated by Smart Ward Management System</i>",
        styles['Normal']
    )
    elements.append(footer_text)
    
    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f'monthly_report_{report_date.strftime("%Y_%m")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
@user_passes_test(is_admin)
def reports_dashboard(request):
    """Main reports dashboard page with export options."""
    total_complaints = Complaint.objects.count()
    total_schemes = Scheme.objects.count()
    
    months = []
    for i in range(6):
        date = timezone.now() - timedelta(days=30*i)
        months.append({
            'value': date.strftime('%Y-%m'),
            'label': date.strftime('%B %Y')
        })
    
    wards = Ward.objects.all().order_by('ward_number')
    
    context = {
        'total_complaints': total_complaints,
        'total_schemes': total_schemes,
        'months': months,
        'wards': wards,
    }
    
    return render(request, 'reports/reports_dashboard.html', context)
