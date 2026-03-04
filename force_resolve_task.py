#!/usr/bin/env python
"""Force resolve ticket_id for a specific task"""
import os
import sys
import django

sys.path.insert(0, '/app')
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.tasks import resolve_and_check_task
from monitors.models import MonitorTask

# Get task 34 (the newest one)
task = MonitorTask.objects.get(id=34)
print(f"Task #{task.id}:")
print(f"  Date: {task.dates[0] if task.dates else 'N/A'}")
print(f"  Visitors: {task.visitors}")
print(f"  Ticket ID: {task.ticket_id or 'None'}")
print(f"  Last Checked: {task.last_checked or 'Never'}")
print()

print("Forcing ID resolution...")
print()

# Call the function directly (synchronously for testing)
result = resolve_and_check_task(34)

print()
print(f"Result: {result}")
print()

# Check task again
task.refresh_from_db()
print("After resolution:")
print(f"  Ticket ID: {task.ticket_id or 'None'}")
print(f"  Last Checked: {task.last_checked or 'Never'}")
print(f"  Status: {task.last_status}")
