# 🔧 Time Slot Click Fix

## Issue: "Si prega di selezionare un orario della visita"

**Error Message:** "Please select a visit time" (Italian)

**Cause:** Extension was clicking PROCEDI button before the time slot was actually selected. The `selectTimeSlot` function was returning `true` but the click wasn't registering.

---

## ✅ Fixes Applied

### Fix 1: Multiple Click Methods

**Before:**
```javascript
slot.click();  // Single click attempt
return true;
```

**After:**
```javascript
// Try multiple methods to ensure click registers
slot.focus();
await sleep(200);

slot.click();
await sleep(300);

slot.dispatchEvent(new MouseEvent('click', { 
  bubbles: true, 
  cancelable: true, 
  view: window 
}));
await sleep(300);

// Handle radio/checkbox inputs
if (slot.type === 'radio' || slot.type === 'checkbox') {
  slot.checked = true;
  slot.dispatchEvent(new Event('change', { bubbles: true }));
}

await sleep(1000);  // Wait for selection to register
return true;
```

**Result:** More reliable clicking with multiple fallback methods.

---

### Fix 2: Verify Selection Before Proceeding

**Added verification step:**
```javascript
// After selecting time slot
const procediButton = document.querySelector("[data-cy='bookVisit']");
if (procediButton && procediButton.disabled) {
  console.error('PROCEDI button still disabled - retrying...');
  // Try selecting time slot again
  await selectTimeSlot(preferredTime);
}
```

**Result:** Extension checks if PROCEDI button is enabled before proceeding. If not, it retries the time selection.

---

### Fix 3: Better Logging

**Added detailed logging:**
```javascript
console.log('🎯 Found matching time slot:', text);
console.log('Attempting to click time slot...');
console.log('✅ Clicked time slot:', preferredTime);
console.log('Verifying time slot selection...');
```

**Result:** Easier to debug what's happening in the console.

---

## 🔄 How to Apply

1. **Reload extension:** `chrome://extensions/` → reload button
2. **Clear cache:**
   ```javascript
   chrome.storage.local.remove('processedSlotIds');
   ```
3. **Test again:** Click "Start Monitoring"

---

## ✅ Expected Behavior After Fix

**Console output:**
```
⏰ Step 3/10: Selecting time slot...
Found 12 time slots
🎯 Found matching time slot: 10:00
Attempting to click time slot...
✅ Clicked time slot: 10:00
Verifying time slot selection...
✅ Selected time slot: 10:00
➡️ Step 4/10: Proceeding to checkout...
```

**What should happen:**
1. ✅ Extension finds time slot
2. ✅ Extension clicks it (multiple methods)
3. ✅ Extension waits for selection to register
4. ✅ Extension verifies PROCEDI button is enabled
5. ✅ Extension clicks PROCEDI
6. ✅ Page advances to checkout (no error message)

---

## 🐛 If Issue Persists

### Check Console Output

Look for:
```
❌ PROCEDI button still disabled - time slot not selected properly
```

If you see this, it means the click still isn't working. Try:

### Debug: Check Element Type

Run in console:
```javascript
const slot = document.querySelector("[data-cy='time']");
console.log('Element type:', slot.tagName);
console.log('Element type attribute:', slot.type);
console.log('Is radio:', slot.type === 'radio');
console.log('Is checkbox:', slot.type === 'checkbox');
console.log('Parent element:', slot.parentElement.tagName);
```

### Possible Element Types:

1. **Button** - Should work with `click()`
2. **Radio button** - Needs `checked = true` + `change` event
3. **Div/Span** - Might need parent element clicked
4. **Inside dropdown** - Dropdown needs to be opened first

---

## 🔧 Additional Fixes to Try

### If time slots are radio buttons:

The fix already handles this, but if it's not working, try:

```javascript
// Find the radio button
const radio = document.querySelector(`input[type="radio"][value="${preferredTime}"]`);
if (radio) {
  radio.checked = true;
  radio.dispatchEvent(new Event('change', { bubbles: true }));
  radio.dispatchEvent(new Event('input', { bubbles: true }));
}
```

### If time slots are in a custom component:

```javascript
// Click the parent container
const timeContainer = slot.closest('[data-cy*="time"]') || slot.parentElement;
timeContainer.click();
```

### If there's a dropdown:

```javascript
// Open dropdown first
const dropdown = document.querySelector('[aria-label*="time"]');
if (dropdown) {
  dropdown.click();
  await sleep(500);
}
// Then select time
slot.click();
```

---

## 📝 Files Modified

- `browser-extension/content.js` - selectTimeSlot function (lines 594-670)
- `browser-extension/content.js` - startAutoBookingFlow verification (lines 325-350)

---

## ✅ Status

- ✅ Multiple click methods added
- ✅ Verification step added
- ✅ Better logging added
- ✅ Retry logic added
- ✅ Ready to test

---

## 🚀 Next Steps

1. ✅ Reload extension
2. ✅ Clear processed slots cache
3. ✅ Start monitoring
4. ✅ Watch console for detailed logging
5. ✅ Verify time slot is selected before PROCEDI
6. ✅ Check that no error message appears

---

**Expected result:** Extension should now properly select time slot and proceed to checkout without the "Please select a visit time" error!
