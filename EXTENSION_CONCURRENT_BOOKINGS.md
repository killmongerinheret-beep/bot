# Extension Concurrent Bookings Configuration

## 🖥️ How Many Tabs Can Open Simultaneously?

The extension supports **configurable concurrent bookings** per computer.

### Default Configuration
- **Default**: 10 concurrent bookings
- **Configurable**: Yes, can be increased
- **Recommended**: 10-20 for stable performance
- **Maximum**: Limited by your computer's resources

---

## 🔧 Current Limits

### Per Computer
- **Default**: 10 incognito windows open simultaneously
- **Each window**: 1 booking process
- **Total**: 10 bookings at the same time per computer

### Multiple Computers
- **Computer 1**: 10 concurrent bookings
- **Computer 2**: 10 concurrent bookings
- **Computer 3**: 10 concurrent bookings
- **Total**: 30 concurrent bookings (3 computers × 10)

### System-Wide
- **Unlimited computers**: Each computer can run extension
- **Unlimited agencies**: Each agency can have multiple computers
- **Total capacity**: Computers × Concurrent bookings per computer

---

## 📊 Performance Considerations

### Computer Resources

| Concurrent Bookings | RAM Usage | CPU Usage | Recommended For |
|---------------------|-----------|-----------|-----------------|
| 5 | ~2GB | Low | Basic PC |
| 10 | ~4GB | Medium | Standard PC |
| 20 | ~8GB | High | High-end PC |
| 30 | ~12GB | Very High | Workstation |
| 50+ | ~20GB+ | Extreme | Server |

### Browser Limits
- **Chrome/Edge**: Can handle 50+ incognito windows
- **Memory**: Each window uses ~200-400MB RAM
- **CPU**: Each booking uses ~5-10% CPU during active booking

---

## 🚀 How to Increase Concurrent Bookings

### Method 1: Extension Settings (Recommended)

1. Open extension
2. Click "Settings"
3. Find "Max Concurrent Bookings" field
4. Change from `10` to desired number (e.g., `20`)
5. Click "Save"

**Current Code** (already supports this):
```javascript
// In browser-extension/popup.js
config.maxConcurrentBookings = parseInt(document.getElementById('maxConcurrentBookings').value);
```

### Method 2: Edit Extension Code

If the settings UI doesn't have the field yet, add it:

**Edit `browser-extension/popup.html`:**
```html
<div class="form-group">
    <label for="maxConcurrentBookings">Max Concurrent Bookings:</label>
    <input type="number" id="maxConcurrentBookings" value="10" min="1" max="50">
    <small>Number of simultaneous booking windows (default: 10)</small>
</div>
```

**Edit `browser-extension/popup.js`:**
```javascript
// Load settings
chrome.storage.local.get(['maxConcurrentBookings'], (result) => {
    document.getElementById('maxConcurrentBookings').value = result.maxConcurrentBookings || 10;
});

// Save settings
document.getElementById('saveBtn').addEventListener('click', () => {
    const maxConcurrentBookings = parseInt(document.getElementById('maxConcurrentBookings').value) || 10;
    
    chrome.storage.local.set({
        maxConcurrentBookings: maxConcurrentBookings
    }, () => {
        alert('Settings saved! Max concurrent bookings: ' + maxConcurrentBookings);
    });
});
```

---

## 🧪 Testing Concurrent Bookings

### Test Script Created

I've created `test_extension_flow_august.py` to test the extension with multiple slots.

**Run the test:**
```powershell
cd D:\bot\travelagenntbot
python test_extension_flow_august.py
```

**What it does:**
1. Creates test agency
2. Creates 5 test tasks for August 2026
3. Creates 10-15 available slots
4. Extension will detect all slots
5. Extension will open windows (up to your configured limit)

**Expected output:**
```
🧪 TEST EXTENSION FLOW - AUGUST SLOTS
================================================================================

✅ Created test agency: Test Agency (ID: 1)
✅ Created test buyer profile: John Doe

📋 Creating 5 test tasks for August...
   ✅ Created task 1: 01/08/2026 (ID: 1)
   ✅ Created task 2: 02/08/2026 (ID: 2)
   ✅ Created task 3: 03/08/2026 (ID: 3)
   ✅ Created task 4: 04/08/2026 (ID: 4)
   ✅ Created task 5: 05/08/2026 (ID: 5)

🎫 Creating test available slots...
   ✅ Created slot: 01/08/2026 09:00 (ID: 1)
   ✅ Created slot: 01/08/2026 10:00 (ID: 2)
   ✅ Created slot: 02/08/2026 09:00 (ID: 3)
   ✅ Created slot: 02/08/2026 10:00 (ID: 4)
   ✅ Created slot: 02/08/2026 11:00 (ID: 5)
   ... (10-15 total slots)

================================================================================
🎉 TEST SETUP COMPLETE!
================================================================================

📊 Summary:
   Agency: Test Agency (ID: 1)
   Tasks: 5
   Available Slots: 13

📅 Test Dates:
   01/08/2026: 2 slots at 09:00, 10:00
   02/08/2026: 3 slots at 09:00, 10:00, 11:00
   03/08/2026: 2 slots at 09:00, 10:00
   04/08/2026: 3 slots at 09:00, 10:00, 11:00
   05/08/2026: 3 slots at 09:00, 10:00, 11:00

🔧 Extension Configuration:
   Backend URL: http://localhost:8000
   Agency ID: 1
   Backend Listener: ON

🧪 Testing Steps:
   1. Configure extension with Agency ID: 1
   2. Enable Backend Listener Mode
   3. Extension will detect 13 available slots
   4. Extension will open 10 incognito windows (or your configured limit)
   5. Watch the magic happen! 🎉

📝 API Endpoint to Test:
   GET http://localhost:8000/api/v1/available-slots/?agency_id=1

🗑️  To Clean Up After Testing:
   python test_extension_flow_august.py --cleanup

================================================================================
```

---

## 🧪 Testing Steps

### Step 1: Run Test Script
```powershell
python test_extension_flow_august.py
```

### Step 2: Configure Extension
1. Open extension
2. Settings:
   - Backend URL: `http://localhost:8000`
   - Agency ID: `1` (from test script output)
   - Max Concurrent Bookings: `10` (or more)
3. Enable Backend Listener Mode

### Step 3: Watch Extension Work
1. Extension polls backend every 10 seconds
2. Detects 13 available slots
3. Opens 10 incognito windows (or your configured limit)
4. Each window starts booking process
5. Monitor console logs

### Step 4: Verify API Response
```powershell
# Test API endpoint
curl http://localhost:8000/api/v1/available-slots/?agency_id=1
```

**Expected response:**
```json
{
  "slots": [
    {
      "id": 1,
      "date": "01/08/2026",
      "time": "09:00",
      "visitors": 2,
      "ticket_name": "Vatican Museums - Standard Entry",
      "task_id": 1
    },
    {
      "id": 2,
      "date": "01/08/2026",
      "time": "10:00",
      "visitors": 2,
      "ticket_name": "Vatican Museums - Standard Entry",
      "task_id": 1
    },
    ... (13 total slots)
  ]
}
```

### Step 5: Clean Up After Testing
```powershell
python test_extension_flow_august.py --cleanup
```

---

## 📊 Concurrent Booking Scenarios

### Scenario 1: Single Computer, 10 Slots
```
Computer 1:
  - Max Concurrent: 10
  - Available Slots: 13
  - Opens: 10 windows immediately
  - Remaining: 3 slots wait for first batch to complete
```

### Scenario 2: Single Computer, 20 Slots
```
Computer 1:
  - Max Concurrent: 10
  - Available Slots: 20
  - Opens: 10 windows immediately
  - Remaining: 10 slots wait for first batch to complete
  - Second batch: Opens 10 more windows when first batch completes
```

### Scenario 3: Multiple Computers, 30 Slots
```
Computer 1 (Agency 1):
  - Max Concurrent: 10
  - Available Slots: 10 (for Agency 1)
  - Opens: 10 windows

Computer 2 (Agency 2):
  - Max Concurrent: 10
  - Available Slots: 10 (for Agency 2)
  - Opens: 10 windows

Computer 3 (Agency 3):
  - Max Concurrent: 10
  - Available Slots: 10 (for Agency 3)
  - Opens: 10 windows

Total: 30 concurrent bookings across 3 computers
```

### Scenario 4: High-End PC, 50 Slots
```
Computer 1 (High-End):
  - Max Concurrent: 30
  - Available Slots: 50
  - Opens: 30 windows immediately
  - Remaining: 20 slots wait for first batch
  - RAM: ~12GB
  - CPU: ~60-80% during booking
```

---

## 🎯 Recommended Configurations

### Basic Setup (1 Computer)
```
Computer: Standard PC (8GB RAM)
Max Concurrent: 10
Expected Performance: Stable
Use Case: Small agency, 10-20 bookings/day
```

### Medium Setup (2-3 Computers)
```
Computer 1: 10 concurrent
Computer 2: 10 concurrent
Computer 3: 10 concurrent
Total: 30 concurrent
Expected Performance: Very stable
Use Case: Medium agency, 50-100 bookings/day
```

### Large Setup (5+ Computers)
```
Computer 1-5: 10 concurrent each
Total: 50 concurrent
Expected Performance: Excellent
Use Case: Large agency, 200+ bookings/day
```

### High-Performance Setup (Dedicated Servers)
```
Server 1: 30 concurrent
Server 2: 30 concurrent
Server 3: 30 concurrent
Total: 90 concurrent
Expected Performance: Maximum
Use Case: Enterprise, 500+ bookings/day
```

---

## 🔧 Troubleshooting

### Issue: Extension Opens Fewer Windows Than Expected

**Check max concurrent setting:**
```javascript
// Open extension console
chrome.storage.local.get(['maxConcurrentBookings'], (result) => {
    console.log('Max concurrent:', result.maxConcurrentBookings);
});
```

**Fix: Increase limit:**
1. Open extension settings
2. Change "Max Concurrent Bookings" to higher number
3. Save and reload extension

### Issue: Computer Slows Down

**Symptoms:**
- High RAM usage
- High CPU usage
- Browser becomes unresponsive

**Solutions:**
1. Reduce max concurrent bookings (10 → 5)
2. Close other applications
3. Upgrade computer RAM
4. Use multiple computers instead

### Issue: Some Windows Don't Open

**Possible causes:**
- Browser popup blocker
- Insufficient permissions
- Memory limit reached

**Solutions:**
1. Allow popups for extension
2. Check extension permissions
3. Restart browser
4. Reduce concurrent bookings

---

## 📝 Summary

### Current Limits
- **Default**: 10 concurrent bookings per computer
- **Configurable**: Yes, via extension settings
- **Recommended**: 10-20 for most computers
- **Maximum**: Limited by computer resources

### Testing
- **Test script**: `test_extension_flow_august.py`
- **Creates**: 13 test slots for August 2026
- **Tests**: Extension concurrent booking capability
- **Cleanup**: `python test_extension_flow_august.py --cleanup`

### Scaling
- **Single computer**: 10-30 concurrent bookings
- **Multiple computers**: Unlimited (10 per computer)
- **Total capacity**: Computers × Concurrent bookings

---

**Next Steps:**
1. Run test script: `python test_extension_flow_august.py`
2. Configure extension with test agency ID
3. Watch extension open multiple windows
4. Adjust max concurrent bookings as needed
5. Clean up: `python test_extension_flow_august.py --cleanup`
