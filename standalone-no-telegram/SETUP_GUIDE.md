# Setup Guide - Standalone Version (No Telegram)

## 🎯 Overview

This guide shows how to set up the standalone version that works without Telegram.

---

## 📋 Step 1: Update Google Sheets Format

Your Google Sheet needs 2 tabs:

### Tab 1: "Booking Requests"

| Column | Required | Format | Example |
|--------|----------|--------|---------|
| Request ID | ✅ Yes | Text | REQ-001 |
| Date | ✅ Yes | DD/MM/YYYY | 28/03/2026 |
| Visitors | ✅ Yes | Number | 2 |
| Ticket Type | ✅ Yes | standard/guided | standard |
| Language | ⚠️ If guided | ENG/ITA/FRA/DEU/SPA | ENG |
| Status | ✅ Yes | pending/monitoring/booked | pending |
| Booking Ref | ⚠️ Auto-filled | Text | VAT-2026-001 |
| Created At | ⚠️ Optional | Timestamp | 2026-05-22 10:00:00 |

**Example**:
```
Request ID | Date       | Visitors | Ticket Type | Language | Status    | Booking Ref | Created At
REQ-001    | 28/03/2026 | 2        | standard    |          | pending   |             | 2026-05-22 10:00:00
REQ-002    | 29/03/2026 | 4        | guided      | ENG      | pending   |             | 2026-05-22 10:05:00
```

### Tab 2: "Participants"

Keep your existing format, just add Request ID column:

| Column | Required | Format | Example |
|--------|----------|--------|---------|
| Request ID | ✅ Yes | Text | REQ-001 |
| First Name | ✅ Yes | Text | John |
| Last Name | ✅ Yes | Text | Doe |
| Email | ✅ Yes | Email | john@example.com |
| Phone | ✅ Yes | Phone | +39 123456789 |
| Birth Date | ⚠️ Optional | YYYY-MM-DD | 1990-01-15 |
| City | ⚠️ Optional | Text | Roma |
| Country | ⚠️ Optional | Text | Italia |

**Example**:
```
Request ID | First Name | Last Name | Email              | Phone          | Birth Date
REQ-001    | John       | Doe       | john@example.com  | +39 123456789  | 1990-01-15
REQ-001    | Jane       | Doe       | jane@example.com  | +39 987654321  | 1992-03-20
REQ-002    | Mario      | Rossi     | mario@example.com | +39 555123456  | 1985-07-10
```

---

## 📋 Step 2: Copy Files to Main Project

### Copy New Files

```powershell
# Copy booking sync service
Copy-Item standalone-no-telegram\backend\services\booking_sync_service.py backend\services\

# Copy booking sync task
Copy-Item standalone-no-telegram\backend\monitors\tasks_booking_sync.py backend\monitors\

# Copy migration
Copy-Item standalone-no-telegram\backend\monitors\migrations\0028_add_external_reference.py backend\monitors\migrations\
```

### Update Existing Files

**Option 1: Manual Update** (Recommended)
- Open the files in `standalone-no-telegram/backend/` folder
- Copy the relevant sections to your main project files
- See comments marked with `# ADD THIS` or `# UPDATE THIS`

**Option 2: Replace Files** (Backup first!)
```powershell
# Backup current files
Copy-Item backend\core\settings.py backend\core\settings.py.backup
Copy-Item backend\core\celery.py backend\core\celery.py.backup
Copy-Item backend\monitors\views.py backend\monitors\views.py.backup

# Copy updated files
Copy-Item standalone-no-telegram\backend\core\settings.py backend\core\
Copy-Item standalone-no-telegram\backend\core\celery.py backend\core\
Copy-Item standalone-no-telegram\backend\monitors\views.py backend\monitors\
```

---

## 📋 Step 3: Run Migrations

```powershell
# Create migration
docker-compose exec backend python manage.py makemigrations

# Apply migration
docker-compose exec backend python manage.py migrate

# Verify
docker-compose exec backend python manage.py showmigrations monitors
```

Expected output:
```
[X] 0027_add_google_sheet_url
[X] 0028_add_external_reference
```

---

## 📋 Step 4: Restart Services

```powershell
# Restart backend and worker
docker-compose restart backend worker_vatican

# Check logs
docker-compose logs -f backend worker_vatican
```

Look for:
```
[INFO] Celery beat schedule loaded
[INFO] Task: monitors.tasks_booking_sync.sync_booking_requests
[INFO] Schedule: every 5 minutes
```

---

## 📋 Step 5: Test Auto-Sync

### Add Test Request to Google Sheets

**Booking Requests tab**:
```
REQ-TEST-001 | 28/03/2026 | 2 | standard | | pending | | 2026-05-22 10:00:00
```

**Participants tab**:
```
REQ-TEST-001 | John | Doe | john@example.com | +39 123456789 | 1990-01-15
REQ-TEST-001 | Jane | Doe | jane@example.com | +39 987654321 | 1992-03-20
```

### Trigger Sync Manually

```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.tasks_booking_sync import sync_booking_requests

# Run sync
result = sync_booking_requests()
print(result)

# Expected output:
# {'success': True, 'total_created': 1}

exit()
```

### Verify Task Created

```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import MonitorTask

# Find task by external reference
task = MonitorTask.objects.filter(external_reference='REQ-TEST-001').first()

if task:
    print(f"✅ Task created successfully!")
    print(f"   ID: {task.id}")
    print(f"   Date: {task.date}")
    print(f"   Visitors: {task.visitors}")
    print(f"   External Ref: {task.external_reference}")
    print(f"   Active: {task.is_active}")
else:
    print("❌ Task not found")

exit()
```

---

## 📋 Step 6: Verify Worker Monitoring

```powershell
# Check worker logs
docker-compose logs -f worker_vatican
```

Expected output:
```
[INFO] Monitoring 1 tasks
[INFO] Task REQ-TEST-001: 28/03/2026, 2 visitors
[INFO] Checking Vatican API...
[INFO] No slots available (expected)
```

---

## 📋 Step 7: Test Extension Auto-Booking

### Create Test Slot

```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import HeldSlot, MonitorTask

# Get the task we created
task = MonitorTask.objects.filter(external_reference='REQ-TEST-001').first()

if task:
    # Create test slot
    slot = HeldSlot.objects.create(
        task=task,
        slot_id='TEST-STANDALONE-001',
        date=task.date,
        slot_time='10:00',
        ticket_id='2129030053',
        ticket_name='Vatican Museums - Standard Entry',
        visitors=task.visitors,
        adult_count=task.visitors,
        child_count=0,
        status='held',
        total_price=32.00
    )
    
    print(f"✅ Test slot created: {slot.id}")
    print(f"   Extension should detect within 10 seconds!")
else:
    print("❌ Task not found - run Step 5 first")

exit()
```

### Watch Extension

**Extension Console** (Right-click extension icon → Inspect):
```
🎉 Found 1 available slots from backend!
📦 Opening incognito window for REQ-TEST-001
✅ Opened incognito window #1 for 28/03/2026 10:00
```

**Incognito Window** (F12):
```
🚀 Auto-booking started...
📝 Step 5/10: Filling form with participants...
  Manager: John Doe (john@example.com)  ← From Google Sheets
  Participant 1: John Doe               ← From Google Sheets
  Participant 2: Jane Doe               ← From Google Sheets
```

---

## 📋 Step 8: Verify Google Sheets Update

After booking completes, check your Google Sheets:

**Booking Requests tab** should update:
```
REQ-TEST-001 | 28/03/2026 | 2 | standard | | booked | VAT-2026-001 | 2026-05-22 10:00:00
                                              ^^^^^^   ^^^^^^^^^^^^
                                              Status   Booking Ref
```

---

## 📋 Step 9: Clean Up Test Data

```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import MonitorTask, HeldSlot

# Delete test task and slot
MonitorTask.objects.filter(external_reference='REQ-TEST-001').delete()
HeldSlot.objects.filter(slot_id__startswith='TEST').delete()

print("✅ Test data cleaned up")
exit()
```

Also delete test row from Google Sheets.

---

## 📋 Step 10: Configure for Production

### Enable Auto-Sync

Auto-sync is already enabled! It runs every 5 minutes automatically.

To change frequency, edit `backend/core/settings.py`:

```python
CELERY_BEAT_SCHEDULE = {
    'sync-booking-requests': {
        'task': 'monitors.tasks_booking_sync.sync_booking_requests',
        'schedule': crontab(minute='*/5'),  # Change to */10 for 10 minutes
    },
}
```

### Configure Extension on Multiple Computers

**Computer 1** (Your main computer):
```
1. Install Chrome
2. Load extension from browser-extension folder
3. Configure:
   Backend URL: http://localhost:8000
   (or your server IP if backend is remote)
4. Start Backend Listener
5. Keep browser open 24/7
```

**Computer 2** (Another computer):
```
1. Copy browser-extension folder to Computer 2
2. Install Chrome
3. Load extension
4. Configure:
   Backend URL: http://your-server-ip:8000
   (same backend as Computer 1)
5. Start Backend Listener
```

**Both computers will**:
- Poll the same backend
- See the same available slots
- Can book different slots simultaneously
- Work independently

---

## 🔧 Troubleshooting

### Issue: Auto-Sync Not Running

**Check Celery Beat**:
```powershell
docker-compose logs -f backend | Select-String "beat"
```

Should see:
```
[INFO] beat: Starting...
[INFO] Scheduler: Sending due task sync-booking-requests
```

**Solution**: Restart backend
```powershell
docker-compose restart backend
```

### Issue: Tasks Not Created from Sheets

**Check sync logs**:
```powershell
docker-compose logs backend | Select-String "Syncing booking requests"
```

**Manual sync**:
```powershell
docker-compose exec backend python manage.py shell
>>> from monitors.tasks_booking_sync import sync_booking_requests
>>> result = sync_booking_requests()
>>> print(result)
```

**Common causes**:
1. Sheet not shared with service account
2. Wrong sheet tab names (must be "Booking Requests" and "Participants")
3. Missing required columns
4. Status not "pending"

### Issue: Extension Not Detecting Slots

**Check API**:
```powershell
curl http://localhost:8000/api/v1/available-slots/
```

Should return slots with participant data.

**Check extension console** (F12):
```
🔄 Checking backend for available slots...
```

Should poll every 10 seconds.

---

## ✅ Success Checklist

- [ ] Google Sheets has 2 tabs: "Booking Requests" + "Participants"
- [ ] Service account has access to sheet
- [ ] Files copied to main project
- [ ] Migration applied
- [ ] Services restarted
- [ ] Auto-sync running (check logs)
- [ ] Test request added to sheet
- [ ] Task created automatically
- [ ] Worker monitoring task
- [ ] Test slot created
- [ ] Extension detected slot
- [ ] Incognito window opened
- [ ] Form filled with sheet data
- [ ] Google Sheets status updated

---

## 🎯 Production Workflow

### Daily Operation

1. **Bokun creates booking** → Updates Google Sheets
2. **Backend auto-syncs** (every 5 minutes) → Creates MonitorTask
3. **Worker monitors Vatican** (every 5 seconds) → Creates HeldSlot when found
4. **Extension auto-books** (polls every 10 seconds) → Completes booking
5. **Backend updates sheet** → Status: "booked", Booking Ref: "VAT-XXX"

### No Manual Intervention Needed!

Just:
- Keep backend/worker running (Docker)
- Keep browser open with extension (any computer)
- Add booking requests to Google Sheets
- System handles everything else

---

## 📚 Additional Resources

- **Main Documentation**: See parent folder for complete guides
- **Extension Guide**: `../EXTENSION_COMPLETE_GUIDE.md`
- **Proxy Setup**: `../OXYLABS_PROXY_SETUP.md`
- **Troubleshooting**: `../QUICK_REFERENCE.md`

---

**System is now fully automated! No Telegram required.** 🚀
