# Complete System Workflow - Telegram to Google Sheets to Auto-Booking

**Everything in one place!** 📚

---

## 🎯 Overview

Your system has **multiple services** working together. Each service has a specific job:

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOCKER SERVICES                               │
├─────────────────────────────────────────────────────────────────┤
│ 1. backend          - Django API & Admin                        │
│ 2. worker_vatican   - Celery worker (monitors Vatican)          │
│ 3. telegram_bot     - Telegram bot (user interface)             │
│ 4. redis            - Message broker & cache                    │
│ 5. db               - PostgreSQL database                       │
│ 6. nginx            - Web server                                │
│ 7. frontend         - React dashboard (optional)                │
│ 8. harvester        - Proxy harvester (optional)                │
│ 9. solver           - Captcha solver (optional)                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Complete Workflow (Step-by-Step)

### Phase 1: Setup (One Time)

#### Step 1.1: Google Sheets Setup
**Service Needed:** None (manual)

```
1. Create Google Sheet
2. Add columns: First Name, Last Name, Email, Phone, Birth Date, Gender, Notes
3. Add participant data
4. Name sheet: "Vatican_Participants"
5. Make public (Share → Anyone with link → Viewer)
6. Copy URL
```

**Example Sheet:**
| First Name | Last Name | Email              | Phone       |
|------------|-----------|-------------------|-------------|
| Mario      | Rossi     | mario@example.com | 3401234567  |
| Luigi      | Verdi     | luigi@example.com | 3407654321  |

---

#### Step 1.2: Import Participants to Database
**Services Needed:** `backend`, `db`

```bash
docker-compose exec backend python /app/backend/manage.py import_participants \
  --agency=WOR \
  --sheet-url="https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
```

**What happens:**
```
backend service
    ↓
Reads Google Sheet via gspread
    ↓
Stores in PostgreSQL (db service)
    ↓
BuyerProfile.participants_json = [{"first_name": "Mario", ...}]
```

**Result:** Participants now in database ✅

---

### Phase 2: Create Monitor Task

#### Step 2.1: User Starts Telegram Bot
**Services Needed:** `telegram_bot`, `backend`, `db`

```
User opens Telegram
    ↓
Sends: /start
    ↓
telegram_bot service receives message
    ↓
Queries backend API
    ↓
Shows main menu
```

---

#### Step 2.2: User Creates Monitor
**Services Needed:** `telegram_bot`, `backend`, `db`

```
User clicks: "🎫 Create Monitor"
    ↓
telegram_bot shows date picker
    ↓
User selects: June 15, 2026
    ↓
telegram_bot shows visitor count
    ↓
User selects: 2 adults, 0 children
    ↓
telegram_bot shows ticket type
    ↓
User selects: Standard Entry
    ↓
telegram_bot shows time slots
    ↓
User selects: 10:00, 14:00
    ↓
telegram_bot shows mode
    ↓
User selects: ⚡ Snipe
    ↓
telegram_bot asks for participant names
    ↓
User enters: Mario Rossi, Luigi Verdi
    ↓
telegram_bot confirms
    ↓
User clicks: ✅ Confirm
    ↓
telegram_bot calls backend API
    ↓
backend creates MonitorTask in db
    ↓
telegram_bot shows: "✅ Monitor created!"
```

**Database Record Created:**
```json
{
  "agency_id": 14,
  "site": "vatican",
  "dates": ["2026-06-15"],
  "preferred_times": ["10:00", "14:00"],
  "visitors": 2,
  "adult_count": 2,
  "child_count": 0,
  "ticket_type": 0,
  "tier": "snipe",
  "participants_json": "[{\"first_name\":\"Mario\",\"last_name\":\"Rossi\"}...]",
  "is_active": true
}
```

---

### Phase 3: Monitoring (Automatic)

#### Step 3.1: Worker Picks Up Task
**Services Needed:** `worker_vatican`, `redis`, `db`

```
Celery Beat (in worker_vatican)
    ↓
Every 5 seconds triggers: instant_sniper_scan
    ↓
Queries db for active MonitorTasks
    ↓
Finds: Task for June 15, 2026
    ↓
Dispatches check task to redis queue
```

---

#### Step 3.2: Worker Checks Vatican API
**Services Needed:** `worker_vatican`, `redis`

```
worker_vatican picks up task from redis
    ↓
Calls Vatican Search API
    ↓
GET https://tickets.museivaticani.va/api/search/resultPerTag
    params: {
      lang: 'it',
      visitorNum: 2,
      visitDate: '15/06/2026',
      area: '1',
      tag: 'MV-Biglietti'
    }
    ↓
Gets fresh ticket IDs: [{"id": "2129030053", "name": "Musei Vaticani"}]
    ↓
Calls Vatican Timeavail API
    ↓
GET https://tickets.museivaticani.va/api/visit/timeavail
    params: {
      lang: 'it',
      visitLang: '',
      visitTypeId: '2129030053',
      visitorNum: 2,
      visitDate: '15/06/2026'
    }
    ↓
Gets available slots: [{"time": "10:00", "availability": "AVAILABLE"}]
```

**If NO slots found:**
```
worker_vatican logs: "No slots available"
    ↓
Waits 5 seconds
    ↓
Checks again (loop continues)
```

**If slots found:**
```
worker_vatican logs: "🎉 Slot found!"
    ↓
Proceeds to Phase 4
```

---

### Phase 4: Slot Found (Notification + Hold)

#### Step 4.1: Create HeldSlot
**Services Needed:** `worker_vatican`, `db`

```
worker_vatican creates HeldSlot in db
    ↓
HeldSlot record:
{
  "task_id": 123,
  "date": "15/06/2026",
  "slot_time": "10:00",
  "ticket_id": "2129030053",
  "visitors": 2,
  "status": "held",
  "payment_ready": false
}
```

---

#### Step 4.2: Send Telegram Notification
**Services Needed:** `worker_vatican`, `telegram_bot`, `redis`

```
worker_vatican sends notification task to redis
    ↓
telegram_bot picks up notification task
    ↓
Sends message to Telegram group
    ↓
User receives:
"🎉 Slot available!
Date: 15/06/2026
Time: 10:00
Visitors: 2
Ticket: Musei Vaticani - Biglietti d'ingresso"
```

---

### Phase 5: Extension Auto-Booking

#### Step 5.1: Extension Polls Backend
**Services Needed:** `backend`, `db`

```
Browser Extension (running on user's computer)
    ↓
Every 10 seconds polls:
GET http://localhost:8000/api/v1/available-slots/
    ↓
backend queries db for HeldSlots
    ↓
Returns:
{
  "slots": [{
    "id": 123,
    "date": "15/06/2026",
    "time": "10:00",
    "visitors": 2,
    "profile": {
      "first_name": "Mario",
      "last_name": "Rossi",
      "email": "mario@example.com"
    },
    "participants": [
      {"first_name": "Mario", "last_name": "Rossi"},
      {"first_name": "Luigi", "last_name": "Verdi"}
    ],
    "card": {
      "number": "4111...",
      "expiry": "12/2026"
    }
  }]
}
```

---

#### Step 5.2: Extension Opens Incognito Window
**Services Needed:** None (runs in browser)

```
Extension detects slot available
    ↓
Opens new incognito window
    ↓
Loads: https://tickets.museivaticani.va/
    ↓
Content script injected
```

---

#### Step 5.3: Content Script Auto-Books
**Services Needed:** None (runs in browser)

```
Content script starts auto-booking flow:

Step 1: Select ticket
    ↓
Step 2: Set quantity (2 visitors)
    ↓
Step 3: Select time (10:00)
    ↓
Step 4: Click PROCEDI
    ↓
Step 5: Fill checkout form
    - Adult 1: Mario Rossi
    - Adult 2: Luigi Verdi
    - Email: mario@example.com
    - Phone: 3401234567
    ↓
Step 6: Wait for Turnstile
    ↓
Step 7: Click BUY
    ↓
Step 8: Fill payment form
    - Card: 4111...
    - Expiry: 12/2026
    - CVV: 123
    ↓
Step 9: Click PAY
    ↓
Booking complete! ✅
```

---

#### Step 5.4: Extension Marks Slot as Booked
**Services Needed:** `backend`, `db`

```
Extension calls:
POST http://localhost:8000/api/v1/slots/123/mark-booked/
Body: {
  "reference": "VAT-2026-123456",
  "epay_url": "https://epay.vatican.va/..."
}
    ↓
backend updates HeldSlot in db:
{
  "status": "paying",
  "payment_ready": true
}
```

---

### Phase 6: Auto-Sync (Background)

#### Step 6.1: Hourly Auto-Sync
**Services Needed:** `worker_vatican`, `backend`, `db`

```
Every hour, Celery Beat triggers:
sync_participants_from_sheets
    ↓
worker_vatican picks up task
    ↓
Queries db for agencies with google_sheet_url
    ↓
For each agency:
    ↓
  Reads Google Sheet via gspread
    ↓
  Updates BuyerProfile.participants_json in db
    ↓
  Logs: "✅ Synced 3 participants for WOR"
```

**Result:** New participants automatically available! ✅

---

## 🔧 Which Services Are Needed?

### Core Services (Always Needed)

#### 1. **backend** (Django API)
**What it does:**
- Provides REST API endpoints
- Manages database models
- Handles authentication
- Serves extension requests

**Used by:**
- telegram_bot (create tasks)
- worker_vatican (store results)
- Extension (get available slots)

**Must be running:** ✅ Always

---

#### 2. **worker_vatican** (Celery Worker)
**What it does:**
- Monitors Vatican API every 5 seconds
- Checks for available slots
- Creates HeldSlots
- Sends notifications
- Runs auto-sync every hour

**Used by:**
- Celery Beat (scheduled tasks)
- redis (task queue)

**Must be running:** ✅ Always

---

#### 3. **telegram_bot** (Telegram Interface)
**What it does:**
- Receives user commands
- Shows interactive menus
- Creates monitor tasks
- Sends notifications

**Used by:**
- Users (via Telegram app)
- backend (API calls)

**Must be running:** ✅ Always

---

#### 4. **redis** (Message Broker)
**What it does:**
- Queues Celery tasks
- Caches data
- Stores session data

**Used by:**
- backend (cache)
- worker_vatican (task queue)
- telegram_bot (session storage)

**Must be running:** ✅ Always

---

#### 5. **db** (PostgreSQL Database)
**What it does:**
- Stores all data
- MonitorTasks
- HeldSlots
- BuyerProfiles
- Agencies

**Used by:**
- backend (Django ORM)
- All services (via backend)

**Must be running:** ✅ Always

---

### Optional Services

#### 6. **nginx** (Web Server)
**What it does:**
- Reverse proxy
- Serves frontend
- SSL termination

**Used by:**
- External requests
- Frontend

**Must be running:** ⚠️ Optional (for production)

---

#### 7. **frontend** (React Dashboard)
**What it does:**
- Web UI for monitoring
- Task management
- Statistics

**Used by:**
- Users (via browser)

**Must be running:** ⚠️ Optional (Telegram bot is primary UI)

---

#### 8. **harvester** (Proxy Harvester)
**What it does:**
- Finds free proxies
- Tests proxy health
- Updates proxy pool

**Used by:**
- worker_vatican (proxy rotation)

**Must be running:** ⚠️ Optional (if using proxies)

---

#### 9. **solver** (Captcha Solver)
**What it does:**
- Solves Turnstile challenges
- Maintains token pool

**Used by:**
- worker_vatican (when booking)

**Must be running:** ⚠️ Optional (extension handles Turnstile)

---

## 📊 Service Dependencies

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEPENDENCY TREE                               │
└─────────────────────────────────────────────────────────────────┘

telegram_bot
    ├── backend (API calls)
    │   └── db (data storage)
    └── redis (session storage)

worker_vatican
    ├── backend (API calls)
    │   └── db (data storage)
    ├── redis (task queue)
    └── harvester (proxies) [optional]

backend
    ├── db (data storage)
    └── redis (cache)

Extension (Browser)
    └── backend (API calls)
        └── db (data storage)
```

---

## 🚀 Minimal Setup (Core Services Only)

### What You Need

```yaml
services:
  backend:      ✅ Required
  worker_vatican: ✅ Required
  telegram_bot: ✅ Required
  redis:        ✅ Required
  db:           ✅ Required
  nginx:        ⚠️ Optional
  frontend:     ⚠️ Optional
  harvester:    ⚠️ Optional
  solver:       ⚠️ Optional
```

### Start Core Services

```bash
docker-compose up -d backend worker_vatican telegram_bot redis db
```

**Result:** Full system working with 5 services! ✅

---

## 🔄 Complete Flow Summary

### 1. Setup Phase (One Time)
```
Services: backend, db
Action: Import participants from Google Sheets
Result: Participants in database
```

### 2. Create Monitor (User Action)
```
Services: telegram_bot, backend, db
Action: User creates monitor via Telegram
Result: MonitorTask in database
```

### 3. Monitoring (Automatic)
```
Services: worker_vatican, redis, db
Action: Check Vatican API every 5 seconds
Result: Finds available slots
```

### 4. Notification (Automatic)
```
Services: worker_vatican, telegram_bot, db
Action: Create HeldSlot, send Telegram message
Result: User notified
```

### 5. Auto-Booking (Automatic)
```
Services: Extension (browser), backend, db
Action: Poll backend, detect slot, auto-book
Result: Booking completed
```

### 6. Auto-Sync (Background)
```
Services: worker_vatican, backend, db
Action: Sync Google Sheets every hour
Result: Participants always up-to-date
```

---

## 📝 Service Roles Summary

| Service | Role | Always Needed? |
|---------|------|----------------|
| **backend** | API & Database | ✅ Yes |
| **worker_vatican** | Monitor & Sync | ✅ Yes |
| **telegram_bot** | User Interface | ✅ Yes |
| **redis** | Queue & Cache | ✅ Yes |
| **db** | Data Storage | ✅ Yes |
| **nginx** | Web Server | ⚠️ Optional |
| **frontend** | Web Dashboard | ⚠️ Optional |
| **harvester** | Proxy Manager | ⚠️ Optional |
| **solver** | Captcha Solver | ⚠️ Optional |

---

## 🎯 Quick Reference

### Check All Services
```bash
docker-compose ps
```

### Start Core Services
```bash
docker-compose up -d backend worker_vatican telegram_bot redis db
```

### Stop All Services
```bash
docker-compose down
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

### Restart Service
```bash
docker-compose restart worker_vatican
docker-compose restart backend
docker-compose restart telegram_bot
```

---

## 🔍 Troubleshooting

### Issue: "No slots found"
**Check:** worker_vatican logs
```bash
docker-compose logs worker_vatican | grep "Checking"
```

### Issue: "Telegram bot not responding"
**Check:** telegram_bot logs
```bash
docker-compose logs telegram_bot | grep "ERROR"
```

### Issue: "Extension not detecting slots"
**Check:** backend logs
```bash
docker-compose logs backend | grep "available-slots"
```

### Issue: "Auto-sync not running"
**Check:** worker_vatican logs
```bash
docker-compose logs worker_vatican | grep "sync_participants"
```

---

## 🎉 Summary

### Your System Has:

1. **5 Core Services** (always needed)
   - backend, worker_vatican, telegram_bot, redis, db

2. **4 Optional Services** (nice to have)
   - nginx, frontend, harvester, solver

3. **Complete Automation**
   - Telegram → Monitor → Check → Notify → Auto-Book → Sync

4. **Zero Manual Work**
   - Just add rows to Google Sheets
   - System handles everything else

---

## 📚 One-Page Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLETE WORKFLOW                             │
└─────────────────────────────────────────────────────────────────┘

1. SETUP (One Time)
   Google Sheets → backend → db
   
2. CREATE MONITOR
   User → telegram_bot → backend → db
   
3. MONITORING (Every 5s)
   worker_vatican → Vatican API → db
   
4. SLOT FOUND
   worker_vatican → db → telegram_bot → User
   
5. AUTO-BOOKING
   Extension → backend → db
   
6. AUTO-SYNC (Every hour)
   worker_vatican → Google Sheets → db

┌─────────────────────────────────────────────────────────────────┐
│                    SERVICES NEEDED                               │
└─────────────────────────────────────────────────────────────────┘

✅ backend          - API & Database
✅ worker_vatican   - Monitor & Sync
✅ telegram_bot     - User Interface
✅ redis            - Queue & Cache
✅ db               - Data Storage

⚠️ nginx            - Web Server (optional)
⚠️ frontend         - Dashboard (optional)
⚠️ harvester        - Proxies (optional)
⚠️ solver           - Captcha (optional)
```

---

**Everything you need in one file!** 📚✨

