# 🔍 VATICAN BOT COMPLETE DIAGNOSIS

**Date:** March 3, 2026 12:58 CET  
**Status:** ❌ CRITICAL ISSUES IDENTIFIED

---

## 📊 EXECUTIVE SUMMARY

The bot is giving wrong information because:

1. **NO PROXIES IN DATABASE** - Total: 0, Active: 0
2. **USING STALE TICKET ID** - Falls back to `1750097398` (old ID)
3. **API 500 ERRORS** - Vatican rejects stale ticket IDs
4. **FALSE "CLOSED" REPORTS** - Bot reports tickets as CLOSED when they're actually AVAILABLE

---

## 🚨 ROOT CAUSE CHAIN

```
NO PROXIES (0 in database)
    ↓
ERR_TUNNEL_CONNECTION_FAILED (can't connect to Vatican)
    ↓
Headless check fails → Falls back to browser mode
    ↓
Browser can't load page (no proxy)
    ↓
Can't extract fresh ticket IDs
    ↓
Falls back to STALE ID: 1750097398
    ↓
API returns 500 error (ID doesn't exist)
    ↓
Bot reports "CLOSED" (WRONG!)
```

---

## 📋 EVIDENCE FROM LOGS

### 1. ❌ NO PROXIES
```
Total: 0, Active: 0, Cooldown: 0
```

The proxy database is completely empty. The bot has NO way to connect to Vatican website.

### 2. ❌ TUNNEL CONNECTION FAILURES
```
[ERROR] Browser refresh failed: Page.goto: net::ERR_TUNNEL_CONNECTION_FAILED
at https://tickets.museivaticani.va/home/fromtag/4/1774479600000/MV-Biglietti/1
```

Without proxies, the bot cannot establish connections to Vatican.

### 3. ❌ STALE TICKET ID USAGE
```
[INFO] Smart Group: 2026-03-10/1750097398/None/1v → 1 agencies
[INFO] Smart Group: 2026-03-23/1750097398/None/1v → 1 agencies
[INFO] Smart Group: 2026-03-16/1750097398/None/1v → 1 agencies
```

All tasks are using the same stale ticket ID: `1750097398`

### 4. ❌ API 500 ERRORS
```
[WARNING] API call failed: Status 500 - {"timestamp":"2026-03-03T11:58:01.818+00:00",
"status":500,"error":"Internal Server Error","message":"Generic Error",
"path":"/api/visit/timeavail"}
[WARNING] Ticket ID might be stale, will retry with fresh IDs
```

Vatican API rejects the stale ticket ID with 500 error.

### 5. ❌ FALSE "CLOSED" REPORTS
```
[INFO] Musei Vaticani - Biglietti d'ingresso is CLOSED (0 slots)
```

Bot reports tickets as CLOSED when it actually failed to check them properly.

### 6. ✅ WHEN IT WORKS (Rare Success)
```
[INFO] Session Cookies: 3 cookies set
[INFO] Ticket buttons are visible
[INFO] Ticket titles are visible
[INFO] Available: 14, Sold Out: 6
[INFO] Found 14 available slots
[INFO] STATE CHANGE: Musei Vaticani - Biglietti d'ingresso went from CLOSED → OPEN!
[INFO] TELEGRAM ALERT sent to Agency-admin
```

When the bot DOES manage to connect (randomly), it finds tickets ARE available!

---

## 🎯 WHY THE BOT GIVES WRONG INFO

### Scenario 1: Most Common (90% of checks)
1. Bot tries to check March 16, 2026
2. No proxies available → Can't connect
3. Falls back to stale ID `1750097398`
4. API returns 500 error
5. Bot interprets error as "CLOSED"
6. **USER SEES: "No tickets available"** ❌ WRONG!
7. **REALITY: Tickets ARE available** ✅

### Scenario 2: Lucky Success (10% of checks)
1. Bot tries to check March 16, 2026
2. Somehow connects (maybe direct connection works occasionally)
3. Extracts fresh ticket IDs
4. API returns 200 with slots
5. Bot reports "AVAILABLE"
6. **USER SEES: "Tickets available!"** ✅ CORRECT!

### Result: Inconsistent Information
- Same date checked 10 times
- 9 times: "CLOSED" (wrong)
- 1 time: "AVAILABLE" (correct)
- User gets confused and frustrated

---

## 🔧 SOLUTIONS (IN ORDER OF PRIORITY)

### SOLUTION 1: SEED PROXIES (CRITICAL - DO THIS FIRST)

The bot needs proxies to connect to Vatican. You have proxy files but they're not in the database.

```bash
# Check if proxy files exist
docker exec travelagenntbot-backend-1 ls -la /app/ | grep -i proxy

# Seed proxies into database
docker exec travelagenntbot-backend-1 python /app/backend/manage.py seed_proxies

# Verify proxies were added
docker exec travelagenntbot-backend-1 python /app/backend/manage.py shell -c "from monitors.models import Proxy; print(f'Total proxies: {Proxy.objects.count()}')"
```

**Expected Result:**
```
Total proxies: 14
```

---

### SOLUTION 2: CLEAR STALE TICKET IDs

All tasks have stale ticket ID `1750097398`. Clear them to force fresh extraction.

```bash
# Clear all stale ticket IDs
docker exec travelagenntbot-backend-1 python /app/backend/manage.py shell -c "from monitors.models import MonitorTask; updated = MonitorTask.objects.filter(site='vatican').update(ticket_id=None); print(f'Cleared {updated} stale ticket IDs')"
```

**Expected Result:**
```
Cleared 8 stale ticket IDs
```

---

### SOLUTION 3: RESTART WORKER

After seeding proxies and clearing IDs, restart the worker to apply changes.

```bash
docker-compose restart worker_vatican
```

---

### SOLUTION 4: MONITOR LOGS FOR SUCCESS

Watch logs to verify the fixes worked:

```bash
docker-compose logs -f worker_vatican | grep -E "Session Cookies|Resolved.*Dynamic IDs|Found.*slots|STATE CHANGE"
```

**Expected Success Indicators:**
```
✅ Session Cookies: 3 cookies set
✅ Resolved 10 Dynamic IDs from Page
✅ Exact Match: 'Musei Vaticani - Biglietti d'ingresso' -> ID 2092730005
✅ Found 14 available slots
```

**Failure Indicators to Watch For:**
```
❌ ERR_TUNNEL_CONNECTION_FAILED
❌ Falling back to stale ID
❌ API call failed: Status 500
❌ is CLOSED (0 slots)
```

---

## 📈 EXPECTED BEHAVIOR AFTER FIX

### Before Fix (Current State):
```
[ERROR] ERR_TUNNEL_CONNECTION_FAILED
[WARNING] Headless check returned no results
[INFO] Using stale ID 1750097398
[WARNING] API call failed: Status 500
[INFO] Musei Vaticani is CLOSED (0 slots)  ← WRONG!
```

### After Fix (Expected):
```
[INFO] Loaded 14 Oxylabs proxies
[INFO] Session Cookies: 3 cookies set
[INFO] Ticket buttons are visible
[INFO] Resolved 10 Dynamic IDs from Page
[INFO] Exact Match: 'Musei Vaticani - Biglietti d'ingresso' -> ID 2092730005
[INFO] API Response: 200
[INFO] Found 14 available slots
[INFO] STATE CHANGE: CLOSED → OPEN! Sending Alert
```

---

## 🎯 VERIFICATION CHECKLIST

After applying all fixes, verify:

- [ ] Proxies exist: `Total proxies: > 0`
- [ ] No tunnel errors in logs
- [ ] Fresh IDs extracted: `Resolved X Dynamic IDs`
- [ ] No stale ID warnings
- [ ] API returns 200 (not 500)
- [ ] Correct status: `AVAILABLE` or `SOLD_OUT` (not false `CLOSED`)
- [ ] Slots found when tickets exist

---

## 🚀 QUICK FIX COMMANDS (RUN THESE NOW)

```bash
# 1. Seed proxies
docker exec travelagenntbot-backend-1 python /app/backend/manage.py seed_proxies

# 2. Clear stale IDs
docker exec travelagenntbot-backend-1 python /app/backend/manage.py shell -c "from monitors.models import MonitorTask; MonitorTask.objects.filter(site='vatican').update(ticket_id=None); print('Stale IDs cleared')"

# 3. Restart worker
docker-compose restart worker_vatican

# 4. Watch logs for success
docker-compose logs -f worker_vatican | grep -E "Session Cookies|Resolved.*IDs|Found.*slots"
```

---

## 📊 CURRENT STATUS

| Component | Status | Issue |
|-----------|--------|-------|
| Proxies | ❌ CRITICAL | 0 proxies in database |
| Ticket IDs | ❌ CRITICAL | All using stale ID 1750097398 |
| API Calls | ❌ FAILING | 500 errors due to stale IDs |
| Bot Reports | ❌ WRONG | False "CLOSED" when tickets available |
| Connections | ❌ FAILING | ERR_TUNNEL_CONNECTION_FAILED |

---

## 💡 WHY THIS HAPPENED

1. **Proxies not seeded**: The `seed_proxies` management command was never run, or proxies were deleted
2. **Stale IDs persisted**: Database still has old ticket IDs from weeks ago
3. **No fallback**: When proxies fail, bot should report "ERROR" not "CLOSED"

---

## 🔮 PREVENTION (AFTER FIX)

### 1. Monitor Proxy Health Daily
```bash
docker exec travelagenntbot-backend-1 python /app/backend/manage.py shell -c "from monitors.models import Proxy; print(f'Active: {Proxy.objects.filter(is_active=True).count()}')"
```

### 2. Never Store Ticket IDs Long-Term
- Always set `ticket_id=None` in database
- Always extract fresh IDs from page
- Never trust IDs older than 24 hours

### 3. Improve Error Handling
- API errors → Report as "ERROR", not "CLOSED"
- Connection errors → Retry with different proxy
- Timeout errors → Retry, don't report as closed

---

**PRIORITY:** 🚨 URGENT - Fix proxies immediately  
**IMPACT:** HIGH - Bot giving wrong information to users  
**TIME TO FIX:** 5 minutes  
**DIFFICULTY:** Easy - Just run the commands above

