# Extension Update - Agency Support

## 🎯 What This Update Does

Adds agency ID support to the extension so each computer can:
1. Connect to its own agency
2. Only see tasks for that agency
3. Send notifications to that agency's Telegram chat

---

## 📝 Files to Update

### 1. Update `browser-extension/options.html`

Add agency ID field to settings page.

**Find this section:**
```html
<div class="form-group">
    <label for="backendUrl">Backend URL:</label>
    <input type="text" id="backendUrl" placeholder="http://localhost:8000">
</div>
```

**Add after it:**
```html
<div class="form-group">
    <label for="agencyId">Agency ID:</label>
    <input type="number" id="agencyId" placeholder="1" min="1">
    <small>Enter your agency ID (get from backend admin)</small>
</div>
```

---

### 2. Update `browser-extension/options.js`

Save and load agency ID.

**Find the load settings section:**
```javascript
// Load settings
chrome.storage.local.get(['backendUrl', 'backendListenerEnabled'], (result) => {
    document.getElementById('backendUrl').value = result.backendUrl || 'http://localhost:8000';
    document.getElementById('backendListenerToggle').checked = result.backendListenerEnabled || false;
});
```

**Replace with:**
```javascript
// Load settings
chrome.storage.local.get(['backendUrl', 'backendListenerEnabled', 'agencyId'], (result) => {
    document.getElementById('backendUrl').value = result.backendUrl || 'http://localhost:8000';
    document.getElementById('backendListenerToggle').checked = result.backendListenerEnabled || false;
    document.getElementById('agencyId').value = result.agencyId || 1;
});
```

**Find the save settings section:**
```javascript
// Save settings
document.getElementById('saveBtn').addEventListener('click', () => {
    const backendUrl = document.getElementById('backendUrl').value;
    const backendListenerEnabled = document.getElementById('backendListenerToggle').checked;
    
    chrome.storage.local.set({
        backendUrl: backendUrl,
        backendListenerEnabled: backendListenerEnabled
    }, () => {
        showStatus('Settings saved!', 'success');
    });
});
```

**Replace with:**
```javascript
// Save settings
document.getElementById('saveBtn').addEventListener('click', () => {
    const backendUrl = document.getElementById('backendUrl').value;
    const backendListenerEnabled = document.getElementById('backendListenerToggle').checked;
    const agencyId = parseInt(document.getElementById('agencyId').value) || 1;
    
    chrome.storage.local.set({
        backendUrl: backendUrl,
        backendListenerEnabled: backendListenerEnabled,
        agencyId: agencyId
    }, () => {
        showStatus('Settings saved! Agency ID: ' + agencyId, 'success');
    });
});
```

---

### 3. Update `browser-extension/background.js`

Add agency ID to API requests.

**Find the `pollBackend` function:**
```javascript
async function pollBackend() {
    const settings = await chrome.storage.local.get(['backendUrl', 'backendListenerEnabled']);
    
    if (!settings.backendListenerEnabled) {
        return;
    }
    
    const backendUrl = settings.backendUrl || 'http://localhost:8000';
    
    try {
        const response = await fetch(`${backendUrl}/api/v1/available-slots/`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        // ... rest of code
    }
}
```

**Replace with:**
```javascript
async function pollBackend() {
    const settings = await chrome.storage.local.get(['backendUrl', 'backendListenerEnabled', 'agencyId']);
    
    if (!settings.backendListenerEnabled) {
        return;
    }
    
    const backendUrl = settings.backendUrl || 'http://localhost:8000';
    const agencyId = settings.agencyId || 1;
    
    try {
        // Add agency_id to API request
        const response = await fetch(`${backendUrl}/api/v1/available-slots/?agency_id=${agencyId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        // ... rest of code
    }
}
```

**Find the `markSlotBooked` function:**
```javascript
async function markSlotBooked(slotId, reference) {
    const settings = await chrome.storage.local.get(['backendUrl']);
    const backendUrl = settings.backendUrl || 'http://localhost:8000';
    
    try {
        const response = await fetch(`${backendUrl}/api/v1/slots/${slotId}/mark-booked/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                reference: reference
            })
        });
        
        // ... rest of code
    }
}
```

**Replace with:**
```javascript
async function markSlotBooked(slotId, reference) {
    const settings = await chrome.storage.local.get(['backendUrl', 'agencyId']);
    const backendUrl = settings.backendUrl || 'http://localhost:8000';
    const agencyId = settings.agencyId || 1;
    
    try {
        const response = await fetch(`${backendUrl}/api/v1/slots/${slotId}/mark-booked/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                reference: reference,
                agency_id: agencyId  // Add agency ID
            })
        });
        
        // ... rest of code
    }
}
```

---

### 4. Update `browser-extension/popup.js`

Show agency ID in popup.

**Find the status display section:**
```javascript
function updateStatus() {
    chrome.storage.local.get(['backendUrl', 'backendListenerEnabled'], (result) => {
        const statusDiv = document.getElementById('status');
        
        if (result.backendListenerEnabled) {
            statusDiv.innerHTML = `
                <div class="status-item">
                    <span class="status-label">Backend Listener:</span>
                    <span class="status-value enabled">ON</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Backend URL:</span>
                    <span class="status-value">${result.backendUrl || 'Not set'}</span>
                </div>
            `;
        } else {
            statusDiv.innerHTML = `
                <div class="status-item">
                    <span class="status-label">Backend Listener:</span>
                    <span class="status-value disabled">OFF</span>
                </div>
            `;
        }
    });
}
```

**Replace with:**
```javascript
function updateStatus() {
    chrome.storage.local.get(['backendUrl', 'backendListenerEnabled', 'agencyId'], (result) => {
        const statusDiv = document.getElementById('status');
        
        if (result.backendListenerEnabled) {
            statusDiv.innerHTML = `
                <div class="status-item">
                    <span class="status-label">Backend Listener:</span>
                    <span class="status-value enabled">ON</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Backend URL:</span>
                    <span class="status-value">${result.backendUrl || 'Not set'}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Agency ID:</span>
                    <span class="status-value">${result.agencyId || 1}</span>
                </div>
            `;
        } else {
            statusDiv.innerHTML = `
                <div class="status-item">
                    <span class="status-label">Backend Listener:</span>
                    <span class="status-value disabled">OFF</span>
                </div>
            `;
        }
    });
}
```

---

## 🚀 How to Apply Updates

### Step 1: Backup Current Extension

```powershell
cd D:\bot\travelagenntbot
Copy-Item -Recurse browser-extension browser-extension-backup
```

### Step 2: Apply Code Changes

Open each file and make the changes shown above:

1. `browser-extension/options.html` - Add agency ID field
2. `browser-extension/options.js` - Save/load agency ID
3. `browser-extension/background.js` - Add agency ID to API calls
4. `browser-extension/popup.js` - Show agency ID in popup

### Step 3: Reload Extension

1. Open Chrome/Edge
2. Go to `chrome://extensions/`
3. Find "Vatican Bot Extension"
4. Click "Reload" button (🔄)

### Step 4: Configure Agency ID

1. Click extension icon
2. Click "Settings"
3. Enter your agency ID (1, 2, 3, etc.)
4. Click "Save"

### Step 5: Test

1. Click extension icon
2. Verify "Agency ID: X" shows in popup
3. Enable "Backend Listener Mode"
4. Check that extension only sees tasks for your agency

---

## 🧪 Testing

### Test 1: Verify Agency ID Saved

```javascript
// Open extension popup
// Press F12 to open console
// Run:
chrome.storage.local.get(['agencyId'], (result) => {
    console.log('Agency ID:', result.agencyId);
});
```

### Test 2: Verify API Calls Include Agency ID

```javascript
// Open extension background page
// Go to chrome://extensions/
// Click "background page" link under extension
// Go to Network tab
// Look for API calls to /api/v1/available-slots/
// Verify URL includes ?agency_id=X
```

### Test 3: Verify Notifications Go to Correct Chat

1. Create test task for agency 1
2. Worker finds tickets
3. Check Telegram - notification should go to agency 1's chat only
4. Repeat for agency 2, 3, etc.

---

## 📊 What This Enables

### Before Update
- ❌ All extensions see all tasks
- ❌ All notifications go to all Telegram chats
- ❌ Can't distinguish which computer completed booking

### After Update
- ✅ Each extension sees only its agency's tasks
- ✅ Notifications go to correct Telegram chat
- ✅ Know which computer completed each booking
- ✅ Can disable specific computers independently

---

## 🎯 Configuration Examples

### Computer 1 (Office)
```
Backend URL: http://your-server:8000
Agency ID: 1
Telegram Chat: "Vatican Bot - Office"
```

### Computer 2 (Home)
```
Backend URL: http://your-server:8000
Agency ID: 2
Telegram Chat: "Vatican Bot - Home"
```

### Computer 3 (Laptop)
```
Backend URL: http://your-server:8000
Agency ID: 3
Telegram Chat: "Vatican Bot - Laptop"
```

---

## 🔧 Backend API Update (Optional)

If you want to enforce agency filtering on the backend, update the API endpoint:

**Edit `backend/monitors/views.py`:**

Find the `available_slots` view and add agency filtering:

```python
@api_view(['GET'])
def available_slots(request):
    """Get available slots for extension"""
    agency_id = request.query_params.get('agency_id')
    
    # Filter by agency if provided
    if agency_id:
        slots = AvailableSlot.objects.filter(
            task__agency_id=agency_id,
            is_booked=False
        ).order_by('-created_at')
    else:
        # Backward compatibility - return all slots
        slots = AvailableSlot.objects.filter(
            is_booked=False
        ).order_by('-created_at')
    
    # ... rest of code
```

---

## ✅ Success Criteria

After applying updates:

1. ✅ Extension settings show "Agency ID" field
2. ✅ Extension popup shows "Agency ID: X"
3. ✅ API calls include `?agency_id=X` parameter
4. ✅ Extension only sees tasks for its agency
5. ✅ Notifications go to correct Telegram chat
6. ✅ Multiple computers work independently

---

**Update Time**: 15 minutes  
**Complexity**: Low  
**Risk**: Low (backward compatible)  
**Testing**: Required
