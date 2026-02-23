import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json

def update_schedule():
    # 1. Create Interval (every 30 seconds)
    schedule, created = IntervalSchedule.objects.get_or_create(
        every=30,
        period=IntervalSchedule.SECONDS,
    )

    # 2. Update Periodic Task to the CORRECT orchestrator name
    # The name in @shared_task is "orchestrate_all_tasks"
    task_name = 'orchestrate_all_tasks'
    
    PeriodicTask.objects.update_or_create(
        name='Vatican Monitor (Every 30s)',
        defaults={
            'interval': schedule,
            'task': task_name,
            'args': json.dumps([]),
            'enabled': True
        }
    )
    
    # Remove the old broken one if it exists with different name
    PeriodicTask.objects.filter(task='monitors.tasks.monitor_vatican_availability').delete()
    
    print(f"✅ Schedule updated: {task_name} (Every 30s)")

if __name__ == '__main__':
    update_schedule()
