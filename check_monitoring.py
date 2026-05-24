#!/usr/bin/env python3
"""Check if monitoring is running"""

import os
import sys
import django

sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask
from django.utils import timezone
from datetime import timedelta

print("=" * 60)
print("MONITORING STATUS CHECK")
print("=" * 60)

# Check Vatican tasks
vatican_tasks = MonitorTask.objects.filter(is_active=True, site='vatican')
print(f"\n✅ Active Vatican tasks: {vatican_tasks.count()}")

if vatican_tasks.exists():
    for task in vatican_tasks[:3]:
        dates_count = len(task.dates) if task.dates else 0
        print(f"\nTask #{task.id}:")
        print(f"  Area: {task.area_name}")
        print(f"  Dates: {dates_count} dates")
        print(f"  Visitors: {task.visitors}")
        print(f"  Tier: {task.tier}")
        print(f"  Check interval: {task.check_interval}s")
        print(f"  Last checked: {task.last_checked or 'Never'}")
        
        # Check if it's been checked recently
        if task.last_checked:
            time_since = timezone.now() - task.last_checked
            minutes_ago = int(time_since.total_seconds() / 60)
            print(f"  Time since last check: {minutes_ago} minutes ago")
            
            if minutes_ago > 60:
                print(f"  ⚠️ WARNING: Not checked in over 1 hour!")

# Check if any checks are happening
recent_checks = MonitorTask.objects.filter(
    is_active=True,
    last_checked__gte=timezone.now() - timedelta(minutes=10)
)

print(f"\n📊 Tasks checked in last 10 minutes: {recent_checks.count()}")

if recent_checks.count() == 0:
    print("\n⚠️ WARNING: NO MONITORING ACTIVITY IN LAST 10 MINUTES!")
    print("   Possible causes:")
    print("   1. Celery beat not running")
    print("   2. Celery worker not running")
    print("   3. All tasks paused/inactive")
    print("   4. Redis connection issues")

print("\n" + "=" * 60)
