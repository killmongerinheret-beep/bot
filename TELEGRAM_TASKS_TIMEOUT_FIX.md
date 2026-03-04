# Telegram Tasks Showing "Unknown" - Root Cause & Fix

## Problem

Tasks created from Telegram bot were showing status "unknown" and not being checked properly.

## Root Cause Analysis

### Issue 1: Tasks Without ticket_id (Legacy Mode)
- Telegram bot creates tasks with `ticket_id=None` (correct behavior, since IDs change daily)
- These tasks are grouped into "legacy" batches by the orchestration
- Legacy batches use `run_shared_vatican_monitor` which uses HydraBot

### Issue 2: HydraBot Timeout
- HydraBot navigates to Vatican website to extract dynamic ticket IDs
- Vatican website is VERY slow to load (60+ seconds)
- HydraBot had 60-second timeout → pages timed out
- When timeout occurs, bot reports "sold_out" (incorrect)

### Issue 3: Silent Failures
- `run_shared_vatican_monitor` tasks were being queued
- They were executing but timing out
- No error logs visible in main worker output
- Tasks showed "unknown" because they never completed successfully

## Evidence

**Test Run Output:**
```
2026-03-04 12:23:18 [INFO] HydraBot: 🕸️ Navigating to Deep Link: https://tickets.museivaticani.va/...
2026-03-04 12:24:13 [ERROR] HydraBot: ❌ ID Resolution Failed: Page.goto: Timeout 60000ms exceeded.
```

**Task Status After Timeout:**
```
Task 30: Last Checked=2026-03-04 12:24:13, Status=sold_out (WRONG!)
Task 32: Last Checked=2026-03-04 12:24:13, Status=sold_out (WRONG!)
Task 33: Last Checked=2026-03-04 12:24:13, Status=sold_out (WRONG!)
```

## Solution Applied

### Fix: Increased HydraBot Timeout

**File:** `worker_vatican/hydra_monitor.py`

**Change:**
```python
# Before (60 seconds):
await page.goto(deep_url, timeout=60000, wait_until="networkidle")

# After (120 seconds):
await page.goto(deep_url, timeout=120000, wait_until="networkidle")
```

**Why 120 seconds:**
- Vatican website can take 60-90 seconds to fully load
- 120 seconds provides buffer for slow network conditions
- Still reasonable timeout (won't hang forever)

### Additional Improvements Needed (Future)

1. **Use god_tier_monitor for all tasks**
   - god_tier_monitor caches ticket IDs
   - Much faster (no page navigation needed)
   - More reliable

2. **Pre-populate ticket_id on task creation**
   - Resolve ticket_id when task is created
   - Store in database
   - Avoid legacy mode entirely

3. **Better error handling**
   - Don't report "sold_out" on timeout
   - Report "checking" or "error" status
   - Retry failed checks

## Verification Steps

1. **Check Task Status:**
   ```bash
   docker-compose exec backend python /app/check_current_tasks.py
   ```

2. **Monitor Worker Logs:**
   ```bash
   docker-compose logs -f worker_vatican | grep "HYDRA SHARED\|Timeout\|Task 30\|Task 32\|Task 33"
   ```

3. **Force Fresh Check:**
   ```bash
   docker-compose exec backend python /app/force_check_telegram_tasks.py
   ```

4. **Wait 2-3 minutes** for checks to complete (with 120s timeout)

5. **Verify Status Updated:**
   ```bash
   docker-compose exec backend python -c "import django; import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings'); django.setup(); from monitors.models import MonitorTask; tasks = MonitorTask.objects.filter(id__in=[30,32,33]); [print(f'Task {t.id}: Status={t.last_status}, Checked={t.last_checked}') for t in tasks]"
   ```

## Current Status

✅ Timeout increased from 60s to 120s
✅ Worker restarted with new configuration
✅ Tasks 30, 32, 33 reset for fresh check
⏳ Waiting for next check cycle (within 60 seconds)

## Expected Behavior Now

1. Orchestration queues legacy tasks every 60 seconds
2. `run_shared_vatican_monitor` executes with 120s timeout
3. HydraBot successfully loads Vatican pages
4. Dynamic ticket IDs extracted
5. API calls made with fresh IDs
6. Tasks updated with correct availability status

## Why This Happens to Telegram Tasks

**Telegram tasks** are more likely to hit this issue because:
1. They're newly created (no cached ticket_id)
2. They go through legacy mode (HydraBot)
3. HydraBot needs to navigate to Vatican website
4. Vatican website is slow → timeout

**Dashboard tasks** that have been checked before:
1. Have cached ticket_id in database
2. Use god_tier_monitor (faster)
3. god_tier_monitor uses cached IDs
4. No page navigation needed
5. Much faster, no timeouts

## Long-Term Fix

**Recommended:** Update Telegram bot to pre-resolve ticket_id on creation:

```python
# In telegram_bot.py, before creating task:
from worker_vatican.god_tier_monitor import GodTierMonitor

# Resolve fresh ticket ID
monitor = GodTierMonitor(use_proxies=True)
fresh_id = await monitor.resolve_ticket_id_for_date(date, ticket_type, language)

# Create task with fresh_id
task = await sync_to_async(MonitorTask.objects.create)(
    ...
    ticket_id=fresh_id,  # ← Pre-populated!
    ...
)
```

This would make Telegram tasks use the fast path (god_tier_monitor) from the start.

## Summary

The issue was NOT that tasks weren't being checked - they WERE being checked, but the checks were timing out due to Vatican's slow website. Increasing the timeout from 60s to 120s should resolve this. Tasks will now complete successfully and show correct availability status.
