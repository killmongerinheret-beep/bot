# 🧪 TEST EXTENSION NOW - Quick Start Guide

## ✅ Prerequisites Complete

- ✅ Database fixed (google_sheet_url column added)
- ✅ Legacy fields removed (pay_mode, checkout_method, etc.)
- ✅ Test data created (5 tasks, 12 available slots for August 2026)
- ✅ Docker services running

## 🎯 Test Data Summary

**Agency:** Test Agency (ID: 6)
**Tasks:** 5 monitoring tasks
**Available Slots:** 12 slots across 5 days

### Test Dates & Slots:
- **2026-08-01**: 2 slots (09:00, 10:00)
- **2026-08-02**: 3 slots (09:00, 10:00, 11:00)
- **2026-08-03**: 2 slots (09:00, 10:00)
- **2026-08-04**: 3 slots (09:00, 10:00, 11:00)
- **2026-08-05**: 2 slots (09:00, 10:00)

---

## 🚀 Step-by-Step Testing

### Step 1: Verify Backend API

Test that the backend can see the available slots:

```powershell
# Test API endpoint
curl http://localhost:8000/api/v1/available-slots/?agency_id=6
```

**Expected Response:**
```json
{
  "status": "success",
  "slots": [
    {
      "task_id": 12,
      "date": "2026-08-01",
      "time": "09:00",
      "visitors": 2,
      "ticket_type": 0
    },
    // ... 11 more slots
  ],
  "total": 12
}
```

---

### Step 2: Load Extension in Chrome

1. **Open Chrome**
2. **Go to:** `chrome://extensions/`
3. **Enable "Developer mode"** (top right toggle)
4. **Click "Load unpacked"**
5. **Select folder:** `D:\bot\travelagenntbot\browser-extension`

---

### Step 3: Configure Extension

1. **Click extension icon** in Chrome toolbar
2. **Click "Settings"** button
3. **Configure:**
   - **Backend URL:** `http://localhost:8000`
   - **Agency ID:** `6`
   - **Backend Listener Mode:** `ON` (enable checkbox)
   - **Concurrent Bookings:** `10` (default)
4. **Click "Save Settings"**

---

### Step 4: Start Extension

1. **Go back to extension popup**
2. **Click "Start Monitoring"**
3. **Watch the console** (F12 → Console tab)

---

### Step 5: What Should Happen

**Within 10 seconds:**

1. ✅ Extension polls backend API
2. ✅ Detects 12 available slots
3. ✅ Opens 10 incognito windows (concurrent limit)
4. ✅ Each window navigates to Vatican booking page
5. ✅ Extension auto-fills participant data
6. ✅ Extension auto-completes booking

**Console Output:**
```
[Backend Listener] Polling for available slots...
[Backend Listener] Found 12 available slots
[Backend Listener] Opening 10 concurrent booking windows...
[Booking] Window 1: 2026-08-01 09:00
[Booking] Window 2: 2026-08-01 10:00
[Booking] Window 3: 2026-08-02 09:00
...
```

---

## 🔍 Troubleshooting

### Extension Not Detecting Slots

**Check:**
1. Backend URL correct? (`http://localhost:8000`)
2. Agency ID correct? (`6`)
3. Backend Listener Mode enabled?
4. Docker services running? (`docker-compose ps`)

**Test API manually:**
```powershell
curl http://localhost:8000/api/v1/available-slots/?agency_id=6
```

---

### No Windows Opening

**Check:**
1. Chrome allows popups from extension
2. Concurrent bookings setting > 0
3. Console shows "Opening X concurrent booking windows"

**Fix:**
- Go to `chrome://settings/content/popups`
- Allow popups for extension

---

### Windows Open But Don't Book

**Check:**
1. Vatican website structure hasn't changed
2. Extension content script loaded (check console)
3. Participant data exists in database

**Debug:**
- Open one incognito window manually
- Check console for errors
- Verify extension content script injected

---

## 📊 Monitor Progress

### Extension Console (F12)
```
[Backend Listener] Polling...
[Backend Listener] Found 12 slots
[Booking] Opening windows...
[Booking] Window 1: Filling form...
[Booking] Window 1: Submitting...
[Booking] Window 1: Success!
```

### Backend Logs
```powershell
docker-compose logs -f backend
```

Look for:
```
GET /api/v1/available-slots/?agency_id=6
POST /api/v1/booking-complete/
```

---

## 🧹 Clean Up After Testing

When done testing, remove test data:

```powershell
python test_extension_flow_august.py --cleanup
```

This will:
- Delete 5 test tasks
- Delete 12 test slots
- Keep test agency (for future tests)

---

## 🎯 Success Criteria

✅ **Extension detects slots** (console shows "Found 12 slots")
✅ **Windows open** (10 incognito windows appear)
✅ **Forms auto-fill** (participant names populated)
✅ **Bookings complete** (payment links generated)

---

## 📝 Next Steps After Successful Test

1. **Test with real Vatican data** (remove test data, use real monitoring)
2. **Test concurrent booking limits** (try 20, 30, 50 concurrent)
3. **Test multiple computers** (install extension on other PCs)
4. **Configure Telegram notifications** (payment link alerts)

---

## 🆘 Need Help?

**Check these files:**
- `browser-extension/README.md` - Full extension documentation
- `browser-extension/QUICK_START.md` - Extension setup guide
- `standalone-no-telegram/COMPLETE_INSTALL_GUIDE.md` - System setup
- `TEST_EXTENSION_QUICK_START.md` - Detailed testing guide

**Common Issues:**
- **CORS errors:** Backend not allowing extension origin
- **401 Unauthorized:** Agency ID doesn't exist
- **No slots found:** Test data not created or wrong agency ID
- **Windows close immediately:** Vatican website blocking automation

---

## 🎉 You're Ready!

Your test environment is set up and ready to go. Just follow the steps above and watch the extension work its magic!

**Current Status:**
- ✅ Database: Fixed
- ✅ Test Data: Created (12 slots)
- ✅ Backend: Running (http://localhost:8000)
- ✅ Extension: Ready to load

**Next Command:**
```powershell
# Verify API works
curl http://localhost:8000/api/v1/available-slots/?agency_id=6
```

Good luck! 🚀
