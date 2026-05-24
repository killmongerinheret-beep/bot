#!/usr/bin/env python3
"""Check system status - proxies, tasks, notifications"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import Proxy, MonitorTask
from django.utils import timezone
from datetime import timedelta

print("=" * 60)
print("SYSTEM STATUS CHECK")
print("=" * 60)

# Check proxies
print("\n📡 PROXY STATUS:")
total_proxies = Proxy.objects.count()
active_proxies = Proxy.objects.filter(is_active=True).count()
on_cooldown = Proxy.objects.filter(cooldown_until__gt=timezone.now()).count()
high_failures = Proxy.objects.filter(consecutive_failures__gte=3).count()

print(f"  Total proxies: {total_proxies}")
print(f"  Active proxies: {active_proxies}")
print(f"  On cooldown: {on_cooldown}")
print(f"  High failures (≥3): {high_failures}")

if total_proxies == 0:
    print("  ⚠️  WARNING: NO PROXIES CONFIGURED!")
    print("  → Run add_proxies.py to add proxies")
else:
    # Show some proxy details
    print("\n  Sample proxies:")
    for proxy in Proxy.objects.filter(is_active=True)[:3]:
        status = "⏳ Cooldown" if proxy.cooldown_until and proxy.cooldown_until > timezone.now() else "✅ Ready"
        print(f"    {proxy.ip_port} - {status} (failures: {proxy.consecutive_failures})")

# Check monitoring tasks
print("\n📋 MONITORING TASKS:")
total_tasks = MonitorTask.objects.filter(is_active=True).count()
vatican_tasks = MonitorTask.objects.filter(
    is_active=True, 
    agency__name__icontains='vatican'
).count()

print(f"  Total active tasks: {total_tasks}")
print(f"  Vatican tasks: {vatican_tasks}")

# Check recent check results
print("\n🔔 RECENT CHECK RESULTS:")
from monitors.models import CheckResult

recent_24h = timezone.now() - timedelta(hours=24)
recent_48h = timezone.now() - timedelta(hours=48)

results_24h = CheckResult.objects.filter(check_time__gte=recent_24h)
results_48h = CheckResult.objects.filter(check_time__gte=recent_48h)
available_24h = results_24h.filter(status='available')

print(f"  Total checks (24h): {results_24h.count()}")
print(f"  Available found (24h): {available_24h.count()}")
print(f"  Total checks (48h): {results_48h.count()}")

if available_24h.count() > 0:
    print("\n  Recent available slots:")
    for result in available_24h[:5]:
        task = result.task
        print(f"    - Task #{task.id}: {task.area_name} | {result.check_time}")
else:
    print("  ⚠️  No available slots found in last 24 hours")
    
# Check last check times
print("\n📊 LAST CHECK TIMES:")
recent_checks = MonitorTask.objects.filter(
    is_active=True,
    last_checked__isnull=False
).order_by('-last_checked')[:5]

if recent_checks.exists():
    for task in recent_checks:
        print(f"    Task #{task.id}: {task.area_name} - {task.last_checked}")
else:
    print("  ⚠️  No tasks have been checked yet")

# Check task status
print("\n📊 VATICAN TASK DETAILS:")
vatican_tasks_obj = MonitorTask.objects.filter(
    is_active=True, 
    agency__name__icontains='vatican'
)[:10]

for task in vatican_tasks_obj:
    dates_str = ', '.join(task.dates[:3]) if task.dates else 'No dates'
    if len(task.dates) > 3:
        dates_str += f" (+{len(task.dates)-3} more)"
    print(f"  Task #{task.id}: {task.area_name} | {dates_str} | {task.visitors}v | Last: {task.last_checked or 'Never'}")

print("\n" + "=" * 60)
