import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask

task = MonitorTask.objects.get(id=20)
print(f"Task 20 Details:")
print(f"  ticket_name: {task.ticket_name}")
print(f"  ticket_type: {task.ticket_type}")
print(f"  language: {task.language}")
print(f"  ticket_id: {task.ticket_id}")
print(f"  visitors: {task.visitors}")
print(f"  target_date: {task.target_date}")
