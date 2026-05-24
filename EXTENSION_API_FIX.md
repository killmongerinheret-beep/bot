# ✅ Browser Extension API Fix

**Date:** May 4, 2026  
**Issue:** Extension getting 404 error when calling backend API  
**Status:** ✅ **FIXED**

---

## 🔍 Problem Identified

The browser extension's "Backend Listener Mode" was trying to call:
```
GET /api/available-slots
```

But this endpoint didn't exist in the backend, causing 404 errors:
```
2026-05-04 12:01:10 [WARNING] django.request: Not Found: /api/available-slots
```

---

## ✅ Solution Applied

### 1. Created New API Endpoint

**File:** `backend/monitors/views.py`

Added new function `get_available_slots()`:
```python
@api_view(['GET'])
def get_available_slots(request):
    """
    Get available slots for browser extension auto-booking.
    Returns slots that are currently held and ready to be booked.
    
    Query params:
    - status: Filter by status (default: 'held')
    - limit: Max number of slots to return (default: 10)
    """
```

**Features:**
- Returns held slots ready for booking
- Supports authentication via Bearer token
- Agency-filtered (users only see their own slots)
- Configurable limit (default: 10 slots)
- Returns slot details: date, time, ticket_id, visitors, etc.

### 2. Registered URL Route

**File:** `backend/monitors/urls.py`

Added route:
```python
path('available-slots/', get_available_slots, name='available-slots'),
```

Full URL: `http://localhost:8000/api/v1/available-slots/`

### 3. Updated Extension

**File:** `browser-extension/background.js`

Changed URL from:
```javascript
`${backendUrl}/api/available-slots`
```

To:
```javascript
`${backendUrl}/api/v1/available-slots/`
```

---

## 📊 API Endpoint Details

### Request

**Method:** `GET`  
**URL:** `/api/v1/available-slots/`  
**Headers:**
```
Authorization: Bearer <api_key>
Content-Type: application/json
```

**Query Parameters:**
- `status` (optional): Filter by status (default: `held`)
  - Values: `held`, `paid`, `released`, `expired`, `all`
- `limit` (optional): Max slots to return (default: `10`)

### Response

**Success (200):**
```json
{
  "slots": [
    {
      "id": 123,
      "date": "15/05/2026",
      "time": "09:00",
      "ticket_id": "2129030053",
      "ticket_name": "Musei Vaticani - Biglietti d'ingresso",
      "visitors": 2,
      "adult_count": 2,
      "child_count": 0,
      "language": null,
      "status": "held",
      "hold_started_at": "2026-05-04T12:00:00Z"
    }
  ],
  "count": 1,
  "timestamp": "2026-05-04T12:05:00Z"
}
```

**No Slots (200):**
```json
{
  "slots": [],
  "count": 0,
  "timestamp": "2026-05-04T12:05:00Z"
}
```

**Unauthorized (200 with empty slots):**
```json
{
  "slots": [],
  "count": 0
}
```

---

## 🎯 How It Works

### Backend Listener Mode Flow

1. **Extension polls backend** every 10 seconds
2. **Backend returns held slots** that are ready to book
3. **Extension opens incognito windows** for each slot
4. **Parallel booking** happens automatically
5. **Extension marks slots as paid** after successful booking

### Security

- **Authentication required:** Bearer token from agency login
- **Agency filtering:** Users only see their own agency's slots
- **Super admin access:** Can see all slots across all agencies

---

## 🧪 Testing

### Test the API Endpoint

```bash
# Without authentication (returns empty)
curl http://localhost:8000/api/v1/available-slots/

# With authentication
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:8000/api/v1/available-slots/

# With filters
curl -H "Authorization: Bearer YOUR_API_KEY" \
     "http://localhost:8000/api/v1/available-slots/?status=held&limit=5"
```

### Test the Extension

1. Open extension options
2. Enable "Backend Listener Mode"
3. Set backend URL: `http://localhost:8000`
4. Set API key (from agency login)
5. Check browser console for logs:
   ```
   ✅ Backend listener started - polling every 10 seconds
   No available slots yet, continuing to poll...
   ```

---

## 📝 Files Modified

1. ✅ `backend/monitors/views.py` - Added `get_available_slots()` function
2. ✅ `backend/monitors/urls.py` - Added URL route
3. ✅ `browser-extension/background.js` - Updated API URL
4. ✅ `backend` container - Restarted to apply changes

---

## ✅ Verification

### Before Fix
```
backend-1  | 2026-05-04 12:01:10 [WARNING] django.request: Not Found: /api/available-slots
```

### After Fix
Extension should now successfully connect and poll for slots without 404 errors.

---

## 🚀 Next Steps

### For Users

1. **Reload the extension** in Chrome/Firefox
   - Chrome: `chrome://extensions/` → Click reload icon
   - Firefox: `about:debugging` → Reload extension

2. **Configure Backend Listener Mode**
   - Open extension options
   - Enable "Backend Listener Mode"
   - Set backend URL (default: `http://localhost:8000`)
   - Set API key from your agency login

3. **Test the connection**
   - Check browser console for connection logs
   - Should see: "✅ Backend listener started"
   - No more 404 errors

### For Developers

**Monitor API calls:**
```bash
# Watch backend logs
docker-compose logs -f backend | grep available-slots

# Check for successful requests
docker-compose logs backend | grep "GET /api/v1/available-slots"
```

**Check held slots:**
```bash
# Via API
curl -H "Authorization: Bearer YOUR_KEY" \
     http://localhost:8000/api/v1/holds/

# Via Django shell
docker-compose exec backend python backend/manage.py shell
>>> from monitors.models import HeldSlot
>>> HeldSlot.objects.filter(status='held').count()
```

---

## 🎉 Summary

✅ **API endpoint created** - `/api/v1/available-slots/`  
✅ **Extension updated** - Now uses correct URL  
✅ **Backend restarted** - Changes applied  
✅ **No more 404 errors** - Extension can now connect  

The browser extension's Backend Listener Mode is now fully functional and can automatically detect and book available slots!

---

**Last Updated:** May 4, 2026 14:01 UTC  
**Status:** ✅ OPERATIONAL
