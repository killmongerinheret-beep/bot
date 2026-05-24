# 🧪 Test Auto-Booking from Extension

**Easy Way:** Test the auto-booking feature directly from the browser extension!

---

## 🚀 Quick Test (1 Minute)

### Step 1: Reload Extension

1. Go to `chrome://extensions/`
2. Find "Vatican Ticket Monitor"
3. Click the **🔄 Reload** button

### Step 2: Open Extension Options

1. Click the extension icon in toolbar
2. Click "Options" or right-click → "Options"
3. Scroll down to "🧪 Testing & Debugging" section

### Step 3: Create Test Slot

1. Click the **"🧪 Create Test Slot"** button
2. Wait for success message
3. **Open browser console** (Press F12)

### Step 4: Watch It Work!

**Within 10 seconds, you should see:**

**Console:**
```
✅ Backend listener started - polling every 10 seconds
🎉 Found 1 available slots from backend!
📦 Opening 1 incognito windows for parallel booking
✅ Opened incognito window #1 for 15/06/2026 09:00
```

**Browser:**
- ✅ New incognito window opens automatically
- ✅ Navigates to Vatican booking page
- ✅ URL: `https://tickets.museivaticani.va/home/fromtag/2/...`

### Step 5: Clean Up

1. Go back to extension options
2. Click **"🗑️ Delete Test Slot"** button
3. Done!

---

## ✅ What Should Happen

### 1. After Clicking "Create Test Slot"

**Extension Options Page:**
```
✅ Test slot created successfully!
Slot ID: 123
Date: 15/06/2026
Time: 09:00

Watch your browser console (F12)
Within 10 seconds, an incognito window should open automatically!
```

### 2. In Browser Console (F12)

**Within 10 seconds:**
```
🎉 Found 1 available slots from backend!
📦 Opening 1 incognito windows for parallel booking
✅ Opened incognito window #1 for 15/06/2026 09:00
Built URL for 15/06/2026: https://tickets.museivaticani.va/home/fromtag/2/1750032000000/MV-Biglietti/1
```

### 3. Incognito Window

- ✅ Opens automatically (no manual action needed)
- ✅ Window is maximized
- ✅ Navigates to Vatican booking page
- ✅ Shows date selection for June 15, 2026
- ✅ Shows 2 visitors selected

---

## 🎯 Success Criteria

- [x] Extension options page shows success message
- [x] Browser console shows "Found 1 available slots"
- [x] Incognito window opens within 10 seconds
- [x] Vatican booking page loads
- [x] Correct date and visitor count in URL
- [x] No errors in console

---

## 🚨 Troubleshooting

### Button Says "Backend URL not configured"

**Fix:**
1. Go to extension popup (click icon)
2. Enable "Backend Listener Mode"
3. Set Backend URL: `http://localhost:8000`
4. Try again

### Button Says "API returned 404"

**Fix:**
1. Reload the extension: `chrome://extensions/` → Reload
2. Restart backend: `docker-compose restart backend`
3. Try again

### No Incognito Window Opens

**Fix:**
1. Enable incognito permission:
   - Go to `chrome://extensions/`
   - Find extension → Click "Details"
   - Enable "Allow in incognito"
2. Try again

### Console Shows "No available slots yet"

**Possible causes:**
1. Backend API not responding
2. Test slot not created
3. Extension not polling correctly

**Fix:**
```bash
# Check if slot was created
curl http://localhost:8000/api/v1/available-slots/

# Should return:
{"slots":[{"id":123,"date":"15/06/2026",...}],"count":1}
```

---

## 📊 API Endpoints

The extension uses these new endpoints:

### Create Test Slot
```
POST /api/v1/test/create-slot/
Body: {
  "date": "15/06/2026",
  "time": "09:00",
  "visitors": 2
}
```

### Delete Test Slots
```
DELETE /api/v1/test/delete-slots/
```

### Get Available Slots
```
GET /api/v1/available-slots/
```

---

## 🎉 When It Works

**You'll see this flow:**

1. **Click button** → "Creating test slot..."
2. **Success message** → "Test slot created successfully!"
3. **Console (within 10s)** → "🎉 Found 1 available slots"
4. **Incognito window** → Opens automatically
5. **Vatican page** → Loads with correct date

**This proves the auto-booking system works!** 🎯

---

## 🚀 Production Use

Once testing is successful:

1. **Keep Backend Listener Mode ON**
2. **Vatican worker will auto-hold real slots**
3. **Extension will auto-open windows**
4. **You complete the booking**

**No manual testing needed - it will work automatically when real slots open!**

---

## 📝 Alternative Method (Terminal)

If the extension buttons don't work, use terminal:

```bash
# Create test slot
docker-compose exec backend python /app/create_test_slot.py

# Delete test slot
docker-compose exec backend python /app/delete_test_slot.py
```

---

## ✅ Summary

**Testing is now super easy:**

1. ✅ Open extension options
2. ✅ Click "Create Test Slot"
3. ✅ Watch incognito window open
4. ✅ Click "Delete Test Slot"
5. ✅ Done!

**No terminal commands needed!** 🎉

---

**Last Updated:** May 4, 2026 15:07 UTC  
**Status:** Ready to Test from Extension
