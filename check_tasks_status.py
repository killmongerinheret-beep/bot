#!/usr/bin/env python3
"""Check current task status and ticket type differentiation"""
import os
import sys
import django

sys.path.insert(0, 'backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask
from django.core.cache import cache

print("=" * 80)
print("CURRENT ACTIVE TASKS")
print("=" * 80)

tasks = MonitorTask.objects.filter(is_active=True).order_by('id')

for task in tasks:
    date = task.dates[0] if task.dates else "N/A"
    print(f"\nTask #{task.id}:")
    print(f"  Ticket Name: {task.ticket_name}")
    print(f"  Ticket Type: {task.ticket_type} ({'Standard' if task.ticket_type == 0 else 'Guided Tour'})")
    print(f"  Language: {task.language or 'None (Standard)'}")
    print(f"  Date: {date}")
    print(f"  Visitors: {task.visitors}")
    print(f"  Last Status: {task.last_status}")
    print(f"  Last Checked: {task.last_checked}")
    print(f"  Notification Mode: {task.notification_mode}")
    
    # Check cache state
    state_key = f"ticket_state:{task.id}:*:{date}"
    print(f"  Cache State Key Pattern: {state_key}")

print("\n" + "=" * 80)
print("TICKET TYPE DIFFERENTIATION CHECK")
print("=" * 80)

standard_tasks = tasks.filter(ticket_type=0)
guided_tasks = tasks.filter(ticket_type=1)

print(f"\nStandard Tickets (Type 0): {standard_tasks.count()}")
for task in standard_tasks:
    print(f"  - Task #{task.id}: {task.ticket_name} | Lang: {task.language} | Visitors: {task.visitors}")

print(f"\nGuided Tours (Type 1): {guided_tasks.count()}")
for task in guided_tasks:
    print(f"  - Task #{task.id}: {task.ticket_name} | Lang: {task.language} | Visitors: {task.visitors}")

print("\n" + "=" * 80)
print("CACHE STATE CHECK")
print("=" * 80)

# Check for any alert cooldown keys
print("\nChecking for active alert cooldowns...")
for task in tasks:
    date = task.dates[0] if task.dates else "N/A"
    # We don't know the exact ticket_id, so we can't check the exact key
    # But we can check if there are any cooldowns set
    print(f"Task #{task.id}: Would use key pattern 'alert_cooldown:{task.id}:*:{date}'")

print("\n" + "=" * 80)
