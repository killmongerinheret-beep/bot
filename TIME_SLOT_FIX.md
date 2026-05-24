# 🔧 Time Slot Selection Fix

## Issues Found

### Issue 1: "No time specified - booking cancelled"
**Cause:** Content script was looking for `config.preferredTime` but background script was only sending `config.time`.

**Fix:** Added `preferredTime: slot.time` to the config object.

### Issue 2: "Element [data-cy='time'] not found"
**Cause:** Vatican website might not have loaded time slots yet, or the page structure is different.

**Possible reasons:**
1. Ticket selection didn't work (wrong ticket ID)
2. Page hasn't loaded time slots yet
3. Vatican website structure changed
4. No time slots available for the selected date

---

## ✅ Fixes Applied

### Fix 1: Pass Time in Multiple Formats

**Before:**
```javascript
config: {
  time: slot.time,  // Only this
  ...
}
```

**After:**
```javascript
config: {
  time: slot.time,
  preferredTime: slot.time,  // ✅ Added for compatibility
  ...
}
```

### Fix 2: Pass Complete Slot Object

**Before:**
```javascript
slot: slot  // Entire object (might have issues with serialization)
```

**After:**
```javascript
slot: {
  id: slot.id,
  date: slot.date,
  time: slot.time,  // ✅ Explicitly included
  ticket_id: slot.ticket_id,
  ...
}
```

---

## 🔍 Debug Steps

### Step 1: Check if Time is Being Passed

1. Open one of the incognito windows
2. Press F12 (console)
3. Look for:
   ```
   Auto-booking config: {
     time: "10:00",
     preferredTime: "10:00",  // ✅ Should be present
     ...
   }
   ```

### Step 2: Check if Ticket Was Selected

Look for:
```
✅ Clicked ticket button for: Vatican Museums - Standard Entry
```

If you see:
```
❌ Ticket button not found for ID: TEST_TICKET_123
```

**Problem:** Ticket selection failed.

**Solution:** The ticket ID `TEST_TICKET_123` is a test ID. Real Vatican tickets have dynamic IDs that change. For testing, we need to either:
1. Use real Vatican ticket IDs
2. Mock the ticket selection

### Step 3: Check if Time Slots Loaded

In the opened window console, run:
```javascript
document.querySelectorAll("[data-cy='time']").length
```

**Expected:** > 0 (should show available time slots)

**If 0:** Time slots didn't load. Possible reasons:
- Ticket wasn't selected
- Page structure changed
- No slots available for this date

### Step 4: Check Available Times

```javascript
Array.from(document.querySelectorAll("[data-cy='time']"))
  .map(el => el.textContent.trim())
```

**Expected:** Array of times like `["09:00", "10:00", "11:00", ...]`

---

## 🐛 Common Issues

### Issue: "No time slots found on page"

**Cause:** The `[data-cy='time']` selector doesn't match any elements.

**Debug:**
```javascript
// Check if time elements exist with different selector
document.querySelectorAll('[class*="time"]').length
document.querySelectorAll('button').length  // Check all buttons
```

**Solution:** Vatican website structure might have changed. Need to inspect the actual page and update selectors.

---

### Issue: Ticket Selection Fails

**Error:** `Ticket button not found for ID: TEST_TICKET_123`

**Cause:** Test ticket ID doesn't exist on real Vatican website.

**Solution for Testing:**
We need to either:
1. Get real ticket IDs from Vatican Search API
2. Update test data to use real IDs
3. Mock the ticket selection for testing

**Get Real Ticket IDs:**
```javascript
// In Vatican website console
document.querySelectorAll("[data-cy^='bookTicket_']")
  .forEach(btn => {
    const id = btn.getAttribute('data-cy').replace('bookTicket_', '');
    const name = btn.closest('[class*="card"]')?.textContent || 'Unknown';
    console.log(`ID: ${id}, Name: ${name}`);
  });
```

---

### Issue: Time Slot Not Available

**Error:** `Exact time "10:00" not found or not available`

**Cause:** The requested time slot is sold out or doesn't exist.

**Debug:**
```javascript
// Check available times
Array.from(document.querySelectorAll("[data-cy='time']"))
  .filter(el => !el.classList.contains('disabled'))
  .map(el => el.textContent.trim())
```

**Solution:** 
- Use a different time that's actually available
- Or update test data to match available times

---

## 🧪 Testing with Real Vatican Data

Since we're using test data with fake ticket IDs, the extension won't work on the real Vatican website. Here's what we need:

### Option 1: Use Real Vatican Ticket IDs

1. Go to Vatican website manually
2. Select a date (e.g., August 1, 2026)
3. Inspect ticket buttons to get real IDs
4. Update test data with real IDs

### Option 2: Test with Mock/Bypass

For pure extension testing (without real Vatican):
1. Create a mock Vatican page locally
2. Use the same HTML structure
3. Test extension logic without hitting real site

### Option 3: End-to-End Test

1. Use real Vatican monitoring (not test data)
2. Wait for real slots to become available
3. Let extension book real tickets

---

## 🔄 Apply Fixes

1. **Reload extension:** `chrome://extensions/` → reload
2. **Clear cache:**
   ```javascript
   chrome.storage.local.remove('processedSlotIds');
   ```
3. **Test again**

---

## ✅ Expected Behavior After Fix

**Console output:**
```
🚀 Auto-booking started...
Auto-booking config: {
  time: "10:00",
  preferredTime: "10:00",  // ✅ Now present
  date: "01/08/2026",
  ...
}
⏳ Loading Vatican website...
Current page state: ticket_selection
🎫 Step 1/10: Selecting ticket...
✅ Clicked ticket button
👥 Step 2/10: Setting quantity...
⏰ Step 3/10: Selecting time slot...
Found 12 time slots
✅ Selected EXACT time: 10:00
➡️ Step 4/10: Proceeding to checkout...
```

---

## 📝 Files Modified

- `browser-extension/background.js` - Added `preferredTime` and explicit slot object

---

## 🚀 Next Steps

1. ✅ Reload extension
2. ✅ Test with debug console open
3. ✅ Check if time is being passed correctly
4. ✅ Verify ticket selection works
5. ✅ Check if time slots load

If time slots still don't load, we need to:
- Inspect the actual Vatican page structure
- Update selectors to match current website
- Or use real ticket IDs instead of test IDs

---

**Status:** ✅ Time passing fixed, ready to test!

**Note:** Test data uses fake ticket ID `TEST_TICKET_123` which won't exist on real Vatican website. For full end-to-end testing, need real ticket IDs or mock page.
