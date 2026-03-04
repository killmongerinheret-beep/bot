import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask

# Fix Task 24 (April 22)
task = MonitorTask.objects.get(id=24)

print(f"BEFORE:")
print(f"  Ticket Name: {task.ticket_name}")
print(f"  Ticket Type: {task.ticket_type}")
print(f"  Language: {task.language}")
print(f"  Visitors: {task.visitors}")

# Fix: Standard tickets should have language=None
task.language = None
task.save()

print(f"\nAFTER:")
print(f"  Ticket Name: {task.ticket_name}")
print(f"  Ticket Type: {task.ticket_type}")
print(f"  Language: {task.language}")
print(f"  Visitors: {task.visitors}")

print(f"\n✅ Task 24 fixed! Language set to None for standard ticket.")
