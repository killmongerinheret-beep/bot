# Testing Setup Guide - Complete Automation

## 🎯 Goal

Set up complete automation where:
1. ✅ Extension listens 24/7 (browser stays open)
2. ✅ Reads participant data from Google Sheets
3. ✅ Automatically detects available slots
4. ✅ Opens incognito windows and books automatically
5. ✅ Uses Oxylabs proxies for requests

---

## 📋 Step 1: Configure Google Sheets

### 1.1 Share Your Google Sheet

**Share with me (for testing)**:
- Share link: [You'll provide this]
- Permission: Viewer (read-only)

**Share with Service Account (for system)**:
1. Open your Google Sheet
2. Click "Share" button
3. Add service account email from `backend/google-credentials.json`
4. Give "Editor" permission
5. Click "Send"

### 1.2 Google Sheet Format

Your sheet should have these columns:

| First Name | Last Name | Email | Phone | Birth Date | City | Country |
|------------|-----------|-------|-------|------------|------|---------|
| John | Doe | john@example.com | +39 123456789 | 1990-01-15 | Roma | Italia |
| Jane | Doe | jane@example.com | +39 987654321 | 1992-03-20 | Roma | Italia |

**Required Columns**:
- `First Name` or `first_name`
- `Last Name` or `last_name`
- `Email` or `email`
- `Phone` or `phone`

**Optional Columns**:
- `Birth Date` or `birth_date` (format: YYYY-MM-DD)
- `City` or `city`
- `Country` or `country`

### 1.3 Add Sheet URL to Agency

```bash
# Connect to backend
docker-compose exec backend python manage.py shell

# In Python shell:
from monitors.models import Agency

# Get your agency (or create one)
agency = Agency.objects.first()  # or Agency.objects.get(id=1)

# Add Google Sheet URL
agency.google_sheet_url = 'YOUR_GOOGLE_SHEET_URL_HERE'
agency.save()

print(f"✅ Google Sheet URL added to Agency {agency.id}")
exit()
```

---

## 📋 Step 2: Import Participants from Google Sheets

### 2.1 Manual Import (Test First)

```bash
# Import participants
docker-compose exec backend python manage.py import_participants --agency-id 1

# Expected output:
# ✅ Imported 2 participants for Agency 1
# - John Doe (john@example.com)
# - Jane Doe (jane@example.com)
```

### 2.2 Verify Import

```bash
# Check database
docker-compose exec backend python manage.py shell

# In Python shell:
from monitors.models import Agency, BuyerProfile

agency = Agency.objects.first()
profile = agency.buyer_profile

print(f"Profile: {profile.first_name} {profile.last_name}")
print(f"Email: {profile.email}")
print(f"Phone: {profile.phone}")

# Check participants
import json
participants = json.loads(profile.participants_json)
print(f"Participants: {len(participants)}")
for p in participants:
    print(f"  - {p['first_name']} {p['last_name']}")

exit()
```

### 2.3 Enable Auto-Sync (Optional)

**Add Google Sheets dependencies**:

```bash
# Edit requirements.txt
echo "gspread==5.12.0" >> requirements.txt
echo "google-auth==2.23.4" >> requirements.txt
echo "google-auth-oauthlib==1.1.0" >> requirements.txt
echo "google-auth-httplib2==0.1.1" >> requirements.txt

# Rebuild containers
docker-compose build backend worker_vatican

# Restart services
docker-compose up -d
```

**Uncomment auto-sync**:

Edit `backend/core/settings.py`:
```python
# Find this section and uncomment:
CELERY_BEAT_SCHEDULE = {
    # ... other tasks ...
    'sync-google-sheets-hourly': {
        'task': 'monitors.tasks_google_sheets.sync_participants_from_sheets',
        'schedule': crontab(minute=0),  # Every hour
    },
}
```

Edit `backend/core/celery.py`:
```python
# Find this section and uncomment:
app.autodiscover_tasks(['monitors.tasks_google_sheets'])
```

**Restart services**:
```bash
docker-compose restart backend worker_vatican
```

---

## 📋 Step 3: Configure Extension for 24/7 Listening

### 3.1 Install Extension

**Chrome**:
1. Open `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `browser-extension` folder
5. Extension icon appears in toolbar

### 3.2 Configure Extension Settings

Click extension icon → Configure:

```
┌─────────────────────────────────────────┐
│  Vatican Ticket Monitor Settings        │
├─────────────────────────────────────────┤
│                                          │
│  Monitor Mode: ● Backend Listener       │
│                ○ Tab Reload              │
│                ○ API Only                │
│                                          │
│  Backend Configuration:                  │
│  ┌─────────────────────────────────┐   │
│  │ Backend URL:                     │   │
│  │ http://localhost:8000            │   │
│  └─────────────────────────────────┘   │
│                                          │
│  ┌─────────────────────────────────┐   │
│  │ API Key: (leave empty)           │   │
│  └─────────────────────────────────┘   │
│                                          │
│  ┌─────────────────────────────────┐   │
│  │ Max Concurrent Bookings: 10      │   │
│  └─────────────────────────────────┘   │
│                                          │
│  ┌─────────────────────────────────┐   │
│  │ Check Interval: 10 seconds       │   │
│  └─────────────────────────────────┘   │
│                                          │
│  Options:                                │
│  ☐ Hold Mode (manual completion)        │
│  ☑ Auto Pay (automatic payment)         │
│                                          │
│  [Start Backend Listener]                │
│                                          │
└─────────────────────────────────────────┘
```

### 3.3 Start 24/7 Listening

1. Click **"Start Backend Listener"**
2. Extension will poll backend every 10 seconds
3. Keep browser open 24/7
4. Extension runs in background

**Verify it's running**:
- Open browser console (F12)
- Go to extension background page
- Should see: `✅ Backend listener started - polling every 10 seconds`

### 3.4 Keep Browser Running 24/7

**Windows**:
```powershell
# Prevent computer from sleeping
powercfg /change standby-timeout-ac 0
powercfg /change monitor-timeout-ac 30

# Keep Chrome running
# Add Chrome to startup programs
```

**Mac**:
```bash
# Prevent Mac from sleeping
sudo pmset -a sleep 0
sudo pmset -a displaysleep 30

# Keep Chrome running
# System Preferences → Users & Groups → Login Items → Add Chrome
```

**Linux**:
```bash
# Prevent system from sleeping
sudo systemctl mask sleep.target suspend.target hibernate.target

# Keep Chrome running
# Add to startup applications
```

---

## 📋 Step 4: Configure Oxylabs Proxies

### 4.1 Proxy Configuration Options

You have 3 options for using proxies:

#### Option 1: Backend Worker Proxies (Recommended)

**Use proxies for Vatican API monitoring** (worker_vatican):

Edit `backend/monitors/models.py`:
```python
# Add Oxylabs proxies to Proxy model
from monitors.models import Proxy

# Add Oxylabs proxies
Proxy.objects.create(
    host='pr.oxylabs.io',
    port=7777,
    username='your-oxylabs-username',
    password='your-oxylabs-password',
    protocol='http',
    is_active=True
)
```

Or import from your JSON file:
```bash
docker-compose exec backend python manage.py shell

# In Python shell:
import json
from monitors.models import Proxy

# Load your proxy list
with open('/app/Proxy lists (2).json', 'r') as f:
    proxies = json.load(f)

# Add to database
for proxy_data in proxies:
    Proxy.objects.create(
        host=proxy_data['host'],
        port=proxy_data['port'],
        username=proxy_data.get('username'),
        password=proxy_data.get('password'),
        protocol='http',
        is_active=True
    )

print(f"✅ Added {Proxy.objects.count()} proxies")
exit()
```

**Enable proxies in worker**:

Edit `.env`:
```env
USE_PROXIES=True
PROXY_ROTATION=True
```

Restart worker:
```bash
docker-compose restart worker_vatican
```

#### Option 2: Extension Proxies (Chrome Extension)

**Configure Chrome to use proxy**:

1. **Install Proxy Extension** (e.g., Proxy SwitchyOmega)
2. **Configure Oxylabs**:
   ```
   Proxy Protocol: HTTP
   Proxy Server: pr.oxylabs.io
   Proxy Port: 7777
   Username: your-oxylabs-username
   Password: your-oxylabs-password
   ```

3. **Apply to incognito windows**:
   - Enable "Allow in incognito" for proxy extension
   - Proxies will be used for all Vatican requests

#### Option 3: System-Wide Proxy

**Windows**:
```
Settings → Network & Internet → Proxy
Manual proxy setup:
  Address: pr.oxylabs.io
  Port: 7777
  Username: your-oxylabs-username
  Password: your-oxylabs-password
```

**Mac**:
```
System Preferences → Network → Advanced → Proxies
Web Proxy (HTTP): pr.oxylabs.io:7777
Secure Web Proxy (HTTPS): pr.oxylabs.io:7777
Username: your-oxylabs-username
Password: your-oxylabs-password
```

### 4.2 Test Proxy Connection

```bash
# Test Oxylabs proxy
curl -x http://your-username:your-password@pr.oxylabs.io:7777 https://ip.oxylabs.io/location

# Expected output:
# {
#   "ip": "xxx.xxx.xxx.xxx",
#   "country": "IT",  # or other country
#   "city": "Rome"
# }
```

### 4.3 Verify Proxies in Worker

```bash
# Check worker logs
docker-compose logs -f worker_vatican | grep -i proxy

# Expected:
# [INFO] Using proxy: http://pr.oxylabs.io:7777
# [INFO] Proxy rotation enabled
# [INFO] Checking Vatican API via proxy...
```

---

## 📋 Step 5: Create Test Monitoring Task

### 5.1 Via Telegram Bot

```
1. Open Telegram
2. Find your bot
3. Send: /monitor
4. Select date: 28/03/2026
5. Select visitors: 2
6. Select ticket type: Standard Entry
7. Bot creates task
```

### 5.2 Via Backend API

```bash
# Create task via API
curl -X POST http://localhost:8000/api/v1/monitor-tasks/ \
  -H "Content-Type: application/json" \
  -d '{
    "agency_id": 1,
    "date": "28/03/2026",
    "visitors": 2,
    "ticket_type": 0,
    "is_active": true
  }'
```

### 5.3 Via Django Shell

```bash
docker-compose exec backend python manage.py shell

# In Python shell:
from monitors.models import MonitorTask, Agency

agency = Agency.objects.first()

task = MonitorTask.objects.create(
    agency=agency,
    date='28/03/2026',
    visitors=2,
    ticket_type=0,  # 0=standard, 1=guided
    is_active=True
)

print(f"✅ Created task {task.id}")
exit()
```

---

## 📋 Step 6: Create Test Slot (Simulate Finding Availability)

### 6.1 Create Test Slot

```bash
# Create test slot
docker-compose exec backend python manage.py shell

# In Python shell:
from monitors.models import HeldSlot, MonitorTask, Agency
import json

agency = Agency.objects.first()
task = MonitorTask.objects.filter(agency=agency, is_active=True).first()

# Get participants from BuyerProfile
profile = agency.buyer_profile
participants = json.loads(profile.participants_json) if profile.participants_json else []

# Create test slot
slot = HeldSlot.objects.create(
    task=task,
    slot_id='TEST-001',
    date='28/03/2026',
    slot_time='10:00',
    ticket_id='2129030053',
    ticket_name='Vatican Museums - Standard Entry',
    visitors=2,
    adult_count=2,
    child_count=0,
    status='held',
    total_price=32.00
)

print(f"✅ Created test slot: {slot.id}")
print(f"   Date: {slot.date} {slot.slot_time}")
print(f"   Visitors: {slot.visitors}")
print(f"   Participants: {len(participants)}")
exit()
```

### 6.2 Verify Slot is Available

```bash
# Check available slots via API
curl http://localhost:8000/api/v1/available-slots/

# Expected output:
# {
#   "slots": [
#     {
#       "id": 1,
#       "date": "28/03/2026",
#       "time": "10:00",
#       "ticket_id": "2129030053",
#       "visitors": 2,
#       "profile": {
#         "first_name": "John",
#         "last_name": "Doe",
#         "email": "john@example.com",
#         "phone": "+39 123456789"
#       },
#       "participants": [
#         {"first_name": "John", "last_name": "Doe"},
#         {"first_name": "Jane", "last_name": "Doe"}
#       ]
#     }
#   ],
#   "count": 1
# }
```

---

## 📋 Step 7: Watch Extension Auto-Book

### 7.1 Monitor Extension Console

1. **Open Extension Background Page**:
   - Chrome: `chrome://extensions/` → Vatican Ticket Monitor → "background page"
   - Or right-click extension icon → Inspect

2. **Watch Console**:
   ```
   ✅ Backend listener started - polling every 10 seconds
   🔄 Checking backend for available slots...
   🎉 Found 1 available slots from backend!
   📋 1 new slots to process
   📦 Opening 1 incognito windows for parallel booking
   ✅ Opened incognito window #1 for 28/03/2026 10:00 (AUTO mode)
   ```

### 7.2 Watch Incognito Window

Extension will:
1. Open incognito window
2. Navigate to Vatican website
3. Select ticket (using ticket_id from backend)
4. Select quantity (2 visitors)
5. Select time slot (10:00 - STRICT)
6. Fill checkout form with participants from Google Sheets
7. Complete booking

**Watch Console in Incognito Window** (F12):
```
Vatican Ticket Monitor - Content Script Loaded
🚀 Auto-booking started...
⏳ Loading Vatican website...
🎫 Step 1/10: Selecting ticket...
✅ Clicked ticket button for: Vatican Museums - Standard Entry
👥 Step 2/10: Setting quantity...
⏰ Step 3/10: Selecting time slot...
✅ Selected EXACT time: 10:00
➡️ Step 4/10: Proceeding to checkout...
📝 Step 5/10: Filling form with participants...
  Manager: John Doe (john@example.com)
  Participant 1: John Doe
  Participant 2: Jane Doe
🔐 Step 6/10: Solving Turnstile...
💳 Step 7/10: Confirming purchase...
⏳ Step 8/10: Waiting for payment page...
✅ Redirected to payment page
💳 Step 9/10: Filling payment details...
💰 Step 10/10: Submitting payment...
✅ Payment submitted! Waiting for confirmation...
🎉 Booking completed successfully!
```

---

## 📋 Step 8: Verify Complete Flow

### 8.1 Check Backend Logs

```bash
# Worker logs
docker-compose logs -f worker_vatican

# Expected:
# [INFO] Monitoring 1 tasks
# [INFO] Checking Vatican API...
# [INFO] Using proxy: http://pr.oxylabs.io:7777
# [INFO] Found 1 available slot
# [INFO] Created HeldSlot: 28/03/2026 10:00
```

### 8.2 Check Extension Logs

```bash
# Extension background console
# Should show:
# ✅ Backend listener started
# 🔄 Checking backend every 10 seconds
# 🎉 Found available slot
# 📦 Opening incognito window
# ✅ Booking completed
```

### 8.3 Check Database

```bash
docker-compose exec backend python manage.py shell

# In Python shell:
from monitors.models import HeldSlot

# Check slot status
slot = HeldSlot.objects.first()
print(f"Slot status: {slot.status}")
print(f"Date: {slot.date} {slot.slot_time}")
print(f"Payment ready: {slot.payment_ready}")

exit()
```

---

## 📋 Step 9: Clean Up Test Slot

```bash
# Delete test slot
docker-compose exec backend python manage.py shell

# In Python shell:
from monitors.models import HeldSlot

# Delete test slots
HeldSlot.objects.filter(slot_id__startswith='TEST').delete()
print("✅ Test slots deleted")

exit()
```

---

## 🔧 Troubleshooting

### Issue: Extension Not Detecting Slot

**Check**:
1. Backend URL correct in extension settings
2. Backend is running: `docker-compose ps`
3. Slot exists: `curl http://localhost:8000/api/v1/available-slots/`
4. Extension console for errors (F12)

**Solution**:
```bash
# Restart backend
docker-compose restart backend

# Check extension console
# Should see polling messages every 10 seconds
```

### Issue: Participants Not Loading

**Check**:
1. Google Sheet URL added to agency
2. Participants imported: `docker-compose exec backend python manage.py import_participants --agency-id 1`
3. BuyerProfile exists in database

**Solution**:
```bash
# Re-import participants
docker-compose exec backend python manage.py import_participants --agency-id 1

# Verify
docker-compose exec backend python manage.py shell
>>> from monitors.models import Agency
>>> agency = Agency.objects.first()
>>> print(agency.buyer_profile.participants_json)
```

### Issue: Proxies Not Working

**Check**:
1. Proxy credentials correct
2. Oxylabs account active
3. Proxy enabled in `.env`: `USE_PROXIES=True`

**Solution**:
```bash
# Test proxy manually
curl -x http://username:password@pr.oxylabs.io:7777 https://ip.oxylabs.io/location

# Check worker logs
docker-compose logs worker_vatican | grep -i proxy
```

### Issue: Incognito Window Opens But Doesn't Book

**Check**:
1. Content script loaded (F12 in incognito window)
2. Participant data available
3. Vatican website structure hasn't changed

**Solution**:
```bash
# Check incognito window console (F12)
# Should see: "Vatican Ticket Monitor - Content Script Loaded"

# If not, reload extension:
# chrome://extensions/ → Reload extension
```

---

## ✅ Final Checklist

Before going live:

- [ ] Google Sheet shared with service account
- [ ] Participants imported successfully
- [ ] Extension installed and configured
- [ ] Backend Listener started
- [ ] Browser set to stay open 24/7
- [ ] Proxies configured (optional)
- [ ] Test slot created and detected
- [ ] Incognito window opened automatically
- [ ] Auto-booking flow completed
- [ ] Test slot cleaned up

---

## 🎯 Next Steps

1. **Share Google Sheet Link**:
   - Share with me for testing
   - Share with service account for system

2. **Test Complete Flow**:
   - Create test slot
   - Watch extension detect and book
   - Verify participant data used

3. **Go Live**:
   - Create real monitoring tasks
   - Keep browser open 24/7
   - Let extension auto-book when tickets found

---

**Ready to test! Share your Google Sheet link and we'll verify the complete flow.** 🚀
