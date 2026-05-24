# ✅ UPDATED: Test with Real Vatican Availability

## 🎯 What Changed

The test slot feature now checks **REAL Vatican availability** before creating a test slot.

### Before (Option A):
- ❌ Created fake slot for June 15, 2026 at 09:00
- ❌ Opened window even if Vatican had no availability
- ❌ User would see "sold out" when trying to book

### After (Option B):
- ✅ Checks Vatican API for real available slots
- ✅ Searches next 7 days for availability
- ✅ Only creates slot if Vatican actually has availability
- ✅ User can complete real booking when window opens

---

## 🔍 How It Works Now

### Step 1: User Clicks "Create Test Slot"
Extension shows: `🔍 Searching for real availability...`

### Step 2: Backend Checks Vatican API
```
Day 1 (Tomorrow): Check Search API → Check Time Availability
Day 2: Check Search API → Check Time Availability
Day 3: Check Search API → Check Time Availability
...
Day 7: Check Search API → Check Time Availability
```

### Step 3A: If Availability Found ✅
```
✅ Real available slot found and created!
Date: 08/05/2026
Time: 10:30
Ticket: Musei Vaticani - Biglietti d'ingresso
Visitors: 1

🎉 This is a REAL available slot from Vatican!

Watch your browser console (F12)
Within 10 seconds, an incognito window should open automatically!
```

### Step 3B: If No Availability ❌
```
❌ No available slots found in the next 7 days

Vatican has no availability right now. Try again later or check a different date range.

What to do:
• Try again in a few minutes
• Check Vatican website manually
• Slots usually open up 2-3 months in advance
```

---

## 🧪 Testing Instructions

### 1. Reload Extension
1. Go to `chrome://extensions/`
2. Find "Vatican Ticket Monitor"
3. Click **Reload** button

### 2. Delete Old Test Slots
1. Open extension popup
2. Scroll to test section
3. Click **"🗑️ Delete Test"** to clean up old fake slots

### 3. Create Real Test Slot
1. Click **"🧪 Create Test Slot"**
2. Wait 10-20 seconds (it's checking Vatican API)
3. Watch for result:
   - **If available:** Success message with real date/time
   - **If not available:** Error message explaining no slots found

### 4. If Slot Found - Test Auto-Booking
1. Make sure "Backend Listener" mode is selected
2. Click **"Start Monitoring"**
3. Open console (F12)
4. Within 10 seconds, incognito window opens
5. **You can now complete a REAL booking!**

### 5. Clean Up
1. Click **"Stop"** button
2. Click **"🗑️ Delete Test"**
3. Close incognito window

---

## 📊 What the Backend Does

### Vatican API Calls:

**1. Search API** (for each day):
```
GET https://tickets.museivaticani.va/api/search/resultPerTag
Params:
  - lang: it
  - visitorNum: 1
  - visitDate: 05/05/2026
  - tag: MV-Biglietti (standard) or MV-Visite-Guidate (guided)

Response:
  - visits: [{ id, name, availability: "AVAILABLE" }]
```

**2. Time Availability API** (for each available ticket):
```
GET https://tickets.museivaticani.va/api/visit/timeavail
Params:
  - visitTypeId: 2129030053
  - visitorNum: 1
  - visitDate: 05/05/2026
  - visitLang: "" (empty for standard)

Response:
  - timetable: [{ time: "09:00", availability: "AVAILABLE" }]
```

**3. Create Held Slot** (if availability found):
```
Creates HeldSlot in database with:
  - Real date from Vatican
  - Real time from Vatican
  - Real ticket ID from Vatican
  - Real ticket name from Vatican
```

---

## 🎯 Use Cases

### Use Case 1: Test Extension Mechanism
**When:** You want to verify extension polling and window-opening works
**How:** Click "Create Test Slot" and hope Vatican has availability
**Result:** If found, tests complete flow with real data

### Use Case 2: Book Real Tickets
**When:** You want to actually book Vatican tickets
**How:** 
1. Create test slot (finds real availability)
2. Extension opens incognito window
3. Complete booking manually in window
4. You get real Vatican tickets!

### Use Case 3: Monitor Real Availability
**When:** You want to know when Vatican has slots
**How:** Click "Create Test Slot" periodically
**Result:** Shows if Vatican has availability in next 7 days

---

## ⚙️ Configuration Options

You can customize the test by modifying the request body:

```javascript
// In popup.js, line ~360
body: JSON.stringify({
  visitors: 1,           // Change to 2, 3, etc.
  ticket_type: 0,        // 0=standard, 1=guided tour
  language: null         // 'ENG', 'ITA', 'FRA', 'DEU', 'SPA' for guided tours
})
```

**Examples:**

**Test for 2 visitors:**
```javascript
{ visitors: 2, ticket_type: 0, language: null }
```

**Test for guided tour in English:**
```javascript
{ visitors: 1, ticket_type: 1, language: 'ENG' }
```

**Test for family of 4:**
```javascript
{ visitors: 4, ticket_type: 0, language: null }
```

---

## 🐛 Troubleshooting

### "No available slots found in the next 7 days"

**Possible reasons:**
1. **Vatican is fully booked** - Slots open 2-3 months in advance
2. **Monday closure** - Vatican is closed on Sundays and some Mondays
3. **Special events** - Vatican may close for papal events
4. **High season** - Summer months book up quickly

**Solutions:**
- Try again in a few hours
- Check Vatican website manually: https://tickets.museivaticani.va/
- Wait for new dates to open (usually 90 days in advance)

### "Searching for real availability..." takes too long

**Normal behavior:** 10-20 seconds (checking 7 days × 2 API calls each)

**If it takes longer:**
- Vatican API might be slow
- Network issues
- Wait up to 30 seconds before canceling

### Window opens but shows "Sold Out"

**This shouldn't happen anymore!** The test only creates slots for REAL availability.

**If it does happen:**
- Someone else booked the slot in the 10 seconds between check and window opening
- Vatican's availability changed
- This is extremely rare

---

## 📁 Files Modified

### 1. backend/monitors/views.py
**Function:** `create_test_slot()`
**Changes:**
- Added Vatican Search API call
- Added Time Availability API call
- Loops through next 7 days
- Only creates slot if real availability found
- Returns 404 if no availability

### 2. browser-extension/popup.js
**Function:** `createTestSlot()`
**Changes:**
- Shows "Searching for real availability..." message
- Handles 404 response (no availability)
- Shows detailed success message with real data
- Shows helpful error message if no slots found

**Function:** `showTestMessage()`
**Changes:**
- Added 'info' type for blue messages
- Used for "searching..." status

---

## ✅ Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **Realism** | Fake data | Real Vatican availability |
| **Booking Success** | Would fail (sold out) | Can complete real booking |
| **User Experience** | Confusing (why sold out?) | Clear (real slot or no availability) |
| **Testing Value** | Tests mechanism only | Tests complete flow |
| **Practical Use** | Demo only | Can book real tickets |

---

## 🎉 Status

- ✅ Real availability checking implemented
- ✅ Searches next 7 days
- ✅ Only creates slots for real availability
- ✅ Shows helpful messages
- ✅ Can complete real bookings
- ✅ Backend restarted and ready

**Last Updated:** May 4, 2026  
**Status:** READY - Tests Real Availability
