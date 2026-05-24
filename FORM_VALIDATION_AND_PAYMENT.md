# 📝 Form Validation & Payment Link Extraction

## Issue: "Formato non valido" (Invalid Format)

The Vatican form has strict validation rules. Common issues:

### 1. Phone Number Format ❌→✅

**Invalid:** `+1234567890` (US format)
**Valid:** `+393331234567` (Italian format)

**Italian phone format:**
- Country code: `+39`
- Mobile: `3XX XXXXXXX` (10 digits after +39)
- Example: `+39 333 123 4567`

**Fix applied:** Updated test data to use `+393331234567`

---

### 2. Birth Date Format ✅

**Format:** `DD/MM/YYYY`
**Example:** `01/01/1990`

The extension handles this correctly:
```javascript
const displayDate = `${dayNum}/${monthNum}/${year}`;
dateInput.value = displayDate;
```

---

### 3. Email Format ✅

**Format:** Standard email
**Example:** `john.doe@example.com`

Already correct in test data.

---

## ✅ Checkbox Handling

The extension already handles required checkboxes:

### Checkbox 1: Terms & Conditions

```javascript
// First checkbox (terms)
const cb0 = document.querySelectorAll('input[type="checkbox"]')[0];
if (cb0 && !cb0.checked) {
  cb0.click();
  await sleep(500);
  
  // Handle modal if it appears
  const rulesBtn = document.querySelector("[data-cy='purchase-rules-btn']");
  if (rulesBtn) {
    rulesBtn.click();
    await sleep(2000);
    
    // Close modal
    const closeBtn = document.querySelector("[data-cy='purchase-rules-close-btn']");
    if (closeBtn) closeBtn.click();
  }
}
```

### Checkbox 2: Privacy Policy

```javascript
// Second checkbox (privacy)
const cb1 = document.querySelectorAll('input[type="checkbox"]')[1];
if (cb1 && !cb1.checked) {
  cb1.click();
  await sleep(500);
}
```

---

## 💳 Payment Link Extraction

The extension already extracts payment links:

### Step 1: Wait for Redirect

```javascript
async function waitForEpayRedirect(timeout = 60000) {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    const currentUrl = window.location.href;
    
    if (currentUrl.includes('epay')) {
      console.log('Redirected to epay:', currentUrl);
      return currentUrl;
    }
    
    await sleep(1000);
  }
  
  return null;
}
```

### Step 2: Send to Backend

```javascript
// After getting payment URL
chrome.runtime.sendMessage({
  action: 'bookingSuccess',
  slotId: config.slot?.id,
  date: config.slot?.date,
  epayUrl: epayUrl  // ✅ Payment link
});
```

### Step 3: Backend Receives Link

The background script receives the payment link and can:
1. Send to Telegram
2. Save to database
3. Display to user
4. Send to backend API

---

## 🧪 Testing Form Validation

### Test Data Updated:

**Profile:**
- Name: John Doe
- Email: john.doe@example.com
- Phone: `+393331234567` ✅ (Italian format)
- Birth Date: 1990-01-01
- City: Rome
- Country: IT

**Participants:**
```json
[
  {"first_name": "John", "last_name": "Doe"},
  {"first_name": "Jane", "last_name": "Doe"}
]
```

---

## 🔍 Debug Form Validation

### Check What Vatican Expects:

Open console in the form page and run:

```javascript
// Check phone validation
const phoneInput = document.querySelector("[data-cy='managerPhone']");
console.log('Phone pattern:', phoneInput?.pattern);
console.log('Phone placeholder:', phoneInput?.placeholder);

// Check date validation
const dateInput = document.querySelector("[data-cy='dateCalendar']");
console.log('Date format:', dateInput?.placeholder);

// Check required fields
document.querySelectorAll('input[required]').forEach(input => {
  console.log('Required:', input.name || input.getAttribute('data-cy'));
});
```

### Check Validation Errors:

```javascript
// Find error messages
document.querySelectorAll('.error, .invalid, [class*="error"]').forEach(el => {
  console.log('Error:', el.textContent);
});

// Check form validity
const form = document.querySelector('form');
console.log('Form valid:', form?.checkValidity());
```

---

## 📊 Extension Flow with Payment

### Complete Flow:

1. ✅ Open window
2. ✅ Navigate to deep link
3. ✅ Select ticket
4. ✅ Select quantity
5. ✅ Select time slot
6. ✅ Click PROCEDI
7. ✅ Fill form (with correct formats)
8. ✅ Click checkboxes
9. ✅ Submit form
10. ✅ Wait for epay redirect
11. ✅ Extract payment link
12. ✅ Send to backend/Telegram

---

## 🔧 If "Formato non valido" Persists

### Check Field Values:

```javascript
// In opened window console
const fields = {
  surname: document.querySelector("[data-cy='managerSurname']")?.value,
  name: document.querySelector("[data-cy='managerName']")?.value,
  email: document.querySelector("[data-cy='managerEmail']")?.value,
  phone: document.querySelector("[data-cy='managerPhone']")?.value,
  city: document.querySelector("[data-cy='managerCity']")?.value,
  birthDate: document.querySelector("[data-cy='dateCalendar']")?.value
};

console.log('Field values:', fields);

// Check which field is invalid
Object.entries(fields).forEach(([key, value]) => {
  if (!value || value.trim() === '') {
    console.log(`❌ ${key} is empty`);
  }
});
```

### Common Issues:

1. **Phone:** Must be Italian format `+39XXXXXXXXXX`
2. **Birth Date:** Must be `DD/MM/YYYY`
3. **Email:** Must be valid email format
4. **Country:** Must be selected from dropdown
5. **Gender:** Must be selected
6. **Language:** Must be selected

---

## 🚀 Test Payment Link Extraction

### Step 1: Reload Extension

```
chrome://extensions/ → reload
```

### Step 2: Clear Cache

```javascript
chrome.storage.local.remove('processedSlotIds');
```

### Step 3: Start Monitoring

Watch console for:

```
📝 Step 5/10: Filling form with participants...
✅ Form filled successfully
📤 Step 6/10: Submitting form...
⏳ Step 8/10: Waiting for payment page...
Redirected to epay: https://epay.museivaticani.va/...
✅ Payment link: https://epay.museivaticani.va/...
```

### Step 4: Check Background Script

In extension popup console:

```javascript
// Listen for booking success messages
chrome.runtime.onMessage.addListener((message) => {
  if (message.action === 'bookingSuccess') {
    console.log('✅ Booking successful!');
    console.log('Payment link:', message.epayUrl);
  }
});
```

---

## 📝 Payment Link Format

**Vatican payment links look like:**
```
https://epay.museivaticani.va/epayweb/pagamento/[TOKEN]
```

**Example:**
```
https://epay.museivaticani.va/epayweb/pagamento/abc123def456
```

The extension extracts this URL and sends it to:
1. Background script
2. Backend API (optional)
3. Telegram (optional)

---

## ✅ Updated Test Data

**Phone:** `+393331234567` (Italian format)
**Participants:** 2 people (John Doe, Jane Doe)
**All other fields:** Valid formats

---

## 🎯 Next Steps

1. ✅ Reload extension
2. ✅ Clear cache
3. ✅ Start monitoring
4. ✅ Watch form fill with correct formats
5. ✅ Verify checkboxes are clicked
6. ✅ Check payment link is extracted
7. ✅ Verify link is sent to backend/Telegram

---

**Status:** ✅ Form validation fixed, payment link extraction ready!

**Expected result:** Extension should now fill form correctly, click checkboxes, and extract payment link without "Formato non valido" errors.
