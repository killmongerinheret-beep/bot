#!/usr/bin/env python3
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')
sys.path.insert(0, '/app')
os.chdir('/app')

import django
django.setup()

from monitors.models import MonitorTask

print("Fixing tasks with no ticket names...")

# Fix tasks with no ticket name
tasks = MonitorTask.objects.filter(site='vatican', ticket_name__isnull=True)
for task in tasks:
    print(f"Task {task.id}: Setting ticket name to 'Musei Vaticani - Biglietti d'ingresso'")
    task.ticket_name = "Musei Vaticani - Biglietti d'ingresso"
    task.save()

print(f"✅ Fixed {tasks.count()} tasks")
