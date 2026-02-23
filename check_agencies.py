#!/usr/bin/env python3
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')
sys.path.insert(0, '/app')
os.chdir('/app')

import django
django.setup()

from monitors.models import Agency, MonitorTask

print("="*80)
print("VATICAN TASKS - AGENCY CONFIGURATION")
print("="*80)

for task in MonitorTask.objects.filter(site='vatican', is_active=True):
    print(f"\nTask ID: {task.id}")
    print(f"  Agency: {task.agency.name}")
    print(f"  Chat ID: {task.agency.telegram_chat_id or '❌ NOT SET'}")
    print(f"  Ticket: {task.ticket_name}")
    print(f"  Dates: {task.dates}")
    print(f"  Status: {'✅ Will notify' if task.agency.telegram_chat_id else '❌ No notifications'}")
