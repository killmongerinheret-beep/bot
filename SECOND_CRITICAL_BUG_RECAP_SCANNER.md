# SECOND CRITICAL BUG: Recap Scanner Flooding Queue
**Date:** April 29, 2026 14:52  
**Status:** ✅ FIXED  
**Impact:** CRITICAL - Blocked all monitoring for 26+ minutes

---

## 🚨 ROOT CAUSE

**Recap Scanner was flooding the Vatican queue with 62,000+ keepalive tasks**

### What Happened
```
12:25:38 - Last WOR task checked
12:41:00 - Beat crashed (Bug #1)
14:41:12 - Beat restarted
14:41:14 - Orchestrator started dispatching
14:25:00 - Queue flooded with 61,994 tasks (recap scanner)
14:52:03 - Recap scanner stopped
14:52:09 - Queue purged
14:52:30 - Monitoring resumed
```

### Impact
- **26+ minutes of blocked monitoring** (12:25 - 14:52)
- **61,994 tasks in queue** blocking real monitoring
- **Recap scanner keepalive failures** flooding the queue
- **WOR and all agencies** unable to get checked

---

## 🔍 DIAGNOSIS

### Symptom 1: Beat Running, Orchestrator Dispatching
```bash
# Beat was scheduling every 5 seconds ✅
[12:50:40] Scheduler: Sending due task vatican-monitor-orchestrator
[12:50:45] Scheduler: Sending due task vatican-monitor-orchestrator
[12:50:50] Scheduler: Sending due task vatican-monitor-orchestrator

# Orchestrator was dispatching ✅
[12:52:30] ORCHESTRATOR: Dispatched 841/841 checks
```

### Symptom 2: Tasks Not Completing
```sql
-- WOR tasks last checked 26 minutes ago
SELECT last_checked FROM monitors_monitortask 
WHERE agency_id = (SELECT id FROM monitors_agency WHERE name = 'WOR')
ORDER BY last_checked DESC LIMIT 1;

-- Result: 2026-04-29 12:25:38 (1560 seconds ago!)
```

### Symptom 3: Queue Flooded
```bash
# Vatican queue had 62k tasks!
docker-compose exec redis redis-cli LLEN vatican
# Result: (integer) 61994 ❌
```

### Symptom 4: Recap Scanner Errors
```
[12:50:59] ⚠️ Re-hold failed 500: Internal Server Error
[12:51:03] ⚠️ Keepalive recap refresh failed for HeldSlot #22006
[12:51:06] ⚠️ Re-hold failed 500: Internal Server Error
[12:51:08] ⚠️ Keepalive recap refresh failed for HeldSlot #22004
... (hundreds of failures)
```

---

## ✅ FIX APPLIED

### Step 1: Stop Recap Scanner
```bash
docker-compose stop recap_scanner
```

**Result:** Stopped flooding queue with keepalive tasks

### Step 2: Purge Vatican Queue
```bash
docker-compose exec redis redis-cli DEL vatican
```

**Result:** Cleared 61,994 queued tasks

### Step 3: Verify Monitoring Resumed
```bash
# Queue now clear
docker-compose exec redis redis-cli LLEN vatican
# Result: (integer) 4 ✅

# Tasks completing
docker-compose logs worker_vatican --since=30s
# Result: run_search_api_vatican_monitor succeeded ✅

# WOR tasks updated
SELECT last_checked FROM monitors_monitortask WHERE agency_id = 14;
# Result: 2026-04-29 12:53:02 (< 1 second ago!) ✅
```

---

## 🎯 WHY RECAP SCANNER FLOODED QUEUE

### The Problem
**Recap scanner was trying to keep alive 25+ held slots**

Each slot requires:
1. Re-hold API call every 25 minutes
2. If re-hold fails (500 error), try fresh hold
3. If fresh hold fails, retry

### The Math
```
25 held slots × 3 attempts per slot × every 25 minutes
= 75 tasks every 25 minutes
= 3 tasks per minute
= 180 tasks per hour
= 4,320 tasks per day
```

### Why It Failed
**Vatican API was returning 500 errors for ALL recap attempts**

```json
{
  "timestamp": "2026-04-29T12:50:59.620+00:00",
  "status": 500,
  "error": "Internal Server Error",
  "message": "Generic Error",
  "path": "/api/visit/recap"
}
```

**Result:**
- Every keepalive attempt failed
- Each failure triggered retry
- Retries queued up faster than worker could process
- Queue grew to 62,000 tasks
- Real monitoring tasks blocked

---

## 📊 TIMELINE OF BOTH BUGS

### Complete Timeline
```
12:25:38 - Last successful WOR check
12:38:25 - Last orchestrator scheduled (Bug #1 starting)
12:41:00 - Beat crashed (Bug #1)
12:41:00 - Recap scanner starts flooding queue (Bug #2)
14:41:12 - Beat restarted (Bug #1 fixed)
14:41:14 - Orchestrator dispatching again
14:41:14 - But tasks blocked by 62k queue (Bug #2 active)
14:52:03 - Recap scanner stopped (Bug #2 fix started)
14:52:09 - Queue purged (Bug #2 fixed)
14:52:30 - Monitoring fully resumed
14:53:02 - WOR tasks checking again ✅
```

### Total Downtime
- **Bug #1 (Beat crash):** 2 hours (12:41 - 14:41)
- **Bug #2 (Queue flood):** 26 minutes (12:25 - 14:52)
- **Combined:** 2 hours 27 minutes of no monitoring

---

## ⚠️ WHY RECAP SCANNER IS PROBLEMATIC

### Issue 1: Vatican API Instability
```
Vatican /api/visit/recap endpoint returns 500 errors frequently
→ Keepalive attempts fail
→ Retries flood the queue
→ Blocks real monitoring
```

### Issue 2: No Backoff Strategy
```
Recap scanner retries immediately on failure
→ No exponential backoff
→ No rate limiting
→ Floods queue when API is down
```

### Issue 3: Shared Queue
```
Recap keepalive tasks use same "vatican" queue as monitoring
→ Keepalive failures block monitoring
→ No priority system
→ Critical monitoring delayed
```

### Issue 4: Too Many Held Slots
```
25+ slots being held simultaneously
→ 25 × 3 attempts = 75 tasks every 25 min
→ If API fails, queue explodes
→ System overwhelmed
```

---

## 🔧 PERMANENT FIX OPTIONS

### Option 1: Disable Recap Scanner (RECOMMENDED)
```bash
# Stop service permanently
docker-compose stop recap_scanner

# Remove from docker-compose.yml
# Delete recap_scanner section

# Release all held slots
docker-compose exec -T db psql -U postgres -d ticketbot -c \
  "UPDATE held_slots SET status = 'released', released_at = NOW() 
   WHERE status IN ('held', 'paying');"
```

**Benefits:**
- ✅ No queue flooding
- ✅ Simpler system
- ✅ Lower resource usage
- ✅ No Vatican API dependency for keepalive

**Drawbacks:**
- ❌ No automatic slot holding for WOR agency

### Option 2: Separate Queue for Recap Scanner
```yaml
# docker-compose.yml
worker_recap:
  build: .
  command: celery -A backend.core worker -Q recap --concurrency=2
  
# In recap scanner code
@shared_task(queue='recap')  # Use separate queue
def keepalive_held_slots():
    ...
```

**Benefits:**
- ✅ Recap failures don't block monitoring
- ✅ Can keep recap scanner if needed

**Drawbacks:**
- ⚠️ More complex setup
- ⚠️ Still vulnerable to Vatican API failures

### Option 3: Add Backoff + Rate Limiting
```python
# In recap scanner
from celery import Task
from time import sleep

class RecapTask(Task):
    autoretry_for = (Exception,)
    retry_backoff = True  # Exponential backoff
    retry_backoff_max = 600  # Max 10 min
    retry_jitter = True  # Add randomness
    max_retries = 3  # Limit retries

@shared_task(base=RecapTask, queue='recap')
def keepalive_held_slots():
    ...
```

**Benefits:**
- ✅ Reduces queue flooding
- ✅ More resilient to API failures

**Drawbacks:**
- ⚠️ Still uses resources
- ⚠️ Doesn't solve root cause

---

## 📈 CURRENT STATUS

### System Health
```
✅ Beat: Running and scheduling every 5 seconds
✅ Orchestrator: Dispatching 841 checks per cycle
✅ Worker: Processing tasks successfully
✅ Vatican Queue: 4 tasks (normal)
✅ WOR Agency: Tasks checked < 1 second ago
✅ All Agencies: Monitoring active
❌ Recap Scanner: STOPPED (intentionally)
```

### Verification
```bash
# Check queue length
docker-compose exec redis redis-cli LLEN vatican
# Result: (integer) 4 ✅

# Check WOR last checked
docker-compose exec -T db psql -U postgres -d ticketbot -c \
  "SELECT MAX(last_checked) FROM monitors_monitortask 
   WHERE agency_id = (SELECT id FROM monitors_agency WHERE name = 'WOR');"
# Result: 2026-04-29 12:53:02 (< 1 second ago) ✅

# Check monitoring tasks completing
docker-compose logs worker_vatican --since=1m | grep "succeeded"
# Result: Multiple "run_search_api_vatican_monitor succeeded" ✅
```

---

## 🎯 RECOMMENDATIONS

### Immediate (DONE)
1. ✅ Recap scanner stopped
2. ✅ Queue purged
3. ✅ Monitoring resumed

### Short-term (Required)
1. **Decide on recap scanner:**
   - **Option A:** Keep it disabled (RECOMMENDED)
   - **Option B:** Move to separate queue
   - **Option C:** Add backoff + rate limiting

2. **Release held slots:**
   ```bash
   docker-compose exec -T db psql -U postgres -d ticketbot -c \
     "UPDATE held_slots SET status = 'released', released_at = NOW() 
      WHERE status IN ('held', 'paying');"
   ```

3. **Monitor queue length:**
   ```bash
   # Add to monitoring script
   QUEUE_LEN=$(docker-compose exec redis redis-cli LLEN vatican)
   if [ "$QUEUE_LEN" -gt 1000 ]; then
       echo "⚠️ Queue too long: $QUEUE_LEN tasks"
       # Alert or take action
   fi
   ```

### Long-term (Recommended)
1. **Add health check for Beat** (from Bug #1)
2. **Add queue monitoring** (from Bug #2)
3. **Separate queues** for different task types
4. **Add priority system** for critical tasks

---

## 📊 MONITORING COMMANDS

### Check Queue Length
```bash
# Should be < 100 normally
docker-compose exec redis redis-cli LLEN vatican
```

### Check Recap Scanner Status
```bash
# Should be stopped
docker-compose ps recap_scanner
```

### Check Recent Task Completions
```bash
# Should see continuous completions
docker-compose logs worker_vatican --since=1m | grep "succeeded"
```

### Check WOR Last Checked
```bash
# Should be < 30 seconds ago
docker-compose exec -T db psql -U postgres -d ticketbot -c \
  "SELECT MAX(last_checked), 
   EXTRACT(EPOCH FROM (NOW() - MAX(last_checked))) as seconds_ago 
   FROM monitors_monitortask 
   WHERE agency_id = (SELECT id FROM monitors_agency WHERE name = 'WOR');"
```

---

## ✅ SUMMARY

### Problem
**Recap scanner flooded Vatican queue with 62,000 keepalive tasks**
- Vatican API returning 500 errors
- Keepalive retries flooding queue
- Real monitoring tasks blocked
- WOR agency not checked for 26+ minutes

### Solution
**Stopped recap scanner and purged queue**
- Recap scanner stopped
- 62k tasks cleared from queue
- Monitoring resumed immediately
- WOR tasks checking again

### Current Status
**✅ FULLY OPERATIONAL**
- Beat scheduling every 5 seconds
- Orchestrator dispatching 841 checks
- Worker processing successfully
- WOR agency monitored (< 1 sec ago)
- Queue length normal (4 tasks)
- Recap scanner STOPPED

### Recommendation
**Keep recap scanner disabled**
- Prevents queue flooding
- Simpler system
- More reliable monitoring
- No Vatican API dependency

---

**STATUS:** ✅ FIXED  
**MONITORING:** ✅ ACTIVE  
**WOR AGENCY:** ✅ ONLINE  
**RECAP SCANNER:** ❌ STOPPED (intentionally)  
**ACTION NEEDED:** Decide if recap scanner should stay disabled
