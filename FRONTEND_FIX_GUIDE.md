# Frontend Task Display Issue - Debugging Guide

## Issue
Frontend dashboard may not be showing all tasks that exist in the database.

## Root Cause Analysis

### 1. Check API Response
```bash
# Test the API directly
curl http://localhost:8000/api/v1/tasks/?agency_id=1

# Count tasks
curl http://localhost:8000/api/v1/tasks/?agency_id=1 | jq '. | length'
```

**Expected:** Should return all 4 tasks  
**Actual:** API returns 4 tasks correctly ✅

### 2. Check Frontend API Call

The frontend code in `frontend/src/app/page.tsx` looks correct:

```typescript
const tasksData = await api.getTasks(agency.id);
setTasks(tasksData);
```

### 3. Possible Issues

#### Issue A: React State Not Updating
**Symptom:** Tasks array is set but UI doesn't re-render

**Fix:** Add key prop to force re-render
```typescript
{tasks.map((task) => (
  <motion.div key={`task-${task.id}-${task.updated_at}`}>
    <TaskCard task={task} onDelete={handleDeleteTask} />
  </motion.div>
))}
```

#### Issue B: Browser Cache
**Symptom:** Old data cached in browser

**Fix:** Hard refresh
- Windows: `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`

#### Issue C: API URL Mismatch
**Symptom:** Frontend calling wrong API endpoint

**Fix:** Check `frontend/src/lib/api.ts`
```typescript
const getApiUrl = () => {
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8000/api/v1';  // ✅ Correct
    }
  }
  return 'http://backend:8000/api/v1';
};
```

#### Issue D: CORS Error
**Symptom:** Browser blocks API request

**Fix:** Check browser console for CORS errors
```javascript
// Should see in console:
// ✅ GET http://localhost:8000/api/v1/tasks/?agency_id=1 200 OK

// If you see:
// ❌ CORS policy: No 'Access-Control-Allow-Origin' header

// Then fix backend CORS settings in backend/core/settings.py:
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

## Quick Fix Steps

### Step 1: Clear Browser Cache
```bash
# Open browser console (F12)
# Go to Application tab
# Click "Clear storage"
# Reload page
```

### Step 2: Check Network Tab
```bash
# Open browser console (F12)
# Go to Network tab
# Reload page
# Look for /api/v1/tasks/ request
# Check:
#   - Status: Should be 200
#   - Response: Should show all 4 tasks
#   - Preview: Verify JSON structure
```

### Step 3: Add Debug Logging
```typescript
// frontend/src/app/page.tsx
useEffect(() => {
  const initDashboard = async () => {
    try {
      const agency = await api.getMyAgency('local-admin', 'admin@local.com');
      console.log('Agency:', agency);
      
      const tasksData = await api.getTasks(agency.id);
      console.log('Tasks received:', tasksData.length, tasksData);
      
      setTasks(tasksData);
      console.log('Tasks state set');
    } catch (error) {
      console.error('Failed to init dashboard:', error);
    }
  };
  
  initDashboard();
}, []);
```

### Step 4: Force Re-render
```typescript
// Add this to frontend/src/app/page.tsx
const [refreshKey, setRefreshKey] = useState(0);

const refreshTasks = async () => {
  if (!agencyId) return;
  try {
    const tasksData = await api.getTasks(agencyId);
    setTasks(tasksData);
    setRefreshKey(prev => prev + 1); // Force re-render
  } catch (err) {
    console.error(err);
  }
};

// In the render:
<div key={refreshKey} className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
  {tasks.map((task) => (
    <TaskCard key={task.id} task={task} onDelete={handleDeleteTask} />
  ))}
</div>
```

## Verification Checklist

- [ ] API returns all 4 tasks when called directly
- [ ] Browser console shows no errors
- [ ] Network tab shows successful API call
- [ ] Console.log shows correct number of tasks
- [ ] React DevTools shows tasks in state
- [ ] All 4 TaskCard components render

## If Still Not Working

### Nuclear Option: Restart Everything
```bash
# Stop all containers
docker-compose down

# Clear Docker cache
docker system prune -a

# Rebuild and restart
docker-compose up --build -d

# Check logs
docker-compose logs -f frontend
```

### Check for JavaScript Errors
```javascript
// Open browser console
// Look for any red errors
// Common issues:
// - Undefined property access
// - JSON parse errors
// - Type mismatches
```

### Verify Task Data Structure
```typescript
// Add this to TaskCard.tsx
console.log('Rendering task:', task.id, task);

// Check if all tasks have required fields:
// - id
// - area_name
// - dates
// - is_active
```

## Expected Behavior

When working correctly, you should see:

1. **Browser Console:**
```
Agency: {id: 1, name: "Elite Colosseo", ...}
Tasks received: 4 [{...}, {...}, {...}, {...}]
Tasks state set
```

2. **Network Tab:**
```
GET /api/v1/tasks/?agency_id=1
Status: 200 OK
Response: [4 task objects]
```

3. **Dashboard:**
```
┌─────────────┬─────────────┬─────────────┐
│   Task 1    │   Task 2    │   Task 3    │
│  March 11   │  March 23   │  March 10   │
│  Guided     │  Standard   │  Standard   │
└─────────────┴─────────────┴─────────────┘
┌─────────────┐
│   Task 4    │
│  June 15    │
│  Standard   │
└─────────────┘
```

## Common Mistakes

### ❌ Wrong Agency ID
```typescript
// Don't hardcode agency ID
const tasksData = await api.getTasks(1);

// ✅ Use dynamic agency ID
const tasksData = await api.getTasks(agency.id);
```

### ❌ Filtering Active Tasks Only
```typescript
// Don't filter in frontend
const activeTasks = tasks.filter(t => t.is_active);

// ✅ Show all tasks, let user toggle
{tasks.map(task => <TaskCard task={task} />)}
```

### ❌ Pagination Limit
```python
# backend/monitors/views.py
# Make sure there's no pagination limit
class MonitorTaskViewSet(viewsets.ModelViewSet):
    # ❌ Don't add this:
    # pagination_class = LimitOffsetPagination
    
    # ✅ Return all tasks:
    def get_queryset(self):
        return MonitorTask.objects.all()
```

## Success Indicators

✅ All 4 tasks visible in dashboard  
✅ Each task shows correct date  
✅ Status badges display correctly  
✅ Available slots show for active tasks  
✅ Countdown timers work  
✅ Delete button works  

## Still Need Help?

1. **Export Debug Info:**
```bash
# API response
curl http://localhost:8000/api/v1/tasks/?agency_id=1 > tasks_api.json

# Frontend logs
docker-compose logs frontend > frontend_logs.txt

# Browser console
# Right-click console → Save as... → console_logs.txt
```

2. **Check React DevTools:**
- Install React DevTools extension
- Open Components tab
- Find DashboardPage component
- Check `tasks` state
- Verify it has 4 items

3. **Verify Database:**
```bash
# Connect to database
docker-compose exec backend python manage.py shell

# Check tasks
from monitors.models import MonitorTask
tasks = MonitorTask.objects.filter(agency_id=1)
print(f"Total tasks: {tasks.count()}")
for task in tasks:
    print(f"Task {task.id}: {task.area_name} - {task.dates}")
```

Expected output:
```
Total tasks: 4
Task 4: Musei Vaticani - ['2026-03-11']
Task 2: Musei Vaticani - ['23/03/2026']
Task 3: Musei Vaticani - ['2026-03-10']
Task 1: Musei Vaticani - ['15/06/2026']
```

---

**Most Likely Cause:** Browser cache or React state not updating. Try hard refresh first!
