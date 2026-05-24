# 🔍 Debug Time Selection Issue

## Issue: Extension finds time slots but doesn't click them

The extension says "time slot found" but doesn't actually click and proceed. This usually means:

1. The time slot element is found but not clickable
2. The time format doesn't match exactly
3. The element is in a dropdown that needs to be opened first
4. The click event isn't triggering properly

---

## 🧪 Debug Steps

### Step 1: Open Console in One of the Windows

1. One of the incognito windows should be open on Vatican website
2. Press **F12** to open console
3. Look for these messages:
   ```
   Found X time slots
   Available times: ["09:00", "10:00", "11:00", ...]
   ```

### Step 2: Check What Time Slots Look Like

Run this in the console:

```javascript
// Check if time elements exist
const timeSlots = document.querySelectorAll("[data-cy='time']");
console.log('Number of time slots:', timeSlots.length);

// Check their structure
timeSlots.forEach((slot, i) => {
  console.log(`Slot ${i}:`, {
    text: slot.textContent.trim(),
    tag: slot.tagName,
    classes: slot.className,
    disabled: slot.disabled || slot.classList.contains('disabled'),
    visible: slot.offsetParent !== null,
    clickable: window.getComputedStyle(slot).pointerEvents !== 'none'
  });
});
```

### Step 3: Check Time Format Match

```javascript
// What time are we looking for?
const preferredTime = "10:00";  // Replace with your actual time

// Check if any slot matches
const timeSlots = document.querySelectorAll("[data-cy='time']");
const matches = Array.from(timeSlots).filter(slot => {
  const text = slot.textContent.trim();
  return text === preferredTime || text.includes(preferredTime);
});

console.log(`Looking for: "${preferredTime}"`);
console.log(`Matches found: ${matches.length}`);
matches.forEach(m => console.log('  -', m.textContent.trim()));
```

### Step 4: Check if Dropdown Needs to be Opened

```javascript
// Check if there's a dropdown/select element
const dropdown = document.querySelector('select[data-cy*="time"]') ||
                document.querySelector('.time-selector') ||
                document.querySelector('[class*="dropdown"]');

console.log('Dropdown element:', dropdown);

// Check if time slots are hidden
const timeSlots = document.querySelectorAll("[data-cy='time']");
const hiddenSlots = Array.from(timeSlots).filter(s => s.offsetParent === null);
console.log(`Hidden slots: ${hiddenSlots.length} / ${timeSlots.length}`);
```

### Step 5: Try Manual Click

```javascript
// Try to click the first available time slot manually
const timeSlots = document.querySelectorAll("[data-cy='time']");
const firstSlot = Array.from(timeSlots).find(s => 
  !s.classList.contains('disabled') && 
  s.offsetParent !== null
);

if (firstSlot) {
  console.log('Trying to click:', firstSlot.textContent.trim());
  firstSlot.scrollIntoView({ behavior: 'smooth', block: 'center' });
  setTimeout(() => {
    firstSlot.click();
    console.log('Clicked!');
  }, 1000);
} else {
  console.log('No clickable slot found');
}
```

---

## 🔧 Common Issues & Fixes

### Issue 1: Time Slots in Dropdown

**Symptom:** Time slots exist but are hidden (offsetParent === null)

**Fix:** Need to open dropdown first

```javascript
// Add this before selecting time slot
async function openTimeDropdown() {
  const dropdown = document.querySelector('[data-cy*="time-dropdown"]') ||
                  document.querySelector('.time-selector') ||
                  document.querySelector('button[aria-label*="time"]');
  
  if (dropdown) {
    dropdown.click();
    await sleep(1000);  // Wait for dropdown to open
  }
}
```

### Issue 2: Time Format Mismatch

**Symptom:** Console shows different time format than expected

**Example:**
- Looking for: `"10:00"`
- Available: `"10:00 AM"` or `"10.00"` or `"10h00"`

**Fix:** Update matching logic to handle different formats

```javascript
// More flexible matching
const timeMatches = (slotText, preferredTime) => {
  const normalized = slotText.replace(/[^\d:]/g, '');  // Remove non-digits/colons
  return normalized.includes(preferredTime.replace(/[^\d:]/g, ''));
};
```

### Issue 3: Click Not Triggering

**Symptom:** Click happens but nothing changes

**Fix:** Try different click methods

```javascript
// Method 1: Direct click
slot.click();

// Method 2: Mouse event
slot.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));

// Method 3: Focus + Enter
slot.focus();
slot.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
```

### Issue 4: Element Not Visible

**Symptom:** Element exists but offsetParent is null

**Fix:** Scroll into view and wait

```javascript
slot.scrollIntoView({ behavior: 'smooth', block: 'center' });
await sleep(1000);  // Wait for scroll
slot.click();
```

---

## 📝 What to Share

Please run the debug scripts above and share:

1. **Number of time slots found:**
   ```
   Number of time slots: X
   ```

2. **Structure of one slot:**
   ```javascript
   {
     text: "10:00",
     tag: "BUTTON",
     classes: "...",
     disabled: false,
     visible: true,
     clickable: true
   }
   ```

3. **Available times:**
   ```
   Available times: ["09:00", "10:00", "11:00", ...]
   ```

4. **What time you're looking for:**
   ```
   preferredTime: "10:00"
   ```

5. **Any console errors or warnings**

---

## 🔄 Temporary Workaround

If you want to test the rest of the flow, you can manually click a time slot and see if the extension continues. The extension should proceed to the next step after you click.

---

## 🚀 Quick Fixes to Try

### Fix 1: Add Dropdown Opening

If time slots are in a dropdown, add this to `content.js` before line 597:

```javascript
// Try to open dropdown if it exists
const dropdownButton = document.querySelector('[data-cy*="time"]')?.closest('button') ||
                      document.querySelector('button[aria-haspopup="listbox"]');
if (dropdownButton && dropdownButton.getAttribute('aria-expanded') === 'false') {
  dropdownButton.click();
  await sleep(1000);
}
```

### Fix 2: Use More Aggressive Click

Replace line 632 (`slot.click();`) with:

```javascript
// Try multiple click methods
slot.scrollIntoView({ behavior: 'smooth', block: 'center' });
await sleep(500);
slot.focus();
await sleep(200);
slot.click();
slot.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
```

### Fix 3: Add More Logging

Add this after line 619 to see what's happening:

```javascript
console.log(`Checking slot: "${text}"`);
console.log(`  Preferred: "${preferredTime}"`);
console.log(`  Match: ${text === preferredTime || text.includes(preferredTime)}`);
console.log(`  Disabled: ${isDisabled}`);
console.log(`  Visible: ${slot.offsetParent !== null}`);
```

---

**Next Step:** Run the debug scripts and share the output so we can see exactly what's on the page!
