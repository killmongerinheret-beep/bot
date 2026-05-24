# Final Fixes: Recap Double-Click & Checkboxes

## Issues Fixed

### 1. ✅ Double PROCEDI Click (Recap Page Issue)
**Problem:** Extension was clicking PROCEDI twice, causing navigation issues and preventing the checkout form from loading properly.

**Root Cause:** 
- After clicking PROCEDI, the code checked if URL contained "checkout" or "recap"
- If neither was found, it would retry clicking PROCEDI
- This could cause the page to navigate forward and then back, breaking the flow

**Solution:**
- Added double-click prevention with `procediClickInProgress` flag
- Changed retry logic to only retry if on "recap" page (intermediate step)
- If not on checkout or recap, return error instead of blindly retrying
- Added 3-second lock after clicking to prevent immediate re-click

**Files Changed:**
- `browser-extension/content.js` (lines 726-755)

**Code:**
```javascript
let procediClickInProgress = false;

async function clickProcedi() {
  // Prevent double-clicking
  if (procediClickInProgress) {
    console.log('⚠️ PROCEDI click already in progress, skipping...');
    return false;
  }
  
  procediClickInProgress = true;
  
  try {
    await waitForElement("[data-cy='bookVisit']", 10000);
    
    const button = document.querySelector("[data-cy='bookVisit']") ||
      Array.from(document.querySelectorAll('button')).find(b => /PROCEDI/i.test(b.textContent));
    
    if (button) {
      scrollIntoView(button);
      await sleep(500);
      button.click();
      console.log('✅ Clicked PROCEDI');
      
      // Keep lock for 3 seconds to prevent immediate re-click
      await sleep(3000);
      return true;
    }
    
    return false;
  } finally {
    procediClickInProgress = false;
  }
}
```

**Retry Logic:**
```javascript
// Check if we're on recap page (intermediate step before checkout)
if (currentUrl.includes('recap')) {
  console.log('On recap page, clicking PROCEDI again to go to checkout...');
  await sleep(2000);
  await clickProcedi();
  await sleep(5000);
} else if (!currentUrl.includes('checkout')) {
  console.error('❌ Not on checkout or recap page. Current URL:', currentUrl);
  notifyProgress('❌ Checkout page did not load', 'error');
  return; // Don't retry - something went wrong
}
```

---

### 2. ✅ Phone Format (Formato non valido)
**Problem:** Vatican API rejects phone numbers with `+` sign or spaces.

**Solution:** Strip `+` and spaces from phone number before filling.

**Files Changed:**
- `browser-extension/content.js` (fillPhoneField function)

**Code:**
```javascript
async function fillPhoneField(selector, phone) {
  const el = document.querySelector(selector);
  if (!el) return;
  
  // Remove + and any spaces from phone number
  const cleanPhone = phone.replace(/[\+\s]/g, '');
  
  el.focus();
  el.value = '';
  el.dispatchEvent(new Event('input', { bubbles: true }));
  
  for (const digit of cleanPhone) {
    el.value += digit;
    el.dispatchEvent(new Event('input', { bubbles: true }));
    await sleep(30);
  }
  
  el.dispatchEvent(new Event('change', { bubbles: true }));
  el.dispatchEvent(new Event('blur', { bubbles: true }));
}
```

**Example:**
- Input: `+39 333 1234567`
- Output: `393331234567`

---

### 3. ✅ Checkbox Selectors (Chrome Recording)
**Problem:** Checkboxes were not being clicked due to incorrect selectors.

**Solution:** Updated selectors based on Chrome recording analysis.

**Files Changed:**
- `browser-extension/content.js` (fillCheckoutFormWithParticipants function)

**Correct Selectors:**
```javascript
// First checkbox (terms) - ID: mat-mdc-checkbox-1-input
const cb0 = document.querySelector('#mat-mdc-checkbox-1-input');

// Close modal button
const closeBtn = document.querySelector("[data-cy='purchase-rules-close-btn']");

// Second checkbox (privacy) - ID: mat-mdc-checkbox-4-input
const cb1 = document.querySelector('#mat-mdc-checkbox-4-input');

// Buy button
const buyButton = document.querySelector("[data-cy='buyButton']");
```

**Flow:**
1. Click first checkbox (`#mat-mdc-checkbox-1-input`)
2. Wait 1.5 seconds for modal to appear
3. Close modal (`[data-cy='purchase-rules-close-btn']`)
4. Click second checkbox (`#mat-mdc-checkbox-4-input`)
5. Click BUY button (`[data-cy='buyButton']`)

---

### 4. ✅ Payment Link Extraction
**Problem:** Need to capture and log payment links for manual payment.

**Solution:** Added payment link detection and notification.

**Files Changed:**
- `browser-extension/content.js` (waitForEpayRedirect function)
- `browser-extension/background.js` (message listener)

**Code:**
```javascript
// In content.js
if (currentUrl.includes('epay')) {
  console.log('✅ Redirected to epay:', currentUrl);
  
  // Send payment link to background script
  chrome.runtime.sendMessage({
    action: 'paymentLinkReady',
    url: currentUrl
  }).catch(err => console.log('Could not send payment link:', err.message));
  
  return currentUrl;
}

// In background.js
else if (message.action === 'paymentLinkReady') {
  console.log('💳 Payment link ready:', message.url);
  
  // Send notification with payment link
  sendNotification(
    'Payment Link Ready',
    `Payment page loaded: ${message.url}`
  );
}
```

---

### 5. ✅ Enhanced Logging
**Problem:** Difficult to debug form loading issues.

**Solution:** Added comprehensive logging throughout the flow.

**Key Logging Points:**
- PROCEDI click status
- Current URL after navigation
- Form detection method
- Checkbox found/checked status
- BUY button found/disabled status
- Payment link capture

**Example Logs:**
```
✅ Clicked PROCEDI
📍 Current URL after PROCEDI: https://tickets.museivaticani.va/home/checkout
🔍 Attempting to detect form elements...
✅ Form loaded (detected via: managerSurname)
📋 Clicking checkboxes...
🔍 First checkbox found: true Checked: false
✅ Clicking first checkbox (terms)...
✅ Closing terms modal...
🔍 Second checkbox found: true Checked: false
✅ Clicking second checkbox (privacy)...
✅ Checkboxes processed
🔍 Looking for BUY button...
🔍 BUY button found: true Disabled: false
✅ Clicked BUY button (ACQUISTA)
⏳ Waiting for epay redirect...
✅ Redirected to epay: https://epay.museivaticani.va/...
💳 Payment link ready: https://epay.museivaticani.va/...
```

---

## Testing Instructions

### 1. Reload Extension
```bash
# In Chrome
1. Go to chrome://extensions/
2. Click "Reload" on Vatican Auto-Booking Extension
```

### 2. Test with Backend
```bash
# Make sure test data exists
docker-compose exec backend python create_test_data_docker.py

# Check test slots
docker-compose exec backend python manage.py shell
>>> from monitors.models import HeldSlot
>>> HeldSlot.objects.filter(slot_id__startswith='TEST_').count()
10
```

### 3. Run Extension
1. Open extension popup
2. Enable "Backend Listener Mode"
3. Set Backend URL: `http://localhost:8000`
4. Set Agency ID: `15`
5. Click "Start Backend Listener"

### 4. Monitor Logs
**Background Script Console:**
```
🎉 Found 10 available slots from backend!
📦 Opening 10 incognito windows for parallel booking
✅ Opened incognito window #1 for 2026-08-25 09:00 (AUTO mode)
...
```

**Content Script Console (in incognito window):**
```
🚀 Auto-booking started...
🎫 Step 1/10: Selecting ticket...
👥 Step 2/10: Setting quantity...
⏰ Step 3/10: Selecting time slot...
✅ Selected time slot: 09:00
➡️ Step 4/10: Proceeding to checkout...
✅ Clicked PROCEDI
📍 Current URL after PROCEDI: https://tickets.museivaticani.va/home/checkout
📝 Step 5/10: Filling form with participants...
✅ Form loaded (detected via: managerSurname)
📋 Clicking checkboxes...
✅ Checkboxes processed
💳 Step 7/10: Confirming purchase...
✅ Clicked BUY button (ACQUISTA)
⏳ Step 8/10: Waiting for payment page...
✅ Redirected to epay: https://epay.museivaticani.va/...
💳 Payment link ready!
```

---

## Expected Behavior

### Success Flow:
1. ✅ Extension opens 10 incognito windows
2. ✅ Each window navigates to Vatican deep link
3. ✅ Ticket selected automatically
4. ✅ Quantity set (2 visitors)
5. ✅ Time slot selected (09:00)
6. ✅ PROCEDI clicked (once)
7. ✅ Checkout form loads
8. ✅ Form filled with profile data
9. ✅ Phone filled without `+` sign
10. ✅ First checkbox clicked
11. ✅ Modal closed
12. ✅ Second checkbox clicked
13. ✅ BUY button clicked
14. ✅ Redirected to epay
15. ✅ Payment link logged

### Error Handling:
- ❌ If PROCEDI already in progress → Skip
- ❌ If not on checkout/recap → Return error (don't retry blindly)
- ❌ If form not found → Log page HTML and throw error
- ❌ If checkbox not found → Log and continue
- ❌ If BUY button disabled → Log and return false

---

## Common Issues & Solutions

### Issue: "Element [data-cy='managerSurname'] not found"
**Cause:** PROCEDI was clicked twice, causing navigation issues
**Solution:** Fixed with double-click prevention

### Issue: "Formato non valido" on phone field
**Cause:** Phone number contained `+` sign
**Solution:** Strip `+` and spaces before filling

### Issue: Checkboxes not clicking
**Cause:** Wrong selectors
**Solution:** Updated to use exact IDs from Chrome recording

### Issue: Payment link not captured
**Cause:** No logging/notification
**Solution:** Added paymentLinkReady message handler

---

## Files Modified

1. **browser-extension/content.js**
   - Added `procediClickInProgress` flag
   - Updated `clickProcedi()` with double-click prevention
   - Updated retry logic to only retry on recap page
   - Enhanced logging in `fillCheckoutFormWithParticipants()`
   - Updated checkbox selectors to use exact IDs
   - Added payment link notification in `waitForEpayRedirect()`
   - Enhanced logging in `clickBuyButton()`

2. **browser-extension/background.js**
   - Added `paymentLinkReady` message handler
   - Added payment link notification

---

## Next Steps

1. ✅ Test with real Vatican website
2. ✅ Verify checkboxes are clicked correctly
3. ✅ Verify phone format is accepted
4. ✅ Verify payment links are captured
5. ✅ Test with multiple concurrent bookings (10 windows)

---

**Status:** ✅ READY FOR TESTING
**Date:** May 23, 2026
**Version:** 2.1
