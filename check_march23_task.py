#!/usr/bin/env python3
"""Check Task 26 (March 23, 2026) configuration and recent results"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask
from datetime import datetime

# Find tasks for March 23, 2026
tasks = MonitorTask.objects.filter(dates__contains='2026-03-23')

print('\n' + '='*60)
print('TASKS MONITORING MARCH 23, 2026')
print('='*60)

for task in tasks:
    print(f'\nTask ID: {task.id}')
    print(f'Ticket Type: {task.ticket_type} (0=Standard, 1=Guided)')
    print(f'Ticket Name: {task.ticket_name}')
    print(f'Language: {task.language}')
    print(f'Visitors: {task.visitors}')
    print(f'Area: {task.area_name}')
    print(f'Last Check: {task.last_checked}')
    print(f'Dates: {task.dates}')
    
    # Check if configuration is correct
    print('\n🔍 Configuration Check:')
    if task.ticket_type == 0:
        if task.language is None:
            print('  ✅ Standard ticket with language=None (CORRECT)')
        else:
            print(f'  ❌ Standard ticket with language={task.language} (WRONG)')
    else:
        if task.language:
            print(f'  ✅ Guided tour with language={task.language} (CORRECT)')
        else:
            print('  ❌ Guided tour with language=None (WRONG)')
    
    print('-'*60)

print('\n')
