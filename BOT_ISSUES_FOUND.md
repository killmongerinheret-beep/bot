# 🚨 BOT ISSUES FOUND - CRITICAL

**Date:** March 3, 2026  
**Status:** ❌ MULTIPLE CRITICAL ISSUES

---

## 🔍 ISSUES IDENTIFIED FROM LOGS

### 1. ❌ NO ACTIVE PROXIES
**Severity:** CRITICAL  
**Impact:** Bot cannot connect to Vatican website

```
Active proxies: 0
```

**Symptoms:**
```
ERR_TUNNEL_CONNECTION_FAILED
Browser refresh failed: Page.goto: net::ERR_TUNNEL_CONNECTION_FAILED
```

**Why This Happens:**
- All proxies are disabled or on cooldown
- Proxy database is empty
- Proxies failed too many times and were deactivated

**Fix:**
```bash
# Check proxy status
docker exec backend python /app/backend/manage.py shell -c "
from monitors.models import Proxy;
print(f'Total proxies: {Proxy.objects.count()}');
print(f'Active proxies: {Proxy.objects.filter(is_active=True).count()}');
print(f'On cooldown: {Proxy.objects.filter(cooldown_until__isnull=False).count()}')
"

# Reset all proxies
docker exec backend python /app/backend/manage.py shell -c "
from monitors.models import Proxy;
Proxy.objects.all().update(is_active=True, consecutive_failures=0, cooldown_until=None);
print('All proxies reset')
"
```

---

### 2. ❌ STALE TICKET IDs
**Severity:** CRITICAL  
**Impact:** Bot uses old ticket IDs, gets API 500 errors, reports false "CLOSED"

```
Timeout waiting for ticket elements
Resolving fresh ID for name 'Musei Vaticani - Biglietti d'ingresso' among 0 candidates
No name match for 'Musei Vaticani - Biglietti d'ingresso'. Candidates: []
Falling back to stale ID 1750097398 (Risky)
```

**Why This Happens:**
1. Bot can't load Vatican page (proxy issues)
2. No tickets extracted (0 candidates)
3. Falls back to database ticket_id `1750097398`
4. This ID is stale (Vatican changes IDs frequently)
5. API returns 500 error
6. Bot reports "CLOSED" (wrong!)

**The Chain of Failure:**
```
No Proxies → Can't Load Page → No Tickets Extracted → Use Stale ID → API 500 → Report CLOSED
```

---

### 3. ❌ API ERRORS (500/504)
**Severity:** HIGH  
**Impact:** Vatican API rejects requests

```
API call failed: Status 500 - Internal Server Error
API call failed: Status 504 - Gateway Timeout
Ticket ID might be stale, will retry with fresh IDs
```

**Why This Happens:**
- Using stale ticket ID `1750097398`
- Vatican API doesn't recognize this ID anymore
- Returns 500 error instead of valid response

**Correct Flow:**
1. Navigate to deep link
2. Extract fresh ticket IDs from page
3. Use fresh ID in API call
4. Get valid response

**Current Broken Flow:**
1. Try to navigate (fails - no proxies)
2. Can't extract IDs (page didn't load)
3. Use stale ID from database
4. API rejects it (500 error)
5. Report as CLOSED (wrong!)

---

### 4. ❌ FALSE "CLOSED" REPORTS
**Severity:** CRITICAL  
**Impact:** Users get wrong information

```
Musei Vaticani - Biglietti d'ingresso is CLOSED (0 slots)
```

**Why This Is Wrong:**
- Bot didn't actually check availability
- It failed to load the page
- It used a stale ID
- API returned error
- Bot interpreted error as "closed"

**Reality:**
- Tickets might be AVAILABLE
- Bot just couldn't check properly
- Users miss booking opportunities

---

## 🎯 ROOT CAUSE ANALYSIS

### Primary Issue: NO PROXIES
```
Active proxies: 0
```

This causes a cascade of failures:

```
No Proxies
    ↓
Can't Connect to Vatican
    ↓
Can't Load Ticket Page
    ↓
Can't Extract Fresh IDs
    ↓
Falls Back to Stale ID (1750097398)
    ↓
API Returns 500 Error
    ↓
Bot Reports "CLOSED" (WRONG!)
```

---

## ✅ SOLUTIONS

### Solution 1: Fix Proxies (URGENT)

#### Check Proxy Status:
```bash
docker exec backend python /app/backend/manage.py shell -c "
from monitors.models import Proxy;
from django.utils import timezone;
now = timezone.now();
total = Proxy.objects.count();
active = Proxy.objects.filter(is_active=True).count();
cooldown = Proxy.objects.filter(cooldown_until__gt=now).count();
print(f'Total: {total}, Active: {active}, Cooldown: {cooldown}')
"
```

#### Reset All Proxies:
```bash
docker exec backend python /app/backend/manage.py shell -c "
from monitors.models import Proxy;
Proxy.objects.all().update(
    is_active=True,
    consecutive_failures=0,
    fail_count=0,
    cooldown_until=None
);
print('✅ All proxies reset and activated')
"
```

#### Seed Proxies (if empty):
```bash
docker exec backend python /app/backend/manage.py seed_proxies
```

---

### Solution 2: Clear Stale Ticket IDs

#### Option A: Set to NULL (Recommended)
```bash
docker exec backend python /app/backend/manage.py shell -c "
from monitors.models import MonitorTask;
updated = MonitorTask.objects.filter(site='vatican').update(ticket_id=None);
print(f'✅ Cleared {updated} stale ticket IDs')
"
```

This forces the bot to always extract fresh IDs.

#### Option B: Update to Fresh IDs
Run the bot once with proxies working, it will update IDs automatically.

---

### Solution 3: Improve Error Handling

The bot should NOT report "CLOSED" when it encounters errors. It should report "ERROR" or "UNKNOWN".

**Current Logic:**
```python
if api_error:
    report_as_closed()  # ❌ WRONG
```

**Correct Logic:**
```python
if api_error:
    report_as_error()  # ✅ CORRECT
    retry_with_fresh_ids()
```

---

## 🔧 IMMEDIATE ACTIONS NEEDED

### 1. Reset Proxies (NOW)
```bash
docker exec backend python /app/backend/manage.py shell -c "
from monitors.models import Proxy;
Proxy.objects.all().update(is_active=True, consecutive_failures=0, cooldown_until=None);
print('Proxies reset')
"
```

### 2. Clear Stale IDs (NOW)
```bash
docker exec backend python /app/backend/manage.py shell -c "
from monitors.models import MonitorTask;
MonitorTask.objects.filter(site='vatican').update(ticket_id=None);
print('Stale IDs cleared')
"
```

### 3. Restart Worker (NOW)
```bash
docker-compose restart worker_vatican
```

### 4. Monitor Logs
```bash
docker-compose logs -f worker_vatican | grep -E "CLOSED|AVAILABLE|ERROR|WARNING"
```

---

## 📊 EXPECTED BEHAVIOR AFTER FIX

### Before Fix:
```
[ERROR] ERR_TUNNEL_CONNECTION_FAILED
[WARNING] No name match. Candidates: []
[WARNING] Falling back to stale ID 1750097398
[WARNING] API call failed: Status 500
[INFO] Musei Vaticani is CLOSED (0 slots)  ← WRONG!
```

### After Fix:
```
[INFO] 🍪 Session Cookies: 3 cookies set
[INFO] ✅ Ticket buttons are visible
[INFO] 🔢 Resolved 10 Dynamic IDs from Page
[INFO]    • ID: 2092730005 | Name: Musei Vaticani - Biglietti d'ingresso
[INFO] ✅ Exact Match: 'Musei Vaticani - Biglietti d'ingresso' -> ID 2092730005
[INFO] ✅ API Response: 200 - 20 total slots
[INFO] ✅ Found 10 available slots
[INFO] ℹ️ Musei Vaticani still AVAILABLE - no alert needed
```

---

## 🎯 VERIFICATION CHECKLIST

After applying fixes:

- [ ] Proxies are active: `Active proxies: > 0`
- [ ] No tunnel errors: No `ERR_TUNNEL_CONNECTION_FAILED`
- [ ] Fresh IDs extracted: `Resolved X Dynamic IDs from Page`
- [ ] No stale ID warnings: No `Falling back to stale ID`
- [ ] No API 500 errors: `API Response: 200`
- [ ] Correct status reports: `AVAILABLE` or `SOLD_OUT` (not false `CLOSED`)
- [ ] Slots found: `Found X available slots`

---

## 📝 PREVENTION

### 1. Monitor Proxy Health
```bash
# Daily check
docker exec backend python /app/backend/manage.py shell -c "
from monitors.models import Proxy;
print(f'Active: {Proxy.objects.filter(is_active=True).count()}')
"
```

### 2. Never Store Ticket IDs
- Always set `ticket_id=None` in database
- Always extract fresh IDs from page
- Never fall back to stale IDs

### 3. Proper Error Handling
- API errors → Report as "ERROR", not "CLOSED"
- Connection errors → Retry with different proxy
- Timeout errors → Retry, don't report as closed

---

## 🚨 CURRENT STATUS

| Issue | Status | Impact |
|-------|--------|--------|
| No Active Proxies | ❌ CRITICAL | Bot can't connect |
| Stale Ticket IDs | ❌ CRITICAL | API 500 errors |
| False CLOSED Reports | ❌ CRITICAL | Wrong information |
| API Errors | ❌ HIGH | Can't check availability |

**Action Required:** IMMEDIATE - Fix proxies and clear stale IDs

---

**Last Checked:** March 3, 2026 12:54 CET  
**Status:** ❌ BOT NOT WORKING CORRECTLY  
**Priority:** 🚨 URGENT FIX NEEDED
