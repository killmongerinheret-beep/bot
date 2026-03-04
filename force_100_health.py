#!/usr/bin/env python
"""
Force 100/100 Health Score
Resolves all tasks without ticket_id immediately
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask
from monitors.tasks import resolve_and_check_task
from django.core.cache import cache

print("=" * 80)
print("FORCING 100/100 HEALTH SCORE")
print("=" * 80)
print()

# Get all tasks without ticket_id
tasks_no_id = MonitorTask.objects.filter(is_active=True, ticket_id__isnull=True)

print(f"Found {tasks_no_id.count()} tasks without ticket_id")
print()

if tasks_no_id.count() == 0:
    print("✅ All tasks already have ticket_id!")
    print("   Health score should be 100/100")
else:
    print("Queuing tasks for immediate resolution:")
    print()
    
    for task in tasks_no_id:
        # Clear any existing resolution lock
        queue_key = f"resolving:{task.id}"
        cache.delete(queue_key)
        
        # Queue for resolution
        resolve_and_check_task.apply_async(
            args=[task.id],
            queue='vatican',
            countdown=2  # Small delay to avoid overwhelming
        )
        
        print(f"  ✅ Task #{task.id}: {task.dates[0] if task.dates else 'None'} - {task.ticket_name}")
    
    print()
    print(f"✅ Queued {tasks_no_id.count()} tasks for resolution")
    print()
    print("Estimated completion time: 5-10 minutes")
    print()
    print("Monitor progress:")
    print("  docker-compose logs -f worker_vatican | grep 'RESOLVING\\|Resolved and saved'")
    print()
    print("Check health score:")
    print("  docker-compose exec backend python /app/comprehensive_system_check.py")

print()
print("=" * 80)
print("COMPLETE")
print("=" * 80)
