# Real-Time Notifications Setup Guide

## Overview
Real-time WebSocket notifications using Django Channels for instant updates without page refresh.

## Features
- ✅ Real-time complaint status change notifications
- ✅ New scheme announcements
- ✅ Meeting announcements
- ✅ Worker task assignments
- ✅ Popup notifications with sound
- ✅ Notification badge counter
- ✅ Persistent notification storage

## Installation

### 1. Install Required Packages

```bash
# Activate virtual environment
venv\Scripts\activate

# Install Django Channels and dependencies
pip install channels==4.0.0
pip install channels-redis==4.1.0
pip install daphne==4.0.0
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Run Migrations

```bash
python manage.py makemigrations notifications
python manage.py migrate
```

### 3. Run Server with Daphne (ASGI)

Instead of `python manage.py runserver`, use:

```bash
daphne -b 0.0.0.0 -p 8000 ward.asgi:application
```

Or for development:
```bash
python manage.py runserver
```
(Django 6.0+ supports ASGI natively)

## Configuration

### Settings Added (ward/settings.py):
```python
INSTALLED_APPS = [
    'daphne',  # Must be first
    ...
    'channels',
    'notifications',
]

ASGI_APPLICATION = 'ward.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}
```

### ASGI Configuration (ward/asgi.py):
- WebSocket routing configured
- Authentication middleware added
- Protocol router setup

## Usage

### 1. Automatic Notifications

**Complaint Status Changes:**
- Triggers when complaint status changes
- Notifies citizen automatically
- Shows popup with status update

**Worker Assignment:**
- Triggers when complaint assigned to worker
- Notifies both citizen and worker
- Shows task details

**Complaint Resolution:**
- Triggers when worker marks complaint resolved
- Notifies citizen to provide feedback
- Shows resolution details

### 2. Manual Notifications

**Send to Single User:**
```python
from notifications.utils import send_notification

send_notification(
    user=user_object,
    notification_type='complaint_status',
    title='Status Updated',
    message='Your complaint has been resolved',
    link='/complaints/123/'
)
```

**Send to Multiple Users:**
```python
from notifications.utils import send_bulk_notification

send_bulk_notification(
    users=user_queryset,
    notification_type='new_scheme',
    title='New Scheme Available',
    message='Check eligibility now!',
    link='/schemes/match/'
)
```

**Notify New Scheme:**
```python
from notifications.utils import notify_new_scheme

notify_new_scheme(scheme_object)
```

**Notify Meeting:**
```python
from notifications.utils import notify_meeting_announced

notify_meeting_announced(meeting_object)
```

## WebSocket Connection

### Client-Side (Automatic):
- WebSocket connects on page load
- Reconnects automatically if disconnected
- Updates notification badge in real-time

### WebSocket URL:
```
ws://localhost:8000/ws/notifications/
```

### Message Format:
```json
{
    "type": "notification",
    "notification": {
        "id": 1,
        "type": "complaint_status",
        "title": "Complaint Updated",
        "message": "Your complaint has been resolved",
        "link": "/complaints/123/",
        "created_at": "2024-01-15 10:30:00"
    }
}
```

## Notification Types

1. **complaint_status** - Complaint status changed
2. **new_scheme** - New scheme added
3. **meeting_announced** - Meeting scheduled
4. **complaint_assigned** - Task assigned to worker
5. **complaint_resolved** - Complaint resolved

## UI Components

### Notification Bell:
- Located in top navbar
- Shows unread count badge
- Click to view all notifications

### Popup Notifications:
- Appears top-right corner
- Auto-dismisses after 10 seconds
- Includes action button
- Plays sound alert

### Notification Container:
- Fixed position: top-right
- Stacks multiple notifications
- Smooth slide-in animation
- Bootstrap alert styling

## API Endpoints

### Get Notifications:
```
GET /notifications/list/
```
Returns JSON array of user notifications

### Mark All Read:
```
POST /notifications/mark-all-read/
```
Marks all notifications as read

### Unread Count:
```
GET /notifications/unread-count/
```
Returns unread notification count

## Database Model

### Notification Model:
```python
class Notification(models.Model):
    user = ForeignKey(User)
    notification_type = CharField(choices=NOTIFICATION_TYPES)
    title = CharField(max_length=200)
    message = TextField()
    link = CharField(max_length=500)
    is_read = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
```

## Integration Points

### Complaint Views (complaints/views.py):
- `reassign_worker()` - Sends assignment notifications
- `complete_task()` - Sends resolution notifications

### Scheme Views (schemes/views.py):
Add to scheme creation:
```python
from notifications.utils import notify_new_scheme
notify_new_scheme(scheme)
```

### Meeting Views (governance/views.py):
Add to meeting creation:
```python
from notifications.utils import notify_meeting_announced
notify_meeting_announced(meeting)
```

## Testing

### 1. Test WebSocket Connection:
- Open browser console (F12)
- Look for "WebSocket connected" message
- Check for errors

### 2. Test Notifications:
```python
# In Django shell
python manage.py shell

from accounts.models import User
from notifications.utils import send_notification

user = User.objects.first()
send_notification(
    user=user,
    notification_type='complaint_status',
    title='Test Notification',
    message='This is a test',
    link='/dashboard/'
)
```

### 3. Test Complaint Status Change:
1. Login as admin
2. Assign complaint to worker
3. Check citizen receives notification
4. Check worker receives notification

### 4. Test Badge Counter:
1. Send multiple notifications
2. Check badge shows correct count
3. Mark as read
4. Check badge updates

## Troubleshooting

### WebSocket Connection Failed:
**Error:** "WebSocket connection failed"
**Solution:** 
- Check server is running with ASGI support
- Verify ASGI_APPLICATION in settings
- Check firewall/proxy settings

### Notifications Not Appearing:
**Error:** No popup shown
**Solution:**
- Check browser console for errors
- Verify WebSocket is connected
- Check notification permissions
- Clear browser cache

### Badge Not Updating:
**Error:** Badge shows wrong count
**Solution:**
- Refresh page
- Check `/notifications/unread-count/` endpoint
- Verify database has notifications

### Import Error:
**Error:** "No module named 'channels'"
**Solution:**
```bash
pip install channels==4.0.0 daphne==4.0.0
```

### Migration Error:
**Error:** "No such table: notifications_notification"
**Solution:**
```bash
python manage.py makemigrations notifications
python manage.py migrate
```

## Production Deployment

### Use Redis for Channel Layer:

1. Install Redis:
```bash
pip install channels-redis
```

2. Update settings.py:
```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

3. Start Redis server:
```bash
redis-server
```

### Run with Daphne:
```bash
daphne -b 0.0.0.0 -p 8000 ward.asgi:application
```

### Use Supervisor/Systemd:
Create service file for auto-restart

## Performance Notes

- InMemoryChannelLayer: Development only
- RedisChannelLayer: Production recommended
- WebSocket connections: ~1KB per user
- Notification storage: Cleanup old notifications periodically

## Security

- WebSocket requires authentication
- Anonymous users are disconnected
- User-specific notification groups
- CSRF protection on API endpoints

## Future Enhancements

- Email notifications
- SMS notifications
- Push notifications (PWA)
- Notification preferences
- Notification history page
- Mark individual as read
- Delete notifications
- Notification categories filter

## Files Created

1. `notifications/models.py` - Notification model
2. `notifications/consumers.py` - WebSocket consumer
3. `notifications/routing.py` - WebSocket routing
4. `notifications/utils.py` - Notification helpers
5. `notifications/views.py` - API views
6. `notifications/urls.py` - URL configuration
7. `notifications/admin.py` - Admin interface
8. `ward/asgi.py` - ASGI configuration
9. `templates/base.html` - Updated with WebSocket client

## Support

For issues:
1. Check Django Channels documentation
2. Verify WebSocket connection in browser console
3. Check Django logs for errors
4. Test with simple notification first
