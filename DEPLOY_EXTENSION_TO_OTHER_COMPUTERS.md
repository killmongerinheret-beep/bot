# Deploy Extension to Other Computers

## ✅ Extension Cleaned and Ready!

The extension folder has been cleaned and a deployment package has been created.

---

## 📦 What's in the Clean Package

### Essential Files Only:
```
vatican-auto-booking-extension-v1.0.zip
├── manifest.json          # Extension configuration
├── background.js          # Background service worker
├── content.js             # Page automation script
├── popup.html/js/css      # Extension popup UI
├── options.html/js        # Options page
├── settings.html/js       # Settings page
├── icons/                 # Extension icons
├── README.md              # Main documentation
├── INSTALLATION.md        # Installation guide
└── QUICK_START.md         # Quick start guide
```

### Removed (Development Files):
- ❌ HAR debug files
- ❌ Extra documentation (20+ MD files)
- ❌ Development tools
- ❌ Test files

---

## 🚀 Deploy to Other Computers

### Method 1: Use the ZIP Package (Recommended)

1. **Copy the ZIP file to target computer:**
   ```
   vatican-auto-booking-extension-v1.0.zip
   ```

2. **On target computer:**
   ```
   1. Unzip the file
   2. Open Chrome
   3. Go to chrome://extensions/
   4. Enable "Developer mode" (top right)
   5. Click "Load unpacked"
   6. Select the unzipped folder
   7. Done! ✅
   ```

### Method 2: Copy the Folder Directly

1. **Copy the entire `browser-extension` folder to target computer**

2. **On target computer:**
   ```
   1. Open Chrome
   2. Go to chrome://extensions/
   3. Enable "Developer mode"
   4. Click "Load unpacked"
   5. Select the browser-extension folder
   6. Done! ✅
   ```

---

## 🔧 Configuration on Each Computer

After installing the extension on each computer:

### 1. Configure Backend Connection
```
1. Click extension icon
2. Go to "Settings" or "Options"
3. Set Backend URL: http://YOUR_BACKEND_IP:8000
4. Set Agency ID: (unique for each computer/agency)
5. Save settings
```

### 2. Enable Backend Listener Mode
```
1. Click extension icon
2. Enable "Backend Listener Mode"
3. Click "Start Backend Listener"
4. Extension will poll backend every 10 seconds
```

### 3. Verify Connection
```
1. Check extension popup
2. Should show: "Backend Listener: Active"
3. Check background console for:
   "🎉 Found X available slots from backend!"
```

---

## 🏢 Multi-Computer Setup

### Scenario: 5 Computers, Each Booking for Different Agency

**Computer 1:**
- Agency ID: 1
- Backend URL: http://192.168.1.100:8000

**Computer 2:**
- Agency ID: 2
- Backend URL: http://192.168.1.100:8000

**Computer 3:**
- Agency ID: 3
- Backend URL: http://192.168.1.100:8000

**Computer 4:**
- Agency ID: 4
- Backend URL: http://192.168.1.100:8000

**Computer 5:**
- Agency ID: 5
- Backend URL: http://192.168.1.100:8000

Each computer will:
- Poll backend for slots assigned to their agency
- Open 10 concurrent incognito windows
- Book tickets independently

---

## 📋 Deployment Checklist

### Before Deployment:
- [x] Extension cleaned (unnecessary files removed)
- [x] ZIP package created
- [ ] Backend server accessible from target computers
- [ ] Agency IDs assigned for each computer
- [ ] Test data or real monitoring tasks created

### On Each Target Computer:
- [ ] Chrome installed
- [ ] Extension installed (load unpacked)
- [ ] Backend URL configured
- [ ] Agency ID configured
- [ ] Backend Listener enabled
- [ ] Connection verified (check console)

### Testing:
- [ ] Extension polls backend successfully
- [ ] Slots detected from backend
- [ ] Incognito windows open
- [ ] Forms fill automatically
- [ ] Extension stops at checkout (manual review mode)
- [ ] Manual ACQUISTA click works

---

## 🔄 Updating the Extension

When you make changes to the extension:

1. **On development computer:**
   ```bash
   # Clean and package
   cd browser-extension
   ./clean-for-deployment.sh  # Linux/Mac
   # OR
   clean-for-deployment.bat   # Windows
   ```

2. **Copy new ZIP to target computers**

3. **On each target computer:**
   ```
   1. Go to chrome://extensions/
   2. Find the extension
   3. Click "Reload" button
   4. Or remove and reinstall
   ```

---

## 🐛 Troubleshooting

### Extension not loading
**Solution:** Make sure all files are present (manifest.json, background.js, content.js, etc.)

### Backend connection fails
**Solution:** 
- Check backend URL is correct
- Verify backend is accessible from target computer
- Check firewall settings

### No slots detected
**Solution:**
- Verify Agency ID is correct
- Check backend has slots for that agency
- Check backend logs: `docker-compose logs -f backend`

### Forms not filling
**Solution:**
- Check content script console (F12 in incognito window)
- Verify profile data exists in backend
- Check for JavaScript errors

---

## 📊 Monitoring Multiple Computers

### Backend Logs:
```bash
# Watch all booking activity
docker-compose logs -f backend | grep "available-slots"

# Check which agencies are polling
docker-compose logs -f backend | grep "Agency"
```

### Extension Logs:
On each computer:
```
1. Open chrome://extensions/
2. Find extension
3. Click "Inspect views: background page"
4. Watch console for:
   - "Found X available slots"
   - "Opened incognito window"
   - "Booking paused"
```

---

## 🎯 Best Practices

### 1. Unique Agency IDs
- Assign unique Agency ID to each computer
- Prevents conflicts and duplicate bookings

### 2. Backend Accessibility
- Use static IP for backend server
- Or use domain name (e.g., booking.yourcompany.com)
- Ensure firewall allows connections

### 3. Regular Updates
- Keep extension updated on all computers
- Test changes on one computer first
- Then deploy to others

### 4. Monitoring
- Check backend logs regularly
- Monitor extension console on each computer
- Set up alerts for errors

---

## 📁 Files Included

### In ZIP Package:
```
vatican-auto-booking-extension-v1.0.zip (created in parent directory)
```

### In Extension Folder:
```
browser-extension/
├── Core Files (required)
│   ├── manifest.json
│   ├── background.js
│   ├── content.js
│   
├── UI Files (required)
│   ├── popup.html/js/css
│   ├── options.html/js
│   ├── settings.html/js
│   
├── Assets (required)
│   └── icons/
│       ├── icon16.png
│       ├── icon48.png
│       └── icon128.png
│
├── Documentation (optional but recommended)
│   ├── README.md
│   ├── INSTALLATION.md
│   └── QUICK_START.md
│
└── Deployment Scripts (for re-packaging)
    ├── clean-for-deployment.sh
    ├── clean-for-deployment.bat
    ├── package-chrome.sh
    └── package-chrome.bat
```

---

## ✅ Summary

**What's Ready:**
- ✅ Extension cleaned (20+ unnecessary files removed)
- ✅ ZIP package created: `vatican-auto-booking-extension-v1.0.zip`
- ✅ Deployment scripts included
- ✅ Documentation included

**How to Deploy:**
1. Copy ZIP to target computer
2. Unzip
3. Load unpacked in Chrome
4. Configure backend URL and agency ID
5. Enable backend listener
6. Done!

**What's Removed:**
- ❌ HAR debug files
- ❌ 20+ extra documentation files
- ❌ Development tools
- ❌ Test files

**What's Kept:**
- ✅ All essential extension files
- ✅ Core documentation (README, INSTALLATION, QUICK_START)
- ✅ Deployment scripts for future updates

---

**Status:** ✅ Ready to deploy to other computers!
**Package:** `vatican-auto-booking-extension-v1.0.zip`
**Size:** ~50KB (clean and minimal)
