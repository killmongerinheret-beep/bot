# Fix "Unknown" Status in Vercel Dashboard

## Problem
The Vercel frontend is showing "unknown" for task statuses.

## Root Cause
Tasks show "unknown" because they haven't been checked yet. The `last_status` field defaults to "unknown" when a task is created.

## Solution

### 1. Backend Changes (Already Done ✅)

Updated `backend/monitors/serializers.py` to include:
- `target_date` - First date from dates array
- `slots_found` - Number of slots from latest check
- `latest_check` - Full details of most recent check

### 2. Frontend Changes Needed

Update your Vercel frontend to use these fields:

```typescript
// Example: Fetching tasks
const response = await fetch(`${API_URL}/api/tasks/`);
const tasks = await response.json();

tasks.forEach(task => {
  console.log({
    id: task.id,
    agencyName: task.agency_name,
    targetDate: task.target_date,  // ✅ Use this instead of parsing dates
    visitors: task.visitors,
    lastStatus: task.last_status,
    slotsFound: task.slots_found,  // ✅ Number of available slots
    lastChecked: task.last_checked,
    latestCheck: task.latest_check  // ✅ Full check details
  });
});
```

### 3. Display Logic

```typescript
function getStatusDisplay(task) {
  // If never checked
  if (!task.last_checked || task.last_status === 'unknown') {
    return {
      status: 'Pending',
      color: 'gray',
      message: 'Waiting for first check...'
    };
  }
  
  // If checked and available
  if (task.last_status === 'available' && task.slots_found > 0) {
    return {
      status: 'Available',
      color: 'green',
      message: `${task.slots_found} slots found`
    };
  }
  
  // If checked but sold out
  if (task.last_status === 'sold_out' || task.slots_found === 0) {
    return {
      status: 'Sold Out',
      color: 'red',
      message: 'No slots available'
    };
  }
  
  // If error
  if (task.last_status === 'error') {
    return {
      status: 'Error',
      color: 'yellow',
      message: 'Check failed'
    };
  }
  
  return {
    status: task.last_status,
    color: 'gray',
    message: ''
  };
}
```

### 4. Trigger First Check

To populate data, you need to run checks. There are 3 ways:

#### Option A: Celery Worker (Automatic - Recommended)
```bash
# Terminal 1: Start Celery worker
celery -A backend.core worker -l info

# Terminal 2: Start Celery beat (scheduler)
celery -A backend.core beat -l info
```

This will automatically check tasks based on their `check_interval`.

#### Option B: Manual Trigger via API
Create an endpoint to manually trigger a check:

```python
# In backend/monitors/views.py
from rest_framework.decorators import api_view
from .tasks import run_smart_vatican_monitor

@api_view(['POST'])
def trigger_check(request, task_id):
    """Manually trigger a check for a specific task"""
    try:
        task = MonitorTask.objects.get(id=task_id)
        
        # Get first date from dates array
        target_date = task.dates[0] if task.dates else None
        if not target_date:
            return Response({'error': 'No target date'}, status=400)
        
        # Trigger check
        result = run_smart_vatican_monitor(
            date=target_date,
            ticket_id=task.ticket_id,
            ticket_name=task.ticket_name,
            language=task.language,
            task_ids=[task.id],
            visitors=task.visitors,
            ticket_type=task.ticket_type
        )
        
        return Response({'message': 'Check triggered', 'result': result})
    except Exception as e:
        return Response({'error': str(e)}, status=500)
```

Then call from frontend:
```typescript
await fetch(`${API_URL}/api/tasks/${taskId}/trigger-check/`, {
  method: 'POST'
});
```

#### Option C: Django Shell (Testing)
```bash
python backend/manage.py shell

>>> from backend.monitors.tasks import run_smart_vatican_monitor
>>> from backend.monitors.models import MonitorTask
>>> 
>>> task = MonitorTask.objects.first()
>>> run_smart_vatican_monitor(
...     date=task.dates[0],
...     ticket_id=task.ticket_id,
...     ticket_name=task.ticket_name,
...     language=task.language,
...     task_ids=[task.id],
...     visitors=task.visitors,
...     ticket_type=task.ticket_type
... )
```

### 5. API Response Format

**GET /api/tasks/**
```json
[
  {
    "id": 1,
    "agency": 1,
    "agency_name": "My Agency",
    "site": "vatican",
    "area_name": "Musei Vaticani",
    "dates": ["2026-03-28"],
    "target_date": "2026-03-28",
    "preferred_times": ["09:00", "10:00"],
    "visitors": 1,
    "ticket_type": 0,
    "ticket_id": "1870625167",
    "ticket_name": "Musei Vaticani - Biglietti d'ingresso",
    "language": null,
    "check_interval": 60,
    "is_active": true,
    "last_checked": "2026-02-28T12:58:33.000Z",
    "last_status": "available",
    "slots_found": 9,
    "latest_check": {
      "id": 123,
      "check_time": "2026-02-28T12:58:33.000Z",
      "status": "available",
      "slots_found": 9,
      "details": {
        "date": "28/03/2026",
        "slots": ["09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "14:30", "15:00"],
        "tickets": [...]
      }
    }
  }
]
```

### 6. Vercel Environment Variables

Make sure these are set in Vercel:

```env
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

### 7. CORS Configuration

Ensure Django allows requests from Vercel:

```python
# backend/core/settings.py
CORS_ALLOWED_ORIGINS = [
    "https://your-app.vercel.app",
    "http://localhost:3000",  # For local development
]

CORS_ALLOW_CREDENTIALS = True
```

### 8. Testing Checklist

- [ ] Backend API is running
- [ ] Celery worker is running
- [ ] Celery beat is running
- [ ] At least one task exists in database
- [ ] Task has been checked (last_status != 'unknown')
- [ ] Frontend can reach backend API
- [ ] CORS is configured correctly
- [ ] Environment variables are set in Vercel

### 9. Quick Test

```bash
# Test if backend is reachable
curl http://your-backend-url.com/api/health/

# Test if tasks endpoint works
curl http://your-backend-url.com/api/tasks/

# Check response format
curl http://your-backend-url.com/api/tasks/ | jq '.[0]'
```

### 10. Common Issues

**Issue: Still showing "unknown"**
- Tasks haven't been checked yet
- Start Celery worker and beat
- Or manually trigger a check

**Issue: Frontend can't reach backend**
- Check CORS configuration
- Verify API_URL environment variable
- Check network tab in browser console

**Issue: No tasks in response**
- Create tasks in Django admin
- Or via API POST /api/tasks/

**Issue: Slots not showing**
- Check `latest_check.details.slots` in API response
- Verify CheckResult is being created
- Check backend logs for errors
