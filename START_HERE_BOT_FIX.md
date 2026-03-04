# 🚨 START HERE: Bot Giving Wrong Information

**Problem:** Bot says tickets are CLOSED when they're actually AVAILABLE

**Root Cause:** No proxies in database (0 proxies)

**Fix Time:** 5 minutes

**Difficulty:** Easy

---

## 🎯 QUICK DIAGNOSIS

I analyzed the bot logs and found the exact issue:

### The Problem Chain
```
No Proxies (0 in DB)
  ↓
Can't connect to Vatican
  ↓
Can't extract fresh ticket IDs
  ↓
Uses stale ID from 3 weeks ago (1750097398)
  ↓
Vatican API rejects it (500 error)
  ↓
Bot reports "CLOSED" ← WRONG!
```

### The Evidence
```bash
# Proxy status
Total: 0, Active: 0, Cooldown: 0

# Log errors
❌ ERR_TUNNEL_CONNECTION_FAILED
❌ API call failed: Status 500
❌ Musei Vaticani is CLOSED (0 slots) ← WRONG!

# When it rarely works
✅ Found 14 available slots ← CORRECT!
```

---

## 🔧 THE FIX (Run This Now)

### Option 1: Automated Script
```powershell
.\fix_bot_now.ps1
```

### Option 2: Manual Commands
```bash
# 1. Seed proxies (adds 14 Oxylabs proxies)
docker exec travelagenntbot-backend-1 python /app/backend/manage.py seed_proxies

# 2. Clear stale ticket IDs
docker exec travelagenntbot-backend-1 python /app/backend/manage.py shell -c "from monitors.models import MonitorTask; MonitorTask.objects.filter(site='vatican').update(ticket_id=None); print('Cleared stale IDs')"

# 3. Restart worker
docker-compose restart worker_vatican
```

---

## ✅ VERIFICATION

Wait 2-3 minutes, then check logs:

```powershell
docker-compose logs -f worker_vatican | Select-String -Pattern "Session Cookies|Resolved.*IDs|Found.*slots|STATE CHANGE"
```

### Success Indicators
```
✅ Loaded 14 Oxylabs proxies
✅ Session Cookies: 3 cookies set
✅ Resolved 10 Dynamic IDs from Page
✅ Exact Match: 'Musei Vaticani' -> ID 2092730005
✅ Found 14 available slots
✅ STATE CHANGE: CLOSED → OPEN!
```

### Failure Indicators (Should NOT see these)
```
❌ ERR_TUNNEL_CONNECTION_FAILED
❌ Falling back to stale ID
❌ API call failed: Status 500
❌ is CLOSED (0 slots)
```

---

## 📊 BEFORE vs AFTER

### Before Fix
- **Bot says:** "CLOSED" for March 16
- **Reality:** 14 slots available
- **User:** Confused and frustrated
- **Logs:** Connection errors, 500 errors, stale IDs

### After Fix
- **Bot says:** "AVAILABLE - 14 slots" for March 16
- **Reality:** 14 slots available
- **User:** Happy, can book tickets
- **Logs:** Fresh IDs, 200 responses, correct status

---

## 📚 DETAILED DOCUMENTATION

For more details, see:

1. **BOT_DIAGNOSIS_COMPLETE.md** - Full technical analysis
2. **BOT_WRONG_INFO_SUMMARY.md** - Quick summary
3. **BOT_ISSUE_FLOWCHART.md** - Visual flowchart
4. **BOT_ISSUES_FOUND.md** - Original issue report

---

## 🎯 WHY THIS HAPPENED

1. **Proxies never seeded** - The `seed_proxies` command was never run
2. **Stale IDs persisted** - Database kept old ticket IDs from weeks ago
3. **Poor error handling** - Bot reports "CLOSED" instead of "ERROR" when API fails

---

## 🔮 PREVENTION (After Fix)

### Daily Health Check
```bash
docker exec travelagenntbot-backend-1 python /app/backend/manage.py shell -c "from monitors.models import Proxy; print(f'Active proxies: {Proxy.objects.filter(is_active=True).count()}')"
```

Should show: `Active proxies: 14` (or similar)

### Weekly Maintenance
```bash
# Reset any proxies on cooldown
docker exec travelagenntbot-backend-1 python /app/backend/manage.py shell -c "from monitors.models import Proxy; Proxy.objects.all().update(is_active=True, consecutive_failures=0, cooldown_until=None)"
```

---

## 🚀 NEXT STEPS

1. ✅ Run the fix commands above
2. ✅ Wait 2-3 minutes for worker to restart
3. ✅ Check logs for success indicators
4. ✅ Verify dashboard shows correct status
5. ✅ Test with a known available date (March 16, 2026)

---

## ❓ TROUBLESHOOTING

### If proxies still show 0 after seeding:
```bash
# Check if proxy files exist
docker exec travelagenntbot-backend-1 ls -la /app/ | grep -i proxy

# If files missing, check parent directory
docker exec travelagenntbot-backend-1 find /app -name "*proxy*" -o -name "*Proxy*"
```

### If bot still reports CLOSED:
```bash
# Force clear Redis cache
docker exec travelagenntbot-backend-1 python /app/backend/manage.py shell -c "from django.core.cache import cache; cache.clear(); print('Cache cleared')"

# Restart all services
docker-compose restart
```

---

**STATUS:** Ready to fix  
**PRIORITY:** 🚨 URGENT  
**IMPACT:** HIGH - Affects all Vatican ticket checks  
**CONFIDENCE:** 100% - Root cause identified with evidence

---

## 🎬 TL;DR

**Problem:** Bot has 0 proxies, can't connect, uses stale IDs, gets 500 errors, reports wrong info

**Fix:** Seed proxies, clear stale IDs, restart worker

**Time:** 5 minutes

**Run:** `.\fix_bot_now.ps1`

**Done!** ✅
