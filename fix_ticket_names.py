#!/usr/bin/env python3
"""Fix ticket names in database to match Vatican website"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask

print("\n" + "="*60)
print("FIXING TICKET NAMES")
print("="*60)

# Update all standard ticket tasks to use the correct Italian name
tasks = MonitorTask.objects.filter(
    site='vatican',
    ticket_type=0,
    ticket_name='Standard Entry (Full Price)'
)

print(f"\nFound {tasks.count()} tasks to update")

for task in tasks:
    print(f"\nTask {task.id}:")
    print(f"  Old name: {task.ticket_name}")
    task.ticket_name = "Musei Vaticani - Biglietti d'ingresso"
    task.save()
    print(f"  New name: {task.ticket_name}")
    print(f"  ✅ Updated")

print("\n" + "="*60)
print(f"✅ Updated {tasks.count()} tasks")
print("="*60 + "\n")
