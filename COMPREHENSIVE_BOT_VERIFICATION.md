# Comprehensive Vatican Bot Verification Report

## Executive Summary
**Date**: February 28, 2026  
**Status**: ⚠️ CRITICAL ISSUES FOUND - Visitor count not passed through call chain

## Issues Found

### 1. ❌ CRITICAL: Visitor Count Not Passed Through Call Chain

**Impact**: Bot is checking with wrong visitor counts, missing real availability

**Evidence**:
- Task #19 configured for 1 visitor
- Deep link shows `/fromtag/2/...` (using 2 visitors instead of 1)
- User confirmed March 16 has slots for 1 visitor, but bot can't see them

**Root Cause**: Missing `visitors` parameter in function signatures and calls

**Files Affected**:
1. `backend/monitors/tasks.py` - orchestrate_all_tasks, run_god_tier_vatican_monitor, run_smart_vatican_monitor
2. `worker_vatican/god_tier_monitor.py` - check_availability_headless
3. `worker_vatican/hydra_monitor.py` - resolve_all_dynamic_ids, check_via_click, check_via_api

### 2. ✅ VERIFIED: New API Method Implementation

**Status**: Implemented correctly in god_tier_monitor_v2.py

**Features**:
- ✅ Session caching with JSESSIONID
- ✅ ID extraction with Playwright
- ✅ Direct API calls with curl_cffi
- ✅ Proper cookie handling
- ✅ 3-retry logic with session regeneration

**Code Location**: `worker_vatican/god_tier_monitor_v2.py`
- Line 356: `check_availability()` - Main entry point
- Line 200: `refresh_session_with_browser()` - Playwright ID extraction
- Line 300: API calls with cached session

### 3. ✅ VERIFIED: Proxy Loading

**Status**: Working correctly

**Evidence**:
```python
# worker_vatican/hydra_monitor.py line 60-90
def _load_proxies(self):
    # Loads from "Proxy lists.json" (Oxylabs format)
    # 14 Italian Oxylabs proxies loaded successfully
```

**Logs Show**: `✅ Loaded 14 Oxylabs proxies (Primary)`

### 4. ⚠️ ISSUE: Visitor Count Defaults

**Current Defaults**:
- `hydra_monitor.py` line 711: `resolve_all_dynamic_ids()` - `visitors=2` (hardcoded)
- `hydra_monitor.py` line 1132: `check_via_click()` - `visitors=2` (default parameter)
- `hydra_monitor.py` line 1207: `check_via_api()` - `visitors=2` (default parameter)
- `god_tier_monitor_v2.py` line 356: `check_availability()` - `visitors=None` (then defaults to 2)

**Problem**: These defaults override the actual task.visitors value

## Detailed Analysis

### Call Chain Analysis

**Current Flow** (BROKEN):
```
orchestrate_all_tasks()
  ↓ (missing visitors parameter!)
run_god_tier_vatican_monitor(date, ticket_id, ticket_name, language, task_ids)
  ↓ (missing visitors parameter!)
monitor.check_availability_headless(date_str, ticket_type, languages)
  ↓ (missing visitors parameter!)
Falls back to run_smart_vatican_monitor(date, ticket_id, ticket_name, language, task_ids)
  ↓ (missing visitors parameter!)
bot.resolve_all_dynamic_ids(page, ticket_type, target_date, visitors=2 HARDCODED!)
```

**Expected Flow** (FIXED):
```
orchestrate_all_tasks()
  ↓ Extract task.visitors from database
run_god_tier_vatican_monitor(date, ticket_id, ticket_name, language, task_ids, visitors)
  ↓ Pass visitors parameter
monitor.check_availability_headless(date_str, ticket_type, languages, visitors)
  ↓ Pass visitors parameter
Falls back to run_smart_vatican_monitor(date, ticket_id, ticket_name, language, task_ids, visitors)
  ↓ Pass visitors parameter
bot.resolve_all_dynamic_ids(page, ticket_type, target_date, visitors=visitors)
```

### Deep Link Format Verification

**Correct Format**:
```
/home/fromtag/{visitors}/{timestamp}/{slug}/1
```

**Examples**:
- 1 visitor, standard: `/home/fromtag/1/1773615600000/MV-Biglietti/1`
- 2 visitors, standard: `/home/fromtag/2/1773615600000/MV-Biglietti/1`
- 2 visitors, guided: `/home/fromtag/2/1773615600000/MV-Visite-Guidate/1`

**Current Implementation** (hydra_monitor.py line 711):
```python
link_visitors = visitors  # ✅ Uses parameter
deep_url = f"https://tickets.museivaticani.va/home/fromtag/{link_visitors}/{ts}/{slug}/1"
```

**Problem**: The `visitors` parameter is hardcoded to 2 in the function call!

### API Call Format Verification

**Correct Format**:
```
/api/visit/timeavail?lang=it&visitLang={LANG}&visitTypeId={ID}&visitorNum={NUM}&visitDate={DD/MM/YYYY}
```

**Current Implementation** (god_tier_monitor_v2.py line 400):
```python
url = (
    f"https://tickets.museivaticani.va/api/visit/timeavail"
    f"?lang={api_lang}{visit_lang_param}"
    f"&visitTypeId={t_id}&visitorNum={eff_visitors}&visitDate={api_date}"
)
```

**Status**: ✅ Correct format, but `eff_visitors` defaults to 2 if not passed!

## Required Fixes

### Fix 1: Update orchestrate_all_tasks() to Extract and Pass Visitor Count

**File**: `backend/monitors/tasks.py`  
**Line**: ~970

**Current Code**:
```python
for (date, ticket_id, language), data in smart_groups.items():
    task_ids = data['task_ids']
    ticket_name = data['ticket_name']
    
    run_god_tier_vatican_monitor.apply_async(
        args=[date, ticket_id, ticket_name, language, task_ids],
        countdown=jitter
    )
```

**Fixed Code**:
```python
for (date, ticket_id, language, visitors), data in smart_groups.items():
    task_ids = data['task_ids']
    ticket_name = data['ticket_name']
    
    run_god_tier_vatican_monitor.apply_async(
        args=[date, ticket_id, ticket_name, language, task_ids, visitors],
        countdown=jitter
    )
```

**Also Update Grouping Logic** (line ~920):
```python
# OLD: key = (date, task.ticket_id, task.language or None)
# NEW: key = (date, task.ticket_id, task.language or None, task.visitors)
```

### Fix 2: Update run_god_tier_vatican_monitor() Signature

**File**: `backend/monitors/tasks.py`  
**Line**: ~394

**Current**:
```python
def run_god_tier_vatican_monitor(date, ticket_id, ticket_name, language, task_ids, use_browser_fallback=True):
```

**Fixed**:
```python
def run_god_tier_vatican_monitor(date, ticket_id, ticket_name, language, task_ids, visitors=2, use_browser_fallback=True):
```

**Pass to monitor** (line ~420):
```python
async def headless_check():
    return await monitor.check_availability_headless(
        date_str=date,
        ticket_type=ticket_type,
        languages=languages,
        visitors=visitors  # ADD THIS
    )
```

**Pass to fallback** (line ~438):
```python
return run_smart_vatican_monitor(date, ticket_id, ticket_name, language, task_ids, visitors)
```

### Fix 3: Update run_smart_vatican_monitor() Signature

**File**: `backend/monitors/tasks.py`  
**Line**: ~179

**Current**:
```python
def run_smart_vatican_monitor(date, ticket_id, ticket_name, language, task_ids):
```

**Fixed**:
```python
def run_smart_vatican_monitor(date, ticket_id, ticket_name, language, task_ids, visitors=2):
```

**Pass to bot** (line ~213):
```python
resolved_ids = await bot.resolve_all_dynamic_ids(
    page,
    ticket_type=ticket_type,
    target_date=date,
    visitors=visitors  # CHANGE FROM visitors=2
)
```

### Fix 4: Update god_tier_monitor.py check_availability_headless()

**File**: `worker_vatican/god_tier_monitor.py`  
**Line**: ~200

**Current**:
```python
async def check_availability_headless(
    self, 
    date_str: str, 
    ticket_type: int = 0,
    languages: List[str] = None
) -> List[Dict]:
```

**Fixed**:
```python
async def check_availability_headless(
    self, 
    date_str: str, 
    ticket_type: int = 0,
    languages: List[str] = None,
    visitors: int = 2
) -> List[Dict]:
```

**Pass to refresh** (line ~210):
```python
if not await self.refresh_session_with_browser(ticket_type, date_str, visitors=visitors):
```

**Use in API calls** (line ~250):
```python
visitors = visitors  # Use parameter instead of hardcoded 3 or 2
```

### Fix 5: Update god_tier_monitor_v2.py check_availability()

**File**: `worker_vatican/god_tier_monitor_v2.py`  
**Line**: ~300

**Current**:
```python
async def check_availability(
    self, 
    date_str: str, 
    ticket_type: int = 0,
    languages: List[str] = None,
    visitors: int = None
) -> List[Dict]:
```

**Status**: ✅ Already has visitors parameter, but defaults to None then 2

**Fix**: Change default to 1 (most common case):
```python
visitors: int = 1  # Change from None
```

**Or better**: Make it required (no default)

### Fix 6: Update hydra_monitor.py resolve_all_dynamic_ids()

**File**: `worker_vatican/hydra_monitor.py`  
**Line**: ~680

**Current**:
```python
async def resolve_all_dynamic_ids(self, page, ticket_type, target_date, visitors=2, force_refresh=False):
```

**Status**: ✅ Already has visitors parameter with default

**Fix**: Change default to 1:
```python
visitors=1  # Change from visitors=2
```

### Fix 7: Update hydra_monitor.py check_via_click()

**File**: `worker_vatican/hydra_monitor.py`  
**Line**: ~1132

**Current**:
```python
async def check_via_click(self, page, ticket_id, ticket_name, ticket_index=0, visit_date=None, visitors=2):
```

**Fix**: Change default to 1:
```python
visitors=1  # Change from visitors=2
```

### Fix 8: Update hydra_monitor.py check_via_api()

**File**: `worker_vatican/hydra_monitor.py`  
**Line**: ~1207

**Current**:
```python
async def check_via_api(self, page, visit_type_id, target_date, visitors=2, language="ENG", visit_lang=""):
```

**Fix**: Change default to 1:
```python
visitors=1  # Change from visitors=2
```

## Verification Checklist

After fixes are applied, verify:

- [ ] Task #19 (March 16, 1 visitor) shows correct deep link: `/fromtag/1/...`
- [ ] Task #19 API calls use `visitorNum=1`
- [ ] Task #19 finds "Musei Vaticani" tickets (not Palazzo Papale)
- [ ] God-tier monitor logs show correct visitor count
- [ ] Proxies are loaded (14 Oxylabs proxies)
- [ ] No errors in logs about missing parameters
- [ ] Dashboard shows correct availability for 1-visitor tasks

## Testing Commands

```bash
# Check task configuration
python backend/manage.py shell
from monitors.models import MonitorTask
task = MonitorTask.objects.get(id=19)
print(f"Visitors: {task.visitors}")
print(f"Dates: {task.dates}")
print(f"Language: {task.language}")

# Trigger manual check
from monitors.tasks import orchestrate_all_tasks
orchestrate_all_tasks()

# Watch logs
docker-compose logs -f celery_worker
```

## Summary

**Critical Issues**: 1 (visitor count not passed)  
**Verified Working**: 2 (API method, proxy loading)  
**Minor Issues**: 1 (default visitor counts should be 1, not 2)

**Priority**: HIGH - Fix visitor count parameter passing immediately

**Estimated Impact**: This fix will allow the bot to correctly check availability for tasks with different visitor counts, especially 1-visitor tasks which are currently broken.
