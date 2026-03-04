#!/usr/bin/env python3
"""Force check on Telegram-created tasks"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask

# Reset last_checked for tasks 30, 32, 33
tasks = MonitorTask.objects.filter(id__in=[30, 32, 33])

print(f"Resetting {tasks.count()} tasks for fresh check...")
for task in tasks:
    print(f"  Task {task.id}: {task.dates[0]}, {task.visitors} visitors")
    task.last_checked = None
    task.save()

print("\n✅ Tasks reset. They will be checked within 60 seconds.")
print("Monitor the worker logs: docker-compose logs -f worker_vatican")
