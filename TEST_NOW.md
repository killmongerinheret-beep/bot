# Test Extension NOW - Quick Guide

## ✅ System is Ready!

All Docker services are running and the API is working correctly.

---

## 🚀 Test in 3 Minutes

### Step 1: Reload Extension (30 seconds)
```
1. Open Chrome
2. Go to: chrome://extensions/
3. Find: "Vatican Auto-Booking Extension"
4. Click: "Reload" button 🔄
```

### Step 2: Configure Extension (1 minute)
```
1. Click extension icon in toolbar
2. Enable "Backend Listener Mode"
3. Set Backend URL: http://localhost:8000
4. Set Agency ID: 15
5. Click "Start Backend Listener"
```

### Step 3: Open Background Console (30 seconds)
```
1. Go to: chrome://extensions/
2. Find extension
3. Click: "Inspect views: background page"
4. Watch console
```

### Step 4: Watch It Work! (1 minute)
```
Expected console output:
🎉 Found 5 available slots from backend!
📦 Opening 5 incognito windows for parallel booking
✅ Opened incognito window #1 for 25/08/2026 09:00
✅ Opened incognito window #2 for 26/08/2026 09:00
...
```

---

## 📋 What Will Happen

### Extension Will:
1. ✅ Poll backend every 10 seconds
2. ✅ Detect 5 available slots
3. ✅ Open 5 incognito windows
4. ✅ Navigate to Vatican booking pages
5. ✅ Fill forms automatically
6. ✅ Click checkboxes
7. ✅ Solve Turnstile
8. ⏸️ **STOP at checkout** (manual review mode)

### You Will:
1. 👀 Review the filled form
2. ✅ Verify all fields are correct
3. ✅ Check phone has no + sign
4. ✅ Check checkboxes are checked
5. 👆 Click ACQUISTA manually (if testing)

---

## ⚠️ Important: Test Data Limitation

The current slots use **fake Vatican IDs** for testing:
- ✅ Forms will fill correctly
- ✅ You can verify form data
- ❌ Clicking ACQUISTA will fail with "General Error"

**Why?** Vatican doesn't recognize test IDs (TEST_1, TEST_TICKET_123, etc.)

**Solution for Real Booking:**
- Use real Vatican dates
- Let worker find real available slots
- Extension books with real Vatican IDs

---

## 🔍 Verify API is Working

Before testing extension, verify API:

```bash
curl http://localhost:8000/api/v1/available-slots/?agency_id=15
```

Expected response:
```json
{
  "slots": [
    {
      "id": 22177,
      "date": "25/08/2026",
      "slot_time": "09:00",
      "ticket_name": "Vatican Museums - Standard Entry",
      ...
    },
    ...
  ],
  "count": 5
}
```

---

## 🐛 Troubleshooting

### Extension not detecting slots?
**Check:**
1. Backend URL is correct: `http://localhost:8000`
2. Agency ID is correct: `15`
3. Backend Listener is enabled
4. Background console shows polling messages

### API returns empty?
**Run:**
```bash
curl http://localhost:8000/api/v1/available-slots/?agency_id=15
```
Should return 5 slots. If not, backend needs restart.

### Incognito windows not opening?
**Check:**
1. Chrome allows incognito for extension
2. No popup blocker
3. Background console for errors

### Forms not filling?
**Check:**
1. Content script console (F12 in incognito window)
2. Look for JavaScript errors
3. Verify Vatican page loaded correctly

---

## ✅ Success Indicators

### Background Console:
```
✅ "Found 5 available slots from backend!"
✅ "Opening 5 incognito windows"
✅ "Opened incognito window #1"
```

### Incognito Windows:
```
✅ Vatican page loads
✅ Ticket selected
✅ Time selected
✅ Form filled
✅ Checkboxes checked
✅ Stopped at checkout
```

### Form Data:
```
✅ Name filled
✅ Email filled
✅ Phone filled (no + sign)
✅ City filled
✅ Country: Italia
✅ Checkboxes: ✓✓
```

---

## 📊 Current System Status

```
✅ Backend: Running (30 hours uptime)
✅ Database: 5 held slots for agency 15
✅ API: Working (returns 5 slots)
✅ Worker: Running
✅ Redis: Healthy
```

**All systems operational!** 🟢

---

## 🎯 Quick Commands

```bash
# Check Docker
docker-compose ps

# Test API
curl http://localhost:8000/api/v1/available-slots/?agency_id=15

# Check slots
docker-compose exec backend python /app/backend/manage.py shell --command="from monitors.models import HeldSlot; print(f'Slots: {HeldSlot.objects.filter(status=\"held\").count()}')"

# Backend logs
docker-compose logs -f backend
```

---

## 📚 Full Documentation

- **SYSTEM_STATUS_REPORT.md** - Complete system status
- **QUICK_TEST_GUIDE.md** - Quick testing guide
- **TESTING_MANUAL_REVIEW_MODE.md** - Manual review mode guide
- **FIX_GENERAL_ERROR.md** - Why "General Error" happens

---

**Status:** ✅ Ready to test NOW!
**Time needed:** 3 minutes
**Expected result:** Extension fills forms and stops at checkout
