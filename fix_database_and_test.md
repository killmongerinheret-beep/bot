# Fix Database and Test Extension

## 🐛 Problem

The database is missing the `google_sheet_url` column, which means migrations haven't been run yet.

---

## ✅ Solution (2 Options)

### Option 1: Run Migrations (Recommended)

This adds the `google_sheet_url` column needed for the standalone system.

```powershell
# Run migrations
docker-compose exec backend python manage.py migrate

# Verify
docker-compose exec backend python manage.py showmigrations monitors
```

**Expected output:**
```
monitors
 [X] 0001_initial
 [X] 0002_proxy_sitecredential
 ...
 [X] 0028_add_external_reference (if you copied standalone files)
```

---

### Option 2: Use Fixed Test Script (Quick)

I've updated the test script to work without the `google_sheet_url` field.

```powershell
# Just run the test again
python test_extension_flow_august.py
```

The script now checks if the column exists before using it.

---

## 🚀 Recommended: Do Both

**Step 1: Run migrations (adds google_sheet_url)**
```powershell
docker-compose exec backend python manage.py migrate
```

**Step 2: Run test script**
```powershell
python test_extension_flow_august.py
```

---

## 🔍 Check Current Database State

```powershell
# Check what migrations are applied
docker-compose exec backend python manage.py showmigrations monitors

# Check database schema
docker-compose exec backend python manage.py dbshell
```

In dbshell:
```sql
.schema monitors_agency
.exit
```

---

## ✅ After Running Migrations

You should see:
```sql
CREATE TABLE monitors_agency (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255),
    api_key VARCHAR(255),
    telegram_chat_id VARCHAR(100),
    owner_id VARCHAR(100),
    plan VARCHAR(20),
    is_active BOOLEAN,
    created_at DATETIME,
    google_sheet_url VARCHAR(500)  -- ✅ This column should exist
);
```

---

## 🧪 Test Extension After Fix

```powershell
# 1. Run migrations (if not done)
docker-compose exec backend python manage.py migrate

# 2. Run test script
python test_extension_flow_august.py

# 3. Configure extension
# Backend URL: http://localhost:8000
# Agency ID: 1

# 4. Enable Backend Listener Mode

# 5. Watch windows open!

# 6. Clean up
python test_extension_flow_august.py --cleanup
```

---

## 📝 Summary

**Problem**: Missing `google_sheet_url` column  
**Cause**: Migrations not run  
**Solution**: Run `docker-compose exec backend python manage.py migrate`  
**Alternative**: Use fixed test script (already updated)  
**Time**: 1 minute
