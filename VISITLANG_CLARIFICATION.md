# visitLang Parameter - Clarification

## ✅ Correct Implementation

### For Standard Tickets (ticket_type == 0)
**DO NOT include visitLang parameter at all:**

```python
# ✅ CORRECT
url = f"https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitTypeId={id}&visitorNum={v}&visitDate={date}"

# Result URL:
# https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitTypeId=2129030053&visitorNum=2&visitDate=28/03/2026
```

### For Guided Tours (ticket_type == 1)
**Include visitLang with actual language value:**

```python
# ✅ CORRECT
url = f"https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitLang={language}&visitTypeId={id}&visitorNum={v}&visitDate={date}"

# Result URL (language = "ENG"):
# https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitLang=ENG&visitTypeId=1594188966&visitorNum=1&visitDate=28/03/2026
```

---

## ❌ Wrong Implementation

### Empty visitLang Parameter
```python
# ❌ WRONG - Has visitLang with empty value
url = f"https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitLang=&visitTypeId={id}&visitorNum={v}&visitDate={date}"

# Result URL:
# https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitLang=&visitTypeId=2085325042&visitorNum=1&visitDate=28/03/2026
#                                                              ^^^ EMPTY - This is wrong!
```

**Problem:** Vatican API may interpret empty `visitLang=` as invalid parameter.

---

## 🔍 Where Empty visitLang Comes From

### Scenario 1: Empty String Instead of None
```python
# ❌ WRONG
language = ""  # Empty string
visit_lang_param = f"&visitLang={language}"  # Results in "&visitLang="

# ✅ CORRECT
language = None  # or not set
visit_lang_param = f"&visitLang={language}" if language else ""  # Results in ""
```

### Scenario 2: Not Checking Ticket Type
```python
# ❌ WRONG - Always includes visitLang
visit_lang_param = f"&visitLang={language or ''}"  # If language is None, becomes "&visitLang="

# ✅ CORRECT - Only for guided tours
if ticket_type == 1 and language:
    visit_lang_param = f"&visitLang={language}"
else:
    visit_lang_param = ""
```

### Scenario 3: Database Has Empty String
```python
# ❌ WRONG - Database stores empty string
task.language = ""  # Empty string in database

# When building URL:
visit_lang_param = f"&visitLang={task.language}"  # Results in "&visitLang="

# ✅ CORRECT - Check for empty
if ticket_type == 1 and task.language:  # Checks both None and empty string
    visit_lang_param = f"&visitLang={task.language}"
else:
    visit_lang_param = ""
```

---

## 🔧 Fix Implementation

### Current Code (god_tier_monitor.py line 434)
```python
# ✅ CORRECT - Already implemented correctly
visit_lang_param = f"&visitLang={lang_code}" if is_guided else ""
```

This is correct because:
1. Only adds parameter if `is_guided` is True
2. `lang_code` is guaranteed to have a value when `is_guided` is True
3. Returns empty string for standard tickets

### Current Code (hydra_monitor.py line 316)
```python
# ✅ CORRECT - Already implemented correctly
lang_param = f"&visitLang={lang_code}" if lang_code else ""
```

This is correct because:
1. Only adds parameter if `lang_code` is truthy (not None, not empty)
2. Returns empty string otherwise

---

## 🎯 Best Practice Pattern

```python
def build_api_url(ticket_type, ticket_id, visitors, date, language=None):
    """
    Build Vatican API URL with correct visitLang handling.
    
    Args:
        ticket_type: 0 for standard, 1 for guided
        ticket_id: Fresh ticket ID from dynamic resolution
        visitors: Number of visitors
        date: Date in DD/MM/YYYY format
        language: Language code (ENG, ITA, etc.) - only for guided tours
    """
    base_url = "https://tickets.museivaticani.va/api/visit/timeavail"
    
    # Build parameters
    params = {
        "lang": "it",
        "visitTypeId": ticket_id,
        "visitorNum": visitors,
        "visitDate": date
    }
    
    # Add visitLang ONLY for guided tours with valid language
    if ticket_type == 1 and language:
        params["visitLang"] = language
    
    # Build URL
    param_str = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{base_url}?{param_str}"

# Examples:
# Standard ticket:
# build_api_url(0, "2129030053", 2, "28/03/2026")
# → https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitTypeId=2129030053&visitorNum=2&visitDate=28/03/2026

# Guided tour:
# build_api_url(1, "1594188966", 1, "28/03/2026", "ENG")
# → https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitTypeId=1594188966&visitorNum=1&visitDate=28/03/2026&visitLang=ENG
```

---

## 📊 Verification

### Check Current Implementation
```bash
# Search for visitLang usage
grep -r "visitLang" worker_vatican/ backend/

# Look for patterns that might create empty values
grep -r "visitLang=\${" worker_vatican/ backend/
grep -r "visitLang=.*or ''" worker_vatican/ backend/
```

### Test URLs
```python
# Test standard ticket URL
url = "https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitTypeId=2129030053&visitorNum=2&visitDate=28/03/2026"
assert "visitLang" not in url, "Standard ticket should not have visitLang"

# Test guided tour URL
url = "https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitLang=ENG&visitTypeId=1594188966&visitorNum=1&visitDate=28/03/2026"
assert "visitLang=ENG" in url, "Guided tour should have visitLang with value"
assert "visitLang=&" not in url, "Should not have empty visitLang"
```

---

## 🚨 If You See Empty visitLang

If you see URLs like:
```
https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitLang=&visitTypeId=...
```

**Check these locations:**

1. **Database:** Check if `task.language` is empty string instead of None
2. **Code:** Check if conditional logic is missing
3. **Logs:** Check where the URL is being constructed

**Quick Fix:**
```python
# Add this check before building URL
if language == "":
    language = None  # Convert empty string to None

# Or use this pattern
visit_lang_param = f"&visitLang={language}" if (ticket_type == 1 and language) else ""
```

---

**Updated:** February 28, 2026  
**Status:** Steering file updated with correct specification
