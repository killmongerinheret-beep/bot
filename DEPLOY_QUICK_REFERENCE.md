# Deploy Extension - Quick Reference

## 📦 Package Ready!

**File:** `vatican-auto-booking-extension-v1.0.zip` (70 KB)
**Location:** Root directory

---

## 🚀 Deploy in 3 Steps

### 1. Copy ZIP to Target Computer
```
vatican-auto-booking-extension-v1.0.zip
```

### 2. Unzip
```
Extract to: vatican-auto-booking-extension/
```

### 3. Load in Chrome
```
1. Open Chrome
2. Go to: chrome://extensions/
3. Enable "Developer mode" (top right)
4. Click "Load unpacked"
5. Select the unzipped folder
6. Done! ✅
```

---

## ⚙️ Configure (Each Computer)

### Backend URL:
```
http://YOUR_BACKEND_IP:8000
```

### Agency ID:
```
Computer 1: Agency ID = 1
Computer 2: Agency ID = 2
Computer 3: Agency ID = 3
etc.
```

### Enable Listener:
```
1. Click extension icon
2. Enable "Backend Listener Mode"
3. Click "Start Backend Listener"
```

---

## ✅ Verify

### Extension Console:
```
chrome://extensions/ → Inspect views: background page

Expected:
🎉 Found X available slots from backend!
📦 Opening X incognito windows...
```

### Backend Logs:
```bash
docker-compose logs -f backend | grep "available-slots"

Expected:
GET /api/v1/available-slots/?agency_id=1
```

---

## 🔄 Update Extension

### On Development Computer:
```bash
cd browser-extension
./clean-for-deployment.sh  # Linux/Mac
# OR
clean-for-deployment.bat   # Windows
```

### On Target Computers:
```
1. Copy new ZIP
2. Unzip (replace old files)
3. chrome://extensions/ → Reload
```

---

## 📚 Full Documentation

- **DEPLOY_EXTENSION_TO_OTHER_COMPUTERS.md** - Complete deployment guide
- **EXTENSION_DEPLOYMENT_SUMMARY.md** - What was cleaned and why
- **QUICK_TEST_GUIDE.md** - Testing guide
- **TESTING_MANUAL_REVIEW_MODE.md** - Manual review mode guide

---

## 🐛 Quick Troubleshooting

### Extension not loading?
```
Check: All files present (manifest.json, background.js, etc.)
```

### Backend connection fails?
```
Check: Backend URL correct
Check: Backend accessible from target computer
Check: Firewall settings
```

### No slots detected?
```
Check: Agency ID correct
Check: Backend has slots for that agency
Check: Backend logs
```

---

**Status:** ✅ Ready to deploy!
**Package:** 70 KB, 15 essential files
**Time to deploy:** ~5 minutes per computer
