from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Notification


@login_required
def notification_list(request):
    """Get all notifications for current user."""
    notifications = Notification.objects.filter(user=request.user)[:50]
    
    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = [{
            'id': n.id,
            'type': n.notification_type,
            'title': n.title,
            'message': n.message,
            'link': n.link,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for n in notifications]
        return JsonResponse({'notifications': data})
    
    return render(request, 'notifications/notification_list.html', {'notifications': notifications})


@login_required
def mark_all_read(request):
    """Mark all notifications as read."""
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@login_required
def mark_read(request, notification_id):
    """Mark a single notification as read."""
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, id=notification_id, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@login_required
def unread_count(request):
    """Get unread notification count."""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})
