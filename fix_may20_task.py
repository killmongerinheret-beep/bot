#!/usr/bin/env python3
"""
Fix May 20 Task - Remove Language for Standard Ticket
======================================================
The May 20 task is incorrectly configured with language="ENG" 
for a standard ticket, causing it to be treated as a guided tour.

This script fixes it by setting language=None.
"""

import os
import sys
import django

sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from backend.monitors.models import MonitorTask

print("=" * 80)
print("FIX MAY 20 TASK - Remove Language for Standard Ticket")
print("=" * 80)

# Find tasks for May 20, 2026
tasks = MonitorTask.objects.filter(
    is_active=True,
    site='vatican',
    dates__contains='2026-05-20'
) | MonitorTask.objects.filter(
    is_active=True,
    site='vatican',
    dates__contains='20/05/2026'
)

print(f"\nFound {tasks.count()} tasks with May 20, 2026")

for task in tasks:
    print(f"\n{'='*80}")
    print(f"Task ID: {task.id}")
    print(f"Agency: {task.agency.name}")
    print(f"Ticket Name: {task.ticket_name}")
    print(f"Ticket ID: {task.ticket_id}")
    print(f"Ticket Type: {task.ticket_type} (0=Standard, 1=Guided)")
    print(f"Language: {task.language}")
    print(f"Visitors: {task.visitors}")
    print(f"Dates: {task.dates[:3]}...")
    
    # Check if this is the problematic task
    if task.language and task.ticket_name and 'standard' in task.ticket_name.lower():
        print(f"\n❌ PROBLEM DETECTED:")
        print(f"   This is a STANDARD ticket but has language='{task.language}'")
        print(f"   This causes the bot to treat it as a guided tour!")
        
        print(f"\n🔧 FIXING:")
        print(f"   Setting language=None and ticket_type=0")
        
        task.language = None
        task.ticket_type = 0
        task.save()
        
        print(f"   ✅ FIXED!")
        print(f"   - Language: {task.language}")
        print(f"   - Ticket Type: {task.ticket_type}")
    elif task.language:
        print(f"\n✅ This appears to be a guided tour (has language)")
    else:
        print(f"\n✅ This is correctly configured (no language)")

print("\n" + "=" * 80)
print("DONE")
print("=" * 80)
print("\nNext steps:")
print("1. Restart worker: docker-compose restart worker_vatican")
print("2. Monitor logs: docker-compose logs -f worker_vatican")
print("3. Look for May 20 checks with correct slug: /MV-Biglietti/")
print("=" * 80)
