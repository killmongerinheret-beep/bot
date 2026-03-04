# Monday Issue Analysis - March 23, 2026

**Date:** March 4, 2026  
**Critical Finding:** March 23, 2026 is a MONDAY

---

## User Report

"check this 23 march and i suspect all dates on monday give a strange errors"

---

## Evidence

### March 23 HTML (User Provided)
```html
<div _ngcontent-ng-c2204097420="" id="ticket_1371996992">
  <span _ngcontent-ng-c2204097420="" class="muvaTicketTitle">
    Musei Vaticani - Biglietti d'ingresso
  </span>
</div>
```

✅ Ticket ID: `1371996992`  
✅ Ticket Name: "Musei Vaticani - Biglietti d'ingresso"  
✅ Ticket EXISTS on Vatican website

### Bot Extraction Results
```
Found 20 ticket types:
   • ID: 578732396 - Specola Vaticana - Visita Guidata Gruppi
   • ID: dx_0 - Unknown
   • ID: 1311288547 - Palazzo Papale - Cupole Astronomiche
   • ID: dx_1 - Unknown
   • ID: 123818166 - Palazzo Papale - Biglietti d'ingresso
   • ID: dx_2 - Unknown
   ...
   ❌ "Musei Vaticani" NOT in list
```

---

## Root Cause

### Issue 1: Ticket ID Not Extracted
- Bot finds 20 IDs but half are "Unknown"
- ID `1371996992` (Musei Vaticani) is NOT in the extracted list
- Bot only finds: Specola, Palazzo Papale, Borgo Laudato si'

### Issue 2: Monday-Specific Behavior
- March 23, 2026 = Monday
- Vatican may use different HTML structure on Mondays
- Possible reasons:
  1. Musei Vaticani closed on Mondays (but HTML shows it exists!)
  2. Different Angular rendering on Mondays
  3. Ticket hidden/collapsed by default on Mondays
  4. Different page load timing on Mondays

---

## Hypothesis

Vatican website has Monday-specific behavior where:
1. Musei Vaticani ticket EXISTS (as shown in HTML)
2. But it's hidden/collapsed/rendered differently
3. Bot's extraction logic misses it

---

## Solution Needed

### Fix 1: Improve HTML Extraction
- Wait longer for Angular to fully render
- Expand ALL collapsed sections
- Check for hidden elements (`display: none`, `.d-none`, `.hidden`)
- Search in shadow DOM if Vatican uses it

### Fix 2: Monday-Specific Logic
- Detect if date is Monday
- Use different extraction strategy for Mondays
- Add extra wait time for Monday pages
- Force-expand all accordion/collapse elements

### Fix 3: Fallback to Direct HTML Parsing
- If JavaScript extraction fails
- Parse raw HTML for `id="ticket_XXXXX"` patterns
- Extract title from `<span class="muvaTicketTitle">`

---

## Testing Plan

1. Check all Monday dates in March/April 2026
2. Compare extraction results vs actual HTML
3. Verify if Musei Vaticani is consistently missing on Mondays
4. Test with longer wait times
5. Test with forced expansion of all elements

---

## Immediate Action

Need to:
1. Fix extraction logic to find `ticket_1371996992`
2. Test on other Monday dates
3. Verify if this is Monday-specific or random

---

**Status:** CRITICAL - Bot missing valid tickets on Mondays
