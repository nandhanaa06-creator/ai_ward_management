from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification


def send_notification(user, notification_type, title, message, link=None):
    """
    Create and send real-time notification to user.
    """
    # Create notification in database
    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link
    )
    
    # Send via WebSocket
    channel_layer = get_channel_layer()
    group_name = f'notifications_{user.id}'
    
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'notification_message',
            'notification': {
                'id': notification.id,
                'type': notification_type,
                'title': title,
                'message': message,
                'link': link,
                'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }
    )
    
    return notification


def send_bulk_notification(users, notification_type, title, message, link=None):
    """
    Send notification to multiple users.
    """
    for user in users:
        send_notification(user, notification_type, title, message, link)


def notify_complaint_status_change(complaint, old_status, new_status):
    """
    Notify citizen when complaint status changes.
    """
    status_messages = {
        'assigned': 'Your complaint has been assigned to a field worker.',
        'in_progress': 'Work has started on your complaint.',
        'resolved': 'Your complaint has been resolved. Please provide feedback.',
        'rejected': 'Your complaint has been reviewed.',
        'urgent_review': 'Your complaint has been marked as urgent and is under review.'
    }
    
    message = status_messages.get(new_status, f'Status changed to {new_status}')
    
    send_notification(
        user=complaint.user,
        notification_type='complaint_status',
        title=f'Complaint #{complaint.id} Status Updated',
        message=message,
        link=f'/complaints/{complaint.id}/'
    )


def notify_new_scheme(scheme):
    """
    Notify all citizens about new scheme.
    """
    from accounts.models import User
    
    citizens = User.objects.filter(role='citizen')
    
    send_bulk_notification(
        users=citizens,
        notification_type='new_scheme',
        title='New Scheme Available',
        message=f'{scheme.name} - Check if you are eligible!',
        link='/schemes/match/'
    )


def notify_meeting_announced(meeting):
    """
    Notify ward citizens about new meeting.
    """
    from accounts.models import User
    
    ward_citizens = User.objects.filter(role='citizen', ward=meeting.ward)
    
    send_bulk_notification(
        users=ward_citizens,
        notification_type='meeting_announced',
        title='Grama Sabha Meeting Announced',
        message=f'Meeting scheduled on {meeting.meeting_date.strftime("%B %d, %Y")} at {meeting.location}',
        link=f'/governance/meeting/{meeting.id}/'
    )


def notify_complaint_assigned(complaint):
    """
    Notify worker when complaint is assigned.
    """
    if complaint.assigned_worker:
        send_notification(
            user=complaint.assigned_worker,
            notification_type='complaint_assigned',
            title='New Task Assigned',
            message=f'Complaint #{complaint.id}: {complaint.title}',
            link=f'/complaints/{complaint.id}/'
        )
