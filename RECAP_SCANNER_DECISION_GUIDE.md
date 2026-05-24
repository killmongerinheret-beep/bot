# Recap Scanner Decision Guide
**Service:** `recap_scanner`  
**Status:** ✅ Running  
**Purpose:** Auto-hold Vatican slots for WOR agency

---

## 🤔 WHAT IS THE RECAP SCANNER?

### Purpose
Automatically scans Vatican tickets and **holds** (recaps) available slots without manual intervention.

### What It Does
1. **Scans** all dates in next 2 months (May-June 2026)
2. **Checks** both standard tickets AND guided tours
3. **Holds** any available slots automatically (via `/api/visit/recap`)
4. **Keeps alive** held slots with periodic re-recap (every 25 min)
5. **Watches** specific priority slot: June 15, 09:30, 20 visitors

### How It Works
```
Every 30 seconds:
  1. Call Search API → Get fresh ticket IDs
  2. Call Time Availability API → Check slots
  3. If AVAILABLE → Call Recap API → Hold slot
  4. Save to HeldSlot table
  5. Send admin notification
  6. Keep session alive (re-recap every 25 min)
```

---

## 📊 CURRENT ACTIVITY

### Service Status
```yaml
Service: recap_scanner
Command: python fast_recap_scanner.py --continuous --visitors 2
Status: ✅ Running
Restart: always (auto-restart on crash)
```

### Recent Activity
```
✅ Successfully recapped guided tour slots (#21987-22016)
✅ Watching June 15 09:30 with 20 visitors every 15 seconds
✅ Sending admin notifications for new recaps
⚠️ Many recap failures (❌ recap FAILED messages)
⚠️ Using direct connection (not proxy pool)
```

### Held Slots
```sql
9 active held slots (status='held')
All for WOR agency
Mix of standard and guided tours
Ages: 1-24 hours
```

---

## ⚠️ ISSUES FOUND

### 1. Recap Failures
```
❌ recap FAILED messages in logs
```

**Possible Causes:**
- Slots already taken by other users
- Session expired before recap
- Rate limiting (using direct connection)
- Vatican API rejecting request

**Impact:** Some slots not held, log noise

### 2. Not Using Proxies
```python
# Code says:
USE_PROXIES = True
load_proxies()  # Loads from database

# But in practice:
_proxy_pool = []  # Empty or not loading correctly
```

**Impact:** 
- Higher chance of rate limiting
- More recap failures
- Single IP doing all requests

### 3. Admin-Only Notifications
```python
_ADMIN_CHAT = os.getenv('ADMIN_TELEGRAM_IDS', '').split(',')[0]
tg_send(f"🔒 New recap: {slot_details}")
```

**Impact:** Only admin gets notified, not agency groups

### 4. Creates Silent Tasks
```python
# Good: Won't interfere with orchestrator
task, _ = MonitorTask.objects.get_or_create(
    agency=agency,
    area_name="Musei Vaticani - Biglietti d'ingresso",
    defaults={
        'is_active': False,          # ← Won't be picked up by orchestrator
        'notification_mode': 'silent', # ← No notifications
    }
)
```

**Impact:** ✅ No conflict with main monitoring (this is good!)

---

## 🎯 DECISION MATRIX

### ✅ KEEP RECAP SCANNER IF:

**Business Need:**
- [ ] You want automatic slot holding for WOR agency
- [ ] You need to lock slots before manual booking
- [ ] June 15 09:30 slot is critical for business
- [ ] You want to hold slots for later payment

**Operational:**
- [ ] You're okay with some recap failures
- [ ] Admin notifications are sufficient
- [ ] You have capacity to monitor held slots
- [ ] You want to maximize slot capture

**Example Use Case:**
> "We need to automatically grab any Vatican slots that open for WOR agency, hold them for 24 hours, then decide which ones to pay for."

### ❌ DISABLE RECAP SCANNER IF:

**Business Need:**
- [ ] You only want notifications (not auto-holding)
- [ ] You prefer manual booking after notification
- [ ] You don't need slots held automatically
- [ ] WOR agency doesn't need this feature

**Operational:**
- [ ] Recap failures are causing too much log noise
- [ ] You want cleaner logs
- [ ] You don't want to manage held slots
- [ ] You prefer simpler system

**Example Use Case:**
> "We just want to be notified when slots open, then book manually. We don't need automatic holding."

---

## 🔧 OPTION 1: KEEP & FIX

If you decide to **KEEP** the recap scanner, fix these issues:

### Fix 1: Enable Proxy Usage

**Check proxy pool:**
```bash
docker-compose exec -T db psql -U postgres -d ticketbot -c \
  "SELECT COUNT(*) as active_proxies FROM monitors_proxy WHERE is_active = true;"
```

**If 0 proxies:**
```bash
# Add proxies to database
docker-compose exec backend python backend/manage.py shell

from monitors.models import Proxy
Proxy.objects.create(
    ip_port='142.111.48.253:7030',
    username='your_username',
    password='your_password',
    is_active=True
)
```

**Verify loading:**
```bash
# Check recap_scanner logs
docker-compose logs recap_scanner | grep "Loaded.*proxies"
# Should see: "Loaded X proxies for rotation"
```

### Fix 2: Investigate Recap Failures

**Check recent failures:**
```bash
docker-compose logs recap_scanner --tail=200 | grep "recap FAILED"
```

**Common causes:**
- Slot already taken (expected, not a bug)
- Session expired (need fresher session)
- Rate limiting (need proxies)
- Invalid ticket ID (need fresh ID from search)

**Add more logging:**
```python
# In fast_recap_scanner.py, add after recap attempt:
if not recap_id:
    logger.error(f"Recap failed: status={r2.status_code}, response={r2.text[:200]}")
```

### Fix 3: Add Agency Group Notifications

**Current:** Only admin gets notified  
**Better:** Send to agency Telegram groups

```python
# In fast_recap_scanner.py, replace tg_send() with:
from monitors.notification_utils import send_telegram_signal
from monitors.models import TelegramGroup

# Get agency's approved groups
groups = TelegramGroup.objects.filter(
    agency=agency,
    status='approved',
    notification_enabled=True
)

for group in groups:
    send_telegram_signal(
        group.chat_id,
        f"🔒 Slot held: {date} {slot_time} | #{held.id}"
    )
```

### Fix 4: Reduce Log Noise

**Option A:** Only log failures (not every attempt)
```python
# Change from:
log(f"{date} {slot_time} — recap FAILED", 'ERR')

# To:
if consecutive_failures > 5:
    log(f"{date} {slot_time} — {consecutive_failures} failures", 'ERR')
```

**Option B:** Separate log file
```python
# Add to fast_recap_scanner.py:
import logging
recap_logger = logging.getLogger('recap_scanner')
recap_handler = logging.FileHandler('recap_scanner.log')
recap_logger.addHandler(recap_handler)
```

---

## 🛑 OPTION 2: DISABLE

If you decide to **DISABLE** the recap scanner:

### Method 1: Stop Service (Temporary)
```bash
# Stop immediately
docker-compose stop recap_scanner

# Restart if needed later
docker-compose start recap_scanner
```

### Method 2: Disable Auto-Restart (Permanent)
```yaml
# Edit docker-compose.yml:
recap_scanner:
  build: .
  restart: "no"  # Change from "always" to "no"
  command: python /app/fast_recap_scanner.py --continuous --visitors 2
  # ... rest of config
```

```bash
# Apply changes
docker-compose up -d recap_scanner
```

### Method 3: Remove Service (Complete Removal)
```yaml
# Edit docker-compose.yml:
# Delete entire recap_scanner section (lines ~80-95)
```

```bash
# Apply changes
docker-compose up -d

# Remove stopped container
docker-compose rm recap_scanner
```

### Cleanup Held Slots (Optional)
```bash
# Release all held slots from recap scanner
docker-compose exec -T db psql -U postgres -d ticketbot -c \
  "UPDATE held_slots 
   SET status = 'released', released_at = NOW() 
   WHERE task_id IN (
     SELECT id FROM monitors_monitortask 
     WHERE agency_id = (SELECT id FROM monitors_agency WHERE name = 'WOR')
     AND is_active = false
   );"
```

---

## 📊 COMPARISON

| Feature | With Recap Scanner | Without Recap Scanner |
|---------|-------------------|----------------------|
| **Slot Detection** | ✅ Automatic | ✅ Automatic (via orchestrator) |
| **Notification** | ✅ Yes (admin only) | ✅ Yes (all approved groups) |
| **Auto-Hold** | ✅ Yes | ❌ No (manual booking) |
| **Session Management** | ✅ Automatic keepalive | ❌ N/A |
| **Complexity** | ⚠️ Higher | ✅ Lower |
| **Log Noise** | ⚠️ More (failures) | ✅ Less |
| **Resource Usage** | ⚠️ Higher (extra service) | ✅ Lower |
| **Use Case** | Bulk slot holding | Notification + manual booking |

---

## 🎯 RECOMMENDATION

### For Most Users: **DISABLE**

**Reasons:**
1. ✅ Main monitoring already detects slots (orchestrator)
2. ✅ Telegram notifications already working
3. ✅ Simpler system (one less service)
4. ✅ Cleaner logs (no recap failures)
5. ✅ Lower resource usage

**When to book:**
- Get Telegram notification
- Click booking link
- Complete payment manually

### For Power Users: **KEEP & FIX**

**Reasons:**
1. ✅ Automatic slot holding (no manual action)
2. ✅ 24-hour hold window (decide later)
3. ✅ Bulk slot capture (hold many at once)
4. ✅ Priority slot watching (June 15 09:30)

**Requirements:**
- Fix proxy usage (reduce failures)
- Monitor held slots regularly
- Manage payment for held slots
- Accept some log noise

---

## 🚀 QUICK START

### To Disable (Recommended for Most)
```bash
# Stop the service
docker-compose stop recap_scanner

# Verify it's stopped
docker-compose ps | grep recap_scanner
# Should show: Exit 0 or not running
```

### To Keep & Fix
```bash
# 1. Check proxy pool
docker-compose exec -T db psql -U postgres -d ticketbot -c \
  "SELECT COUNT(*) FROM monitors_proxy WHERE is_active = true;"

# 2. If 0, add proxies (see Fix 1 above)

# 3. Restart service
docker-compose restart recap_scanner

# 4. Monitor logs
docker-compose logs -f recap_scanner
```

---

## 📈 MONITORING

### If Keeping Recap Scanner

**Check held slots:**
```bash
docker-compose exec -T db psql -U postgres -d ticketbot -c \
  "SELECT id, date, slot_time, ticket_name, status, 
   EXTRACT(EPOCH FROM (NOW() - hold_started_at))/3600 as age_hours
   FROM held_slots 
   WHERE status IN ('held', 'paying') 
   ORDER BY hold_started_at DESC;"
```

**Check recap activity:**
```bash
# Recent recaps
docker-compose logs recap_scanner --tail=50 | grep "NEW\|FAILED"

# Success rate
docker-compose logs recap_scanner | grep -c "NEW"  # Successes
docker-compose logs recap_scanner | grep -c "FAILED"  # Failures
```

**Check proxy usage:**
```bash
docker-compose logs recap_scanner | grep "proxy="
# Should see: proxy=yes (if proxies working)
```

### If Disabled

**Verify stopped:**
```bash
docker-compose ps | grep recap_scanner
# Should show: Exit 0 or not listed
```

**Check main monitoring still working:**
```bash
docker-compose logs worker_vatican --tail=20 | grep "Found.*slots"
# Should see continuous checks
```

---

## ✅ DECISION CHECKLIST

Before deciding, answer these questions:

- [ ] Do we need automatic slot holding? (Yes = Keep, No = Disable)
- [ ] Do we have time to manage held slots? (No = Disable)
- [ ] Are recap failures acceptable? (No = Disable or Fix)
- [ ] Do we have proxies configured? (No = Fix before keeping)
- [ ] Is June 15 09:30 critical? (Yes = Keep, No = Disable)
- [ ] Do we prefer simpler system? (Yes = Disable)

**If mostly "Disable" answers:** Stop the service  
**If mostly "Keep" answers:** Fix the issues first

---

## 📞 SUPPORT

### Check Service Status
```bash
docker-compose ps recap_scanner
```

### View Live Logs
```bash
docker-compose logs -f recap_scanner
```

### Restart Service
```bash
docker-compose restart recap_scanner
```

### Stop Service
```bash
docker-compose stop recap_scanner
```

---

**RECOMMENDATION:** Disable for most users (simpler, cleaner)  
**ALTERNATIVE:** Keep & fix for power users (automatic holding)  
**DECISION:** Up to you based on business needs
