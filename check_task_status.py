#!/usr/bin/env python3

import os
import sys
import django

# Add the backend directory to Python path
sys.path.append('/app/backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask
from django.utils import timezone

def check_task_status():
    tasks = MonitorTask.objects.filter(is_active=True)
    print('=== VATICAN TASK STATUS ===')
    print(f'Total Active Tasks: {tasks.count()}')
    print()

    for task in tasks:
        name = task.ticket_name or '[Unnamed]'
        print(f'Task #{task.id}: {name}')
        print(f'  Agency: {task.agency.name}')
        print(f'  Dates: {task.dates}')
        print(f'  Visitors: {task.visitors}, Language: {task.language or "None"}')
        print(f'  Last Checked: {task.last_checked}')
        print(f'  Last Status: {task.last_status}')
        print(f'  Site: {task.site}')
        print('---')

if __name__ == '__main__':
    check_task_status()