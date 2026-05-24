# Complete Installation Guide - Standalone Vatican Bot

## 🎯 What You're Installing

A fully automated Vatican ticket booking system that works **without Telegram**:

```
BOKUN → Google Sheets → Backend → Worker → Extension → Auto-Booking
```

---

## 📋 Prerequisites

- ✅ Docker & Docker Compose installed
- ✅ Windows PowerShell (you have this)
- ✅ Bokun → Google Sheets automation working
- ✅ Google Sheets service account credentials
- ✅ Oxylabs proxy credentials (optional but recommended)

---

## 🚀 Installation Steps

### Step 1: Copy All Files (5 minutes)

Open PowerShell in your project root (`D:\bot\travelagenntbot`):

```powershell
# Navigate to project root
cd D:\bot\travelagenntbot

# Create services directory if it doesn't exist
New-Item -ItemType Directory -Force -Path backend\services

# Copy new backend files
Copy-Item standalone-no-telegram\backend\services\booking_sync_service.py backend\services\
Copy-Item standalone-no-telegram\backend\monitors\tasks_booking_sync.py backend\monitors\
Copy-Item standalone-no-telegram\backend\monitors\migrations\0028_add_external_reference.py backend\monitors\migrations\

# Copy worker files (these are the core monitoring files)
Copy-Item standalone-no-telegram\worker_vatican\search_api_monitor.py worker_vatican\
Copy-Item standalone-no-telegram\worker_vatican\hydra_monitor.py worker_vatican\

# Copy extension files (no changes needed, but included for completeness)
# Extension already works - no copy needed

# Copy documentation
Copy-Item standalone-no-telegram\README.md standalone-no-telegram\
Copy-Item standalone-no-telegram\SETUP_GUIDE.md standalone-no-telegram\
Copy-Item standalone-no-telegram\QUICK_START.md standalone-no-telegram\
```

---

### Step 2: Update Configuration Files

#### A. Update `backend/core/settings.py`

Open `backend/core/settings.py` and find the `CELERY_BEAT_SCHEDULE` section (around line 200).

Add this new task to the schedule:

```python
CELERY_BEAT_SCHEDULE = {
    # ... existing tasks ...
    
    # ✅ ADD THIS NEW TASK:
    'sync-booking-requests': {
        'task': 'monitors.tasks_booking_sync.sync_booking_requests',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
}
```

**Full example:**
```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'vatican-monitor-orchestrator': {
        'task': 'orchestrate_vatican_tasks_search_api',
        'schedule': 5.0,
        'options': {'queue': 'vatican', 'priority': 5},
    },
    # ... other existing tasks ...
    
    # ✅ NEW: Auto-sync from Google Sheets
    'sync-booking-requests': {
        'task': 'monitors.tasks_booking_sync.sync_booking_requests',
        'schedule': crontab(minute='*/5'),
    },
}
```

#### B. Update `backend/core/celery.py`

Open `backend/core/celery.py` and find the `autodiscover_tasks` section (around line 20).

Add this line:

```python
# ✅ ADD THIS LINE:
app.autodiscover_tasks(['monitors'], related_name='tasks_booking_sync')
```

**Full example:**
```python
# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Explicitly import tasks
app.autodiscover_tasks(['monitors'], related_name='tasks_search_api')
app.autodiscover_tasks(['monitors'], related_name='tasks')
app.autodiscover_tasks(['monitors'], related_name='tasks_hold')
app.autodiscover_tasks(['monitors'], related_name='tasks_sweep')
app.autodiscover_tasks(['monitors'], related_name='tasks_bulk_hold')
app.autodiscover_tasks(['monitors'], related_name='turnstile_pool')
app.autodiscover_tasks(['monitors'], related_name='lightning_snipe')

# ✅ NEW: Booking sync tasks
app.autodiscover_tasks(['monitors'], related_name='tasks_booking_sync')
```

#### C. Update `backend/monitors/views.py`

Open `backend/monitors/views.py` and find the `mark_slot_booked` function (around line 1800).

**Add import at the top of the file:**
```python
from services.booking_sync_service import BookingSyncService
```

**Add this code inside `mark_slot_booked`, after `slot.save()`:**
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

### Step 3: Run Database Migration

```powershell
docker-compose exec backend python manage.py migrate
```

**Expected output:**
```
Running migrations:
  Applying monitors.0028_add_external_reference... OK
```

**If you get an error about migration number conflict:**
```powershell
# Find the latest migration number
docker-compose exec backend python manage.py showmigrations monitors

# Rename the migration file to the next number
# Example: if latest is 0029, rename to 0030
Rename-Item backend\monitors\migrations\0028_add_external_reference.py 0030_add_external_reference.py

# Edit the file and update dependencies line:
# Change: dependencies = [('monitors', '0027_...')]
# To: dependencies = [('monitors', '0029_...')]

# Run migration again
docker-compose exec backend python manage.py migrate
```

---

### Step 4: Restart Services

```powershell
docker-compose restart backend worker_vatican
```

**Wait 10 seconds, then verify:**
```powershell
docker-compose logs backend | Select-String "sync-booking-requests"
```

Should see:
```
[INFO] Scheduler: Sending due task sync-booking-requests
```

---

### Step 5: Configure Google Sheets

#### A. Update Sheet Structure

Your Google Sheets needs **2 tabs**:

**Tab 1: "Booking Requests"**

| Request ID | Date | Visitors | Ticket Type | Language | Status | Booking Ref | Created At |
|------------|------|----------|-------------|----------|--------|-------------|------------|
| REQ-001 | 28/03/2026 | 2 | standard | | pending | | 2026-05-22 10:00:00 |
| REQ-002 | 29/03/2026 | 1 | guided | ENG | pending | | 2026-05-22 10:05:00 |

**Column Details:**
- **Request ID**: Unique ID (e.g., REQ-001, REQ-002)
- **Date**: DD/MM/YYYY format
- **Visitors**: Number (1-10)
- **Ticket Type**: "standard" or "guided"
- **Language**: Empty for standard, "ENG"/"ITA"/"FRA"/"DEU"/"SPA" for guided
- **Status**: "pending" (system updates to "monitoring", "booked", "failed")
- **Booking Ref**: Empty (system fills when booked)
- **Created At**: Timestamp (optional)

**Tab 2: "Participants"**

| Request ID | First Name | Last Name | Email | Phone | Birth Date | City | Country |
|------------|------------|-----------|-------|-------|------------|------|---------|
| REQ-001 | John | Doe | john@example.com | +39 123456789 | 1990-01-15 | Roma | Italia |
| REQ-001 | Jane | Doe | jane@example.com | +39 987654321 | 1992-03-20 | Roma | Italia |
| REQ-002 | Bob | Smith | bob@example.com | +39 555555555 | 1985-07-10 | Milano | Italia |

**Column Details:**
- **Request ID**: Must match Request ID from Tab 1
- **First Name**: Participant first name
- **Last Name**: Participant last name
- **Email**: Participant email
- **Phone**: Phone number with country code
- **Birth Date**: YYYY-MM-DD format
- **City**: City name
- **Country**: Country name

#### B. Share Sheet with Service Account

```powershell
# Get service account email
docker-compose exec backend cat /app/google-credentials.json
```

Look for `"client_email"` - it will look like:
```
"client_email": "vatican-bot@project-123456.iam.gserviceaccount.com"
```

**Share your Google Sheet with this email address** (Editor access).

#### C. Add Sheet URL to Agency

```powershell
# Get your agency ID
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import Agency
agency = Agency.objects.first()
print(f"Agency ID: {agency.id}")
print(f"Agency Name: {agency.name}")

# Update Google Sheet URL
agency.google_sheet_url = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
agency.save()
print("✅ Google Sheet URL updated")
exit()
```

---

### Step 6: Test the System

#### Test 1: Manual Sync

```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.tasks_booking_sync import sync_booking_requests
result = sync_booking_requests()
print(result)
# Should show: {'success': True, 'agencies_synced': 1, 'total_created': X, ...}
exit()
```

#### Test 2: Verify Tasks Created

```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import MonitorTask
tasks = MonitorTask.objects.filter(external_reference__startswith='REQ-')
for task in tasks:
    print(f"✅ Task {task.id}: {task.external_reference} - {task.date} - {task.visitors} visitors")
exit()
```

#### Test 3: Check Worker Logs

```powershell
docker-compose logs -f worker_vatican
```

Should see:
```
[INFO] Monitoring 2 tasks
[INFO] Task REQ-001: 28/03/2026, 2 visitors, standard ticket
[INFO] Task REQ-002: 29/03/2026, 1 visitor, guided tour (ENG)
```

---

### Step 7: Configure Extension

#### A. Install Extension

1. Open Chrome/Edge
2. Go to `chrome://extensions/`
3. Enable "Developer mode"
4. Click "Load unpacked"
5. Select `browser-extension` folder

#### B. Configure Backend URL

1. Click extension icon
2. Click "Settings"
3. Enter backend URL:
   - Local: `http://localhost:8000`
   - Remote: `https://your-domain.com`
4. Click "Save"

#### C. Enable Backend Listener Mode

1. Click extension icon
2. Toggle "Backend Listener Mode" ON
3. Extension will now poll backend every 10 seconds

---

### Step 8: Test Complete Flow

#### A. Add Test Booking Request

In your Google Sheets "Booking Requests" tab, add:

| Request ID | Date | Visitors | Ticket Type | Language | Status | Booking Ref | Created At |
|------------|------|----------|-------------|----------|--------|-------------|------------|
| TEST-001 | 28/03/2026 | 2 | standard | | pending | | 2026-05-22 12:00:00 |

In "Participants" tab, add:

| Request ID | First Name | Last Name | Email | Phone | Birth Date | City | Country |
|------------|------------|-----------|-------|-------|------------|------|---------|
| TEST-001 | Test | User | test@example.com | +39 123456789 | 1990-01-01 | Roma | Italia |
| TEST-001 | Test2 | User2 | test2@example.com | +39 987654321 | 1992-01-01 | Roma | Italia |

#### B. Wait for Auto-Sync (5 minutes max)

Or trigger manually:
```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.tasks_booking_sync import sync_booking_requests
sync_booking_requests()
exit()
```

#### C. Verify Task Created

```powershell
docker-compose logs worker_vatican | Select-String "TEST-001"
```

Should see:
```
[INFO] Task TEST-001: 28/03/2026, 2 visitors
```

#### D. Check Extension

Extension should show:
```
Backend Listener: ON
Polling: Every 10 seconds
Available Slots: 0 (waiting for tickets)
```

When tickets become available, extension will:
1. Detect available slot
2. Open incognito window
3. Auto-fill participant data
4. Complete booking
5. Update Google Sheets status to "booked"

---

## 🔧 Troubleshooting

### Issue: Migration Fails

**Error**: `Migration 0028 already exists`

**Solution**:
```powershell
# Find latest migration
docker-compose exec backend python manage.py showmigrations monitors

# Rename to next number
Rename-Item backend\monitors\migrations\0028_add_external_reference.py 0030_add_external_reference.py

# Edit file and update dependencies
# Run migration again
docker-compose exec backend python manage.py migrate
```

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

### Issue: Extension Not Detecting Slots

**Check extension logs**:
1. Right-click extension icon
2. Click "Inspect popup"
3. Go to Console tab
4. Look for errors

**Common causes**:
1. Backend URL not configured
2. Backend Listener Mode not enabled
3. Backend not running
4. CORS issues (check backend logs)

---

## 📊 System Status Check

Run this to verify everything is working:

```powershell
# Check services running
docker-compose ps

# Check backend logs
docker-compose logs backend | Select-String "sync-booking-requests"

# Check worker logs
docker-compose logs worker_vatican | Select-String "Monitoring"

# Check database
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import Agency, MonitorTask, BuyerProfile

# Check agency
agency = Agency.objects.first()
print(f"Agency: {agency.name}")
print(f"Google Sheet: {agency.google_sheet_url}")

# Check tasks
tasks = MonitorTask.objects.filter(is_active=True)
print(f"\nActive Tasks: {tasks.count()}")
for task in tasks[:5]:
    print(f"  - {task.external_reference}: {task.date}, {task.visitors}v")

# Check buyer profiles
profiles = BuyerProfile.objects.all()
print(f"\nBuyer Profiles: {profiles.count()}")
for profile in profiles:
    print(f"  - {profile.first_name} {profile.last_name}")

exit()
```

---

## ✅ Installation Complete!

Your system is now:
- ✅ Auto-syncing from Google Sheets every 5 minutes
- ✅ Creating monitoring tasks automatically
- ✅ Monitoring Vatican 24/7
- ✅ Extension ready to auto-book
- ✅ Updates Google Sheets when booking completes
- ✅ Works without Telegram

---

## 📚 Next Steps

1. **Add Real Booking Requests** to Google Sheets
2. **Configure Proxies** (see `OXYLABS_PROXY_SETUP.md`)
3. **Test on Multiple Computers** (just install extension + configure backend URL)
4. **Monitor Logs** to ensure everything works

---

## 🆘 Need Help?

Check these files:
- `SETUP_GUIDE.md` - Detailed setup instructions
- `QUICK_START.md` - Quick reference
- `WHATS_DIFFERENT.md` - What changed from Telegram version
- `browser-extension/README.md` - Extension documentation

---

**Installation Time**: ~15 minutes  
**Complexity**: Medium  
**Telegram Required**: No ❌  
**Fully Automated**: Yes ✅  
**Multi-Computer**: Yes ✅
