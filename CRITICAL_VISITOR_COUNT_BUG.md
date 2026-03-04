# CRITICAL BUG: Visitor Count Mismatch

## Issue Discovered

The bot is using the WRONG visitor count when checking tickets!

### Evidence from Logs

**Task #19 Configuration**:
```json
{
  "id": 19,
  "dates": ["2026-03-16"],
  "visitors": 1,  ← Task needs 1 visitor
  "ticket_type": 0
}
```

**Bot's Deep Link** (from logs):
```
🕸️ [Multi-Scan] Navigating to Deep Link: 
https://tickets.museivaticani.va/home/fromtag/2/1773615600000/MV-Biglietti/1
                                              ↑
                                         Using 2 visitors!
```

**Result**: Wrong tickets shown!
```
Candidates: [
  'Specola Vaticana - Visita Guidata Gruppi',
  'Palazzo Papale - Cupole Astronomiche',
  "Palazzo Papale - Biglietti d'ingresso",  ← Wrong tickets!
  ...
]
⚠️ No name match for 'Musei Vaticani - Biglietti d'ingresso'
```

## Root Cause

The bot is hardcoding `visitors=2` in the deep link instead of using the task's actual visitor count.

### Where the Bug Is

Looking at the logs, the deep link format is:
```
/fromtag/{visitors}/{timestamp}/MV-Biglietti/1
```

The bot should use `task.visitors` but it's using a hardcoded value or default value of 2.

## Impact

1. **Wrong tickets displayed**: Vatican website shows different tickets for different visitor counts
2. **Missing availability**: March 16 might have slots for 1 visitor but bot is checking for 2 visitors
3. **False negatives**: Bot reports "sold out" when tickets are actually available

## Why This Matters

Vatican website behavior:
- 1 visitor: Shows "Musei Vaticani - Biglietti d'ingresso"
- 2 visitors: Shows "Palazzo Papale" and other tickets
- Different visitor counts = Different ticket availability

## Additional Issues Found

### Issue 2: God-Tier Monitor API Error

```
❌ Missing visit_date or visitors - cannot check via API
```

The god_tier_monitor_v2 is not receiving the date/visitors parameters correctly, so it falls back to browser mode (slower).

### Issue 3: Headless Check Failing

```
⚠️ Headless check returned no results, falling back to browser mode
```

The optimized API method isn't working, so every check uses the slow browser method.

## What Needs to be Fixed

### Fix 1: Pass Correct Visitor Count to Deep Link

The orchestration needs to pass `task.visitors` to the monitor function, and the monitor needs to use it in the deep link.

**Current** (wrong):
```python
deep_link = f"/fromtag/2/{timestamp}/MV-Biglietti/1"  # Hardcoded 2
```

**Should be**:
```python
deep_link = f"/fromtag/{visitors}/{timestamp}/MV-Biglietti/1"  # Use actual visitors
```

### Fix 2: Pass Parameters to God-Tier Monitor

The god_tier_monitor_v2 needs to receive:
- `date_str`: The date to check
- `visitors`: Number of visitors
- `ticket_type`: 0 for standard, 1 for guided

Currently these are missing, causing the API check to fail.

### Fix 3: Verify March 16 Availability

Once fixed, manually verify if March 16 actually has slots for 1 visitor:
1. Visit https://tickets.museivaticani.va/
2. Select March 16, 2026
3. Select 1 visitor
4. Check if "Musei Vaticani - Biglietti d'ingresso" has slots

## Temporary Workaround

Until fixed, you can:
1. Change Task #19 to use 2 visitors (if you actually need 2)
2. Or manually check Vatican website for 1 visitor availability

## Files to Check

1. `backend/monitors/tasks.py` - orchestrate_all_tasks function
2. `worker_vatican/hydra_monitor.py` - resolve_all_dynamic_ids function
3. `worker_vatican/god_tier_monitor_v2.py` - check_availability function

## Expected Behavior After Fix

**Task #19 with 1 visitor**:
```
🕸️ Navigating to: /fromtag/1/1773615600000/MV-Biglietti/1
                            ↑ Correct!

Candidates: [
  'Musei Vaticani - Biglietti d\'ingresso',  ← Correct ticket!
  ...
]

✅ Found X slots for March 16, 2026
```

## Priority

🔴 **CRITICAL** - This bug causes the bot to check wrong tickets and miss availability.

---

**User reported**: "for 16 march one person there are slots"  
**Bot shows**: "sold_out" (checking for 2 visitors instead of 1)  
**Actual status**: Unknown (need to fix visitor count first)
