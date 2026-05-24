# Services Explained - What Each Service Does

**Simple explanation of all Docker services** 🐳

---

## 🎯 Quick Answer

**You need 5 core services running:**

1. **backend** - The brain (API & database manager)
2. **worker_vatican** - The worker (monitors Vatican & syncs Google Sheets)
3. **telegram_bot** - The interface (talks to users)
4. **redis** - The messenger (passes tasks between services)
5. **db** - The memory (stores everything)

**The other 4 services are optional helpers.**

---

## 🔧 Core Services (Always Needed)

### 1. backend (Django API)

**What it is:** Python Django web application

**What it does:**
- Provides REST API endpoints
- Manages database (creates/reads/updates/deletes data)
- Handles user authentication
- Serves requests from extension and Telegram bot

**Example tasks:**
- Extension asks: "Any available slots?" → backend checks database → returns slots
- Telegram bot says: "Create monitor task" → backend saves to database
- Worker says: "I found a slot!" → backend creates HeldSlot in database

**Analogy:** Like a receptionist at a hotel - takes requests, checks records, gives answers

**Must run:** ✅ Always

**Check if running:**
```bash
docker-compose ps | grep backend
curl http://localhost:8000/api/v1/available-slots/
```

---

### 2. worker_vatican (Celery Worker)

**What it is:** Python Celery worker process

**What it does:**
- Monitors Vatican API every 5 seconds
- Checks for available tickets
- Creates HeldSlots when slots found
- Sends Telegram notifications
- Auto-syncs Google Sheets every hour
- Keeps slots alive (recap every 25 minutes)

**Example tasks:**
- Every 5 seconds: "Let me check Vatican API for slots..."
- Slot found: "🎉 Found slot! Creating HeldSlot and notifying user"
- Every hour: "Time to sync Google Sheets participants"

**Analogy:** Like a security guard doing rounds - constantly checking, reporting issues

**Must run:** ✅ Always

**Check if running:**
```bash
docker-compose ps | grep worker_vatican
docker-compose logs worker_vatican | grep "Checking"
```

---

### 3. telegram_bot (Telegram Bot)

**What it is:** Python Telegram bot application

**What it does:**
- Receives messages from users
- Shows interactive menus and keyboards
- Creates monitor tasks via backend API
- Sends notifications to users
- Handles all Telegram commands (/start, /status, etc.)

**Example tasks:**
- User sends /start → Shows main menu
- User clicks "Create Monitor" → Shows date picker
- Slot found → Sends message: "🎉 Slot available!"

**Analogy:** Like a customer service agent - talks to customers, takes orders

**Must run:** ✅ Always

**Check if running:**
```bash
docker-compose ps | grep telegram_bot
docker-compose logs telegram_bot | grep "Bot started"
```

---

### 4. redis (Message Broker & Cache)

**What it is:** Redis in-memory data store

**What it does:**
- Queues Celery tasks (like a to-do list)
- Caches frequently accessed data
- Stores session data
- Passes messages between services

**Example tasks:**
- worker_vatican: "I need to check Vatican API" → redis: "Added to queue"
- backend: "Cache this API response for 5 minutes" → redis: "Cached"
- telegram_bot: "Remember this user's conversation state" → redis: "Stored"

**Analogy:** Like a post office - holds messages until they're picked up

**Must run:** ✅ Always

**Check if running:**
```bash
docker-compose ps | grep redis
docker-compose exec redis redis-cli ping
```

---

### 5. db (PostgreSQL Database)

**What it is:** PostgreSQL relational database

**What it does:**
- Stores ALL data permanently
- MonitorTasks (what to monitor)
- HeldSlots (available slots)
- BuyerProfiles (participant names)
- Agencies (user accounts)
- CheckResults (monitoring history)

**Example tasks:**
- backend: "Save this monitor task" → db: "Saved to monitors_monitortask table"
- worker: "Get all active tasks" → db: "Here are 73 active tasks"
- Extension: "Get available slots" → backend → db: "Here are 3 held slots"

**Analogy:** Like a filing cabinet - stores everything permanently

**Must run:** ✅ Always

**Check if running:**
```bash
docker-compose ps | grep db
docker-compose exec db psql -U postgres -d ticketbot -c "SELECT COUNT(*) FROM monitors_monitortask;"
```

---

## ⚠️ Optional Services (Nice to Have)

### 6. nginx (Web Server)

**What it is:** Nginx reverse proxy

**What it does:**
- Routes web traffic
- Serves frontend files
- Handles SSL/HTTPS
- Load balancing

**When needed:**
- Production deployment
- Serving frontend dashboard
- SSL certificates

**Can skip if:**
- Using Telegram bot only (no web dashboard)
- Development environment
- Accessing backend directly

**Must run:** ⚠️ Optional (production only)

---

### 7. frontend (React Dashboard)

**What it is:** React web application

**What it does:**
- Web UI for monitoring
- Task management interface
- Statistics and charts
- Alternative to Telegram bot

**When needed:**
- Want web dashboard
- Multiple users managing tasks
- Visual statistics

**Can skip if:**
- Using Telegram bot only
- Don't need web interface

**Must run:** ⚠️ Optional (Telegram is primary UI)

---

### 8. harvester (Proxy Harvester)

**What it is:** Python proxy scraper

**What it does:**
- Finds free proxies online
- Tests proxy health
- Updates proxy pool in database
- Rotates dead proxies

**When needed:**
- Using proxies for Vatican API
- Need IP rotation
- Avoiding rate limits

**Can skip if:**
- Not using proxies
- Have static proxy list
- Direct connection works

**Must run:** ⚠️ Optional (if using proxies)

---

### 9. solver (Captcha Solver)

**What it is:** Turnstile token solver

**What it does:**
- Pre-solves Turnstile challenges
- Maintains token pool
- Provides tokens for booking

**When needed:**
- Server-side booking
- Remote agents
- No browser available

**Can skip if:**
- Using browser extension (extension handles Turnstile)
- Manual booking only

**Must run:** ⚠️ Optional (extension handles this)

---

## 📊 Service Communication

```
┌─────────────────────────────────────────────────────────────────┐
│                    HOW SERVICES TALK                             │
└─────────────────────────────────────────────────────────────────┘

telegram_bot ←→ backend ←→ db
     ↓              ↓
   redis ←→ worker_vatican
                    ↓
              Vatican API

Extension ←→ backend ←→ db
```

**Example conversation:**

```
User (Telegram): "Create monitor for June 15"
    ↓
telegram_bot: "Let me call backend API"
    ↓
backend: "Let me save to database"
    ↓
db: "Saved! Task ID: 123"
    ↓
backend: "Done!"
    ↓
telegram_bot: "✅ Monitor created!"

---

worker_vatican: "Time to check tasks"
    ↓
redis: "Here's your task queue"
    ↓
worker_vatican: "Let me check Vatican API"
    ↓
Vatican API: "Here are available slots"
    ↓
worker_vatican: "Found slot! Let me save it"
    ↓
backend: "Let me save to database"
    ↓
db: "Saved! HeldSlot ID: 456"
    ↓
worker_vatican: "Let me notify user"
    ↓
telegram_bot: "Sending notification..."
    ↓
User (Telegram): "🎉 Slot available!"

---

Extension: "Any available slots?"
    ↓
backend: "Let me check database"
    ↓
db: "Here's HeldSlot ID: 456"
    ↓
backend: "Here's the slot with participant data"
    ↓
Extension: "Got it! Opening incognito window..."
```

---

## 🎯 What Happens If a Service Stops?

### backend stops
**Impact:** ❌ Critical
- Telegram bot can't create tasks
- Extension can't get slots
- Worker can't save results
**Fix:** `docker-compose restart backend`

---

### worker_vatican stops
**Impact:** ❌ Critical
- No monitoring (won't find slots)
- No auto-sync (Google Sheets won't update)
- No notifications
**Fix:** `docker-compose restart worker_vatican`

---

### telegram_bot stops
**Impact:** ⚠️ High
- Users can't create monitors
- No Telegram notifications
- Extension still works
**Fix:** `docker-compose restart telegram_bot`

---

### redis stops
**Impact:** ❌ Critical
- Worker can't get tasks
- No task queue
- No caching
**Fix:** `docker-compose restart redis`

---

### db stops
**Impact:** ❌ Critical
- Nothing works (no data)
- All services fail
**Fix:** `docker-compose restart db`

---

### nginx stops
**Impact:** ⚠️ Low
- Frontend not accessible
- Backend still works directly
**Fix:** `docker-compose restart nginx`

---

### frontend stops
**Impact:** ⚠️ Low
- Web dashboard not accessible
- Telegram bot still works
**Fix:** `docker-compose restart frontend`

---

### harvester stops
**Impact:** ⚠️ Low
- Proxy pool not updated
- Existing proxies still work
**Fix:** `docker-compose restart harvester`

---

### solver stops
**Impact:** ⚠️ Low
- No pre-solved tokens
- Extension still solves Turnstile
**Fix:** `docker-compose restart solver`

---

## 🚀 Minimal Setup

### Start Only Core Services

```bash
docker-compose up -d backend worker_vatican telegram_bot redis db
```

**Result:** Full system working! ✅

### Check Core Services

```bash
docker-compose ps | grep -E "backend|worker_vatican|telegram_bot|redis|db"
```

**Should show:**
```
backend          running
worker_vatican   running
telegram_bot     running
redis            running
db               running
```

---

## 📊 Resource Usage

### Core Services (Always Running)

| Service | CPU | RAM | Disk |
|---------|-----|-----|------|
| backend | Low | 200MB | 10MB |
| worker_vatican | Medium | 300MB | 10MB |
| telegram_bot | Low | 150MB | 5MB |
| redis | Low | 50MB | 100MB |
| db | Low | 100MB | 500MB |
| **Total** | **~800MB RAM** | **~625MB Disk** |

### Optional Services

| Service | CPU | RAM | Disk |
|---------|-----|-----|------|
| nginx | Low | 20MB | 5MB |
| frontend | Low | 50MB | 50MB |
| harvester | Low | 100MB | 5MB |
| solver | Medium | 200MB | 5MB |

---

## 🎯 Quick Reference

### Check All Services
```bash
docker-compose ps
```

### Start Core Services Only
```bash
docker-compose up -d backend worker_vatican telegram_bot redis db
```

### Start All Services
```bash
docker-compose up -d
```

### Stop All Services
```bash
docker-compose down
```

### Restart Service
```bash
docker-compose restart worker_vatican
```

### View Logs
```bash
docker-compose logs -f worker_vatican
```

### Check Service Health
```bash
# Backend
curl http://localhost:8000/api/v1/available-slots/

# Redis
docker-compose exec redis redis-cli ping

# Database
docker-compose exec db psql -U postgres -d ticketbot -c "SELECT 1;"

# Worker (check logs)
docker-compose logs worker_vatican | grep "Checking"
```

---

## 🎉 Summary

### Core Services (5) - Always Needed ✅
1. **backend** - API & database manager
2. **worker_vatican** - Monitor & sync worker
3. **telegram_bot** - User interface
4. **redis** - Message broker
5. **db** - Data storage

### Optional Services (4) - Nice to Have ⚠️
6. **nginx** - Web server (production)
7. **frontend** - Web dashboard (alternative UI)
8. **harvester** - Proxy manager (if using proxies)
9. **solver** - Captcha solver (extension handles this)

### Minimum to Run
```bash
docker-compose up -d backend worker_vatican telegram_bot redis db
```

**That's it! 5 services = full system working!** ✨

---

**Now you understand what each service does!** 🎓

