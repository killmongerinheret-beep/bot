#!/usr/bin/env python
"""
Fix March 23 data and send fresh notifications for all tasks
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
print("FIXING MARCH 23 AND SENDING NOTIFICATIONS")
print("=" * 80)
print()

# Step 1: Clear all resolution locks
print("Step 1: Clearing all resolution locks...")
all_tasks = MonitorTask.objects.filter(is_active=True, site='vatican')
for task in all_tasks:
    queue_key = f"resolving:{task.id}"
    if cache.get(queue_key):
        cache.delete(queue_key)
        print(f"  Cleared lock for Task #{task.id}")

print(f"✅ Cleared {all_tasks.count()} locks")
print()

# Step 2: Clear all ticket_ids to force fresh resolution
print("Step 2: Clearing all ticket_ids to force fresh resolution...")
cleared_count = 0
for task in all_tasks:
    if task.ticket_id:
        task.ticket_id = None
        task.save(update_fields=['ticket_id'])
        cleared_count += 1

print(f"✅ Cleared {cleared_count} stale ticket_ids")
print()

# Step 3: Queue all tasks for immediate check
print("Step 3: Queuing all tasks for immediate fresh check...")
for i, task in enumerate(all_tasks):
    # Queue with staggered countdown (2-30 seconds)
    countdown = 2 + (i * 3)
    
    result = resolve_and_check_task.apply_async(
        args=[task.id],
        queue='vatican',
        countdown=countdown
    )
    
    print(f"  Task #{task.id} ({task.ticket_name[:30]}...) - queued for {countdown}s")

print(f"\n✅ Queued {all_tasks.count()} tasks")
print()

print("=" * 80)
print("ALL TASKS QUEUED FOR FRESH CHECK")
print("=" * 80)
print()
print("Timeline:")
print("  • Next 2-90 seconds: All tasks will resolve fresh ticket IDs")
print("  • Each task takes 30-60 seconds to complete")
print("  • Total time: ~3-5 minutes for all checks")
print()
print("After checks complete:")
print("  • Fresh data will be in database")
print("  • Telegram notifications will be sent for state changes")
print("  • Dashboard will show updated data")
print()
print("Wait 5 minutes, then check Telegram for notifications!")
print()
