# Final Setup Guide - Complete Auto-Sync System

**Everything you need to get auto-sync working!**

---

## 🎯 What You Have Now

### ✅ Implemented (Backend Complete)
1. **Auto-sync task** - Runs every hour automatically
2. **Manual sync API** - Trigger sync on-demand
3. **Webhook support** - Real-time sync capability
4. **Multi-agency support** - Syncs all agencies
5. **Error handling** - Robust and reliable
6. **Monitoring** - Full logging

### ⏳ Pending (Quick Setup)
1. Install Google Sheets dependencies (2 minutes)
2. Create Google Sheet (5 minutes)
3. Run first import (1 minute)
4. Verify auto-sync (1 minute)

**Total time: ~10 minutes**

---

## 🚀 Complete Setup (Step-by-Step)

### Step 1: Install Dependencies (2 minutes)

```bash
# Install Google Sheets packages
docker-compose exec backend pip install gspread google-auth google-auth-oauthlib google-auth-httplib2

# Verify installation
docker-compose exec backend pip list | grep gspread
```

**Expected output:**
```
gspread                5.12.0
google-auth            2.23.4
google-auth-oauthlib   1.1.0
google-auth-httplib2   0.1.1
```

---

### Step 2: Create Google Sheet (5 minutes)

#### 2.1 Create New Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Click **+ Blank** to create new sheet
3. Name it: `Vatican Participants`

#### 2.2 Add Column Headers

Add these exact column names in row 1:

| First Name | Last Name | Email | Phone | Birth Date | Gender | Notes |
|------------|-----------|-------|-------|------------|--------|-------|

#### 2.3 Add Sample Data

Add a few test participants:

| First Name | Last Name | Email              | Phone       | Birth Date | Gender | Notes  |
|------------|-----------|-------------------|-------------|------------|--------|--------|
| Mario      | Rossi     | mario@example.com | 3401234567  | 15/01/1990 | M      | Adult  |
| Luigi      | Verdi     | luigi@example.com | 3407654321  | 20/05/1985 | M      | Adult  |
| Anna       | Bianchi   | anna@example.com  | 3409876543  | 10/03/1992 | F      | Adult  |

#### 2.4 Name the Sheet Tab

1. Right-click the sheet tab at bottom (says "Sheet1")
2. Click **Rename**
3. Enter: `Vatican_Participants`
4. Press Enter

#### 2.5 Make Sheet Public

1. Click **Share** button (top right)
2. Click **Change to anyone with the link**
3. Set to **Viewer**
4. Click **Copy link**
5. Save this URL - you'll need it!

**Example URL:**
```
https://docs.google.com/spreadsheets/d/1ABC123XYZ456DEF789/edit
```

---

### Step 3: First Import (1 minute)

```bash
# Replace YOUR_SHEET_ID with your actual sheet ID from the URL
docker-compose exec backend python /app/backend/manage.py import_participants \
  --agency=WOR \
  --sheet-url="https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
```

**Expected output:**
```
📊 Importing participants from Google Sheet...
✅ Found 3 participants:
  1. Mario Rossi (Adult)
  2. Luigi Verdi (Adult)
  3. Anna Bianchi (Adult)
✅ Updated agency Google Sheet URL
✅ Saved 3 participants to BuyerProfile
```

---

### Step 4: Verify Auto-Sync (1 minute)

#### 4.1 Check Celery Beat Schedule

```bash
docker-compose logs worker_vatican | grep "sync_participants"
```

**Should see:**
```
[tasks: sync_participants_from_sheets]
```

#### 4.2 Test Manual Sync

```bash
curl -X POST http://localhost:8000/api/v1/google-sheets/sync/ \
  -H "Content-Type: application/json" \
  -d '{"agency_name": "WOR"}'
```

**Expected response:**
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

#### 4.3 Check Database

```bash
docker-compose exec -T db psql -U postgres -d ticketbot -c "
SELECT 
    a.name,
    a.google_sheet_url IS NOT NULL as has_sheet_url,
    bp.participants_json IS NOT NULL as has_participants
FROM agencies a
LEFT JOIN buyer_profiles bp ON bp.agency_id = a.id
WHERE a.name = 'WOR';
"
```

**Expected output:**
```
 name | has_sheet_url | has_participants 
------+---------------+------------------
 WOR  | t             | t
```

---

## ✅ Verification Checklist

- [ ] Google Sheets dependencies installed
- [ ] Google Sheet created with correct columns
- [ ] Sheet named `Vatican_Participants`
- [ ] Sheet is public (anyone with link can view)
- [ ] First import completed successfully
- [ ] Agency has google_sheet_url in database
- [ ] BuyerProfile has participants_json populated
- [ ] Manual sync API works
- [ ] Auto-sync task is scheduled

---

## 🔄 How to Use

### Adding New Participants

**Just add a new row to your Google Sheet!**

```
1. Open Google Sheet
2. Add new row with participant data
3. Wait up to 1 hour (automatic sync)
   OR
   Trigger manual sync immediately
4. Done! ✅
```

### Manual Sync (Immediate)

```bash
curl -X POST http://localhost:8000/api/v1/google-sheets/sync/ \
  -H "Content-Type: application/json" \
  -d '{"agency_name": "WOR"}'
```

### Check Sync Logs

```bash
# Recent syncs
docker-compose logs backend | grep "Synced.*participants"

# Real-time monitoring
docker-compose logs -f worker_vatican | grep "sync_participants"
```

---

## 🎯 Complete Workflow

### 1. Setup (One Time)
```
Install dependencies → Create Google Sheet → First import → Verify
```

### 2. Daily Use (Automatic)
```
Add row to Google Sheet → Wait up to 1 hour → Participants synced automatically
```

### 3. Extension Integration
```
Extension polls backend → Gets participants → Auto-fills forms → Books tickets
```

---

## 📊 System Architecture

```
┌─────────────────┐
│  Google Sheets  │  ← You add rows here
│  Vatican_       │
│  Participants   │
└────────┬────────┘
         │
         │ Every hour (Celery Beat)
         ↓
┌─────────────────┐
│  Auto-Sync Task │  ← sync_participants_from_sheets()
│  (Automatic)    │
└────────┬────────┘
         │
         │ Reads sheet via gspread
         ↓
┌─────────────────┐
│    Database     │  ← BuyerProfile.participants_json
│  BuyerProfile   │     Updated automatically
└────────┬────────┘
         │
         │ Extension polls
         ↓
┌─────────────────┐
│  GET /api/v1/   │  ← Returns participants
│ available-slots │
└────────┬────────┘
         │
         │ Extension uses data
         ↓
┌─────────────────┐
│    Extension    │  ← Auto-fills forms
│  Auto-Booking   │     with participant names
└─────────────────┘
```

---

## 🔧 Troubleshooting

### Issue: "No participants found"

**Check sheet structure:**
```bash
# Test sheet access
docker-compose exec backend python /app/backend/manage.py shell -c "
from services.google_sheets_service import get_sheets_service
from monitors.models import Agency

agency = Agency.objects.get(name='WOR')
service = get_sheets_service()
participants = service.get_participants_from_sheet(agency.google_sheet_url)
print(f'Found {len(participants)} participants')
"
```

**Common causes:**
- Sheet name is not `Vatican_Participants`
- Column headers don't match exactly
- Sheet is not public
- No data rows (only headers)

---

### Issue: "Google Sheets client not initialized"

**Check dependencies:**
```bash
docker-compose exec backend pip list | grep gspread
```

**If missing, install:**
```bash
docker-compose exec backend pip install gspread google-auth google-auth-oauthlib google-auth-httplib2
```

---

### Issue: Auto-sync not running

**Check Celery Beat:**
```bash
docker-compose ps | grep worker_vatican
```

**Check schedule:**
```bash
docker-compose logs worker_vatican | grep "sync_participants"
```

**Restart if needed:**
```bash
docker-compose restart worker_vatican
```

---

## 📝 Summary

### What You Get

1. **Automatic hourly sync** - No manual work
2. **Manual sync API** - Trigger anytime
3. **Webhook support** - Real-time sync option
4. **Multi-agency** - Works for all agencies
5. **Robust** - Error handling and logging
6. **Monitored** - Full visibility

### Time Investment

- **Setup:** 10 minutes (one time)
- **Daily use:** 0 minutes (automatic)
- **Maintenance:** 0 minutes (none needed)

### Benefits

- ✅ Never run import command again
- ✅ Always up-to-date (within 1 hour)
- ✅ Add rows anytime
- ✅ Zero maintenance
- ✅ Fully automated

---

## 🎉 You're Done!

**The system is now fully automated!**

Just add rows to your Google Sheet and the system handles the rest:

1. ✅ Auto-sync every hour
2. ✅ Extension polls backend
3. ✅ Forms auto-filled
4. ✅ Bookings completed
5. ✅ Zero manual work

**Enjoy your automated Vatican ticket booking system!** 🚀

---

## 📚 Documentation

- **AUTO_SYNC_SUMMARY.md** - Quick overview
- **GOOGLE_SHEETS_AUTO_SYNC.md** - Complete auto-sync guide
- **QUICK_START_GOOGLE_SHEETS.md** - Initial setup
- **GOOGLE_SHEETS_IMPLEMENTATION_COMPLETE.md** - Technical details
- **SYSTEM_FLOW_DIAGRAM.md** - Visual workflow

---

**Questions? Check the documentation or logs!** 📖

