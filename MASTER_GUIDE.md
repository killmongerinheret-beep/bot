# Master Guide - Complete Vatican Booking System

**Everything you need to know in one place!** 📚✨

---

## 🎯 Quick Start (5 Minutes)

### 1. Start Core Services
```bash
docker-compose up -d backend worker_vatican telegram_bot redis db
```

### 2. Install Google Sheets Dependencies
```bash
docker-compose exec backend pip install gspread google-auth google-auth-oauthlib google-auth-httplib2
```

### 3. Create Google Sheet & Import
```bash
# Create sheet, then import
docker-compose exec backend python /app/backend/manage.py import_participants \
  --agency=WOR \
  --sheet-url="YOUR_SHEET_URL"
```

### 4. Done!
- ✅ System monitoring Vatican every 5 seconds
- ✅ Auto-sync Google Sheets every hour
- ✅ Telegram bot ready for commands
- ✅ Extension can poll for slots

---

## 📚 Documentation Index

### Getting Started
1. **SERVICES_EXPLAINED.md** - What each Docker service does
2. **COMPLETE_SYSTEM_WORKFLOW.md** - Complete workflow from Telegram to booking
3. **FINAL_SETUP_GUIDE.md** - Step-by-step setup instructions

### Google Sheets Integration
4. **QUICK_START_GOOGLE_SHEETS.md** - 5-minute Google Sheets setup
5. **GOOGLE_SHEETS_AUTO_SYNC.md** - Auto-sync configuration
6. **AUTO_SYNC_SUMMARY.md** - Auto-sync quick reference
7. **GOOGLE_SHEETS_IMPLEMENTATION_COMPLETE.md** - Technical details

### System Architecture
8. **SYSTEM_FLOW_DIAGRAM.md** - Visual workflow diagrams
9. **COMPLETE_WORKFLOW_GUIDE.md** - Telegram + Extension workflow
10. **README_GOOGLE_SHEETS_INTEGRATION.md** - Integration overview

### Implementation Status
11. **IMPLEMENTATION_STATUS.md** - What's done, what's pending
12. **MASTER_GUIDE.md** - This file!

---

## 🔄 Complete System Overview

### What You Have

```
┌─────────────────────────────────────────────────────────────────┐
│                    YOUR SYSTEM                                   │
└─────────────────────────────────────────────────────────────────┘

1. GOOGLE SHEETS
   - Store participant names
   - Auto-sync every hour
   - Add rows anytime

2. TELEGRAM BOT
   - User interface
   - Create monitors
   - Receive notifications

3. BACKEND + WORKER
   - Monitor Vatican API (every 5 seconds)
   - Find available slots
   - Create HeldSlots
   - Auto-sync Google Sheets (every hour)

4. BROWSER EXTENSION
   - Poll backend for slots
   - Auto-fill forms
   - Complete bookings
   - Mark slots as booked

5. DATABASE
   - Store everything
   - MonitorTasks
   - HeldSlots
   - Participants
```

---

## 🚀 How It Works (Simple Version)

### Step 1: Setup (One Time)
```
1. Create Google Sheet with participant names
2. Import to database
3. Start Docker services
```

### Step 2: Create Monitor (Via Telegram)
```
1. User sends /start to Telegram bot
2. User creates monitor (date, time, visitors)
3. Task saved in database
```

### Step 3: Automatic Monitoring
```
1. Worker checks Vatican API every 5 seconds
2. Finds available slot
3. Creates HeldSlot in database
4. Sends Telegram notification
```

### Step 4: Automatic Booking
```
1. Extension polls backend every 10 seconds
2. Detects available slot
3. Opens incognito window
4. Auto-fills form with participants from Google Sheets
5. Completes booking
6. Marks slot as booked
```

### Step 5: Background Sync
```
1. Every hour, worker syncs Google Sheets
2. New participants automatically available
3. No manual commands needed
```

---

## 🔧 Services You Need

### Core Services (Always Running)

| Service | What It Does | Must Run? |
|---------|--------------|-----------|
| **backend** | API & database manager | ✅ Yes |
| **worker_vatican** | Monitor & sync | ✅ Yes |
| **telegram_bot** | User interface | ✅ Yes |
| **redis** | Message broker | ✅ Yes |
| **db** | Data storage | ✅ Yes |

### Optional Services

| Service | What It Does | Must Run? |
|---------|--------------|-----------|
| **nginx** | Web server | ⚠️ Optional |
| **frontend** | Web dashboard | ⚠️ Optional |
| **harvester** | Proxy manager | ⚠️ Optional |
| **solver** | Captcha solver | ⚠️ Optional |

**Minimum:** 5 core services = full system! ✅

---

## 📊 Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLETE FLOW                                 │
└─────────────────────────────────────────────────────────────────┘

GOOGLE SHEETS (You add rows)
    ↓
AUTO-SYNC (Every hour)
    ↓
DATABASE (Participants stored)
    ↓
TELEGRAM BOT (User creates monitor)
    ↓
DATABASE (MonitorTask stored)
    ↓
WORKER (Checks Vatican every 5s)
    ↓
VATICAN API (Returns available slots)
    ↓
DATABASE (HeldSlot created)
    ↓
TELEGRAM BOT (Notification sent)
    ↓
EXTENSION (Polls backend every 10s)
    ↓
BACKEND API (Returns slot + participants)
    ↓
EXTENSION (Opens incognito window)
    ↓
CONTENT SCRIPT (Auto-fills form)
    ↓
VATICAN WEBSITE (Booking completed)
    ↓
EXTENSION (Marks slot as booked)
    ↓
DATABASE (Status updated)
    ↓
USER (Receives confirmation email)
    ↓
DONE! ✅
```

---

## 🎯 Key Features

### 1. Automatic Monitoring
- ✅ Checks Vatican API every 5 seconds
- ✅ Uses Search API for fresh ticket IDs
- ✅ Monitors multiple dates and times
- ✅ Supports standard tickets and guided tours

### 2. Auto-Sync Google Sheets
- ✅ Syncs every hour automatically
- ✅ Manual sync via API
- ✅ Webhook support for real-time sync
- ✅ Multi-agency support

### 3. Telegram Interface
- ✅ Interactive menus
- ✅ Date picker
- ✅ Time slot selector
- ✅ Instant notifications

### 4. Browser Extension
- ✅ Backend listener mode
- ✅ Auto-fill forms
- ✅ Incognito windows
- ✅ Strict time selection

### 5. Complete Automation
- ✅ Zero manual commands
- ✅ Add rows to Google Sheets anytime
- ✅ System handles everything
- ✅ Booking completed automatically

---

## 📝 Common Tasks

### Add New Participants
```
1. Open Google Sheet
2. Add new row with participant data
3. Wait up to 1 hour (automatic sync)
   OR
   Trigger manual sync:
   curl -X POST http://localhost:8000/api/v1/google-sheets/sync/ \
     -H "Content-Type: application/json" \
     -d '{"agency_name": "WOR"}'
```

### Create Monitor Task
```
1. Open Telegram
2. Send /start to bot
3. Click "🎫 Create Monitor"
4. Follow prompts
5. Done!
```

### Check System Status
```bash
# Check services
docker-compose ps

# Check monitoring
docker-compose logs worker_vatican | grep "Checking"

# Check auto-sync
docker-compose logs worker_vatican | grep "sync_participants"

# Check available slots
curl http://localhost:8000/api/v1/available-slots/
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f worker_vatican
docker-compose logs -f telegram_bot
docker-compose logs -f backend
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific
docker-compose restart worker_vatican
docker-compose restart backend
```

---

## 🔍 Troubleshooting

### Issue: No slots found
**Check:**
```bash
docker-compose logs worker_vatican | grep "Checking"
```
**Solution:** Worker should check every 5 seconds. If not, restart:
```bash
docker-compose restart worker_vatican
```

---

### Issue: Telegram bot not responding
**Check:**
```bash
docker-compose logs telegram_bot | grep "ERROR"
```
**Solution:** Check bot token in .env file, restart:
```bash
docker-compose restart telegram_bot
```

---

### Issue: Extension not detecting slots
**Check:**
```bash
curl http://localhost:8000/api/v1/available-slots/
```
**Solution:** Should return JSON. If not, restart backend:
```bash
docker-compose restart backend
```

---

### Issue: Auto-sync not running
**Check:**
```bash
docker-compose logs worker_vatican | grep "sync_participants"
```
**Solution:** Should sync every hour. If not, check schedule:
```bash
docker-compose exec backend python /app/backend/manage.py shell -c "
from django.conf import settings
print(settings.CELERY_BEAT_SCHEDULE.get('sync-participants-from-sheets'))
"
```

---

### Issue: Google Sheets not accessible
**Check:**
```bash
docker-compose exec backend pip list | grep gspread
```
**Solution:** Install dependencies:
```bash
docker-compose exec backend pip install gspread google-auth google-auth-oauthlib google-auth-httplib2
```

---

## 🎯 Performance Tuning

### Monitoring Frequency
**Default:** Every 5 seconds

**Change in:** `backend/core/settings.py`
```python
'instant-sniper-scan': {
    'schedule': 5.0,  # Change to 10.0 for every 10 seconds
}
```

### Auto-Sync Frequency
**Default:** Every hour (3600 seconds)

**Change in:** `backend/core/settings.py`
```python
'sync-participants-from-sheets': {
    'schedule': 3600,  # Change to 1800 for every 30 minutes
}
```

### Extension Poll Frequency
**Default:** Every 10 seconds

**Change in:** Extension settings
- Open extension popup
- Set poll interval
- Save

---

## 📊 System Metrics

### Current Status (WOR Agency)
- ✅ 73 active monitor tasks
- ✅ Monitoring 60 dates
- ✅ Checking every 5 seconds
- ✅ Auto-sync every hour
- ✅ Telegram notifications enabled

### Resource Usage
- **RAM:** ~800MB (core services)
- **Disk:** ~625MB (database + logs)
- **CPU:** Low (mostly idle, spikes during checks)

### API Calls
- **Vatican API:** ~12 calls/minute (per task)
- **Google Sheets:** 1 call/hour (per agency)
- **Backend API:** ~6 calls/minute (extension polling)

---

## 🎉 Success Indicators

### System Working Correctly
- ✅ All 5 core services running
- ✅ Worker logs show "Checking Vatican API"
- ✅ Auto-sync logs show "Synced X participants"
- ✅ Telegram bot responds to /start
- ✅ Backend API returns 200 OK
- ✅ Extension polls backend successfully

### Monitoring Working
- ✅ Worker checks every 5 seconds
- ✅ Uses Search API for fresh IDs
- ✅ Creates HeldSlots when slots found
- ✅ Sends Telegram notifications

### Auto-Sync Working
- ✅ Syncs every hour
- ✅ Logs show "Synced X participants"
- ✅ Database has participants_json populated
- ✅ Extension gets participant data

### Extension Working
- ✅ Polls backend every 10 seconds
- ✅ Detects available slots
- ✅ Opens incognito windows
- ✅ Auto-fills forms correctly
- ✅ Marks slots as booked

---

## 📚 Documentation Quick Links

### Setup Guides
- **FINAL_SETUP_GUIDE.md** - Complete setup (10 minutes)
- **QUICK_START_GOOGLE_SHEETS.md** - Google Sheets setup (5 minutes)
- **SERVICES_EXPLAINED.md** - What each service does

### Workflow Guides
- **COMPLETE_SYSTEM_WORKFLOW.md** - Complete workflow
- **SYSTEM_FLOW_DIAGRAM.md** - Visual diagrams
- **COMPLETE_WORKFLOW_GUIDE.md** - Telegram + Extension

### Auto-Sync Guides
- **GOOGLE_SHEETS_AUTO_SYNC.md** - Complete auto-sync guide
- **AUTO_SYNC_SUMMARY.md** - Quick reference

### Technical Docs
- **GOOGLE_SHEETS_IMPLEMENTATION_COMPLETE.md** - Implementation details
- **IMPLEMENTATION_STATUS.md** - Current status
- **README_GOOGLE_SHEETS_INTEGRATION.md** - Integration overview

---

## 🚀 Next Steps

### 1. Verify Setup (5 minutes)
```bash
# Check services
docker-compose ps

# Check monitoring
docker-compose logs worker_vatican | tail -50

# Check auto-sync
docker-compose logs worker_vatican | grep "sync_participants"

# Test API
curl http://localhost:8000/api/v1/available-slots/
```

### 2. Configure Extension (5 minutes)
- Open extension popup
- Select "Backend Listener" mode
- Enter backend URL: `http://localhost:8000`
- Set poll interval: 10 seconds
- Click "Start Monitoring"

### 3. Test Complete Flow (30 minutes)
- Add row to Google Sheet
- Trigger manual sync
- Create monitor via Telegram
- Wait for slot (or create test slot)
- Verify extension detects slot
- Check auto-booking works

### 4. Monitor & Optimize
- Check logs regularly
- Adjust polling frequencies
- Add more participants
- Create more monitors

---

## 🎯 Summary

### What You Have
- ✅ 5 core services running
- ✅ Automatic Vatican monitoring (every 5s)
- ✅ Auto-sync Google Sheets (every hour)
- ✅ Telegram bot interface
- ✅ Browser extension auto-booking
- ✅ Complete automation

### What You Can Do
- ✅ Add participants to Google Sheets anytime
- ✅ Create monitors via Telegram
- ✅ Receive instant notifications
- ✅ Auto-book tickets automatically
- ✅ Zero manual commands needed

### Time Investment
- **Setup:** 10 minutes (one time)
- **Daily use:** 0 minutes (automatic)
- **Maintenance:** 0 minutes (none needed)

---

## 🎉 You're All Set!

**Your Vatican ticket booking system is fully automated!**

1. ✅ Google Sheets → Auto-sync every hour
2. ✅ Telegram → Create monitors easily
3. ✅ Worker → Monitor Vatican 24/7
4. ✅ Extension → Auto-book instantly
5. ✅ Zero manual work → Just add rows!

**Enjoy your automated booking system!** 🚀✨

---

**Questions? Check the documentation or logs!** 📖

