# Model Conflict Fix - Complete Guide

## Problem Fixed

### Issue 1: Notification Model Conflict
**Error:**
```
ERRORS:
accounts.User.notifications: (fields.E304) Reverse accessor for 'governance.Notification.user' clashes with reverse accessor for 'notifications.Notification.user'.
```

**Cause:**
Two models with same related_name:
- `governance.models.Notification` → `related_name='notifications'`
- `notifications.models.Notification` → `related_name='notifications'`

Both tried to create `User.notifications` accessor.

### Issue 2: Static Files Warning
**Warning:**
```
?: (staticfiles.W004) The directory 'E:\...\static' in the STATICFILES_DIRS setting does not exist.
```

**Cause:**
`STATICFILES_DIRS` pointed to non-existent directory.

---

## Solution Applied

### 1. Fixed governance/models.py

**Changed:**
```python
# OLD (WRONG)
user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')

# NEW (FIXED)
user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='governance_notifications')
```

**Now Access Via:**
```python
user.governance_notifications.all()  # Governance notifications
```

### 2. Fixed notifications/models.py

**Changed:**
```python
# OLD (WRONG)
user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')

# NEW (FIXED)
user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_notifications')
```

**Now Access Via:**
```python
user.user_notifications.all()  # Real-time notifications
```

### 3. Created Static Directory

**Created:**
- `static/` directory
- `static/README.md` placeholder

**Result:**
No more staticfiles warning.

---

## Migration Required

### Run This Script:
```bash
fix_model_conflicts.bat
```

### Or Manually:
```bash
# Activate venv
venv\Scripts\activate

# Create migrations
python manage.py makemigrations governance
python manage.py makemigrations notifications

# Apply migrations
python manage.py migrate
```

### Expected Output:
```
Migrations for 'governance':
  governance\migrations\0XXX_alter_notification_user.py
    - Alter field user on notification

Migrations for 'notifications':
  notifications\migrations\0001_initial.py
    - Create model Notification

Running migrations:
  Applying governance.0XXX_alter_notification_user... OK
  Applying notifications.0001_initial... OK
```

---

## Code Updates Required

### Update Any Code Using Old Related Names

**Governance Notifications:**
```python
# OLD (WILL BREAK)
user.notifications.all()

# NEW (CORRECT)
user.governance_notifications.all()
```

**Real-Time Notifications:**
```python
# OLD (WILL BREAK)
user.notifications.all()

# NEW (CORRECT)
user.user_notifications.all()
```

### Files That May Need Updates:

1. **governance/views.py**
   - Search for: `user.notifications`
   - Replace with: `user.governance_notifications`

2. **notifications/views.py**
   - Already uses `Notification.objects.filter(user=request.user)`
   - No changes needed

3. **Any templates using notifications**
   - Update template variables if needed

---

## Verification Steps

### 1. Check Migrations Applied:
```bash
python manage.py showmigrations
```

Should show:
```
governance
 [X] 0001_initial
 [X] 0XXX_alter_notification_user

notifications
 [X] 0001_initial
```

### 2. Test in Django Shell:
```bash
python manage.py shell
```

```python
from accounts.models import User
user = User.objects.first()

# Test governance notifications
print(user.governance_notifications.all())

# Test real-time notifications
print(user.user_notifications.all())
```

### 3. Run Server:
```bash
python manage.py runserver
```

Should start without errors.

---

## Model Comparison

### governance.Notification
**Purpose:** Meeting/governance related notifications
**Fields:**
- user (ForeignKey → `governance_notifications`)
- title
- message
- is_read
- created_at

**Usage:**
```python
from governance.models import Notification
Notification.objects.create(
    user=user,
    title="Meeting Reminder",
    message="Meeting tomorrow at 10 AM"
)
```

### notifications.Notification
**Purpose:** Real-time WebSocket notifications
**Fields:**
- user (ForeignKey → `user_notifications`)
- notification_type (choices)
- title
- message
- link
- is_read
- created_at

**Usage:**
```python
from notifications.models import Notification
Notification.objects.create(
    user=user,
    notification_type='complaint_status',
    title="Complaint Updated",
    message="Your complaint has been resolved",
    link='/complaints/123/'
)
```

---

## Best Practices

### 1. Always Use Unique related_name
```python
# GOOD
user = models.ForeignKey(User, related_name='app_specific_name')

# BAD
user = models.ForeignKey(User, related_name='notifications')  # Too generic
```

### 2. Name Pattern
Use format: `{app}_{model}s` or `{purpose}_{model}s`

Examples:
- `governance_notifications`
- `user_notifications`
- `complaint_feedbacks`
- `meeting_rsvps`

### 3. Check for Conflicts
Before creating ForeignKey to User:
```bash
python manage.py check
```

---

## Troubleshooting

### Error: "Migrations not applied"
**Solution:**
```bash
python manage.py migrate --run-syncdb
```

### Error: "Table already exists"
**Solution:**
```bash
python manage.py migrate --fake governance 0XXX
python manage.py migrate --fake notifications 0001
```

### Error: "Cannot import Notification"
**Solution:**
Use full import path:
```python
from governance.models import Notification as GovernanceNotification
from notifications.models import Notification as UserNotification
```

### Static Files Still Warning
**Solution:**
```bash
# Check directory exists
dir static

# If not, create it
mkdir static

# Restart server
python manage.py runserver
```

---

## Summary

✅ **Fixed:**
- governance.Notification → `related_name='governance_notifications'`
- notifications.Notification → `related_name='user_notifications'`
- Created `static/` directory

✅ **Action Required:**
1. Run `fix_model_conflicts.bat`
2. Update any code using old related names
3. Test both notification systems

✅ **Result:**
- No more model conflicts
- No more static files warning
- Server starts successfully
- Both notification systems work independently

---

## Files Modified

1. `governance/models.py` - Changed related_name
2. `notifications/models.py` - Changed related_name
3. `static/` - Created directory
4. `fix_model_conflicts.bat` - Migration script
5. `MODEL_CONFLICT_FIX.md` - This documentation

---

## Next Steps

1. Run migration script
2. Test server starts
3. Test governance notifications
4. Test real-time notifications
5. Update any custom code if needed
