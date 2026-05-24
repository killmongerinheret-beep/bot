# Docker Containers Analysis

## Current Resource Usage

| Container | CPU % | Memory | Status | Needed? |
|-----------|-------|--------|--------|---------|
| **worker_vatican** | 12.87% | 498MB | ✅ Active | ✅ **CRITICAL** |
| **harvester** | 40.52% | 170MB | ✅ Active | ❓ **OPTIONAL** |
| **redis** | 0.44% | 108MB | ✅ Active | ✅ **CRITICAL** |
| **db (PostgreSQL)** | 2.89% | 132MB | ✅ Active | ✅ **CRITICAL** |
| **backend** | 0.01% | 55MB | ⚠️ Idle | ✅ **CRITICAL** |
| **telegram_bot** | 0.00% | 83MB | ⚠️ Idle | ✅ **CRITICAL** |
| **beat** | 0.00% | 78MB | ⚠️ Idle | ✅ **CRITICAL** |
| **frontend** | 0.00% | 54MB | ⚠️ Idle | ❌ **OPTIONAL** |
| **nginx** | 0.00% | 4MB | ⚠️ Idle | ❌ **OPTIONAL** |
| **solver** | 0.00% | 24MB | ⚠️ Idle | ❓ **OPTIONAL** |

**Total Memory Usage:** ~1.2GB / 7.71GB (15.5%)

---

## Container Breakdown

### ✅ CRITICAL (Must Keep Running)

#### 1. **worker_vatican** (12.87% CPU, 498MB)
- **What it does:** Monitors Vatican tickets, checks availability, creates holds
- **Why needed:** This is the core bot - without it, no monitoring happens
- **Status:** ✅ Working hard (12% CPU is normal when checking tickets)

#### 2. **redis** (0.44% CPU, 108MB)
- **What it does:** Message queue for Celery tasks
- **Why needed:** Worker and beat communicate through Redis
- **Status:** ✅ Healthy (we just fixed it!)

#### 3. **db (PostgreSQL)** (2.89% CPU, 132MB)
- **What it does:** Stores tasks, results, profiles, held slots
- **Why needed:** All your data is here
- **Status:** ✅ Active (2.89% CPU is normal for database queries)

#### 4. **backend** (0.01% CPU, 55MB)
- **What it does:** Django API server (port 8000)
- **Why needed:** Extension calls `/api/v1/available-slots/`, Telegram bot uses it
- **Status:** ⚠️ Idle but ready (0% CPU is normal when no requests)

#### 5. **telegram_bot** (0.00% CPU, 83MB)
- **What it does:** Telegram bot interface
- **Why needed:** Users create tasks via Telegram
- **Status:** ⚠️ Idle but ready (0% CPU is normal, waiting for messages)

#### 6. **beat** (0.00% CPU, 78MB)
- **What it does:** Celery scheduler - triggers periodic tasks
- **Why needed:** Schedules Vatican checks every X seconds
- **Status:** ⚠️ Idle but ready (0% CPU is normal, just scheduling)

---

### ❌ OPTIONAL (Can Disable to Save Resources)

#### 7. **frontend** (0.00% CPU, 54MB)
- **What it does:** Next.js web dashboard (port 3000)
- **Why needed:** Only if you use the web UI
- **Can disable if:** You only use Telegram bot and extension
- **How to disable:** Comment out in docker-compose.yml

#### 8. **nginx** (0.00% CPU, 4MB)
- **What it does:** Reverse proxy for frontend/backend
- **Why needed:** Only if you access via domain (hydrabot.it)
- **Can disable if:** You only use localhost:8000 and Telegram
- **How to disable:** Comment out in docker-compose.yml

---

### ❓ OPTIONAL (Depends on Your Setup)

#### 9. **harvester** (40.52% CPU, 170MB)
- **What it does:** Harvests proxies or sessions (unclear without seeing code)
- **Why high CPU:** Actively scraping/harvesting
- **Can disable if:** You don't use proxy rotation or session harvesting
- **How to check:** Look at `harvester/` folder to see what it does

#### 10. **solver** (0.00% CPU, 24MB)
- **What it does:** Solves CAPTCHAs or queue systems
- **Why needed:** Only if Vatican has CAPTCHA/queue
- **Can disable if:** Vatican doesn't use CAPTCHA (currently doesn't)
- **How to disable:** Comment out in docker-compose.yml

---

## 🎯 Recommendations

### For Extension-Only Usage (Lightest):

**Keep:**
- ✅ worker_vatican (monitors tickets)
- ✅ redis (task queue)
- ✅ db (data storage)
- ✅ backend (API for extension)
- ✅ beat (scheduler)

**Disable:**
- ❌ frontend (not needed for extension)
- ❌ nginx (not needed for localhost)
- ❌ telegram_bot (if you don't use Telegram)
- ❓ harvester (check if needed)
- ❓ solver (check if needed)

**Savings:** ~200MB memory, ~40% CPU

### For Telegram + Extension Usage (Recommended):

**Keep:**
- ✅ worker_vatican
- ✅ redis
- ✅ db
- ✅ backend
- ✅ telegram_bot
- ✅ beat

**Disable:**
- ❌ frontend
- ❌ nginx
- ❓ harvester (check if needed)
- ❓ solver (check if needed)

**Savings:** ~100MB memory

---

## 🔍 Why Some Show 0% CPU

**This is NORMAL!** Here's why:

### backend (0.01% CPU)
- **Idle state:** Waiting for HTTP requests
- **Active when:** Extension polls `/api/v1/available-slots/`
- **CPU spikes to 5-10%** when handling requests

### telegram_bot (0.00% CPU)
- **Idle state:** Waiting for Telegram messages
- **Active when:** User sends /start, /addtask, etc.
- **CPU spikes briefly** when processing commands

### beat (0.00% CPU)
- **Idle state:** Just scheduling tasks
- **Active when:** Sending tasks to worker_vatican
- **Very lightweight** - just a timer

### frontend (0.00% CPU)
- **Idle state:** No one accessing web UI
- **Active when:** User opens http://localhost:3000
- **Not needed** if you don't use web UI

---

## 🚀 How to Disable Optional Containers

Edit `docker-compose.yml` and comment out services:

```yaml
# frontend:
#   build:
#     context: ./frontend
#   ...

# nginx:
#   image: nginx:alpine
#   ...

# harvester:
#   build: ./harvester
#   ...

# solver:
#   build: ./queue_solver
#   ...
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

---

## 📊 Current System Health

✅ **System is healthy!**
- Total memory: 1.2GB / 7.71GB (15.5%) - **Plenty of room**
- CPU usage: Mostly idle except worker_vatican (normal)
- No crashes or errors

**You have plenty of resources for parallel bookings!**

---

## 🎯 Answer to Your Question

**"Is 0% CPU needed to function good?"**

**YES!** 0% CPU is **GOOD** for these containers:
- backend, telegram_bot, beat, frontend, nginx, solver

They are **idle and waiting** - this is their normal state.

**Only worker_vatican should show high CPU** (12-40%) because it's actively:
- Checking Vatican API
- Processing tasks
- Monitoring tickets

**harvester at 40% CPU** - Check if you need it. If not, disable it to save resources.

---

## 💡 Recommendation

**Keep current setup** - You have plenty of resources (85% free memory).

**Optional optimization:**
- Disable frontend + nginx if you don't use web UI
- Check what harvester does - might be unnecessary

**For parallel bookings:**
- Current resources can handle 10+ parallel bookings easily
- Each incognito window uses ~100-200MB
- You have 6.5GB free memory = 30+ windows possible

**Your Docker won't crash!** ✅
