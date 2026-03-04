#!/usr/bin/env python3
"""
Quick Fix: Update Vatican Ticket Names
=======================================
Fixes the ticket name mismatch issue causing check failures.

Run inside Docker:
  docker-compose exec backend python fix_vatican_ticket_names.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from backend.monitors.models import MonitorTask

def main():
    print("=" * 60)
    print("Vatican Ticket Name Fix")
    print("=" * 60)
    
    # Find all Vatican tasks with old ticket names
    old_names = [
        "Musei Vaticani - Biglietti d'ingresso",
        "Musei Vaticani - Biglietti",
        "Vatican Museums - Admission",
    ]
    
    tasks = MonitorTask.objects.filter(
        site='vatican',
        is_active=True
    )
    
    print(f"\nFound {tasks.count()} active Vatican tasks")
    
    updated_count = 0
    cleared_count = 0
    
    for task in tasks:
        ticket_name = task.ticket_name or ""
        
        # Check if using old name
        if any(old in ticket_name for old in old_names):
            print(f"\n❌ Task {task.id}: Using old name '{ticket_name}'")
            print(f"   Current ID: {task.ticket_id}")
            
            # Strategy 1: Clear the ticket_id to force fresh resolution
            if task.ticket_id:
                task.ticket_id = None
                task.save()
                cleared_count += 1
                print(f"   ✅ Cleared stale ID - will auto-resolve on next check")
            
            # Strategy 2: Update to more flexible name pattern
            # Keep the name but clear ID so dynamic resolution works
            updated_count += 1
        else:
            print(f"✅ Task {task.id}: Name OK - '{ticket_name}'")
    
    print("\n" + "=" * 60)
    print(f"Summary:")
    print(f"  - Tasks checked: {tasks.count()}")
    print(f"  - Stale IDs cleared: {cleared_count}")
    print(f"  - Tasks updated: {updated_count}")
    print("=" * 60)
    
    if cleared_count > 0:
        print("\n✅ Fix applied! Next check will resolve fresh ticket IDs.")
        print("   Monitor logs: docker-compose logs -f worker_vatican")
    else:
        print("\n✅ No stale IDs found - system is up to date!")

if __name__ == "__main__":
    main()
