# Google Sheets Auto-Sync - Automatic Participant Updates

**Never run the import command again!** ✨

---

## 🎯 What This Does

The system **automatically syncs** participant names from Google Sheets every hour. When you add a new row to your Google Sheet, it will be imported automatically within 1 hour.

**No manual commands needed!** 🎉

---

## 🔄 How It Works

```
Google Sheets (You add a row)
    ↓
Wait up to 1 hour
    ↓
Auto-Sync Task runs (Celery Beat)
    ↓
Reads Google Sheet
    ↓
Updates Database
    ↓
New participants available immediately!
```

---

## ⚙️ Auto-Sync Configuration

### Option 1: Automatic Hourly Sync (Default) ✅

**Already configured and running!**

The system automatically syncs every hour for all agencies that have `google_sheet_url` configured.

**Schedule:** Every 60 minutes  
**Task Name:** `sync-participants-from-sheets`  
**Queue:** `vatican`

**What it does:**
1. Finds all agencies with Google Sheet URLs
2. Reads each Google Sheet
3. Updates participants in database
4. Logs results

**You don't need to do anything!** Just add rows to your Google Sheet and wait up to 1 hour.

---

### Option 2: Manual Sync (On-Demand)

If you want to sync immediately without waiting:

#### Via API Endpoint

**Sync specific agency:**
```bash
curl -X POST http://localhost:8000/api/v1/google-sheets/sync/ \
  -H "Content-Type: application/json" \
  -d '{"agency_name": "WOR"}'
```

**Sync all agencies:**
```bash
curl -X POST http://localhost:8000/api/v1/google-sheets/sync/ \
  -H "Content-Type: application/json" \
  -d '{}'
```

#### Via Management Command (Old Way)

```bash
docker-compose exec backend python /app/backend/manage.py import_participants --agency=WOR
```

---

### Option 3: Webhook-Based Real-Time Sync (Advanced)

For **instant sync** when you add a row to Google Sheets:

#### Step 1: Set Up Google Apps Script

1. Open your Google Sheet
2. Click **Extensions** → **Apps Script**
3. Paste this code:

```javascript
function onEdit(e) {
  // Get the edited range
  var range = e.range;
  var sheet = range.getSheet();
  
  // Only trigger if editing the Vatican_Participants sheet
  if (sheet.getName() !== 'Vatican_Participants') {
    return;
  }
  
  // Only trigger if editing a data row (not header)
  if (range.getRow() === 1) {
    return;
  }
  
  // Call your backend webhook
  var url = 'http://YOUR_SERVER_IP:8000/api/v1/google-sheets/sync/';
  
  var payload = {
    'agency_name': 'WOR'  // Change to your agency name
  };
  
  var options = {
    'method': 'post',
    'contentType': 'application/json',
    'payload': JSON.stringify(payload),
    'muteHttpExceptions': true
  };
  
  try {
    UrlFetchApp.fetch(url, options);
    Logger.log('Sync triggered successfully');
  } catch (error) {
    Logger.log('Sync failed: ' + error);
  }
}
```

4. Click **Save**
5. Click **Run** → Select `onEdit` → **Authorize**

#### Step 2: Test It

1. Add a new row to your Google Sheet
2. Check backend logs:
   ```bash
   docker-compose logs backend | grep "Synced"
   ```

**Result:** Participants synced **instantly** when you add a row! ⚡

---

## 📊 Sync Status

### Check Auto-Sync Status

```bash
# Check if auto-sync task is scheduled
docker-compose exec backend python /app/backend/manage.py shell -c "
from django.conf import settings
schedule = settings.CELERY_BEAT_SCHEDULE
if 'sync-participants-from-sheets' in schedule:
    print('✅ Auto-sync is configured')
    print(f'Schedule: Every {schedule[\"sync-participants-from-sheets\"][\"schedule\"]} seconds')
else:
    print('❌ Auto-sync not configured')
"
```

### Check Last Sync Time

```bash
# Check backend logs for recent syncs
docker-compose logs backend | grep "Synced.*participants"
```

**Example output:**
```
✅ Synced 3 participants for WOR
✅ Synced 5 participants for TestAgency
🎉 Auto-sync complete: 8 participants synced across 2 agencies
```

---

## 🎯 Sync Frequency Options

### Change Sync Interval

Edit `backend/core/settings.py`:

```python
CELERY_BEAT_SCHEDULE = {
    # ...
    'sync-participants-from-sheets': {
        'task': 'sync_participants_from_sheets',
        'schedule': 1800,  # Change to 30 minutes (1800 seconds)
        'options': {'queue': 'vatican'},
    },
}
```

**Common intervals:**
- Every 15 minutes: `900`
- Every 30 minutes: `1800`
- Every hour: `3600` (default)
- Every 2 hours: `7200`
- Every 6 hours: `21600`

**Restart services after changing:**
```bash
docker-compose restart backend worker_vatican
```

---

## 🔍 Monitoring

### View Sync Logs

```bash
# Real-time logs
docker-compose logs -f worker_vatican | grep "sync_participants"

# Recent syncs
docker-compose logs --tail=100 worker_vatican | grep "Synced"
```

### Check Database

```bash
# Check participants for WOR agency
docker-compose exec -T db psql -U postgres -d ticketbot -c "
SELECT 
    a.id,
    a.name,
    a.google_sheet_url IS NOT NULL as has_sheet_url,
    bp.participants_json IS NOT NULL as has_participants,
    LENGTH(bp.participants_json) as json_length
FROM agencies a
LEFT JOIN buyer_profiles bp ON bp.agency_id = a.id
WHERE a.name = 'WOR';
"
```

---

## 🚨 Troubleshooting

### Auto-Sync Not Running

**Check Celery Beat is running:**
```bash
docker-compose ps | grep worker_vatican
```

**Check logs for errors:**
```bash
docker-compose logs worker_vatican | grep "ERROR"
```

**Manually trigger sync to test:**
```bash
curl -X POST http://localhost:8000/api/v1/google-sheets/sync/ \
  -H "Content-Type: application/json" \
  -d '{"agency_name": "WOR"}'
```

---

### "No participants found"

**Check Google Sheet:**
- Sheet name is `Vatican_Participants`
- Column headers match exactly
- Sheet has data rows (not just headers)
- Sheet is public or service account configured

**Test sheet access:**
```bash
docker-compose exec backend python /app/backend/manage.py shell -c "
from services.google_sheets_service import get_sheets_service
from monitors.models import Agency

agency = Agency.objects.get(name='WOR')
service = get_sheets_service()
participants = service.get_participants_from_sheet(agency.google_sheet_url)
print(f'Found {len(participants)} participants')
for p in participants:
    print(f'  - {p[\"first_name\"]} {p[\"last_name\"]}')
"
```

---

### Sync Fails with Authentication Error

**Check Google Sheets dependencies:**
```bash
docker-compose exec backend pip list | grep gspread
```

**Should show:**
```
gspread                5.12.0
google-auth            2.23.4
google-auth-oauthlib   1.1.0
google-auth-httplib2   0.1.1
```

**If missing, install:**
```bash
docker-compose exec backend pip install gspread google-auth google-auth-oauthlib google-auth-httplib2
```

---

## 📊 API Endpoints

### Manual Sync Endpoint

**URL:** `POST /api/v1/google-sheets/sync/`

**Sync specific agency:**
```bash
curl -X POST http://localhost:8000/api/v1/google-sheets/sync/ \
  -H "Content-Type: application/json" \
  -d '{"agency_name": "WOR"}'
```

**Response:**
```json
{
  "success": true,
  "agency": "WOR",
  "participants_count": 3,
  "participants": [
    {"first_name": "Mario", "last_name": "Rossi"},
    {"first_name": "Luigi", "last_name": "Verdi"},
    {"first_name": "Anna", "last_name": "Bianchi"}
  ]
}
```

**Sync all agencies:**
```bash
curl -X POST http://localhost:8000/api/v1/google-sheets/sync/ \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**
```json
{
  "success": true,
  "agencies_synced": 2,
  "total_participants": 8
}
```

---

## 🎯 Workflow Comparison

### Before (Manual)
```
1. Add row to Google Sheet
2. Open terminal
3. Run: docker-compose exec backend python manage.py import_participants --agency=WOR
4. Wait for import
5. Participants available
```

**Time:** 2-3 minutes  
**Effort:** Manual command every time

---

### After (Auto-Sync)
```
1. Add row to Google Sheet
2. Wait up to 1 hour (or trigger manual sync)
3. Participants available automatically
```

**Time:** 0 seconds (automatic)  
**Effort:** Zero! ✨

---

### With Webhook (Real-Time)
```
1. Add row to Google Sheet
2. Webhook triggers instantly
3. Participants available in 2-3 seconds
```

**Time:** 2-3 seconds  
**Effort:** Zero! ⚡

---

## 📝 Summary

### ✅ What You Get

1. **Automatic hourly sync** - No manual commands needed
2. **Manual sync API** - Trigger sync on-demand via API
3. **Webhook support** - Real-time sync when you add rows
4. **Multi-agency support** - Syncs all agencies automatically
5. **Error handling** - Logs errors, continues with other agencies
6. **Monitoring** - Check logs to see sync status

### 🎯 Recommended Setup

**For most users:**
- Use **automatic hourly sync** (already configured)
- Add rows to Google Sheet anytime
- Wait up to 1 hour for sync
- Zero maintenance required

**For power users:**
- Set up **webhook** for instant sync
- Add rows and see them immediately
- Perfect for high-volume booking

**For testing:**
- Use **manual sync API** to test immediately
- Verify participants imported correctly
- Debug any issues

---

## 🚀 Quick Start

### 1. Verify Auto-Sync is Running

```bash
docker-compose logs worker_vatican | grep "sync_participants"
```

### 2. Add Rows to Google Sheet

Just add new rows - that's it!

### 3. Wait or Trigger Manual Sync

**Wait:** Up to 1 hour for automatic sync

**Or trigger immediately:**
```bash
curl -X POST http://localhost:8000/api/v1/google-sheets/sync/ \
  -H "Content-Type: application/json" \
  -d '{"agency_name": "WOR"}'
```

### 4. Verify Participants Updated

```bash
docker-compose logs backend | grep "Synced.*WOR"
```

**Done!** Your participants are automatically synced! 🎉

---

**No more manual commands - just add rows and go!** ✨

