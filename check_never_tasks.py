#!/usr/bin/env python
"""Check which tasks have never been checked and why"""
import os
import sys
import django

sys.path.insert(0, '/app')
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask
from django.utils import timezone

print("=" * 60)
print("TASKS WITH 'NEVER' LAST CHECK")
print("=" * 60)
print()

tasks = MonitorTask.objects.filter(is_active=True).order_by('id')
print(f"Total active tasks: {tasks.count()}\n")

never_checked = []
recently_checked = []

for task in tasks:
    if task.last_checked is None:
        never_checked.append(task)
    else:
        recently_checked.append(task)

print(f"✅ Tasks that HAVE been checked: {len(recently_checked)}")
print(f"❌ Tasks that have NEVER been checked: {len(never_checked)}")
print()

if never_checked:
    print("=" * 60)
    print("TASKS NEVER CHECKED (Details)")
    print("=" * 60)
    print()
    
    for task in never_checked:
        print(f"Task #{task.id}:")
        print(f"  Date: {task.dates[0] if task.dates else 'N/A'}")
        print(f"  Visitors: {task.visitors}")
        print(f"  Ticket Type: {task.ticket_type} ({'Standard' if task.ticket_type == 0 else 'Guided'})")
        print(f"  Ticket ID: {task.ticket_id or 'None (needs resolution)'}")
        print(f"  Ticket Name: {task.ticket_name or 'N/A'}")
        print(f"  Language: {task.language or 'None'}")
        print(f"  Check Interval: {task.check_interval}s")
        print(f"  Created: {task.created_at}")
        print(f"  Last Checked: Never")
        print(f"  Status: {task.last_status}")
        print()
        
        # Analyze why it might not be checked
        print("  Possible reasons:")
        if not task.ticket_id:
            print("    ⚠️  No ticket_id - needs ID resolution first")
        if not task.dates:
            print("    ⚠️  No dates configured")
        if task.check_interval and task.check_interval > 300:
            print(f"    ⚠️  Long check interval ({task.check_interval}s)")
        
        # Check if it's too new
        age_seconds = (timezone.now() - task.created_at).total_seconds()
        if age_seconds < 120:
            print(f"    ℹ️  Task is very new ({int(age_seconds)}s old) - may not have been checked yet")
        
        print()

if recently_checked:
    print("=" * 60)
    print("RECENTLY CHECKED TASKS (Sample)")
    print("=" * 60)
    print()
    
    for task in recently_checked[:5]:
        age = timezone.now() - task.last_checked
        age_str = f"{int(age.total_seconds() / 60)} minutes ago" if age.total_seconds() < 3600 else f"{int(age.total_seconds() / 3600)} hours ago"
        
        print(f"Task #{task.id}: {task.dates[0] if task.dates else 'N/A'}")
        print(f"  Last checked: {age_str}")
        print(f"  Status: {task.last_status}")
        print(f"  Ticket ID: {task.ticket_id or 'None'}")
        print()

print("=" * 60)
print("ORCHESTRATION STATUS")
print("=" * 60)
print()

# Check if orchestration is running
from django_celery_beat.models import PeriodicTask
try:
    orchestrate_task = PeriodicTask.objects.filter(name__icontains='orchestrate').first()
    if orchestrate_task:
        print(f"✅ Orchestration task found: {orchestrate_task.name}")
        print(f"   Enabled: {orchestrate_task.enabled}")
        print(f"   Interval: {orchestrate_task.interval}")
        print(f"   Last run: {orchestrate_task.last_run_at or 'Never'}")
    else:
        print("⚠️  No orchestration task found in beat schedule")
except Exception as e:
    print(f"⚠️  Could not check beat schedule: {e}")

print()
print("=" * 60)
print("RECOMMENDATIONS")
print("=" * 60)
print()

if never_checked:
    print("For tasks that have never been checked:")
    print()
    print("1. Wait 2-3 minutes - new tasks need time to be picked up")
    print("2. Check worker logs: docker-compose logs -f worker_vatican")
    print("3. Verify orchestration is running: docker-compose logs beat")
    print("4. Force a check manually if needed")
    print()
    
    # Show tasks that need ID resolution
    needs_id = [t for t in never_checked if not t.ticket_id]
    if needs_id:
        print(f"⚠️  {len(needs_id)} task(s) need ticket ID resolution:")
        for t in needs_id:
            print(f"   Task #{t.id} - {t.dates[0] if t.dates else 'N/A'}")
        print()
        print("   These will be resolved automatically on first check")
        print("   via the resolve_and_check_task() function")
        print()
else:
    print("✅ All tasks have been checked at least once!")
    print()

print("Done!")
