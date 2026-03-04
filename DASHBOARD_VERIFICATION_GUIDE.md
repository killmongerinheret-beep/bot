# Dashboard Verification Guide

## Quick Fix for "Unknown" Status

The dashboard shows "unknown" because tasks haven't been checked yet. Follow these steps:

### Step 1: Start Backend Services

```bash
# Terminal 1: Django Server
cd backend
python manage.py runserver

# Terminal 2: Celery Worker
celery -A backend.core worker -l info --pool=solo

# Terminal 3: Celery Beat (Scheduler)
celery -A backend.core beat -l info
```

### Step 2: Create a Test Task (if none exists)

```bash
python backend/manage.py shell
```

```python
from backend.monitors.models import Agency, MonitorTask

# Create agency
agency, _ = Agency.objects.get_or_create(
    name="Test Agency",
    defaults={
        'telegram_chat_id': '123456789',
        'is_active': True
    }
)

# Create task
task = MonitorTask.objects.create(
    agency=agency,
    site='vatican',
    area_name='Musei Vaticani',
    dates=['2026-03-28'],
    preferred_times=['09:00', '10:00'],
    visitors=1,
    ticket_type=0,
    ticket_name='Musei Vaticani - Biglietti d\'ingresso',
    language=None,
    check_interval=60,
    is_active=True
)

print(f"Created task #{task.id}")
```

### Step 3: Trigger a Check

```python
from backend.monitors.tasks import run_smart_vatican_monitor

# Run check
result = run_smart_vatican_monitor(
    date='28/03/2026',  # DD/MM/YYYY format
    ticket_id='',
    ticket_name='Musei Vaticani - Biglietti d\'ingresso',
    language=None,
    task_ids=[task.id],
    visitors=1,
    ticket_type=0
)

print(result)
```

### Step 4: Verify API Response

```bash
# Test API endpoint
curl http://localhost:8000/api/tasks/ | python -m json.tool
```

Expected response:
```json
[
  {
    "id": 1,
    "agency": 1,
    "agency_name": "Test Agency",
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
    "last_checked": "2026-02-28T12:58:33.828000Z",
    "last_status": "available",
    "slots_found": 9,
    "latest_check": {
      "id": 1,
      "check_time": "2026-02-28T12:58:33.828000Z",
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

### Step 5: Update Frontend Code

**React/Next.js Example:**

```typescript
// types.ts
interface Task {
  id: number;
  agency_name: string;
  target_date: string;
  visitors: number;
  last_status: string;
  slots_found: number;
  last_checked: string | null;
  latest_check: {
    status: string;
    slots_found: number;
    details: {
      slots: string[];
    };
  } | null;
}

// TaskCard.tsx
function TaskCard({ task }: { task: Task }) {
  const getStatusDisplay = () => {
    if (!task.last_checked || task.last_status === 'unknown') {
      return {
        label: 'Pending',
        color: 'gray',
        icon: '⏳',
        message: 'Waiting for first check...'
      };
    }
    
    if (task.last_status === 'available' && task.slots_found > 0) {
      return {
        label: 'Available',
        color: 'green',
        icon: '✅',
        message: `${task.slots_found} slots found`
      };
    }
    
    if (task.last_status === 'sold_out' || task.slots_found === 0) {
      return {
        label: 'Sold Out',
        color: 'red',
        icon: '❌',
        message: 'No slots available'
      };
    }
    
    if (task.last_status === 'error') {
      return {
        label: 'Error',
        color: 'yellow',
        icon: '⚠️',
        message: 'Check failed'
      };
    }
    
    return {
      label: task.last_status,
      color: 'gray',
      icon: '❓',
      message: ''
    };
  };
  
  const status = getStatusDisplay();
  
  return (
    <div className="task-card">
      <h3>{task.agency_name}</h3>
      <p>Date: {task.target_date}</p>
      <p>Visitors: {task.visitors}</p>
      
      <div className={`status status-${status.color}`}>
        <span>{status.icon} {status.label}</span>
        <p>{status.message}</p>
      </div>
      
      {task.last_checked && (
        <p className="last-checked">
          Last checked: {new Date(task.last_checked).toLocaleString()}
        </p>
      )}
      
      {task.latest_check?.details?.slots && (
        <div className="slots">
          <h4>Available Times:</h4>
          <ul>
            {task.latest_check.details.slots.slice(0, 5).map(slot => (
              <li key={slot}>{slot}</li>
            ))}
          </ul>
          {task.latest_check.details.slots.length > 5 && (
            <p>... and {task.latest_check.details.slots.length - 5} more</p>
          )}
        </div>
      )}
    </div>
  );
}

// Dashboard.tsx
function Dashboard() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/tasks/`);
        const data = await response.json();
        setTasks(data);
      } catch (error) {
        console.error('Error fetching tasks:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchTasks();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchTasks, 30000);
    return () => clearInterval(interval);
  }, []);
  
  if (loading) return <div>Loading...</div>;
  
  return (
    <div className="dashboard">
      <h1>Vatican Ticket Monitor</h1>
      <div className="tasks-grid">
        {tasks.map(task => (
          <TaskCard key={task.id} task={task} />
        ))}
      </div>
    </div>
  );
}
```

### Step 6: Vercel Configuration

**Environment Variables in Vercel:**
```
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

**CORS in Django (backend/core/settings.py):**
```python
CORS_ALLOWED_ORIGINS = [
    "https://your-app.vercel.app",
    "http://localhost:3000",
]

CORS_ALLOW_CREDENTIALS = True
```

### Step 7: Verify Everything Works

**Checklist:**
- [ ] Django server running on port 8000
- [ ] Celery worker running
- [ ] Celery beat running
- [ ] At least one task created
- [ ] Task has been checked (run_smart_vatican_monitor)
- [ ] API returns task with last_status != 'unknown'
- [ ] API returns slots_found > 0 (if available)
- [ ] Frontend can fetch from API
- [ ] Frontend displays correct status
- [ ] Frontend shows slot count
- [ ] Frontend shows last checked time

### Troubleshooting

**Problem: Still showing "unknown"**
```bash
# Check if Celery is running
ps aux | grep celery

# Check if task was checked
python backend/manage.py shell
>>> from backend.monitors.models import MonitorTask
>>> task = MonitorTask.objects.first()
>>> print(task.last_status)
>>> print(task.last_checked)
```

**Problem: Frontend can't reach backend**
```bash
# Test from command line
curl http://your-backend-url.com/api/tasks/

# Check browser console for CORS errors
# Check Vercel environment variables
```

**Problem: No slots showing**
```bash
# Check CheckResult
python backend/manage.py shell
>>> from backend.monitors.models import CheckResult
>>> result = CheckResult.objects.latest('check_time')
>>> print(result.details)
>>> print(result.status)
```

### Expected Dashboard Display

```
┌─────────────────────────────────────────────┐
│ Task #1 - Test Agency                       │
├─────────────────────────────────────────────┤
│ Date: 2026-03-28                            │
│ Visitors: 1                                 │
│                                             │
│ Status: ✅ Available                        │
│ Message: 9 slots found                      │
│                                             │
│ Last Checked: 2 minutes ago                 │
└─────────────────────────────────────────────┘

📅 Available Time Slots:
  • 09:30
  • 10:00
  • 10:30
  • 11:00
  • 11:30
  • 12:00
  • 12:30
  • 14:30
  • 15:00
```

### Quick Test Script

Save as `test_dashboard_data.sh`:
```bash
#!/bin/bash

echo "Testing Dashboard Data..."
echo ""

# Test health
echo "1. Health Check:"
curl -s http://localhost:8000/api/health/ | python -m json.tool
echo ""

# Test tasks
echo "2. Tasks:"
curl -s http://localhost:8000/api/tasks/ | python -m json.tool | head -50
echo ""

# Test specific task
echo "3. First Task Details:"
TASK_ID=$(curl -s http://localhost:8000/api/tasks/ | python -c "import sys, json; print(json.load(sys.stdin)[0]['id'])")
curl -s http://localhost:8000/api/tasks/$TASK_ID/ | python -m json.tool
echo ""

echo "Done!"
```

Run with: `bash test_dashboard_data.sh`
