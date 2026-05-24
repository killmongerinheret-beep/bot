# 🔄 How to Reload the Browser Extension

**Important:** After updating the extension code, you MUST reload it in your browser for changes to take effect.

---

## ✅ For Chrome/Edge

1. **Open Extensions Page**
   - Type in address bar: `chrome://extensions/`
   - Or click: Menu (⋮) → Extensions → Manage Extensions

2. **Enable Developer Mode**
   - Toggle "Developer mode" switch in top-right corner (if not already on)

3. **Reload the Extension**
   - Find "Vatican Ticket Monitor" extension
   - Click the **🔄 Reload** icon/button
   - Or click "Remove" and then "Load unpacked" to reload fresh

4. **Verify**
   - Open browser console (F12)
   - Check for: "✅ Backend listener started"
   - Should NOT see 404 errors anymore

---

## ✅ For Firefox

1. **Open Debugging Page**
   - Type in address bar: `about:debugging#/runtime/this-firefox`
   - Or Menu → More Tools → Browser Tools → about:debugging

2. **Find Your Extension**
   - Look for "Vatican Ticket Monitor" in the list

3. **Reload the Extension**
   - Click **Reload** button next to the extension
   - Or click "Remove" and then "Load Temporary Add-on"

4. **Verify**
   - Open browser console (F12)
   - Check for: "✅ Backend listener started"
   - Should NOT see 404 errors anymore

---

## 🧪 Test After Reload

### 1. Check Console Logs

Open browser console (F12) and look for:

**✅ Good (After reload):**
```
✅ Backend listener started - polling every 10 seconds
No available slots yet, continuing to poll...
```

**❌ Bad (Before reload):**
```
Backend API error: 404
```

### 2. Check Backend Logs

```bash
docker-compose logs -f backend | grep available-slots
```

**✅ Good (After reload):**
```
GET /api/v1/available-slots/ HTTP/1.1" 200
```

**❌ Bad (Before reload):**
```
Not Found: /api/available-slots
```

---

## 🎯 Quick Reload Commands

### Chrome (Windows)
```
1. Press Ctrl+Shift+E (opens extensions)
2. Click reload icon for Vatican extension
3. Done!
```

### Chrome (Mac)
```
1. Press Cmd+Shift+E (opens extensions)
2. Click reload icon for Vatican extension
3. Done!
```

### Firefox
```
1. Type: about:debugging
2. Find extension → Click Reload
3. Done!
```

---

## ⚠️ If Still Getting 404 Errors

### Option 1: Hard Reload
1. Remove the extension completely
2. Close browser
3. Reopen browser
4. Load extension again from folder

### Option 2: Clear Extension Cache
1. Open extension options
2. Disable "Backend Listener Mode"
3. Close options
4. Reload extension
5. Re-enable "Backend Listener Mode"

### Option 3: Check Extension Files
Make sure `background.js` has the updated URL:
```javascript
const response = await fetch(`${backendUrl}/api/v1/available-slots/`, {
```

NOT the old URL:
```javascript
const response = await fetch(`${backendUrl}/api/available-slots`, {
```

---

## 📝 Summary

**Steps:**
1. ✅ Update extension code (already done)
2. ✅ Reload extension in browser (YOU NEED TO DO THIS)
3. ✅ Verify no more 404 errors
4. ✅ Extension now works with backend API

**The extension will NOT work until you reload it in your browser!**

---

**Last Updated:** May 4, 2026 14:02 UTC
