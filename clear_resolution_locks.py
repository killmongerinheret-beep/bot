#!/usr/bin/env python
"""
Clear resolution locks and force immediate checks
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.cache import cache
from monitors.models import MonitorTask
from monitors.tasks import resolve_and_check_task

print("=" * 80)
print("CLEARING RESOLUTION LOCKS")
print("=" * 80)
print()

# Target tasks
task_ids = [21, 26, 33]

for task_id in task_ids:
    queue_key = f"resolving:{task_id}"
    
    # Check if locked
    if cache.get(queue_key):
        print(f"Task #{task_id}: LOCKED - clearing...")
        cache.delete(queue_key)
        print(f"  ✅ Lock cleared")
    else:
        print(f"Task #{task_id}: Not locked")
    
    # Queue for immediate check
    print(f"  📤 Queuing for immediate check...")
    result = resolve_and_check_task.apply_async(
        args=[task_id],
        queue='vatican'
    )
    print(f"  ✅ Queued: {result.id}")
    print()

print("=" * 80)
print("ALL LOCKS CLEARED AND TASKS QUEUED")
print("=" * 80)
print()
