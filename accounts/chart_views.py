from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from complaints.models import Complaint
from accounts.models import Ward

def is_admin(user):
    return user.is_authenticated and (user.role == 'panchayath_admin' or user.is_superuser)

@login_required
@user_passes_test(is_admin)
def complaints_per_ward_data(request):
    """API endpoint for complaints per ward bar chart"""
    wards = Ward.objects.annotate(
        complaint_count=Count('complaints')
    ).order_by('ward_number')
    
    data = {
        'labels': [f"Ward {w.ward_number}" for w in wards],
        'data': [w.complaint_count for w in wards]
    }
    return JsonResponse(data)

@login_required
@user_passes_test(is_admin)
def monthly_complaints_data(request):
    """API endpoint for monthly complaints line chart (last 6 months)"""
    labels = []
    data = []
    
    for i in range(5, -1, -1):
        month_start = timezone.now() - timedelta(days=30*i)
        month_end = timezone.now() - timedelta(days=30*(i-1)) if i > 0 else timezone.now()
        
        count = Complaint.objects.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        ).count()
        
        labels.append(month_start.strftime('%b %Y'))
        data.append(count)
    
    return JsonResponse({'labels': labels, 'data': data})

@login_required
@user_passes_test(is_admin)
def complaint_categories_data(request):
    """API endpoint for complaint categories pie chart"""
    categories = Complaint.objects.values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    data = {
        'labels': [c['category'] or 'Uncategorized' for c in categories],
        'data': [c['count'] for c in categories]
    }
    return JsonResponse(data)

@login_required
@user_passes_test(is_admin)
def complaint_status_data(request):
    """API endpoint for complaint status pie chart"""
    statuses = Complaint.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    status_labels = {
        'pending': 'Pending',
        'assigned': 'Assigned',
        'in_progress': 'In Progress',
        'resolved': 'Resolved',
        'rejected': 'Rejected',
        'urgent_review': 'Urgent Review'
    }
    
    data = {
        'labels': [status_labels.get(s['status'], s['status'].title()) for s in statuses],
        'data': [s['count'] for s in statuses]
    }
    return JsonResponse(data)
