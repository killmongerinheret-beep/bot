# Vatican API visitLang Parameter - CORRECTION

**Date:** February 28, 2026  
**Status:** ✅ STEERING FILE CORRECTED

---

## 🎯 What Was Wrong

I initially documented that standard tickets should **omit** the `visitLang` parameter entirely. This was INCORRECT.

### ❌ Previous (Wrong) Documentation
```
# Standard ticket - NO visitLang parameter:
https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitTypeId=2129030053&visitorNum=2&visitDate=28/03/2026
```

---

## ✅ What Is Correct

Based on the actual working implementation and your confirmation, standard tickets **MUST include** `visitLang` with an **empty value**.

### ✅ Correct Implementation
```
# Standard ticket - visitLang with EMPTY value:
https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitLang=&visitTypeId=2085325042&visitorNum=1&visitDate=28/03/2026
                                                              ^^^ Empty value - This is CORRECT!

# Guided tour - visitLang with language code:
https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitLang=ENG&visitTypeId=1594188966&visitorNum=1&visitDate=28/03/2026
                                                              ^^^ Language code - This is CORRECT!
```

---

## 📊 Evidence from Working Code

### hydra_monitor.py (Line 1053-1056)
```python
# Build API URL with visitLang parameter for guided tours
visit_lang_param = language if language else ""

# Call API using page.evaluate to leverage browser's session and cookies
api_result = await page.evaluate(f'''async () => {{
    const url = '/api/visit/timeavail?lang=it&visitLang={visit_lang_param}&visitTypeId={ticket_id}&visitorNum={visitors}&visitDate=' + encodeURIComponent('{api_date}');
```

**Key Points:**
1. `visit_lang_param = language if language else ""` - Uses empty string for standard tickets
2. URL always includes `&visitLang={visit_lang_param}` - Parameter is ALWAYS present
3. For standard tickets: `language` is `None`, so `visit_lang_param` becomes `""`
4. Result: `...&visitLang=&visitTypeId=...`

### Logs Confirm It Works
```
[2026-02-28 14:26:34,574: INFO] ✅ API Response: 200 - 20 total slots
[2026-02-28 14:26:44,791: INFO] ✅ API Response: 200 - 20 total slots
[2026-02-28 14:26:53,585: INFO] ✅ API Response: 200 - 20 total slots
```

All these successful API calls are using `visitLang=` with empty value for standard tickets.

---

## 🔧 Correct Implementation Pattern

### Python Code
```python
# ✅ CORRECT - Always include visitLang
visit_lang = language if language else ""  # Empty string for standard, code for guided

url = (
    f"https://tickets.museivaticani.va/api/visit/timeavail"
    f"?lang=it&visitLang={visit_lang}&visitTypeId={ticket_id}&visitorNum={visitors}&visitDate={date}"
)

# Examples:
# Standard ticket (language=None): ...&visitLang=&visitTypeId=...
# Guided tour (language="ENG"): ...&visitLang=ENG&visitTypeId=...
```

### JavaScript Code (in browser)
```javascript
const visitLang = language || "";  // Empty string if no language
const url = `/api/visit/timeavail?lang=it&visitLang=${visitLang}&visitTypeId=${ticketId}&visitorNum=${visitors}&visitDate=${date}`;
```

---

## 📋 Updated Rules

### For Standard Tickets (ticket_type == 0)
- ✅ **ALWAYS include** `&visitLang=` parameter
- ✅ Value should be **empty string** `""`
- ✅ Results in URL: `...&visitLang=&visitTypeId=...`
- ❌ Do NOT omit the parameter entirely

### For Guided Tours (ticket_type == 1)
- ✅ **ALWAYS include** `&visitLang=` parameter
- ✅ Value should be **language code** (ENG, ITA, FRA, DEU, SPA)
- ✅ Results in URL: `...&visitLang=ENG&visitTypeId=...`
- ❌ Do NOT use empty value

---

## 🎯 Why This Matters

The Vatican API expects the `visitLang` parameter to be present in the URL:

1. **Standard tickets:** Empty value signals "no specific language required"
2. **Guided tours:** Language code signals "check this specific language tour"
3. **Missing parameter:** May cause API to behave unexpectedly or return errors

---

## ✅ Steering File Updated

The `.kiro/steering/VATICAN_BOT_RULES.md` file has been corrected to reflect the actual working implementation:

### Changes Made:
1. ✅ Updated STEP 3 to show `visitLang` always included
2. ✅ Corrected examples to show empty value for standard tickets
3. ✅ Updated implementation patterns
4. ✅ Fixed "wrong" examples section
5. ✅ Updated checklist items

---

## 🔍 How to Verify

### Check Current Code
```bash
# Search for visitLang usage
grep -r "visitLang" worker_vatican/

# Should find patterns like:
# visit_lang_param = language if language else ""
# &visitLang={visit_lang_param}&
```

### Check Logs
```bash
# Look for successful API calls
docker-compose logs worker_vatican | grep "API Response: 200"

# All successful calls use visitLang= with empty value for standard tickets
```

### Test API Call
```python
# Standard ticket (with empty visitLang)
url = "https://tickets.museivaticani.va/api/visit/timeavail?lang=it&visitLang=&visitTypeId=2085325042&visitorNum=1&visitDate=28/03/2026"

# This format works and returns 200 with valid JSESSIONID
```

---

## 📚 Summary

**What Changed:**
- ❌ OLD: "Standard tickets should omit visitLang parameter"
- ✅ NEW: "Standard tickets should include visitLang with empty value"

**Why:**
- The actual working code uses `visitLang=` with empty value
- Logs confirm this format returns successful 200 responses
- Vatican API expects the parameter to be present

**Action:**
- Steering file has been corrected
- Future AI interactions will use the correct format
- No code changes needed (code was already correct!)

---

**Thank you for the correction!** The steering file now accurately reflects the working implementation.
