#!/usr/bin/env python
"""
Force fresh checks for March 9, 16, 23 and compare with live data
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
from celery import current_app

print("=" * 80)
print("FORCING FRESH CHECKS FOR MARCH 9, 16, 23")
print("=" * 80)
print()

# Target dates
target_dates = {
    '2026-03-09': 33,
    '2026-03-16': 21,
    '2026-03-23': 26
}

for date_str, task_id in target_dates.items():
    print(f"\n{'=' * 80}")
    print(f"TASK #{task_id} - {date_str}")
    print("=" * 80)
    
    task = MonitorTask.objects.get(id=task_id)
    
    print(f"  Ticket: {task.ticket_name}")
    print(f"  Current ticket_id: {task.ticket_id}")
    print(f"  Visitors: {task.visitors}")
    print(f"  Preferred times: {task.preferred_times}")
    print()
    
    # Clear ticket_id to force fresh resolution
    if task.ticket_id:
        print(f"  🔄 Clearing stale ticket_id {task.ticket_id} to force fresh resolution")
        task.ticket_id = None
        task.save(update_fields=['ticket_id'])
    
    # Queue for immediate check
    print(f"  📤 Queuing task for immediate check...")
    
    # Use Celery to queue the task
    result = resolve_and_check_task.apply_async(
        args=[task_id],
        queue='vatican',
        countdown=2  # 2 second delay
    )
    
    print(f"  ✅ Queued with task ID: {result.id}")
    print(f"  ⏳ Check will run in 2 seconds")

print(f"\n{'=' * 80}")
print("ALL TASKS QUEUED")
print("=" * 80)
print()
print("Tasks will be checked in the next 30-60 seconds.")
print("Each task will:")
print("  1. Navigate to Vatican website")
print("  2. Extract fresh dynamic ticket IDs")
print("  3. Match by name (Musei Vaticani)")
print("  4. Check availability via API")
print("  5. Save fresh data to database")
print()
print("Wait 1-2 minutes, then run:")
print("  docker-compose exec backend python /app/check_march_data_simple.py")
print()
