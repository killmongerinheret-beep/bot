# Test Extension - Quick Start Guide

## 🎯 Goal
Test the extension with fake August slots to see how many tabs open simultaneously.

---

## 🚀 Quick Test (5 Minutes)

### Step 1: Create Test Data (1 minute)
```powershell
cd D:\bot\travelagenntbot
python test_extension_flow_august.py
```

**Output:**
```
✅ Created test agency: Test Agency (ID: 1)
✅ Created 5 test tasks for August
✅ Created 13 available slots

🔧 Extension Configuration:
   Backend URL: http://localhost:8000
   Agency ID: 1
```

---

### Step 2: Configure Extension (2 minutes)

1. **Open Extension Settings**
   - Click extension icon
   - Click "Settings" button

2. **Enter Configuration**
   ```
   Backend URL: http://localhost:8000
   Agency ID: 1
   Max Concurrent Bookings: 10
   ```

3. **Save Settings**
   - Click "Save"
   - Verify "Settings saved!" message

---

### Step 3: Enable Backend Listener (30 seconds)

1. **Open Extension Popup**
   - Click extension icon

2. **Toggle Backend Listener**
   - Turn ON "Backend Listener Mode"
   - Should see "Polling: Every 10 seconds"

3. **Wait for Detection**
   - Extension polls backend every 10 seconds
   - Should detect 13 available slots within 10 seconds

---

### Step 4: Watch the Magic (1 minute)

**What happens:**
1. Extension detects 13 slots
2. Opens 10 incognito windows (your configured limit)
3. Each window starts booking process
4. Remaining 3 slots wait for first batch

**You'll see:**
- 10 incognito windows open simultaneously
- Each window navigates to Vatican booking page
- Extension console shows: "Opening 10 incognito windows for parallel booking"

---

### Step 5: Clean Up (30 seconds)
```powershell
python test_extension_flow_august.py --cleanup
```

**Output:**
```
🗑️  Cleaning up test data...
   Found:
   - 5 tasks
   - 13 slots
   - 1 buyer profiles
   ✅ Cleaned up all test data
```

---

## 🧪 Test Different Concurrent Limits

### Test 1: Default (10 concurrent)
```
Max Concurrent Bookings: 10
Available Slots: 13
Expected: Opens 10 windows, 3 wait
```

### Test 2: Increased (20 concurrent)
```
Max Concurrent Bookings: 20
Available Slots: 13
Expected: Opens 13 windows (all slots)
```

### Test 3: Reduced (5 concurrent)
```
Max Concurrent Bookings: 5
Available Slots: 13
Expected: Opens 5 windows, 8 wait
```

### Test 4: High (30 concurrent)
```
Max Concurrent Bookings: 30
Available Slots: 13
Expected: Opens 13 windows (all slots)
```

---

## 📊 How to Change Concurrent Limit

### Method 1: Extension Settings UI

1. Open extension settings
2. Find "Max Concurrent Bookings" field
3. Change value (e.g., 5, 10, 20, 30)
4. Save
5. Reload extension

### Method 2: Chrome Storage (Developer)

```javascript
// Open extension popup
// Press F12 to open console
// Run:
chrome.storage.local.set({maxConcurrentBookings: 20}, () => {
    console.log('Set to 20 concurrent bookings');
});

// Verify:
chrome.storage.local.get(['maxConcurrentBookings'], (result) => {
    console.log('Current limit:', result.maxConcurrentBookings);
});
```

---

## 🔍 Monitoring Extension Behavior

### Check Extension Console

1. **Open Background Page**
   - Go to `chrome://extensions/`
   - Find "Vatican Bot Extension"
   - Click "background page" link

2. **Watch Console Logs**
   ```
   [Backend Listener] Polling...
   [Backend Listener] Found 13 available slots
   📦 Opening 10 incognito windows for parallel booking
   🪟 Opening incognito window 1/10
   🪟 Opening incognito window 2/10
   ...
   🪟 Opening incognito window 10/10
   ```

### Check API Response

```powershell
# Test API endpoint
curl http://localhost:8000/api/v1/available-slots/?agency_id=1
```

**Expected:**
```json
{
  "slots": [
    {"id": 1, "date": "01/08/2026", "time": "09:00", "visitors": 2},
    {"id": 2, "date": "01/08/2026", "time": "10:00", "visitors": 2},
    {"id": 3, "date": "02/08/2026", "time": "09:00", "visitors": 2},
    ... (13 total)
  ]
}
```

### Check Backend Logs

```powershell
docker-compose logs backend | Select-String "available-slots"
```

---

## 🎯 Expected Results

### With 10 Concurrent Limit

**Slots Available**: 13  
**First Batch**: 10 windows open immediately  
**Second Batch**: 3 windows open after first batch completes  

**Timeline:**
```
0:00 - Extension detects 13 slots
0:01 - Opens 10 incognito windows
0:02 - All 10 windows start booking
0:30 - First window completes booking
0:31 - Opens 11th window (from remaining 3)
0:45 - Second window completes
0:46 - Opens 12th window
1:00 - Third window completes
1:01 - Opens 13th window
1:30 - All 13 bookings complete
```

### With 20 Concurrent Limit

**Slots Available**: 13  
**First Batch**: 13 windows open immediately (all slots)  
**Second Batch**: None (all slots handled in first batch)  

**Timeline:**
```
0:00 - Extension detects 13 slots
0:01 - Opens 13 incognito windows (all at once)
0:02 - All 13 windows start booking
1:00 - All 13 bookings complete
```

---

## 🔧 Troubleshooting

### Issue: Extension Doesn't Detect Slots

**Check:**
1. Backend is running: `docker-compose ps`
2. Test data exists: `python test_extension_flow_august.py` (should show "already exists")
3. API works: `curl http://localhost:8000/api/v1/available-slots/?agency_id=1`
4. Extension configured correctly: Agency ID = 1

**Fix:**
```powershell
# Restart backend
docker-compose restart backend

# Recreate test data
python test_extension_flow_august.py --cleanup
python test_extension_flow_august.py
```

### Issue: No Windows Open

**Check:**
1. Backend Listener Mode is ON
2. Max Concurrent Bookings > 0
3. Browser allows popups
4. Extension has permissions

**Fix:**
1. Toggle Backend Listener OFF then ON
2. Check extension settings
3. Allow popups for extension
4. Reload extension

### Issue: Fewer Windows Than Expected

**Check:**
```javascript
// Open extension console
chrome.storage.local.get(['maxConcurrentBookings'], (result) => {
    console.log('Max concurrent:', result.maxConcurrentBookings);
});
```

**Fix:**
1. Increase max concurrent bookings
2. Save settings
3. Reload extension
4. Try again

---

## 📝 Test Checklist

- [ ] Backend running (`docker-compose ps`)
- [ ] Test data created (`python test_extension_flow_august.py`)
- [ ] Extension installed
- [ ] Extension configured (Backend URL + Agency ID)
- [ ] Max concurrent bookings set (10, 20, etc.)
- [ ] Backend Listener Mode ON
- [ ] Extension detects slots (check console)
- [ ] Windows open (10 or configured limit)
- [ ] Test completed
- [ ] Test data cleaned up (`python test_extension_flow_august.py --cleanup`)

---

## 🎉 Success Criteria

After running the test, you should see:

1. ✅ Extension detects 13 available slots
2. ✅ Extension opens X incognito windows (X = your configured limit)
3. ✅ Each window navigates to Vatican booking page
4. ✅ Extension console shows "Opening X incognito windows"
5. ✅ Remaining slots wait for first batch to complete
6. ✅ All slots eventually processed

---

## 📊 Performance Metrics

### 10 Concurrent Bookings
- **RAM Usage**: ~4GB
- **CPU Usage**: ~30-40%
- **Time to Open**: 1-2 seconds
- **Recommended For**: Standard PC

### 20 Concurrent Bookings
- **RAM Usage**: ~8GB
- **CPU Usage**: ~50-60%
- **Time to Open**: 2-3 seconds
- **Recommended For**: High-end PC

### 30 Concurrent Bookings
- **RAM Usage**: ~12GB
- **CPU Usage**: ~70-80%
- **Time to Open**: 3-5 seconds
- **Recommended For**: Workstation/Server

---

## 🚀 Next Steps

After successful testing:

1. **Clean up test data**
   ```powershell
   python test_extension_flow_august.py --cleanup
   ```

2. **Configure for production**
   - Use real agency ID
   - Use real backend URL
   - Set appropriate concurrent limit

3. **Add real booking requests**
   - Add to Google Sheets
   - Wait for auto-sync
   - Extension will detect real slots

4. **Monitor performance**
   - Watch RAM/CPU usage
   - Adjust concurrent limit if needed
   - Scale to multiple computers if needed

---

**Test Time**: 5 minutes  
**Cleanup Time**: 30 seconds  
**Repeatable**: Yes (run test script again)  
**Safe**: Yes (uses test data only)
