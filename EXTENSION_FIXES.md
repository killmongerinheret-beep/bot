# 🔧 Extension Fixes Applied

## Issues Fixed

### 1. ❌ "Invalid value for state" Error

**Problem:** Chrome's `windows.create` API was rejecting the `state: 'maximized'` parameter when creating incognito windows.

**Fix:** Removed the `state` parameter from window creation. Windows will open in default size instead of maximized.

**Code Changed:**
```javascript
// Before (line 747)
const window = await chrome.windows.create({
  url: vaticanUrl,
  incognito: true,
  focused: i === 0,
  type: 'normal',
  state: 'maximized'  // ❌ Causes error
});

// After
const window = await chrome.windows.create({
  url: vaticanUrl,
  incognito: true,
  focused: i === 0,
  type: 'normal'
  // ✅ state parameter removed
});
```

---

### 2. ❌ "Could not establish connection. Receiving end does not exist"

**Problem:** Background script was trying to send messages to content script before the content script was loaded in the new windows.

**Fix:** Added retry logic with 5 attempts and 2-second delays between attempts.

**Code Changed:**
```javascript
// Before: Single attempt with catch
chrome.tabs.sendMessage(tabId, message).catch(err => {
  console.log('Content script not ready yet, will retry');
  // ❌ But never actually retried
});

// After: Proper retry mechanism
const sendMessageWithRetry = async (tabId, message, maxRetries = 5) => {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      await chrome.tabs.sendMessage(tabId, message);
      console.log(`✅ Message sent (attempt ${attempt})`);
      return true;
    } catch (err) {
      if (attempt < maxRetries) {
        console.log(`⏳ Retrying in 2s... (${attempt}/${maxRetries})`);
        await sleep(2000);
      } else {
        console.error(`❌ Failed after ${maxRetries} attempts`);
        return false;
      }
    }
  }
};
```

---

## How to Apply Fixes

### Step 1: Reload Extension

1. Go to `chrome://extensions/`
2. Find "Vatican Ticket Monitor"
3. Click the **reload icon** (circular arrow)
4. Or toggle it off and on

### Step 2: Clear Processed Slots

The extension tracks which slots it has already opened windows for. Clear this cache:

1. Open extension popup
2. Open browser console (F12)
3. Run:
   ```javascript
   chrome.storage.local.remove('processedSlotIds', () => {
     console.log('✅ Cleared processed slots cache');
   });
   ```
4. Or just restart the browser

### Step 3: Test Again

1. Click "Start Monitoring" in extension popup
2. Watch console for:
   ```
   ✅ Opened incognito window #1 for 2026-08-01 09:00
   ✅ Message sent to tab 123 (attempt 1)
   ```
3. Windows should open without errors

---

## Expected Behavior After Fix

### ✅ What You Should See:

```
[Backend Listener] 🎉 Found 10 available slots from backend!
📋 10 new slots to process
📦 Opening 10 incognito windows for parallel booking
Opening Vatican homepage for slot:
  Date: 2026-08-01 09:00
  Ticket: Vatican Museums - Standard Entry (ID: TEST_TICKET_123)
  Visitors: 2
✅ Opened incognito window #1 for 2026-08-01 09:00 (AUTO mode)
✅ Message sent to tab 456 (attempt 1)
[Auto-booking] 🚀 Auto-booking started...
```

### ❌ What You Should NOT See:

- ❌ "Invalid value for state"
- ❌ "Could not establish connection" (or max 1-2 times before retry succeeds)

---

## Troubleshooting

### Windows Still Not Opening?

**Check:**
1. Extension reloaded? (`chrome://extensions/` → reload button)
2. Incognito mode allowed? (`chrome://extensions/` → Details → "Allow in Incognito")
3. Popups allowed? (Chrome should prompt, click "Allow")

### Content Script Still Not Loading?

**Check:**
1. Vatican website accessible? (Try opening `https://tickets.museivaticani.va/home` manually)
2. Content script permissions? (Check `manifest.json` has `"matches": ["*://tickets.museivaticani.va/*"]`)
3. Console errors? (F12 → Console tab in the opened window)

### Messages Still Failing After 5 Retries?

**Possible causes:**
1. Vatican website structure changed (content script selectors outdated)
2. Network issues (Vatican website slow/down)
3. Content script blocked by CSP (Content Security Policy)

**Debug:**
1. Open one of the incognito windows manually
2. Press F12 → Console
3. Check for content script errors
4. Verify content script loaded: `console.log(window.hasOwnProperty('vaticanAutoBooker'))`

---

## Files Modified

- `browser-extension/background.js` (lines 747, 767-820)

---

## Next Steps

1. ✅ Reload extension
2. ✅ Clear processed slots cache (optional)
3. ✅ Test again
4. ✅ Watch for successful window opening and message sending
5. ✅ Verify auto-booking starts in each window

---

## Success Criteria

✅ 10 windows open without "Invalid value for state" error
✅ Messages sent successfully (within 5 attempts)
✅ Auto-booking starts in each window
✅ No "Could not establish connection" errors (or they resolve after retry)

---

## If Issues Persist

1. Check browser console for new errors
2. Verify Vatican website is accessible
3. Check if content script is loading (`chrome://extensions/` → Inspect views → content script)
4. Try with just 1 slot first (set `maxConcurrentBookings: 1` in settings)

---

**Status:** ✅ Fixes applied, ready to test!

**Next command:** Reload extension and click "Start Monitoring"
