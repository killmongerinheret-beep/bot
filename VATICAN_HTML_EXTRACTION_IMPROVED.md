# Vatican HTML Extraction - Improved to Check Hidden Elements

## Problem

The bot was only extracting tickets from visible HTML elements. If Vatican website had tickets hidden in collapsed sections, accordions, or display:none elements, the bot would miss them.

## Solution Applied

Enhanced the HTML extraction logic to:
1. **Expand collapsed sections** before extracting
2. **Check hidden elements** (display:none, .d-none, .hidden)
3. **Search multiple title selectors** (not just .muvaTicketTitle)
4. **Extract ALL tickets** from the page (let matching logic filter later)

## Code Changes

### File: `worker_vatican/hydra_monitor.py`

### Change 1: Expand Collapsed Sections

**Added before extraction:**
```python
# Try to expand any collapsed sections
try:
    await page.evaluate('''() => {
        const expandButtons = document.querySelectorAll('[data-toggle="collapse"], .accordion-button, .btn-collapse, [aria-expanded="false"]');
        expandButtons.forEach(btn => {
            try {
                btn.click();
            } catch(e) {}
        });
    }''')
    # Wait for expansions to complete
    await page.wait_for_timeout(2000)
    logger.info("✅ Expanded collapsed sections")
except:
    pass
```

**What it does:**
- Finds all collapse/accordion buttons
- Clicks them to expand hidden sections
- Waits 2 seconds for DOM to update
- Reveals tickets that were hidden in collapsed sections

### Change 2: Enhanced Extraction Logic

**New 4-step extraction process:**

**STEP 1: Expand Collapsed Sections**
```javascript
const expandButtons = document.querySelectorAll('[data-toggle="collapse"], .accordion-button, .btn-collapse, [aria-expanded="false"]');
expandButtons.forEach(btn => {
    try {
        btn.click();
    } catch(e) {}
});
```

**STEP 2: Extract from Visible Containers**
```javascript
const ticketContainers = document.querySelectorAll('div[id^="ticket_"]');
ticketContainers.forEach(container => {
    const ticketId = containerId.replace('ticket_', '');
    
    // Check multiple title selectors
    let titleEl = container.querySelector('.muvaTicketTitle');
    if (!titleEl) titleEl = container.querySelector('h1, h2, h3, h4, .card-title, .ticket-title');
    
    const ticketName = titleEl ? titleEl.textContent.trim() : 'Unknown';
    
    results.push({ id: ticketId, name: ticketName });
});
```

**STEP 3: Fallback to data-cy Buttons**
```javascript
if (results.length === 0) {
    const buttons = document.querySelectorAll('[data-cy^="bookTicket_"]');
    // ... extract from buttons
}
```

**STEP 4: Check Hidden Elements**
```javascript
const hiddenContainers = document.querySelectorAll('div[id^="ticket_"][style*="display: none"], div[id^="ticket_"].d-none, div[id^="ticket_"].hidden');
hiddenContainers.forEach(container => {
    // Extract from hidden elements
    if (!results.find(r => r.id === ticketId)) {
        results.push({ id: ticketId, name: ticketName });
    }
});
```

## Key Improvements

### 1. Multiple Title Selectors
**Before:** Only checked `.muvaTicketTitle`
**After:** Checks `.muvaTicketTitle, h1, h2, h3, h4, .card-title, .ticket-title`

**Why:** Vatican might use different CSS classes for titles

### 2. Expand Collapsed Sections
**Before:** Only extracted visible elements
**After:** Clicks expand buttons first, then extracts

**Why:** Tickets might be hidden in collapsed accordions

### 3. Check Hidden Elements
**Before:** Ignored `display:none` elements
**After:** Explicitly searches for hidden elements

**Selectors checked:**
- `div[id^="ticket_"][style*="display: none"]` - Inline style hidden
- `div[id^="ticket_"].d-none` - Bootstrap hidden class
- `div[id^="ticket_"].hidden` - Generic hidden class

### 4. No Filtering During Extraction
**Before:** Filtered tickets during extraction (only Vatican Museums)
**After:** Extracts ALL tickets, lets matching logic filter

**Why:** More flexible, allows proper matching logic to decide

## How It Works Now

### Extraction Flow

1. **Page loads** → Wait for ticket elements (25s timeout)
2. **Wait 3 seconds** → Let Angular finish rendering
3. **Click expand buttons** → Reveal collapsed sections
4. **Wait 2 seconds** → Let expansions complete
5. **Extract visible tickets** → From div[id^="ticket_"]
6. **Extract from buttons** → Fallback if no containers
7. **Extract hidden tickets** → From display:none elements
8. **Deduplicate** → Remove duplicate IDs
9. **Log all tickets** → Show what was found
10. **Cache with JSESSIONID** → Store for reuse

### Example Log Output

```
✅ Ticket elements detected
✅ Expanded collapsed sections
✅ Found 5 ticket titles
🔢 Resolved 5 Dynamic IDs from Page
   • ID: 123456789 | Name: Musei Vaticani - Biglietti d'ingresso
   • ID: 987654321 | Name: Palazzo Papale - Biglietti d'ingresso
   • ID: 456789123 | Name: Specola Vaticana - Visita Guidata
   • ID: 789123456 | Name: Musei Vaticani - Visite Guidate
   • ID: 321654987 | Name: Palazzo Papale - Visita Guidata
```

## Benefits

✅ **Finds hidden tickets** - No longer misses tickets in collapsed sections
✅ **More robust** - Checks multiple selectors and locations
✅ **Better coverage** - Extracts ALL tickets from page
✅ **Proper matching** - Lets matching logic decide which ticket to use
✅ **Handles dynamic HTML** - Works with Angular/React dynamic rendering

## Testing

### Test Hidden Ticket Extraction

1. **Check worker logs** for "Expanded collapsed sections":
   ```bash
   docker-compose logs worker_vatican | grep "Expanded collapsed"
   ```

2. **Verify ticket count** increased:
   ```bash
   docker-compose logs worker_vatican | grep "Resolved.*Dynamic IDs"
   ```

3. **Check if Musei Vaticani found** on March 16:
   ```bash
   docker-compose logs worker_vatican | grep "2026-03-16" | grep "Musei Vaticani"
   ```

### Expected Behavior

**Before:** March 16 might show only 2-3 tickets (Palazzo, Specola)
**After:** March 16 should show ALL tickets including hidden Musei Vaticani (if present)

## Why This Matters

Vatican website structure:
- Some dates show all tickets expanded
- Some dates hide certain tickets in collapsed sections
- Some dates use different HTML structure
- Tickets might be in tabs, accordions, or hidden divs

**This update ensures the bot finds ALL tickets regardless of how Vatican structures the HTML.**

## Status

✅ Collapse/accordion expansion added
✅ Hidden element extraction added
✅ Multiple title selectors added
✅ No filtering during extraction (moved to matching)
✅ Worker restarted with new code

The bot now thoroughly searches the entire HTML including hidden sections to find all available tickets!
