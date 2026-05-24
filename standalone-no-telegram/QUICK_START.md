# Quick Start - Standalone Version

## 🎯 What You Get

A fully automated Vatican ticket booking system that:
- ✅ Reads booking requests from Google Sheets
- ✅ Automatically creates monitoring tasks
- ✅ Monitors Vatican 24/7
- ✅ Auto-books tickets when found
- ✅ Updates Google Sheets with booking status
- ✅ **No Telegram required!**

---

## 📋 Prerequisites

- ✅ Docker installed and running
- ✅ Your current Vatican bot working
- ✅ Google Sheets with service account access
- ✅ Chrome browser for extension

---

## 🚀 Installation (3 Steps)

### 1. Copy Files (1 minute)

```powershell
# Copy new files
Copy-Item standalone-no-telegram\backend\services\booking_sync_service.py backend\services\
Copy-Item standalone-no-telegram\backend\monitors\tasks_booking_sync.py backend\monitors\
Copy-Item standalone-no-telegram\backend\monitors\migrations\0028_add_external_reference.py backend\monitors\migrations\
```

### 2. Update Config (2 minutes)

**Edit `backend/core/settings.py`** - Add to `CELERY_BEAT_SCHEDULE`:
```python
'sync-booking-requests': {
    'task': 'monitors.tasks_booking_sync.sync_booking_requests',
    'schedule': crontab(minute='*/5'),
},
```

**Edit `backend/core/celery.py`** - Add to `autodiscover_tasks`:
```python
'monitors.tasks_booking_sync',
```

**Edit `backend/monitors/views.py`** - See `views.py.additions` file

### 3. Apply Changes (1 minute)

```powershell
# Run migration
docker-compose exec backend python manage.py migrate

# Restart services
docker-compose restart backend worker_vatican
```

**Done!** ✅

---

## 📊 Setup Google Sheets (2 minutes)

### Create Two Sheets

**Sheet 1: "Booking Requests"**
```
Request ID | Date       | Visitors | Ticket Type | Language | Status  | Booking Ref | Created At
REQ-001    | 28/03/2026 | 2        | standard    |          | pending |             | 2026-05-22 10:00:00
```

**Sheet 2: "Participants"**
```
Request ID | First Name | Last Name | Email              | Phone          | Birth Date
REQ-001    | John       | Doe       | john@example.com  | +39 123456789  | 1990-01-15
REQ-001    | Jane       | Doe       | jane@example.com  | +39 987654321  | 1992-03-20
```

---

## 🧪 Test (2 minutes)

### Test Auto-Sync

```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.tasks_booking_sync import sync_booking_requests
result = sync_booking_requests()
print(result)  # Should show: {'success': True, 'total_created': 1}
exit()
```

### Verify Task Created

```powershell
docker-compose exec backend python manage.py shell
```

```python
from monitors.models import MonitorTask
task = MonitorTask.objects.filter(external_reference='REQ-001').first()
print(f"✅ Task: {task.id}, Date: {task.date}, Visitors: {task.visitors}")
exit()
```

### Check Worker

```powershell
docker-compose logs -f worker_vatican
```

Should see:
```
[INFO] Monitoring 1 tasks
[INFO] Task REQ-001: 28/03/2026, 2 visitors
[INFO] Checking Vatican API...
```

---

## 🎬 How It Works

```
1. ADD BOOKING REQUEST TO GOOGLE SHEETS
   ↓
   Request ID: REQ-001
   Date: 28/03/2026
   Visitors: 2
   Status: pending

2. BACKEND AUTO-SYNCS (every 5 minutes)
   ↓
   Creates MonitorTask automatically
   Status changes to: monitoring

3. WORKER MONITORS VATICAN (every 5 seconds)
   ↓
   Checks Vatican Search API
   Creates HeldSlot when tickets found

4. EXTENSION AUTO-BOOKS (polls every 10 seconds)
   ↓
   Detects available slot
   Opens incognito window
   Auto-fills form with Google Sheets data
   Completes booking

5. BACKEND UPDATES GOOGLE SHEETS
   ↓
   Status changes to: booked
   Booking Ref: VAT-2026-001
```

---

## 🔧 Configuration

### Auto-Sync Frequency

Default: Every 5 minutes

To change, edit `backend/core/settings.py`:
```python
'schedule': crontab(minute='*/10'),  # Every 10 minutes
'schedule': crontab(minute='*/1'),   # Every 1 minute
'schedule': crontab(hour='*/1'),     # Every 1 hour
```

### Extension Setup

**On any computer**:
1. Install Chrome
2. Load extension from `browser-extension` folder
3. Configure:
   - Backend URL: `http://your-server-ip:8000`
   - API Key: (leave empty for local)
4. Start Backend Listener
5. Keep browser open 24/7

**Multiple computers can run extension simultaneously!**

---

## 📊 Status Values

| Status | Meaning |
|--------|---------|
| `pending` | New request, not yet monitoring |
| `monitoring` | Worker is checking Vatican |
| `found` | Tickets found, booking in progress |
| `booked` | Successfully booked |
| `failed` | Booking failed |
| `cancelled` | Request cancelled |

---

## ✅ Success Indicators

### Backend Logs
```powershell
docker-compose logs backend | Select-String "Syncing booking requests"
```

Should see every 5 minutes:
```
[INFO] Syncing booking requests for agency 1
[INFO] Agency 1: Created 1 tasks, skipped 0
```

### Worker Logs
```powershell
docker-compose logs worker_vatican | Select-String "Monitoring"
```

Should see:
```
[INFO] Monitoring 1 tasks
[INFO] Task REQ-001: 28/03/2026, 2 visitors
```

### Extension Console
```
Right-click extension icon → Inspect → Console
```

Should see every 10 seconds:
```
🔄 Checking backend for available slots...
```

When slot found:
```
🎉 Found 1 available slots from backend!
📦 Opening incognito window...
```

---

## 🎯 Daily Operation

### What You Do

1. **Add booking requests to Google Sheets**
   - Request ID, Date, Visitors, Ticket Type
   - Status: "pending"

2. **Add participants to Google Sheets**
   - Same Request ID
   - Names, emails, phones

3. **That's it!**

### What System Does

1. **Auto-syncs every 5 minutes**
   - Reads pending requests
   - Creates monitoring tasks
   - Updates status to "monitoring"

2. **Worker monitors 24/7**
   - Checks Vatican every 5 seconds
   - Creates HeldSlot when found

3. **Extension auto-books**
   - Polls backend every 10 seconds
   - Opens incognito windows
   - Completes booking automatically

4. **Updates Google Sheets**
   - Status: "booked"
   - Booking Ref: "VAT-XXX"

---

## 🔄 Bokun Integration

If you have Bokun → Google Sheets automation:

```
BOKUN BOOKING
   ↓ Webhook/API
GOOGLE SHEETS (adds row)
   ↓ Auto-sync (5 min)
BACKEND (creates task)
   ↓ Worker monitors
EXTENSION (auto-books)
   ↓ Updates sheet
GOOGLE SHEETS (status: booked)
   ↓ Webhook/API
BOKUN (booking confirmed)
```

**Fully automated end-to-end!**

---

## 📚 Documentation

- **Installation**: `INSTALL.md` - Detailed installation steps
- **Setup Guide**: `SETUP_GUIDE.md` - Complete setup instructions
- **What's Different**: `WHATS_DIFFERENT.md` - Comparison with Telegram version
- **Main Docs**: `../` - All other documentation

---

## 🆘 Troubleshooting

### Tasks Not Created

1. Check sheet shared with service account
2. Verify sheet names: "Booking Requests" and "Participants"
3. Ensure status is "pending"
4. Check logs: `docker-compose logs backend`

### Extension Not Detecting

1. Check backend URL in extension
2. Verify backend running: `docker-compose ps`
3. Check API: `curl http://localhost:8000/api/v1/available-slots/`
4. Check extension console (F12)

### Worker Not Monitoring

1. Check worker logs: `docker-compose logs worker_vatican`
2. Verify task exists: Check database
3. Restart worker: `docker-compose restart worker_vatican`

---

## 🎉 You're Done!

Your system is now:
- ✅ Fully automated
- ✅ Reading from Google Sheets
- ✅ Monitoring Vatican 24/7
- ✅ Auto-booking tickets
- ✅ Updating Google Sheets
- ✅ Working without Telegram

**Just add booking requests to Google Sheets and let the system handle everything!** 🚀

---

**Setup Time**: ~10 minutes  
**Complexity**: Low 🟢  
**Automation**: 100% ✅  
**Telegram**: Not required ❌  
**Maintenance**: Zero 🎯
