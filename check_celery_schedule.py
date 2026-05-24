#!/usr/bin/env python3
"""Check Celery beat schedule"""

import os
import sys
import django

sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django_celery_beat.models import PeriodicTask

print("=" * 60)
print("CELERY BEAT SCHEDULE")
print("=" * 60)

tasks = PeriodicTask.objects.all()
print(f"\nTotal scheduled tasks: {tasks.count()}")

enabled_tasks = tasks.filter(enabled=True)
print(f"Enabled tasks: {enabled_tasks.count()}")

print("\n📋 SCHEDULED TASKS:")
for task in enabled_tasks:
    print(f"\n  {task.name}:")
    print(f"    Task: {task.task}")
    print(f"    Enabled: {task.enabled}")
    print(f"    Interval: {task.interval or task.crontab or 'N/A'}")
    print(f"    Last run: {task.last_run_at or 'Never'}")

print("\n" + "=" * 60)
