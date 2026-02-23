import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json

def create_schedule():
    # 1. Create Interval (every 30 seconds)
    schedule, created = IntervalSchedule.objects.get_or_create(
        every=30,
        period=IntervalSchedule.SECONDS,
    )

    # 2. Create Periodic Task
    task_name = 'monitors.tasks.monitor_vatican_availability'
    
    # Check if task wrapper exists, if not, maybe it's just 'monitor_vatican_availability' if app label logic
    # But best to stick to explicit path.
    
    PeriodicTask.objects.update_or_create(
        name='Vatican Monitor (Every 30s)',
        defaults={
            'interval': schedule,
            'task': task_name,
            'args': json.dumps([]),
            'enabled': True
        }
    )
    
    print("✅ Schedule created: Vatican Monitor (Every 30s)")
    
    # Also check if we have any tasks in MonitorTask
    from monitors.models import MonitorTask
    count = MonitorTask.objects.filter(is_active=True).count()
    print(f"✅ Found {count} active monitoring tasks waiting in DB.")

if __name__ == '__main__':
    create_schedule()
