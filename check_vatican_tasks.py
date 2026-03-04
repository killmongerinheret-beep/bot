#!/usr/bin/env python3
"""Check Vatican Tasks Status"""
import os
import sys
import django

sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from backend.monitors.models import MonitorTask, CheckResult
from django.utils import timezone
from datetime import timedelta

print('='*80)
print('ACTIVE VATICAN TASKS')
print('='*80)

tasks = MonitorTask.objects.filter(is_active=True, site='vatican').order_by('-created_at')

for task in tasks[:5]:
    print(f'\nTask ID: {task.id}')
    print(f'Agency: {task.agency.name}')
    print(f'Ticket Name: {task.ticket_name}')
    print(f'Ticket ID: {task.ticket_id}')
    print(f'Dates: {task.dates[:3]}...' if len(task.dates) > 3 else f'Dates: {task.dates}')
    print(f'Visitors: {task.visitors}')
    print(f'Ticket Type: {task.ticket_type} (0=Standard, 1=Guided)')
    lang_display = task.language if task.language else "None (Standard)"
    print(f'Language: {lang_display}')
    print(f'Last Status: {task.last_status}')
    print(f'Last Checked: {task.last_checked}')
    
    # Get recent results
    recent = CheckResult.objects.filter(task=task).order_by('-check_time')[:3]
    if recent:
        print(f'\nRecent Check Results:')
        for r in recent:
            details = r.details or {}
            slots = details.get('slots', [])
            slot_count = len(slots) if isinstance(slots, list) else 0
            print(f'  {r.check_time.strftime("%H:%M:%S")}: {r.status} - {slot_count} slots')
            if slots and slot_count <= 5:
                print(f'    Times: {slots}')

print('\n' + '='*80)
print('SUMMARY')
print('='*80)
print(f'Total Active Vatican Tasks: {tasks.count()}')
