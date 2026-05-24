# 🚀 START HERE - Standalone Vatican Bot Setup

## 📖 What You Have

A complete Vatican ticket booking automation system that works **without Telegram**:

```
BOKUN → Google Sheets → Backend → Worker → Extension → Auto-Booking
```

**Status**: ✅ Ready to install  
**Time to Install**: 15 minutes  
**Complexity**: Medium  
**Telegram Required**: No

---

## 📁 What's in This Folder

### 🎯 Start With These (In Order)

1. **START_HERE.md** ← You are here
2. **COMPLETE_INSTALL_GUIDE.md** - Step-by-step installation (15 min)
3. **FILES_TO_COPY.md** - List of files to copy
4. **DAILY_OPERATIONS.md** - How to use the system daily

### 📚 Reference Documents

5. **SYSTEM_FLOW_DIAGRAM.md** - Visual system architecture
6. **SETUP_GUIDE.md** - Detailed setup instructions
7. **QUICK_START.md** - Quick reference guide
8. **WHATS_DIFFERENT.md** - Changes from Telegram version

### 🔧 Code Files (Ready to Copy)

```
backend/
├── services/
│   └── booking_sync_service.py (NEW - Google Sheets sync)
└── monitors/
    ├── tasks_booking_sync.py (NEW - Celery task)
    └── migrations/
        └── 0028_add_external_reference.py (NEW - Database migration)
```

---

## 🎯 Quick Decision Tree

### Do you want to...

#### ✅ Install the system now?
→ Go to **COMPLETE_INSTALL_GUIDE.md**

#### ✅ Understand how it works first?
→ Go to **SYSTEM_FLOW_DIAGRAM.md**

#### ✅ See what files to copy?
→ Go to **FILES_TO_COPY.md**

#### ✅ Learn daily operations?
→ Go to **DAILY_OPERATIONS.md**

#### ✅ Quick reference?
→ Go to **QUICK_START.md**

---

## 🚀 Installation Overview (3 Steps)

### Step 1: Copy Files (5 minutes)
```powershell
# Copy 3 new files
Copy-Item standalone-no-telegram\backend\services\booking_sync_service.py backend\services\
Copy-Item standalone-no-telegram\backend\monitors\tasks_booking_sync.py backend\monitors\
Copy-Item standalone-no-telegram\backend\monitors\migrations\0028_add_external_reference.py backend\monitors\migrations\
```

### Step 2: Update Configuration (5 minutes)
- Edit `backend/core/settings.py` (add 1 task to CELERY_BEAT_SCHEDULE)
- Edit `backend/core/celery.py` (add 1 line)
- Edit `backend/monitors/views.py` (add Google Sheets update code)

### Step 3: Run Migration & Restart (5 minutes)
```powershell
docker-compose exec backend python manage.py migrate
docker-compose restart backend worker_vatican
```

**Done!** System is now fully automated.

---

## ✅ What You Get

### Before (Telegram Version)
- ❌ Manual commands via Telegram bot
- ❌ Telegram required for all operations
- ❌ Manual task creation
- ❌ No Google Sheets integration
- ❌ Single computer only

### After (Standalone Version)
- ✅ Fully automated from Google Sheets
- ✅ No Telegram required
- ✅ Auto-creates tasks every 5 minutes
- ✅ Google Sheets integration built-in
- ✅ Works on multiple computers
- ✅ Extension auto-books when tickets found
- ✅ Updates Google Sheets automatically

---

## 📊 System Components

### 1. Google Sheets (Input)
- **Tab 1**: Booking Requests (REQ-001, date, visitors, status)
- **Tab 2**: Participants (names, emails, phones)
- **Update**: Bokun webhook or manual entry
- **Sync**: Every 5 minutes automatically

### 2. Backend (Django + Celery)
- **Reads**: Google Sheets every 5 minutes
- **Creates**: MonitorTasks automatically
- **Stores**: Participant data in BuyerProfile
- **Updates**: Google Sheets when booking completes

### 3. Worker (Vatican Monitor)
- **Monitors**: All active tasks 24/7
- **Checks**: Vatican API every 5 seconds
- **Detects**: Available tickets instantly
- **Creates**: AvailableSlot for extension

### 4. Extension (Chrome/Edge)
- **Polls**: Backend API every 10 seconds
- **Detects**: Available slots
- **Opens**: Incognito window
- **Books**: Automatically with participant data
- **Updates**: Backend when complete

---

## 🎯 Key Features

### ✅ Fully Automated
- Add row to Google Sheets → System handles everything
- No manual commands needed
- Runs 24/7 automatically

### ✅ Multi-Computer Support
- Install extension on any computer
- Just configure backend URL
- Multiple computers work simultaneously

### ✅ Parallel Booking
- Up to 10 concurrent bookings
- Each in separate incognito window
- Independent booking flows

### ✅ Real-Time Monitoring
- Checks Vatican every 5 seconds
- Uses fast Search API approach
- Detects tickets instantly

### ✅ Auto-Fill Participant Data
- Reads from Google Sheets
- Auto-fills all forms
- Supports multiple participants

### ✅ Status Tracking
- Google Sheets updated automatically
- Status: pending → monitoring → booked
- Booking reference stored

---

## 📋 Prerequisites

Before you start, make sure you have:

- ✅ Docker & Docker Compose installed
- ✅ Windows PowerShell (you have this)
- ✅ Bokun → Google Sheets automation working
- ✅ Google Sheets service account credentials
- ✅ Project running at `D:\bot\travelagenntbot`
- ✅ Backend accessible (http://localhost:8000)

**Optional but recommended:**
- ✅ Oxylabs proxy credentials (avoid rate limits)
- ✅ Multiple computers for parallel booking

---

## 🚦 Installation Checklist

Use this checklist while installing:

### Phase 1: File Copy
- [ ] Created `backend/services/` directory
- [ ] Copied `booking_sync_service.py`
- [ ] Copied `tasks_booking_sync.py`
- [ ] Copied `0028_add_external_reference.py`

### Phase 2: Configuration
- [ ] Updated `backend/core/settings.py` (CELERY_BEAT_SCHEDULE)
- [ ] Updated `backend/core/celery.py` (autodiscover_tasks)
- [ ] Updated `backend/monitors/views.py` (Google Sheets update)

### Phase 3: Database
- [ ] Ran migration: `python manage.py migrate`
- [ ] Migration successful (no errors)

### Phase 4: Services
- [ ] Restarted backend: `docker-compose restart backend`
- [ ] Restarted worker: `docker-compose restart worker_vatican`
- [ ] Verified Celery Beat schedule

### Phase 5: Google Sheets
- [ ] Created "Booking Requests" tab
- [ ] Created "Participants" tab
- [ ] Shared with service account email
- [ ] Added sheet URL to agency

### Phase 6: Extension
- [ ] Installed extension in Chrome/Edge
- [ ] Configured backend URL
- [ ] Enabled Backend Listener Mode
- [ ] Verified polling works

### Phase 7: Testing
- [ ] Added test booking request
- [ ] Verified task created
- [ ] Checked worker logs
- [ ] Verified extension detects slots

---

## 🆘 Need Help?

### Installation Issues
→ See **COMPLETE_INSTALL_GUIDE.md** - Troubleshooting section

### Understanding the System
→ See **SYSTEM_FLOW_DIAGRAM.md** - Visual architecture

### Daily Operations
→ See **DAILY_OPERATIONS.md** - Common tasks

### Quick Reference
→ See **QUICK_START.md** - Command reference

---

## 📞 Support Resources

### Documentation Files
- `COMPLETE_INSTALL_GUIDE.md` - Full installation guide
- `FILES_TO_COPY.md` - File list and copy commands
- `SYSTEM_FLOW_DIAGRAM.md` - Architecture diagram
- `DAILY_OPERATIONS.md` - Daily usage guide
- `QUICK_START.md` - Quick reference
- `SETUP_GUIDE.md` - Detailed setup
- `WHATS_DIFFERENT.md` - Changes from Telegram

### Existing Documentation
- `browser-extension/README.md` - Extension documentation
- `browser-extension/QUICK_START.md` - Extension quick start
- `OXYLABS_PROXY_SETUP.md` - Proxy configuration
- `PC_SETUP_GUIDE.md` - PC setup guide

---

## 🎯 Next Steps

### 1. Read Installation Guide (5 minutes)
Open **COMPLETE_INSTALL_GUIDE.md** and read through it once.

### 2. Install System (15 minutes)
Follow the step-by-step instructions in **COMPLETE_INSTALL_GUIDE.md**.

### 3. Test System (10 minutes)
Add a test booking request and verify it works end-to-end.

### 4. Learn Daily Operations (10 minutes)
Read **DAILY_OPERATIONS.md** to understand daily usage.

### 5. Go Live (Ongoing)
Add real booking requests and let the system run automatically.

---

## ✅ Success Criteria

You'll know the installation is successful when:

1. ✅ Celery Beat shows "sync-booking-requests" in logs
2. ✅ Worker logs show "Monitoring X tasks"
3. ✅ Extension shows "Backend Listener: ON"
4. ✅ Test booking request creates MonitorTask
5. ✅ Google Sheets status updates to "monitoring"
6. ✅ Extension detects available slots
7. ✅ Booking completes automatically
8. ✅ Google Sheets status updates to "booked"

---

## 🎉 Ready to Start?

### Option 1: Quick Install (Experienced Users)
→ Go to **FILES_TO_COPY.md** and copy the commands

### Option 2: Guided Install (Recommended)
→ Go to **COMPLETE_INSTALL_GUIDE.md** and follow step-by-step

### Option 3: Understand First
→ Go to **SYSTEM_FLOW_DIAGRAM.md** to see how it works

---

**Installation Time**: 15 minutes  
**Complexity**: Medium  
**Risk**: Low (only adds features, doesn't break existing)  
**Telegram Required**: No ❌  
**Fully Automated**: Yes ✅  
**Multi-Computer**: Yes ✅  
**Production Ready**: Yes ✅

---

## 📝 Quick Commands

```powershell
# Navigate to project
cd D:\bot\travelagenntbot

# Copy files
Copy-Item standalone-no-telegram\backend\services\booking_sync_service.py backend\services\
Copy-Item standalone-no-telegram\backend\monitors\tasks_booking_sync.py backend\monitors\
Copy-Item standalone-no-telegram\backend\monitors\migrations\0028_add_external_reference.py backend\monitors\migrations\

# Run migration
docker-compose exec backend python manage.py migrate

# Restart services
docker-compose restart backend worker_vatican

# Check status
docker-compose logs backend | Select-String "sync-booking-requests"
docker-compose logs worker_vatican | Select-String "Monitoring"
```

---

**Let's get started! Open COMPLETE_INSTALL_GUIDE.md to begin.**
