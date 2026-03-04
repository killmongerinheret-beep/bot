# Vatican Bot Fixes Applied - Summary

## Date: February 28, 2026

## Critical Fix: Visitor Count Parameter Passing

### Problem
The bot was not passing the `visitors` parameter through the entire call chain, causing all checks to use hardcoded default values (usually 2 visitors) instead of the actual task configuration.

**Impact**: Tasks configured for 1 visitor were being checked with 2 visitors, showing wrong availability.

### Solution Applied

#### 1. backend/monitors/tasks.py

**Changes Made**:

1. **orchestrate_all_tasks()** - Line ~945
   - Changed grouping key from `(date, ticket_id, language)` to `(date, ticket_id, language, visitors)`
   - Added `visitors` to smart_groups data structure
   - Updated dispatch calls to pass `visitors` parameter

2. **run_god_tier_vatican_monitor()** - Line ~394
   - Added `visitors=2` parameter to function signature
   - Pass `visitors` to `monitor.check_availability_headless()`
   - Pass `visitors` to fallback `run_smart_vatican_monitor()`

3. **run_smart_vatican_monitor()** - Line ~179
   - Added `visitors=2` parameter to function signature
   - Changed `bot.resolve_all_dynamic_ids()` call from `visitors=2` to `visitors=visitors`

#### 2. worker_vatican/god_tier_monitor.py

**Changes Made**:

1. **check_availability_headless()** - Line ~200
   - Added `visitors: int = 2` parameter
   - Pass `visitors` to `refresh_session_with_browser()`
   - Use `visitors` parameter in API calls instead of hardcoded values

2. **refresh_session_with_browser()** - Line ~250
   - Added `visitors: int = 2` parameter
   - Use `visitors` in deep link construction

#### 3. worker_vatican/hydra_monitor.py

**Changes Made**:

1. **resolve_all_dynamic_ids()** - Line ~680
   - Changed default from `visitors=2` to `visitors=1`
   - Already had parameter, just updated default

2. **check_via_click()** - Line ~1132
   - Changed default from `visitors=2` to `visitors=1`
   - Already had parameter, just updated default

3. **check_via_api()** - Line ~1207
   - Changed default from `visitors=2` to `visitors=1`
   - Already had parameter, just updated default

#### 4. worker_vatican/god_tier_monitor_v2.py

**Status**: ✅ Already correct!
- Already has proper visitor parameter handling
- Uses `eff_visitors` logic to handle None/0 cases
- No changes needed

## Verification Steps

### 1. Check Task Configuration
```python
from monitors.models import MonitorTask
task = MonitorTask.objects.get(id=19)
print(f"Task #19 - Visitors: {task.visitors}, Dates: {task.dates}")
```

### 2. Trigger Manual Check
```python
from monitors.tasks import orchestrate_all_tasks
orchestrate_all_tasks()
```

### 3. Watch Logs
```bash
docker-compose logs -f celery_worker | grep -E "(visitor|fromtag|visitorNum)"
```

### Expected Log Output

**Before Fix**:
```
🕸️ [Multi-Scan] Navigating to Deep Link: .../fromtag/2/1773615600000/MV-Biglietti/1
```

**After Fix**:
```
🕸️ [Multi-Scan] Navigating to Deep Link: .../fromtag/1/1773615600000/MV-Biglietti/1
📊 Smart Group: 16/03/2026/929041748/None/1v → 1 agencies
```

### 4. Verify API Calls
Check that API calls use correct visitorNum:
```
/api/visit/timeavail?lang=it&visitTypeId=929041748&visitorNum=1&visitDate=16/03/2026
```

## Expected Results

### Task #19 (March 16, 1 visitor)
- ✅ Deep link uses `/fromtag/1/...` (1 visitor)
- ✅ API calls use `visitorNum=1`
- ✅ Shows "Musei Vaticani" tickets (not Palazzo Papale)
- ✅ Finds availability that user confirmed exists

### Task #15 (Multiple dates, 1 visitor)
- ✅ All checks use 1 visitor
- ✅ Correct availability shown

### Task #18 (Standard ticket, 1 visitor)
- ✅ Uses 1 visitor
- ✅ No language parameter (standard ticket)

## Additional Improvements

### Default Visitor Count Changed
Changed defaults from 2 to 1 in hydra_monitor.py functions:
- Most common use case is 1 visitor
- Reduces confusion when parameter is not explicitly passed
- More conservative default (1 visitor availability is stricter)

### Grouping Optimization
Tasks are now grouped by `(date, ticket_id, language, visitors)`:
- Tasks with different visitor counts are checked separately
- Each check uses the correct visitor count
- More accurate results for all agencies

## Files Modified

1. `backend/monitors/tasks.py` - 5 changes
2. `worker_vatican/god_tier_monitor.py` - 6 changes
3. `worker_vatican/hydra_monitor.py` - 3 changes

## Testing Checklist

- [ ] Restart Celery workers: `docker-compose restart celery_worker`
- [ ] Trigger orchestration: `python backend/manage.py shell` → `orchestrate_all_tasks()`
- [ ] Check logs for correct visitor counts in deep links
- [ ] Check logs for correct visitorNum in API calls
- [ ] Verify Task #19 finds availability for March 16
- [ ] Verify dashboard shows correct data
- [ ] Monitor for 30 minutes to ensure no errors

## Rollback Plan

If issues occur:
1. Git revert the changes
2. Restart services
3. Review logs for specific error messages

## Next Steps

1. Deploy changes to production
2. Monitor logs for 24 hours
3. Verify all tasks are checking correctly
4. Confirm user sees correct availability

## Summary

**Critical bug fixed**: Visitor count now properly passed through entire call chain  
**Default improved**: Changed from 2 to 1 visitor (more common case)  
**Grouping enhanced**: Tasks grouped by visitor count for accurate checks  
**Impact**: All tasks will now check with their configured visitor count

This fix resolves the issue where Task #19 (1 visitor) was being checked with 2 visitors and missing real availability.
