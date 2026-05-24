# Quick Installation Guide

## 🚀 Install Standalone Version (5 Minutes)

### Step 1: Copy Files (PowerShell)

```powershell
# Navigate to your project root
cd D:\bot\travelagenntbot

# Copy new files
Copy-Item standalone-no-telegram\backend\services\booking_sync_service.py backend\services\
Copy-Item standalone-no-telegram\backend\monitors\tasks_booking_sync.py backend\monitors\
Copy-Item standalone-no-telegram\backend\monitors\migrations\0028_add_external_reference.py backend\monitors\migrations\
```

### Step 2: Update Configuration Files

#### Update `backend/core/settings.py`

Open the file and find `CELERY_BEAT_SCHEDULE`, then add:

```python
CELERY_BEAT_SCHEDULE = {
    # ... existing tasks ...
    
    # ADD THIS:
    'sync-booking-requests': {
        'task': 'monitors.tasks_booking_sync.sync_booking_requests',
        'schedule': crontab(minute='*/5'),
    },
}
```

#### Update `backend/core/celery.py`

Find `app.autodiscover_tasks` and add the new module:

```python
app.autodiscover_tasks([
    'monitors',
    'monitors.tasks_google_sheets',
    'monitors.tasks_booking_sync',  # ADD THIS LINE
])
```

#### Update `backend/monitors/views.py`

Find the `mark_slot_booked` function and add this import at the top:

```python
from services.booking_sync_service import BookingSyncService
```

Then add this code inside `mark_slot_booked`, after `slot.save()`:

```python
# Update Google Sheets if task has external_reference
if slot.task and slot.task.external_reference:
    try:
        sync_service = BookingSyncService()
        sync_service.update_booking_completion(
            slot.task.id,
            reference or f'VAT-{slot.id}'
        )
    except Exception as e:
        logger.error(f"Error updating Google Sheets: {e}")
```

### Step 3: Run Migration

```powershell
docker-compose exec backend python manage.py migrate
```

Expected output:
```
Running migrations:
  Applying monitors.0028_add_external_reference... OK
```

### Step 4: Restart Services

```powershell
docker-compose restart backend worker_vatican
```

### Step 5: Verify Installation

```powershell
# Check Celery Beat schedule
docker-compose logs backend | Select-String "sync-booking-requests"
```

Should see:
```
[INFO] Scheduler: Sending due task sync-booking-requests
```

---

## 📊 Update Google Sheets

### Add Two Sheets

**Sheet 1: "Booking Requests"**

Headers (Row 1):
```
Request ID | Date | Visitors | Ticket Type | Language | Status | Booking Ref | Created At
```

Example data (Row 2):
```
REQ-001 | 28/03/2026 | 2 | standard | | pending | | 2026-05-22 10:00:00
```

**Sheet 2: "Participants"**

Headers (Row 1):
```
Request ID | First Name | Last Name | Email | Phone | Birth Date | City | Country
```

Example data (Row 2):
```
REQ-001 | John | Doe | john@example.com | +39 123456789 | 1990-01-15 | Roma | Italia
```

---

## 🧪 Test Installation

### Test 1: Manual Sync

```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.tasks_booking_sync import sync_booking_requests
result = sync_booking_requests()
print(result)
# Should show: {'success': True, 'total_created': X}
exit()
```

### Test 2: Verify Task Created

```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import MonitorTask
task = MonitorTask.objects.filter(external_reference='REQ-001').first()
if task:
    print(f"✅ Task created: {task.id}")
    print(f"   Date: {task.date}")
    print(f"   Visitors: {task.visitors}")
else:
    print("❌ No task found")
exit()
```

### Test 3: Check Worker

```powershell
docker-compose logs -f worker_vatican
```

Should see:
```
[INFO] Monitoring 1 tasks
[INFO] Task REQ-001: 28/03/2026, 2 visitors
```

---

## ✅ Installation Complete!

Your system now:
- ✅ Auto-syncs from Google Sheets every 5 minutes
- ✅ Creates monitoring tasks automatically
- ✅ Updates Google Sheets when booking completes
- ✅ Works without Telegram

---

## 🔧 Troubleshooting

### Issue: Migration Fails

**Error**: `Migration 0028 already exists`

**Solution**: The migration number might conflict. Rename it:
```powershell
Rename-Item backend\monitors\migrations\0028_add_external_reference.py 0029_add_external_reference.py
```

Then update the migration file to change `0027` to `0028` in dependencies.

### Issue: Sync Not Running

**Check Celery Beat**:
```powershell
docker-compose logs backend | Select-String "beat"
```

**Restart backend**:
```powershell
docker-compose restart backend
```

### Issue: Tasks Not Created

**Check logs**:
```powershell
docker-compose logs backend | Select-String "Syncing booking requests"
```

**Common causes**:
1. Sheet not shared with service account
2. Wrong sheet names (must be "Booking Requests" and "Participants")
3. Status not "pending"
4. Missing required columns

---

## 📚 Next Steps

1. ✅ Installation complete
2. ✅ Add real booking requests to Google Sheets
3. ✅ Wait 5 minutes for auto-sync (or trigger manually)
4. ✅ Worker monitors Vatican automatically
5. ✅ Extension auto-books when tickets found
6. ✅ Google Sheets updates with booking status

**See `SETUP_GUIDE.md` for detailed usage instructions.**

---

**Installation time: ~5 minutes** ⏱️  
**Complexity: Low** 🟢  
**Telegram required: No** ❌  
**Fully automated: Yes** ✅
