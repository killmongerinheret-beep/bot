#!/usr/bin/env python
"""Check task configuration"""

import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')
sys.path.insert(0, '/app')
os.chdir('/app')

import django
django.setup()

from monitors.models import MonitorTask

tasks = MonitorTask.objects.filter(site='vatican', is_active=True)

print(f"\n{'='*60}")
print(f"Active Vatican Tasks: {tasks.count()}")
print(f"{'='*60}\n")

for task in tasks:
    print(f"Task ID: {task.id}")
    print(f"  Agency: {task.agency.name}")
    print(f"  Dates: {task.dates}")
    print(f"  Ticket: {task.ticket_name}")
    print(f"  Language: '{task.language}'")
    print(f"  Visitors: {task.visitors}")
    print(f"  Preferred Times: {task.preferred_times}")
    print(f"  Notification Mode: {task.notification_mode}")
    print()
