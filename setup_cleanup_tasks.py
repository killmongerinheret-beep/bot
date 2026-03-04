#!/usr/bin/env python
"""
Setup periodic cleanup tasks for Vatican bot
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
from django.utils import timezone

def setup_cleanup_tasks():
    """Create or update periodic cleanup tasks"""
    
    print("🔧 Setting up periodic cleanup tasks...")
    
    # 1. Cleanup expired monitor tasks (every 30 minutes)
    interval_30min, _ = IntervalSchedule.objects.get_or_create(
        every=30,
        period=IntervalSchedule.MINUTES,
    )
    
    task1, created = PeriodicTask.objects.get_or_create(
        name='Cleanup Expired Monitor Tasks',
        defaults={
            'task': 'cleanup_expired_monitor_tasks',
            'interval': interval_30min,
            'enabled': True,
        }
    )
    if not created:
        task1.task = 'cleanup_expired_monitor_tasks'
        task1.interval = interval_30min
        task1.crontab = None
        task1.clocked = None
        task1.solar = None
        task1.enabled = True
        task1.save()
    
    print(f"  ✅ Cleanup Expired Monitor Tasks - {'Created' if created else 'Updated'}")
    
    # 2. Cleanup backed-up queues (every hour)
    interval_1hour, _ = IntervalSchedule.objects.get_or_create(
        every=1,
        period=IntervalSchedule.HOURS,
    )
    
    task2, created = PeriodicTask.objects.get_or_create(
        name='Cleanup Backed-Up Queues',
        defaults={
            'task': 'cleanup_backed_up_queues',
            'interval': interval_1hour,
            'enabled': True,
        }
    )
    if not created:
        task2.task = 'cleanup_backed_up_queues'
        task2.interval = interval_1hour
        task2.crontab = None
        task2.clocked = None
        task2.solar = None
        task2.enabled = True
        task2.save()
    
    print(f"  ✅ Cleanup Backed-Up Queues - {'Created' if created else 'Updated'}")
    
    # 3. Cleanup old results (daily at 3 AM)
    crontab_3am, _ = CrontabSchedule.objects.get_or_create(
        minute='0',
        hour='3',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
    )
    
    task3, created = PeriodicTask.objects.get_or_create(
        name='Cleanup Old Results',
        defaults={
            'task': 'cleanup_old_results',
            'crontab': crontab_3am,
            'enabled': True,
        }
    )
    if not created:
        task3.task = 'cleanup_old_results'
        task3.crontab = crontab_3am
        task3.interval = None
        task3.clocked = None
        task3.solar = None
        task3.enabled = True
        task3.save()
    
    print(f"  ✅ Cleanup Old Results - {'Created' if created else 'Updated'}")
    
    print("\n📊 Current Periodic Tasks:")
    for task in PeriodicTask.objects.all():
        schedule = task.interval or task.crontab
        print(f"  • {task.name}")
        print(f"    Task: {task.task}")
        print(f"    Schedule: {schedule}")
        print(f"    Enabled: {task.enabled}")
        print(f"    Last run: {task.last_run_at or 'Never'}")
        print()
    
    print("✅ Setup complete!")

if __name__ == '__main__':
    setup_cleanup_tasks()
