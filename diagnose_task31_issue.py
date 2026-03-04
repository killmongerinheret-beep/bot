#!/usr/bin/env python3
"""Diagnose why Task 31 is not being checked"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask
from django.utils import timezone

print("=" * 70)
print("DIAGNOSING TASK 31 ISSUE")
print("=" * 70)

# Get all active Vatican tasks
active_tasks = MonitorTask.objects.filter(is_active=True, site='vatican')

print(f"\nTotal active Vatican tasks: {active_tasks.count()}")

# Group tasks like orchestration does
now = timezone.now()
smart_groups = {}
legacy_groups = {}

for task in active_tasks:
    interval_seconds = getattr(task, 'check_interval', 120)
    if not interval_seconds or interval_seconds < 60:
        interval_seconds = 60
        
    should_run = False
    if not task.last_checked:
        should_run = True
    else:
        elapsed = (now - task.last_checked).total_seconds()
        if elapsed >= interval_seconds:
            should_run = True
    
    print(f"\nTask {task.id}:")
    print(f"  Dates: {task.dates}")
    print(f"  Ticket ID: {task.ticket_id}")
    print(f"  Last Checked: {task.last_checked}")
    print(f"  Should Run: {should_run}")
            
    if should_run and task.dates:
        if task.ticket_id:
            # Smart grouping
            for date in task.dates:
                key = (date, task.ticket_id, task.language or None, task.visitors)
                if key not in smart_groups:
                    smart_groups[key] = []
                smart_groups[key].append(task.id)
                print(f"  → Added to SMART group: {key}")
        else:
            # Legacy grouping
            key = (task.ticket_type, task.language if task.ticket_type == 1 else None)
            if key not in legacy_groups:
                legacy_groups[key] = set()
            for d in task.dates:
                legacy_groups[key].add(d)
            print(f"  → Added to LEGACY group: {key} with dates {task.dates}")

print("\n" + "=" * 70)
print("SMART GROUPS:")
print("=" * 70)
for key, task_ids in smart_groups.items():
    print(f"{key}: {task_ids}")

print("\n" + "=" * 70)
print("LEGACY GROUPS:")
print("=" * 70)
for key, dates in legacy_groups.items():
    print(f"{key}: {sorted(dates)}")

print("\n" + "=" * 70)
print("TASK 31 SPECIFIC CHECK:")
print("=" * 70)
task31 = MonitorTask.objects.get(id=31)
print(f"Task 31 dates: {task31.dates}")
print(f"Task 31 ticket_id: {task31.ticket_id}")
print(f"Task 31 ticket_type: {task31.ticket_type}")
print(f"Task 31 language: {task31.language}")

# Check if Task 31's date is in any legacy group
task31_key = (task31.ticket_type, task31.language if task31.ticket_type == 1 else None)
if task31_key in legacy_groups:
    print(f"\n✅ Task 31 should be in legacy group: {task31_key}")
    print(f"   Dates in this group: {sorted(legacy_groups[task31_key])}")
    if task31.dates[0] in legacy_groups[task31_key]:
        print(f"   ✅ Task 31's date ({task31.dates[0]}) IS in the group!")
    else:
        print(f"   ❌ Task 31's date ({task31.dates[0]}) is NOT in the group!")
else:
    print(f"\n❌ Task 31's group key {task31_key} not found in legacy groups!")
