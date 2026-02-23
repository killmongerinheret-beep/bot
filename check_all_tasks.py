#!/usr/bin/env python3
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')
sys.path.insert(0, '/app')
os.chdir('/app')

import django
django.setup()

from monitors.models import MonitorTask

print("="*80)
print("ALL MONITORING TASKS STATUS")
print("="*80)

for task in MonitorTask.objects.filter(is_active=True).order_by('site', 'id'):
    status = "✅" if task.agency.telegram_chat_id else "❌"
    chat = task.agency.telegram_chat_id or "NOT SET"
    ticket = task.ticket_name or "None"
    print(f"\nTask {task.id}: {task.site.upper()}")
    print(f"  Agency: {task.agency.name}")
    print(f"  Chat ID: {status} {chat}")
    print(f"  Ticket: {ticket[:50]}")
    print(f"  Dates: {task.dates}")
    print(f"  Language: {task.language or 'None'}")
    print(f"  Visitors: {task.visitors}")
    print(f"  Status: {'Active' if task.is_active else 'Inactive'}")

print("\n" + "="*80)
print(f"Total Active Tasks: {MonitorTask.objects.filter(is_active=True).count()}")
print("="*80)
