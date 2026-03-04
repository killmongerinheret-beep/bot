import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask

# Find tasks for April 22
tasks = MonitorTask.objects.filter(dates__contains='2026-04-22')

print(f"Found {tasks.count()} tasks for April 22, 2026:\n")

for task in tasks:
    print(f"Task ID: {task.id}")
    print(f"  Ticket Name: {task.ticket_name}")
    print(f"  Ticket ID: {task.ticket_id}")
    print(f"  Ticket Type: {task.ticket_type} (0=standard, 1=guided)")
    print(f"  Language: {task.language}")
    print(f"  Visitors: {task.visitors}")
    print(f"  Dates: {task.dates}")
    print(f"  Is Active: {task.is_active}")
    print()
