# 🔧 Database Fixes Summary

## Issues Found & Fixed

### Issue 1: Missing `google_sheet_url` Column ❌

**Error:**
```
django.db.utils.OperationalError: no such column: monitors_agency.google_sheet_url
```

**Cause:**
- Migration `0027_add_google_sheet_url` was applied but column didn't exist in local SQLite database

**Fix:**
- Manually added column using `check_and_fix_db.py`
- Column added: `google_sheet_url VARCHAR(500) NULL`

**Status:** ✅ FIXED

---

### Issue 2: Legacy Fields with NOT NULL Constraints ❌

**Error:**
```
sqlite3.IntegrityError: NOT NULL constraint failed: monitors_monitortask.pay_mode
```

**Cause:**
- Model comments said fields were "removed" but they still existed in database with NOT NULL constraints
- Fields: `pay_mode`, `checkout_method`, `remote_worker_needed`, `remote_worker_claimed`, `agent_target`

**Why These Fields Existed:**
- Originally used for old booking system
- Extension now handles these automatically:
  - `pay_mode`: Extension always auto-pays
  - `checkout_method`: Extension always uses browser
  - `remote_worker_*`: Extension handles worker coordination
  - `agent_target`: Extension handles agent targeting

**Fix:**
1. Created migration `0028_remove_monitortask_agent_target_and_more`
2. Faked migration in Docker (PostgreSQL didn't have these fields)
3. Manually removed from local SQLite using `fix_local_sqlite.py`

**Status:** ✅ FIXED

---

### Issue 3: Database Schema Mismatch ❌

**Problem:**
- Docker container uses PostgreSQL (production database)
- Local test scripts use SQLite (development database)
- Schemas were out of sync

**Fix:**
- Synchronized both databases to match current model
- PostgreSQL: Faked migration (fields never existed)
- SQLite: Removed legacy fields manually

**Status:** ✅ FIXED

---

## Scripts Created

### 1. `check_and_fix_db.py`
**Purpose:** Add missing `google_sheet_url` column to Agency table

**Usage:**
```powershell
python check_and_fix_db.py
```

**What it does:**
- Checks if column exists
- Adds column if missing
- Verifies fix

---

### 2. `check_monitortask_schema.py`
**Purpose:** Inspect MonitorTask table schema

**Usage:**
```powershell
python check_monitortask_schema.py
```

**What it shows:**
- All columns in table
- Data types and constraints
- Legacy fields that should be removed

---

### 3. `fix_local_sqlite.py`
**Purpose:** Remove legacy fields from MonitorTask table

**Usage:**
```powershell
python fix_local_sqlite.py
```

**What it does:**
- Creates new table without legacy fields
- Copies existing data (11 tasks preserved)
- Replaces old table
- Recreates indices

**Fields Removed:**
- `pay_mode`
- `checkout_method`
- `remote_worker_needed`
- `remote_worker_claimed`
- `agent_target`

---

### 4. `test_extension_flow_august.py`
**Purpose:** Create test data for extension testing

**Usage:**
```powershell
# Create test data
python test_extension_flow_august.py

# Clean up test data
python test_extension_flow_august.py --cleanup
```

**What it creates:**
- 5 monitoring tasks (August 2026)
- 12 available slots across 5 days
- Test agency (ID: 6)
- Test buyer profile

---

## Database State After Fixes

### Agency Table ✅
```
Columns:
  - id
  - name
  - api_key
  - telegram_chat_id
  - created_at
  - is_active
  - owner_id
  - plan
  - google_sheet_url ← ADDED
```

### MonitorTask Table ✅
```
Columns (25 total):
  - id, site, area_name
  - dates (JSON array)
  - preferred_times (JSON array)
  - visitors, adult_count, child_count
  - ticket_type, ticket_id, ticket_name, ticket_label
  - language (for guided tours)
  - tier, match_strategy, notification_mode
  - check_interval
  - is_active, last_checked, last_status
  - last_result_summary
  - participants_json
  - created_at, updated_at
  - agency_id

Removed Fields:
  ❌ pay_mode
  ❌ checkout_method
  ❌ remote_worker_needed
  ❌ remote_worker_claimed
  ❌ agent_target
```

---

## Migration Status

### Docker (PostgreSQL)
```
✅ 0027_add_google_sheet_url - Applied
✅ 0028_remove_monitortask_agent_target_and_more - Faked (fields didn't exist)
```

### Local (SQLite)
```
✅ google_sheet_url - Manually added
✅ Legacy fields - Manually removed
✅ Data preserved - 11 existing tasks kept
```

---

## Test Data Created

### Agency
- **Name:** Test Agency
- **ID:** 6
- **API Key:** (auto-generated)

### Tasks (5)
- **IDs:** 12, 13, 14, 15, 16
- **Dates:** Aug 1-5, 2026
- **Ticket Type:** Standard (0)
- **Visitors:** 2 adults
- **Tier:** Snipe (auto-book)

### Available Slots (12)
- **Aug 1:** 09:00, 10:00
- **Aug 2:** 09:00, 10:00, 11:00
- **Aug 3:** 09:00, 10:00
- **Aug 4:** 09:00, 10:00, 11:00
- **Aug 5:** 09:00, 10:00

---

## Verification Commands

### Check Agency Table
```powershell
python check_and_fix_db.py
```

### Check MonitorTask Table
```powershell
python check_monitortask_schema.py
```

### Test API Endpoint
```powershell
curl http://localhost:8000/api/v1/available-slots/?agency_id=6
```

### View Test Data
```powershell
python -c "import django; import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings'); import sys; sys.path.insert(0, 'backend'); django.setup(); from monitors.models import MonitorTask; print(f'Tasks: {MonitorTask.objects.count()}')"
```

---

## Next Steps

1. ✅ **Database Fixed** - All schema issues resolved
2. ✅ **Test Data Created** - 12 slots ready for testing
3. ⏭️ **Test Extension** - Follow `TEST_EXTENSION_NOW.md`
4. ⏭️ **Configure Extension** - Agency ID: 6, Backend: http://localhost:8000
5. ⏭️ **Watch It Work** - Extension should detect and book 12 slots

---

## Files to Keep

**Utility Scripts:**
- `check_and_fix_db.py` - Useful for future schema checks
- `check_monitortask_schema.py` - Useful for debugging
- `fix_local_sqlite.py` - Keep for reference
- `test_extension_flow_august.py` - Reusable for testing

**Documentation:**
- `DATABASE_FIXES_SUMMARY.md` - This file
- `TEST_EXTENSION_NOW.md` - Testing guide

**Can Delete:**
- None - all scripts are useful for future maintenance

---

## Lessons Learned

1. **Always check both databases** (Docker PostgreSQL + Local SQLite)
2. **Migrations can show as applied but not actually run** (check actual schema)
3. **Legacy fields need proper removal** (not just comments in code)
4. **Test data is essential** (can't test extension without available slots)
5. **SQLite JSON queries limited** (no `contains` lookup, use Python filtering)

---

## Status: ✅ ALL FIXED

Your database is now clean, synchronized, and ready for extension testing!

**Current State:**
- ✅ Schema matches model
- ✅ No legacy fields
- ✅ Test data created
- ✅ Both databases synchronized
- ✅ Ready for testing

**Next Command:**
```powershell
# Start testing!
curl http://localhost:8000/api/v1/available-slots/?agency_id=6
```
