import os
import django

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json

# 1. Setup Periodic Orchestration (Run every 1 minute)
schedule, created = IntervalSchedule.objects.get_or_create(
    every=1,
    period=IntervalSchedule.MINUTES,
)

pt, created = PeriodicTask.objects.get_or_create(
    interval=schedule,
    name='Orchestrate Monitoring',
    task='orchestrate_all_tasks', # The @shared_task name
)

print(f"DEBUG: Periodic Task {'created' if created else 'already exists'}")

# 1.1 Session Refreshers (10 Minutes)
schedule_10m, _ = IntervalSchedule.objects.get_or_create(
    every=10, period=IntervalSchedule.MINUTES
)

PeriodicTask.objects.get_or_create(
    interval=schedule_10m,
    name='Refresh Colosseum Session',
    task='refresh_colosseum_session',
)

PeriodicTask.objects.get_or_create(
    interval=schedule_10m,
    name='Refresh Vatican Session',
    task='refresh_vatican_session',
)

# 1.2 Data Cleanup (Daily)
schedule_1d, _ = IntervalSchedule.objects.get_or_create(
    every=1, period=IntervalSchedule.DAYS
)

PeriodicTask.objects.get_or_create(
    interval=schedule_1d,
    name='Cleanup Old Results',
    task='cleanup_old_results',
)

# 2. Check Active Tasks
active_tasks = MonitorTask.objects.filter(is_active=True).count()
print(f"DEBUG: Active monitoring tasks in DB: {active_tasks}")

if active_tasks == 0:
    print("WARNING: No active tasks found! Please add a monitor task on the dashboard.")

# 3. List existing periodic tasks
all_pts = list(PeriodicTask.objects.values('name', 'task', 'enabled'))
print(f"DEBUG: All registered background jobs: {all_pts}")
