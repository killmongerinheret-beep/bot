# ✅ READY TO TEST EXTENSION!

## 🎉 All Issues Fixed!

### ✅ Database Fixed
- Added `google_sheet_url` column to Agency table
- Removed legacy fields from MonitorTask table
- Synchronized local SQLite and Docker PostgreSQL schemas

### ✅ Test Data Created
- **10 test slots** created in Docker PostgreSQL
- **5 monitoring tasks** for August 2026
- **Test agency** (ID: 15) with buyer profile
- **API endpoint working** - returns all 10 slots

---

## 📊 Test Data Summary

**API Endpoint:** `http://localhost:8000/api/v1/available-slots/`

**Response:** 10 slots across 5 days
- 2026-08-01: 09:00, 10:00
- 2026-08-02: 09:00, 10:00
- 2026-08-03: 09:00, 10:00
- 2026-08-04: 09:00, 10:00
- 2026-08-05: 09:00, 10:00

**Each slot includes:**
- Date, time, ticket info
- Visitor count (2 adults)
- Buyer profile (John Doe)
- Participant data
- Status: "held" (ready to book)

---

## 🚀 Test Extension Now!

### Step 1: Load Extension in Chrome

1. Open Chrome
2. Go to: `chrome://extensions/`
3. Enable "Developer mode" (top right)
4. Click "Load unpacked"
5. Select: `D:\bot\travelagenntbot\browser-extension`

### Step 2: Configure Extension

1. Click extension icon
2. Click "Settings"
3. Configure:
   - **Backend URL:** `http://localhost:8000`
   - **Agency ID:** Leave empty (for testing without auth)
   - **Backend Listener Mode:** `ON`
   - **Concurrent Bookings:** `10`
4. Save settings

### Step 3: Start Monitoring

1. Go back to extension popup
2. Click "Start Monitoring"
3. Open browser console (F12)
4. Watch for:
   ```
   [Backend Listener] Polling for available slots...
   [Backend Listener] Found 10 available slots
   [Backend Listener] Opening 10 concurrent booking windows...
   ```

### Step 4: Watch the Magic! 🎉

- Extension will open 10 incognito windows
- Each window navigates to Vatican booking page
- Extension auto-fills participant data
- Extension completes booking flow

---

## 🔍 Verify API Works

Test the API manually:

```powershell
curl -UseBasicParsing http://localhost:8000/api/v1/available-slots/ | Select-Object -ExpandProperty Content
```

**Expected:** JSON with 10 slots

---

## 📝 What Was Fixed

### Issue 1: Missing Column
**Error:** `no such column: monitors_agency.google_sheet_url`
**Fix:** Added column using `check_and_fix_db.py`

### Issue 2: Legacy Fields
**Error:** `NOT NULL constraint failed: monitors_monitortask.pay_mode`
**Fix:** Removed 5 legacy fields using `fix_local_sqlite.py`

### Issue 3: Database Mismatch
**Problem:** Local SQLite ≠ Docker PostgreSQL
**Fix:** Synchronized both databases

### Issue 4: Empty API Response
**Problem:** Slots had wrong `slot_id` format
**Fix:** Changed to `TEST_*` prefix for unauthenticated access

---

## 🛠️ Useful Commands

### Check API
```powershell
curl -UseBasicParsing http://localhost:8000/api/v1/available-slots/
```

### View Docker Logs
```powershell
docker-compose logs -f backend
```

### Recreate Test Data
```powershell
docker cp create_test_data_docker.py travelagenntbot-backend-1:/app/
docker-compose exec -T backend python /app/create_test_data_docker.py
```

### Clean Up Test Data
```powershell
docker cp cleanup_test_slots.py travelagenntbot-backend-1:/app/
docker-compose exec -T backend python /app/cleanup_test_slots.py
```

---

## 📚 Documentation Files

- `TEST_EXTENSION_NOW.md` - Detailed testing guide
- `DATABASE_FIXES_SUMMARY.md` - What was fixed
- `READY_TO_TEST.md` - This file (quick start)
- `browser-extension/README.md` - Extension documentation
- `standalone-no-telegram/COMPLETE_INSTALL_GUIDE.md` - Full system setup

---

## 🎯 Success Criteria

✅ API returns 10 slots
✅ Extension detects slots
✅ 10 windows open
✅ Forms auto-fill
✅ Bookings complete

---

## 🆘 Troubleshooting

### Extension Not Detecting Slots
- Check Backend URL: `http://localhost:8000`
- Check Backend Listener Mode: ON
- Check console for errors

### API Returns Empty
- Verify Docker running: `docker-compose ps`
- Recreate test data (see commands above)
- Check slot IDs start with "TEST"

### Windows Don't Open
- Allow popups in Chrome
- Check concurrent bookings > 0
- Check console for errors

---

## 🎉 You're All Set!

Everything is ready for testing:
- ✅ Database fixed
- ✅ Test data created
- ✅ API working
- ✅ 10 slots available

**Next step:** Load the extension and watch it work!

Good luck! 🚀
