#!/usr/bin/env python
"""
Verify all tasks have fresh data
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask, CheckResult
from django.utils import timezone

print("=" * 80)
print("VERIFICATION: ALL TASKS DATA")
print("=" * 80)
print()

all_tasks = MonitorTask.objects.filter(is_active=True, site='vatican').order_by('id')

fresh_count = 0
stale_count = 0
error_count = 0

for task in all_tasks:
    print(f"Task #{task.id}: {task.ticket_name}")
    print(f"  Date: {task.dates[0] if task.dates else 'N/A'}")
    print(f"  Ticket ID: {task.ticket_id or 'None'}")
    print(f"  Visitors: {task.visitors}")
    print(f"  Last checked: {task.last_checked or 'Never'}")
    print(f"  Last status: {task.last_status}")
    
    # Get latest check result
    latest_result = CheckResult.objects.filter(task=task).order_by('-check_time').first()
    
    if latest_result:
        # Extract slots
        details = latest_result.details
        slots = []
        
        if isinstance(details, dict):
            if 'slots' in details:
                slots = details['slots']
            elif 'updates' in details:
                for date, items in details.get('updates', {}).items():
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict) and 'slots' in item:
                                slots.extend(item['slots'])
        
        slots = list(set(slots))
        slots.sort()
        
        print(f"  Slots: {len(slots)} found")
        if slots:
            print(f"    {', '.join(slots[:10])}")
            if len(slots) > 10:
                print(f"    ... and {len(slots) - 10} more")
        
        # Check freshness
        if latest_result.check_time:
            age_minutes = (timezone.now() - latest_result.check_time).total_seconds() / 60
            if age_minutes < 10:
                print(f"  ✅ FRESH ({int(age_minutes)} minutes old)")
                fresh_count += 1
            else:
                print(f"  ⚠️ STALE ({int(age_minutes)} minutes old)")
                stale_count += 1
        else:
            print(f"  ❌ ERROR: No check time")
            error_count += 1
    else:
        print(f"  ❌ ERROR: No check results")
        error_count += 1
    
    print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"  ✅ Fresh data: {fresh_count}/{all_tasks.count()}")
print(f"  ⚠️ Stale data: {stale_count}/{all_tasks.count()}")
print(f"  ❌ Errors: {error_count}/{all_tasks.count()}")
print()

if fresh_count == all_tasks.count():
    print("🎯 ALL TASKS HAVE FRESH DATA!")
elif fresh_count >= all_tasks.count() * 0.9:
    print("✅ Most tasks have fresh data (90%+)")
else:
    print("⚠️ Some tasks need attention")

print()
