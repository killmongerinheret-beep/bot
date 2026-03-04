#!/usr/bin/env python3
"""Check what ticket names are stored in the database"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask

print("\n" + "="*60)
print("TASK TICKET NAMES IN DATABASE")
print("="*60)

tasks = MonitorTask.objects.filter(site='vatican', ticket_type=0).order_by('id')

for task in tasks:
    print(f"\nTask {task.id}:")
    print(f"  Ticket Name: {task.ticket_name}")
    print(f"  Ticket Type: {task.ticket_type}")
    print(f"  Language: {task.language}")
    print(f"  Dates: {task.dates}")

print("\n")
