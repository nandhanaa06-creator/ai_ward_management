from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from complaints.models import Complaint, ComplaintFeedback


def is_admin(user):
    return user.is_authenticated and (user.role == 'panchayath_admin' or user.is_superuser)


@login_required
@user_passes_test(is_admin)
def worker_analytics_dashboard(request):
    """Main worker analytics dashboard with overview metrics."""
    
    workers = User.objects.filter(role='field_worker').annotate(
        total_completed=Count('assigned_tasks', filter=Q(assigned_tasks__status='resolved')),
        total_assigned=Count('assigned_tasks'),
        active_tasks=Count('assigned_tasks', filter=Q(assigned_tasks__status__in=['assigned', 'in_progress']))
    ).order_by('-total_completed')
    
    total_workers = workers.count()
    total_completed = sum(w.total_completed for w in workers)
    total_active = sum(w.active_tasks for w in workers)
    
    avg_rating = ComplaintFeedback.objects.filter(
        complaint__assigned_worker__role='field_worker'
    ).aggregate(Avg('rating'))['rating__avg'] or 0
    
    top_performers = workers[:5]
    
    week_ago = timezone.now() - timedelta(days=7)
    recent_completions = Complaint.objects.filter(
        assigned_worker__role='field_worker',
        status='resolved',
        updated_at__gte=week_ago
    ).count()
    
    context = {
        'workers': workers,
        'total_workers': total_workers,
        'total_completed': total_completed,
        'total_active': total_active,
        'avg_rating': round(avg_rating, 2),
        'top_performers': top_performers,
        'recent_completions': recent_completions,
    }
    
    return render(request, 'analytics/worker_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def worker_detail_analytics(request, worker_id):
    """Detailed analytics for a specific worker."""
    
    worker = get_object_or_404(User, id=worker_id, role='field_worker')
    
    all_tasks = Complaint.objects.filter(assigned_worker=worker)
    
    total_assigned = all_tasks.count()
    total_completed = all_tasks.filter(status='resolved').count()
    total_pending = all_tasks.filter(status__in=['assigned', 'in_progress']).count()
    
    completion_rate = (total_completed / total_assigned * 100) if total_assigned > 0 else 0
    
    resolved_tasks = all_tasks.filter(status='resolved')
    resolution_times = []
    
    for task in resolved_tasks:
        if task.created_at and task.updated_at:
            delta = task.updated_at - task.created_at
            resolution_times.append(delta.total_seconds() / 86400)
    
    avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
    
    feedbacks = ComplaintFeedback.objects.filter(complaint__assigned_worker=worker)
    total_feedbacks = feedbacks.count()
    avg_rating = feedbacks.aggregate(Avg('rating'))['rating__avg'] or 0
    
    rating_distribution = {
        5: feedbacks.filter(rating=5).count(),
        4: feedbacks.filter(rating=4).count(),
        3: feedbacks.filter(rating=3).count(),
        2: feedbacks.filter(rating=2).count(),
        1: feedbacks.filter(rating=1).count(),
    }
    
    monthly_data = []
    for i in range(5, -1, -1):
        month_start = timezone.now() - timedelta(days=30*i)
        month_end = timezone.now() - timedelta(days=30*(i-1)) if i > 0 else timezone.now()
        
        completed = all_tasks.filter(
            status='resolved',
            updated_at__gte=month_start,
            updated_at__lt=month_end
        ).count()
        
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'completed': completed
        })
    
    category_stats = resolved_tasks.values('category').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    recent_tasks = all_tasks.order_by('-updated_at')[:10]
    
    context = {
        'worker': worker,
        'total_assigned': total_assigned,
        'total_completed': total_completed,
        'total_pending': total_pending,
        'completion_rate': round(completion_rate, 1),
        'avg_resolution_time': round(avg_resolution_time, 1),
        'total_feedbacks': total_feedbacks,
        'avg_rating': round(avg_rating, 2),
        'rating_distribution': rating_distribution,
        'monthly_data': monthly_data,
        'category_stats': category_stats,
        'recent_tasks': recent_tasks,
    }
    
    return render(request, 'analytics/worker_detail.html', context)


@login_required
@user_passes_test(is_admin)
def worker_comparison_chart(request):
    """API endpoint for worker comparison chart data."""
    
    workers = User.objects.filter(role='field_worker').annotate(
        completed=Count('assigned_tasks', filter=Q(assigned_tasks__status='resolved'))
    ).order_by('-completed')[:10]
    
    data = {
        'labels': [w.get_full_name() or w.username for w in workers],
        'completed': [w.completed for w in workers],
    }
    
    return JsonResponse(data)


@login_required
@user_passes_test(is_admin)
def worker_rating_chart(request):
    """API endpoint for worker rating comparison."""
    
    workers = User.objects.filter(role='field_worker')
    
    worker_ratings = []
    for worker in workers:
        avg_rating = ComplaintFeedback.objects.filter(
            complaint__assigned_worker=worker
        ).aggregate(Avg('rating'))['rating__avg']
        
        if avg_rating:
            worker_ratings.append({
                'name': worker.get_full_name() or worker.username,
                'rating': round(avg_rating, 2)
            })
    
    worker_ratings.sort(key=lambda x: x['rating'], reverse=True)
    worker_ratings = worker_ratings[:10]
    
    data = {
        'labels': [w['name'] for w in worker_ratings],
        'ratings': [w['rating'] for w in worker_ratings],
    }
    
    return JsonResponse(data)


@login_required
@user_passes_test(is_admin)
def worker_monthly_performance(request, worker_id):
    """API endpoint for worker monthly performance chart."""
    
    worker = get_object_or_404(User, id=worker_id, role='field_worker')
    
    labels = []
    completed = []
    
    for i in range(5, -1, -1):
        month_start = timezone.now() - timedelta(days=30*i)
        month_end = timezone.now() - timedelta(days=30*(i-1)) if i > 0 else timezone.now()
        
        count = Complaint.objects.filter(
            assigned_worker=worker,
            status='resolved',
            updated_at__gte=month_start,
            updated_at__lt=month_end
        ).count()
        
        labels.append(month_start.strftime('%b %Y'))
        completed.append(count)
    
    data = {
        'labels': labels,
        'completed': completed,
    }
    
    return JsonResponse(data)


@login_required
@user_passes_test(is_admin)
def worker_category_breakdown(request, worker_id):
    """API endpoint for worker category breakdown chart."""
    
    worker = get_object_or_404(User, id=worker_id, role='field_worker')
    
    categories = Complaint.objects.filter(
        assigned_worker=worker,
        status='resolved'
    ).values('category').annotate(
        count=Count('id')
    ).order_by('-count')[:6]
    
    data = {
        'labels': [c['category'] or 'Uncategorized' for c in categories],
        'data': [c['count'] for c in categories],
    }
    
    return JsonResponse(data)


@login_required
@user_passes_test(is_admin)
def export_worker_performance_pdf(request, worker_id):
    """Export worker performance report as PDF."""
    from io import BytesIO
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.enums import TA_CENTER
    
    worker = get_object_or_404(User, id=worker_id, role='field_worker')
    
    all_tasks = Complaint.objects.filter(assigned_worker=worker)
    total_completed = all_tasks.filter(status='resolved').count()
    total_assigned = all_tasks.count()
    
    resolved_tasks = all_tasks.filter(status='resolved')
    resolution_times = []
    for task in resolved_tasks:
        if task.created_at and task.updated_at:
            delta = task.updated_at - task.created_at
            resolution_times.append(delta.total_seconds() / 86400)
    
    avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
    
    feedbacks = ComplaintFeedback.objects.filter(complaint__assigned_worker=worker)
    avg_rating = feedbacks.aggregate(Avg('rating'))['rating__avg'] or 0
    
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
    
    title = Paragraph(f"Worker Performance Report", title_style)
    elements.append(title)
    
    subtitle = Paragraph(
        f"{worker.get_full_name() or worker.username}<br/>Generated on: {timezone.now().strftime('%B %d, %Y')}",
        styles['Normal']
    )
    elements.append(subtitle)
    elements.append(Spacer(1, 0.3*inch))
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Tasks Assigned', str(total_assigned)],
        ['Tasks Completed', str(total_completed)],
        ['Completion Rate', f"{(total_completed/total_assigned*100):.1f}%" if total_assigned > 0 else "0%"],
        ['Average Resolution Time', f"{avg_resolution_time:.1f} days"],
        ['Average Citizen Rating', f"{avg_rating:.2f}/5.0"],
        ['Total Feedbacks', str(feedbacks.count())],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    elements.append(summary_table)
    
    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f'worker_performance_{worker.username}_{timezone.now().strftime("%Y%m%d")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response
