# Browser Extension Test Guide

## ✅ COMPLETED: Test Slot Functionality Added to Extension

The test slot functionality has been successfully added to the browser extension popup. You can now create and delete test slots directly from the extension without using terminal commands.

---

## 🎯 How to Test Auto-Booking

### Step 1: Reload the Extension

1. Open Chrome and go to `chrome://extensions/`
2. Find "Vatican Ticket Monitor" extension
3. Click the **Reload** button (circular arrow icon)
4. This ensures the new test button code is loaded

### Step 2: Open Extension Popup

1. Click the extension icon in your browser toolbar
2. The popup window will open
3. Scroll down to the **"🧪 Test Auto-Booking"** section (pink/purple gradient background)

### Step 3: Configure Backend Listener Mode (First Time Only)

1. In the popup, find **"Monitor Mode"** dropdown
2. Select **"🚀 Backend Listener (FASTEST - RECOMMENDED)"**
3. The **Backend Configuration** section will appear
4. Verify settings:
   - **Backend URL:** `http://localhost:8000` (should be pre-filled)
   - **API Key:** Leave empty (optional)
   - **Max Concurrent Bookings:** `10` (default)

### Step 4: Create Test Slot

1. Scroll to the **"🧪 Test Auto-Booking"** section
2. Click the **"🧪 Create Test Slot"** button
3. Watch for success message:
   ```
   ✅ Test slot created successfully!
   Slot ID: 123
   Date: 15/06/2026
   Time: 09:00
   
   Watch your browser console (F12)
   Within 10 seconds, an incognito window should open automatically!
   ```

### Step 5: Watch for Incognito Window

1. **Open browser console** (Press F12 or right-click → Inspect)
2. Go to **Console** tab
3. Within **10 seconds**, you should see:
   - Console logs: `🎉 Found 1 available slots from backend!`
   - An **incognito window** opens automatically
   - Vatican booking page loads in the incognito window

### Step 6: Clean Up Test

1. After testing, click **"🗑️ Delete Test"** button
2. This removes the test slot from the database
3. Prevents false positives in future tests

---

## 🔍 What Happens Behind the Scenes

### Backend Listener Flow:

1. **Extension polls backend** every 10 seconds
   - Calls: `http://localhost:8000/api/v1/available-slots/`
   - Checks for held slots ready for booking

2. **Backend returns available slots**
   - Test slot created with date `15/06/2026`, time `09:00`
   - Status: `held` (ready for booking)

3. **Extension opens incognito windows**
   - Opens up to 10 windows simultaneously (configurable)
   - Each window loads Vatican booking page
   - Auto-fills booking details (if profile configured)

4. **User completes booking manually**
   - Extension opens the page
   - User clicks through booking steps
   - User enters payment details

---

## 🐛 Troubleshooting

### ❌ "Backend URL not configured" Error

**Solution:**
1. Select "Backend Listener" mode in Monitor Mode dropdown
2. Backend Configuration section will appear
3. Verify URL is `http://localhost:8000`

### ❌ "API returned 404" Error

**Solution:**
1. Check backend is running: `docker-compose ps`
2. Backend should show "Up" status
3. Restart backend if needed: `docker-compose restart backend`

### ❌ No Incognito Window Opens

**Possible causes:**

1. **Extension not reloaded**
   - Go to `chrome://extensions/`
   - Click Reload button on Vatican Ticket Monitor

2. **Backend not running**
   - Run: `docker-compose ps`
   - Check if backend is "Up"

3. **Test slot not created**
   - Check console for error messages
   - Try creating test slot again

4. **Polling not started**
   - Make sure you selected "Backend Listener" mode
   - Click "Start Monitoring" button first

### ❌ Console Shows "No available slots yet"

**This is normal!** The extension polls every 10 seconds. Wait up to 10 seconds after creating the test slot.

---

## 📊 Expected Console Output

### Successful Test:

```javascript
Config: {date: '15/06/2026', visitors: 1, ticketType: 0, ...}
✅ Backend listener started - polling every 10 seconds
No available slots yet, continuing to poll...
No available slots yet, continuing to poll...
🎉 Found 1 available slots from backend!
Opening incognito window for: 15/06/2026 09:00
✅ Opened incognito window for slot: 15/06/2026 09:00
```

---

## 🎯 Alternative Testing Method (Terminal)

If the extension test doesn't work, you can still test via terminal:

```bash
# Create test slot
docker-compose exec backend python /app/create_test_slot.py

# Delete test slot
docker-compose exec backend python /app/delete_test_slot.py
```

---

## 📝 Files Modified

1. **browser-extension/popup.js**
   - Added `createTestSlot()` function
   - Added `deleteTestSlot()` function
   - Added `showTestMessage()` helper
   - Added event listeners for test buttons

2. **browser-extension/popup.html**
   - Added test section with buttons
   - Added test message display area

3. **backend/monitors/views.py** (already existed)
   - `create_test_slot()` endpoint
   - `delete_test_slots()` endpoint

4. **backend/monitors/urls.py** (already existed)
   - `/api/v1/test/create-slot/` route
   - `/api/v1/test/delete-slots/` route

---

## ✅ System Status

- **Redis:** ✅ Stable, no restarts
- **Vatican Worker:** ✅ Active, monitoring tickets
- **Backend API:** ✅ Running on port 8000
- **Browser Extension:** ✅ Connected, polling every 10 seconds
- **Test Endpoints:** ✅ Registered and working

---

## 🚀 Next Steps

1. **Reload extension** in Chrome
2. **Open popup** by clicking extension icon
3. **Click "Create Test Slot"** button
4. **Watch console** (F12) for logs
5. **Wait 10 seconds** for incognito window to open
6. **Click "Delete Test"** to clean up

---

**Last Updated:** May 4, 2026  
**Status:** Ready for Testing
