
import os
import django
import sys
import json

# Setup Django
sys.path.append('/app/backend')
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule

def register_tasks():
    print("Registering Periodic Tasks...")
    
    # 1. Orchestration - Every 10 seconds (High Frequency Dispatch)
    # We use Interval for this
    schedule_10s, _ = IntervalSchedule.objects.get_or_create(
        every=10,
        period=IntervalSchedule.SECONDS,
    )
    
    PeriodicTask.objects.update_or_create(
        name='Orchestrate All Monitors',
        defaults={
            'interval': schedule_10s,
            'task': 'orchestrate_all_tasks',
            'enabled': True,
        }
    )
    print("✅ Registered: Orchestrate All Monitors (10s)")

    # 2. Cleanup Expired Tasks - Every Day at Midnight
    # We use Crontab for this
    schedule_midnight, _ = CrontabSchedule.objects.get_or_create(
        minute='0',
        hour='0',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
    )
    
    PeriodicTask.objects.update_or_create(
        name='Cleanup Expired Monitor Tasks',
        defaults={
            'crontab': schedule_midnight,
            'task': 'cleanup_expired_monitor_tasks',
            'enabled': True,
        }
    )
    print("✅ Registered: Cleanup Expired Tasks (Daily)")

    # 3. Cleanup Old Results - Daily at 1 AM
    schedule_1am, _ = CrontabSchedule.objects.get_or_create(
        minute='0',
        hour='1',
    )
    
    PeriodicTask.objects.update_or_create(
        name='Cleanup Old Check Results',
        defaults={
            'crontab': schedule_1am,
            'task': 'cleanup_old_results',
            'enabled': True,
        }
    )
    print("✅ Registered: Cleanup Old Results (Daily 1AM)")
    
    # 4. Session Refreshers - Every 30 mins
    schedule_30m, _ = IntervalSchedule.objects.get_or_create(
        every=30,
        period=IntervalSchedule.MINUTES,
    )
    
    PeriodicTask.objects.update_or_create(
        name='Refresh Vatican Session',
        defaults={
            'interval': schedule_30m,
            'task': 'refresh_vatican_session',
            'enabled': True,
        }
    )
    
    PeriodicTask.objects.update_or_create(
        name='Refresh Colosseum Session',
        defaults={
            'interval': schedule_30m,
            'task': 'refresh_colosseum_session',
            'enabled': True,
        }
    )
    print("✅ Registered: Session Refreshers (30m)")

if __name__ == '__main__':
    register_tasks()
