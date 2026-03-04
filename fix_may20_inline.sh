#!/bin/bash
docker-compose exec backend python backend/manage.py shell <<EOF
from monitors.models import MonitorTask

# Find May 20 tasks
tasks = MonitorTask.objects.filter(is_active=True, site='vatican')
may20_tasks = [t for t in tasks if any('2026-05-20' in d or '20/05/2026' in d for d in t.dates)]

print(f"Found {len(may20_tasks)} tasks with May 20, 2026")

for task in may20_tasks:
    print(f"\nTask {task.id}: {task.ticket_name}")
    print(f"  Type: {task.ticket_type}, Lang: {task.language}, Visitors: {task.visitors}")
    
    if task.language and 'standard' in task.ticket_name.lower():
        print(f"  ❌ PROBLEM: Standard ticket with language={task.language}")
        print(f"  🔧 FIXING: Setting language=None, ticket_type=0")
        task.language = None
        task.ticket_type = 0
        task.save()
        print(f"  ✅ FIXED!")
    else:
        print(f"  ✅ OK")

print("\nDone! Restart worker to apply changes.")
EOF
