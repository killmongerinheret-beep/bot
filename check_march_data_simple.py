#!/usr/bin/env python
"""
Simple check of March 9, 16, 23 data in database
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask, CheckResult
from datetime import datetime

print("=" * 80)
print("CHECKING MARCH 9, 16, 23 DATA IN DATABASE")
print("=" * 80)
print()

# Target dates
target_dates = ['2026-03-09', '2026-03-16', '2026-03-23']

for date_str in target_dates:
    print(f"\n{'=' * 80}")
    print(f"DATE: {date_str}")
    print("=" * 80)
    
    # Find tasks for this date
    tasks = MonitorTask.objects.filter(
        is_active=True,
        dates__contains=[date_str]
    )
    
    if not tasks.exists():
        # Try DD/MM/YYYY format
        year, month, day = date_str.split('-')
        date_formatted = f"{day}/{month}/{year}"
        tasks = MonitorTask.objects.filter(
            is_active=True,
            dates__contains=[date_formatted]
        )
    
    if not tasks.exists():
        print(f"⚠️ No tasks found for {date_str}")
        continue
    
    print(f"\nFound {tasks.count()} task(s):")
    
    for task in tasks:
        print(f"\n  Task #{task.id}:")
        print(f"    Ticket: {task.ticket_name}")
        print(f"    Ticket ID: {task.ticket_id}")
        print(f"    Visitors: {task.visitors}")
        print(f"    Preferred times: {task.preferred_times}")
        print(f"    Last checked: {task.last_checked}")
        print(f"    Last status: {task.last_status}")
        
        # Get latest check result
        latest_result = CheckResult.objects.filter(task=task).order_by('-check_time').first()
        
        if not latest_result:
            print(f"    ⚠️ No check results found")
            continue
        
        # Extract slots from stored data
        details = latest_result.details
        stored_slots = []
        
        if isinstance(details, dict):
            if 'slots' in details:
                stored_slots = details['slots']
            elif 'updates' in details:
                for date, items in details.get('updates', {}).items():
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict) and 'slots' in item:
                                stored_slots.extend(item['slots'])
        
        stored_slots = list(set(stored_slots))
        stored_slots.sort()
        
        print(f"    Check time: {latest_result.check_time}")
        print(f"    Status: {latest_result.status}")
        print(f"    Total slots: {len(stored_slots)}")
        
        if stored_slots:
            print(f"    Slots: {', '.join(stored_slots[:20])}")
            if len(stored_slots) > 20:
                print(f"           ... and {len(stored_slots) - 20} more")
        else:
            print(f"    ❌ NO SLOTS STORED")
        
        # Check if data is stale (older than 10 minutes)
        if latest_result.check_time:
            from django.utils import timezone
            age_minutes = (timezone.now() - latest_result.check_time).total_seconds() / 60
            if age_minutes > 10:
                print(f"    ⚠️ Data is {int(age_minutes)} minutes old (may be stale)")
            else:
                print(f"    ✅ Data is fresh ({int(age_minutes)} minutes old)")

print(f"\n{'=' * 80}")
print("ANALYSIS COMPLETE")
print("=" * 80)
print()
print("Next step: Force re-check these dates to get fresh data")
print()
