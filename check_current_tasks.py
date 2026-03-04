"""
Check current Vatican tasks in database and their status
"""
import sys
import os
sys.path.insert(0, 'backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from monitors.models import MonitorTask
from django.utils import timezone

# Get all Vatican tasks
tasks = MonitorTask.objects.filter(site='vatican', is_active=True).order_by('id')

print('='*70)
print('CURRENT VATICAN TASKS IN DATABASE')
print('='*70)
print(f'Total active tasks: {tasks.count()}\n')

for task in tasks:
    print(f'Task ID: {task.id}')
    print(f'Agency: {task.agency.name}')
    print(f'Dates: {task.dates}')
    print(f'Visitors: {task.visitors}')
    ticket_type_str = "Standard" if task.ticket_type == 0 else "Guided Tour"
    print(f'Ticket Type: {task.ticket_type} ({ticket_type_str})')
    print(f'Ticket Name: {task.ticket_name}')
    print(f'Ticket ID (cached): {task.ticket_id or "None"}')
    print(f'Language: {task.language or "None (Standard ticket)"}')
    print(f'Last Checked: {task.last_checked}')
    print(f'Last Status: {task.last_status}')
    print(f'Last Result: {task.last_result_summary}')
    print(f'Check Interval: {task.check_interval}s')
    print('-'*70)
