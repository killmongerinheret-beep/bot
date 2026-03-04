import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask

# Find all standard tickets (ticket_type=0) with language set
bad_tasks = MonitorTask.objects.filter(ticket_type=0).exclude(language=None)

print(f"Found {bad_tasks.count()} standard ticket tasks with language set:\n")

for task in bad_tasks:
    print(f"Task {task.id}: {task.ticket_name}")
    print(f"  BEFORE: ticket_type={task.ticket_type}, language={task.language}")
    
    # Fix: Standard tickets should have language=None
    task.language = None
    task.save()
    
    print(f"  AFTER:  ticket_type={task.ticket_type}, language={task.language}")
    print()

print(f"✅ Fixed {bad_tasks.count()} tasks!")
