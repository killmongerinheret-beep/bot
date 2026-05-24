# Files to Copy - Complete List

## 📁 Files Already in `standalone-no-telegram/` Folder

These files are ready to copy to your main project:

### Backend Files (New)
```
standalone-no-telegram/backend/services/booking_sync_service.py
standalone-no-telegram/backend/monitors/tasks_booking_sync.py
standalone-no-telegram/backend/monitors/migrations/0028_add_external_reference.py
```

### Configuration Updates (Manual Edits)
```
backend/core/settings.py (add CELERY_BEAT_SCHEDULE entry)
backend/core/celery.py (add autodiscover_tasks line)
backend/monitors/views.py (add Google Sheets update code)
```

### Documentation
```
standalone-no-telegram/README.md
standalone-no-telegram/SETUP_GUIDE.md
standalone-no-telegram/INSTALL.md
standalone-no-telegram/QUICK_START.md
standalone-no-telegram/WHATS_DIFFERENT.md
standalone-no-telegram/COMPLETE_INSTALL_GUIDE.md
standalone-no-telegram/FILES_TO_COPY.md (this file)
```

---

## 📁 Files Already Working in Your Project

These files are **already in your project** and work correctly. **No changes needed**:

### Worker Vatican Files (Core Monitoring)
```
worker_vatican/search_api_monitor.py ✅ Already working
worker_vatican/hydra_monitor.py ✅ Already working
worker_vatican/__init__.py ✅ Already working
```

### Backend Monitoring Tasks
```
backend/monitors/tasks_search_api.py ✅ Already working
backend/monitors/tasks.py ✅ Already working
backend/monitors/models.py ✅ Already working
backend/monitors/views.py ✅ Already working (will add Google Sheets update)
backend/monitors/serializers.py ✅ Already working
```

### Browser Extension (No Changes)
```
browser-extension/background.js ✅ Already working
browser-extension/content.js ✅ Already working
browser-extension/popup.js ✅ Already working
browser-extension/popup.html ✅ Already working
browser-extension/manifest.json ✅ Already working
browser-extension/options.js ✅ Already working
browser-extension/options.html ✅ Already working
```

---

## 🚀 Quick Copy Commands (PowerShell)

Run these commands from your project root (`D:\bot\travelagenntbot`):

```powershell
# Create services directory if needed
New-Item -ItemType Directory -Force -Path backend\services

# Copy new backend files
Copy-Item standalone-no-telegram\backend\services\booking_sync_service.py backend\services\
Copy-Item standalone-no-telegram\backend\monitors\tasks_booking_sync.py backend\monitors\
Copy-Item standalone-no-telegram\backend\monitors\migrations\0028_add_external_reference.py backend\monitors\migrations\
```

---

## ✏️ Manual Configuration Updates

### 1. Update `backend/core/settings.py`

Find `CELERY_BEAT_SCHEDULE` and add:

```python
'sync-booking-requests': {
    'task': 'monitors.tasks_booking_sync.sync_booking_requests',
    'schedule': crontab(minute='*/5'),
},
```

### 2. Update `backend/core/celery.py`

Add this line after other `autodiscover_tasks` calls:

```python
app.autodiscover_tasks(['monitors'], related_name='tasks_booking_sync')
```

### 3. Update `backend/monitors/views.py`

Add import at top:
```python
from services.booking_sync_service import BookingSyncService
```

Add code in `mark_slot_booked` function after `slot.save()`:
```python
# Update Google Sheets if task has external_reference
if slot.task and slot.task.external_reference:
    try:
        sync_service = BookingSyncService()
        sync_service.update_booking_completion(
            slot.task.id,
            reference or f'VAT-{slot.id}'
        )
        logger.info(f"Updated Google Sheets for request {slot.task.external_reference}")
    except Exception as e:
        logger.error(f"Error updating Google Sheets: {e}")
```

---

## 🗄️ Database Migration

After copying files and updating configuration:

```powershell
docker-compose exec backend python manage.py migrate
```

---

## 🔄 Restart Services

```powershell
docker-compose restart backend worker_vatican
```

---

## ✅ Verification

Check that everything is working:

```powershell
# Check Celery Beat schedule
docker-compose logs backend | Select-String "sync-booking-requests"

# Check worker is monitoring
docker-compose logs worker_vatican | Select-String "Monitoring"

# Check database
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import MonitorTask
print(f"Active tasks: {MonitorTask.objects.filter(is_active=True).count()}")
exit()
```

---

## 📊 What Each File Does

### `booking_sync_service.py`
- Reads Google Sheets (2 tabs: Booking Requests + Participants)
- Creates MonitorTasks automatically
- Updates Google Sheets when booking completes
- Handles participant data

### `tasks_booking_sync.py`
- Celery task that runs every 5 minutes
- Syncs all agencies with Google Sheets configured
- Creates tasks for "pending" requests
- Skips already-processed requests

### `0028_add_external_reference.py`
- Database migration
- Adds `external_reference` field to MonitorTask
- Stores Google Sheets Request ID (e.g., "REQ-001")
- Used to link tasks back to Google Sheets

### Configuration Updates
- **settings.py**: Adds Celery Beat schedule for auto-sync
- **celery.py**: Registers new task module
- **views.py**: Updates Google Sheets when booking completes

---

## 🎯 What Stays the Same

These components work exactly as before:

1. **Vatican Monitoring** - Uses existing `search_api_monitor.py`
2. **Browser Extension** - No changes needed
3. **Database Models** - Only adds one field
4. **API Endpoints** - All existing endpoints work
5. **Worker Logic** - Uses existing monitoring code

---

## 🆕 What's New

1. **Google Sheets Auto-Sync** - Runs every 5 minutes
2. **External Reference Tracking** - Links tasks to Google Sheets
3. **Automatic Task Creation** - No manual commands needed
4. **Status Updates** - Google Sheets updated when booking completes
5. **Participant Management** - Reads from Google Sheets

---

## 📝 Summary

**Files to Copy**: 3 new files  
**Files to Edit**: 3 configuration files  
**Files Already Working**: 50+ files (no changes)  
**Total Installation Time**: ~15 minutes  
**Complexity**: Medium  
**Risk**: Low (only adds new features, doesn't break existing)

---

**Next Step**: See `COMPLETE_INSTALL_GUIDE.md` for step-by-step instructions.
