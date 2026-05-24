# 🧪 Test Extension Auto-Booking Feature

**Purpose:** Verify the browser extension will automatically open tabs and book when slots become available

---

## 📋 Test Plan

### What We're Testing

When the Vatican bot detects an available slot and holds it:
1. ✅ Extension should detect the held slot via API
2. ✅ Extension should open incognito window automatically
3. ✅ Extension should navigate to Vatican booking page
4. ✅ Extension should inject auto-booking script
5. ✅ User completes the booking manually or via automation

---

## 🎯 Test Scenario 1: Manual Slot Creation (Immediate Test)

### Step 1: Create a Test Held Slot

Run this in Django shell to create a fake held slot:

```bash
docker-compose exec backend python backend/manage.py shell
```

Then paste this code:

```python
from monitors.models import HeldSlot, MonitorTask, Agency
from django.utils import timezone
from datetime import timedelta

# Get or create a test agency
agency, _ = Agency.objects.get_or_create(
    name="Test Agency",
    defaults={
        'email': 'test@example.com',
        'telegram_chat_id': '123456789'
    }
)

# Get or create a test task
task, _ = MonitorTask.objects.get_or_create(
    agency=agency,
    site='vatican',
    defaults={
        'ticket_name': 'Musei Vaticani - Biglietti d\'ingresso',
        'dates': ['15/06/2026'],
        'visitors': 2,
        'is_active': True
    }
)

# Create a test held slot
held_slot = HeldSlot.objects.create(
    task=task,
    date='15/06/2026',
    slot_time='09:00',
    slot_id='TEST123456',
    ticket_id='2129030053',
    ticket_name='Musei Vaticani - Biglietti d\'ingresso',
    visitors=2,
    adult_count=2,
    child_count=0,
    total_price=35.00,
    status='held',
    hold_started_at=timezone.now(),
    last_keepalive_at=timezone.now()
)

print(f"✅ Created test held slot: ID={held_slot.id}")
print(f"   Date: {held_slot.date}")
print(f"   Time: {held_slot.slot_time}")
print(f"   Status: {held_slot.status}")
```

### Step 2: Verify Extension Detects It

1. **Open browser console** (F12)
2. **Wait 10 seconds** (extension polls every 10 seconds)
3. **Look for this message:**
   ```
   🎉 Found 1 available slots from backend!
   📦 Opening 1 incognito windows for parallel booking
   ✅ Opened incognito window #1 for 15/06/2026 09:00
   ```

### Step 3: Verify Incognito Window Opens

**Expected Behavior:**
- ✅ New incognito window opens automatically
- ✅ Navigates to Vatican booking page
- ✅ URL includes date and visitor count
- ✅ Window is maximized

**Example URL:**
```
https://tickets.museivaticani.va/home/fromtag/2/1750032000000/MV-Biglietti/1
```

### Step 4: Clean Up Test Data

```python
# In Django shell
from monitors.models import HeldSlot
HeldSlot.objects.filter(slot_id='TEST123456').delete()
print("✅ Test slot deleted")
```

---

## 🎯 Test Scenario 2: Real Slot Detection (Production Test)

### Prerequisites

1. ✅ Vatican worker is monitoring tickets
2. ✅ At least one snipe/hold task is active
3. ✅ Extension is in Backend Listener Mode
4. ✅ Extension has valid API key

### When a Real Slot Opens

**Automatic Flow:**

1. **Vatican Worker Detects Opening**
   ```
   ✅ 3 slots for Musei Vaticani - Biglietti d'ingresso 15/06/2026
   🎯 Auto-hold triggered for 15/06/2026 09:00 (task #123)
   ```

2. **Slot is Held in Database**
   - Status: `held`
   - Hold duration: 55 minutes
   - Stored in `HeldSlot` table

3. **Extension Polls Backend** (every 10 seconds)
   ```
   GET /api/v1/available-slots/
   Response: {"slots": [{"id": 123, "date": "15/06/2026", ...}]}
   ```

4. **Extension Opens Incognito Window**
   ```
   🎉 Found 1 available slots from backend!
   📦 Opening 1 incognito windows for parallel booking
   ✅ Opened incognito window #1 for 15/06/2026 09:00
   ```

5. **User Completes Booking**
   - Fill in personal details
   - Complete payment
   - Extension marks slot as paid

---

## 🔍 Verification Checklist

### Before Test
- [ ] Extension installed and enabled
- [ ] Backend Listener Mode is ON
- [ ] Backend URL is set: `http://localhost:8000`
- [ ] API key is configured
- [ ] Browser console is open (F12)
- [ ] Incognito mode is allowed for extension

### During Test
- [ ] Console shows "✅ Backend listener started"
- [ ] Console shows polling messages every 10 seconds
- [ ] No 404 errors in console
- [ ] Backend API is responding

### When Slot is Detected
- [ ] Console shows "🎉 Found X available slots"
- [ ] Incognito window opens automatically
- [ ] Window navigates to Vatican booking page
- [ ] URL contains correct date and visitor count
- [ ] Window is maximized

### After Booking
- [ ] Slot status changes to "paid" in database
- [ ] Extension continues polling for more slots
- [ ] No errors in console

---

## 🧪 Quick Test Commands

### Check if Extension is Working
```javascript
// In browser console
chrome.storage.local.get(['backendListenerActive', 'backendListenerConfig'], (result) => {
  console.log('Backend Listener Active:', result.backendListenerActive);
  console.log('Backend URL:', result.backendListenerConfig?.backendUrl);
  console.log('API Key:', result.backendListenerConfig?.apiKey ? '✅ Set' : '❌ Not set');
});
```

### Manually Trigger Check
```javascript
// In browser console (if you have access to background script)
// This will force an immediate check instead of waiting 10 seconds
checkBackendForAvailableSlots(backendListenerConfig);
```

### Check Backend API Directly
```bash
# From terminal
curl http://localhost:8000/api/v1/available-slots/

# Expected response (no slots):
{"slots":[],"count":0,"timestamp":"2026-05-04T14:10:00Z"}

# Expected response (with slots):
{"slots":[{"id":123,"date":"15/06/2026","time":"09:00",...}],"count":1,...}
```

---

## 📊 Expected Results

### Test Scenario 1 (Manual Slot)
**Timeline:**
- T+0s: Create test slot in database
- T+10s: Extension detects slot
- T+11s: Incognito window opens
- T+12s: Vatican page loads

**Success Criteria:**
- ✅ Extension detects slot within 10 seconds
- ✅ Incognito window opens automatically
- ✅ Correct URL is loaded
- ✅ No errors in console

### Test Scenario 2 (Real Slot)
**Timeline:**
- Vatican worker detects opening
- Auto-hold grabs the slot
- Extension detects held slot (within 10s)
- Incognito window opens
- User completes booking

**Success Criteria:**
- ✅ Worker successfully holds slot
- ✅ Extension detects within 10 seconds
- ✅ Window opens automatically
- ✅ Booking can be completed
- ✅ Slot marked as paid

---

## 🚨 Troubleshooting

### Extension Not Detecting Slots

**Check 1: Backend API**
```bash
curl http://localhost:8000/api/v1/available-slots/
```
Should return JSON (not 404)

**Check 2: Extension Config**
- Open extension options
- Verify Backend Listener Mode is ON
- Verify backend URL: `http://localhost:8000`
- Verify API key is set

**Check 3: Console Logs**
- Open browser console (F12)
- Should see: "✅ Backend listener started"
- Should NOT see: "Backend API error: 404"

**Check 4: Reload Extension**
```
chrome://extensions/ → Click reload icon
```

### Incognito Window Not Opening

**Check 1: Incognito Permission**
- Go to `chrome://extensions/`
- Find Vatican extension
- Click "Details"
- Enable "Allow in incognito"

**Check 2: Popup Blocker**
- Check if browser is blocking popups
- Allow popups for the extension

**Check 3: Console Errors**
- Check for JavaScript errors in console
- Look for permission errors

### Wrong URL in Incognito Window

**Check:** Slot data format
```javascript
// Expected slot format:
{
  "id": 123,
  "date": "15/06/2026",  // DD/MM/YYYY
  "time": "09:00",
  "ticket_id": "2129030053",
  "visitors": 2,
  "ticket_name": "Musei Vaticani - Biglietti d'ingresso"
}
```

---

## 📝 Test Results Template

```
TEST DATE: _______________
TESTER: _______________

SCENARIO 1: Manual Slot Creation
[ ] Test slot created successfully
[ ] Extension detected slot within 10s
[ ] Incognito window opened
[ ] Correct URL loaded
[ ] No errors in console
RESULT: PASS / FAIL

SCENARIO 2: Real Slot Detection
[ ] Worker detected opening
[ ] Auto-hold triggered
[ ] Extension detected held slot
[ ] Incognito window opened
[ ] Booking completed
[ ] Slot marked as paid
RESULT: PASS / FAIL

NOTES:
_________________________________
_________________________________
_________________________________
```

---

## 🎯 Next Steps After Testing

### If Test Passes ✅
- System is ready for production
- Extension will auto-book when slots open
- Monitor logs for successful bookings

### If Test Fails ❌
1. Check console for errors
2. Verify extension permissions
3. Verify backend API is accessible
4. Check slot data format
5. Reload extension and retry

---

## 🚀 Production Readiness

### Checklist Before Going Live

- [ ] Test Scenario 1 passed
- [ ] Extension detects slots reliably
- [ ] Incognito windows open correctly
- [ ] URLs are correct
- [ ] No console errors
- [ ] Backend API responding
- [ ] Vatican worker monitoring actively
- [ ] Telegram notifications working
- [ ] Auto-hold system working

### When Ready
- ✅ Enable Backend Listener Mode
- ✅ Set max concurrent bookings (default: 10)
- ✅ Monitor console for activity
- ✅ Wait for slots to open

---

**Last Updated:** May 4, 2026 14:10 UTC  
**Status:** Ready for Testing
