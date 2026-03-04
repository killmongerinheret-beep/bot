"""
Force a fresh check on a task and verify slots are saved
"""
import os
import sys
import django
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask
from monitors.tasks import run_god_tier_vatican_monitor

# Get a task with available status
task = MonitorTask.objects.filter(
    site='vatican',
    is_active=True,
    last_status='available'
).first()

if not task:
    print("No available tasks found")
    sys.exit(1)

print(f"\n{'='*80}")
print(f"FORCING CHECK ON TASK #{task.id}")
print(f"{'='*80}\n")
print(f"Date: {task.dates[0] if task.dates else 'N/A'}")
print(f"Visitors: {task.visitors}")
print(f"Ticket: {task.ticket_name}")
print(f"Status: {task.last_status}")
print(f"\nBEFORE CHECK:")
print(f"  last_result_summary: {task.last_result_summary[:100] if task.last_result_summary else 'None'}")

# Force a check
print(f"\n🔄 Running check...")
result = run_god_tier_vatican_monitor(
    date=task.dates[0],
    ticket_id=task.ticket_id,
    ticket_name=task.ticket_name,
    language=task.language,
    task_ids=[task.id],
    visitors=task.visitors,
    use_browser_fallback=True
)

print(f"✅ Check result: {result}")

# Wait a moment for DB to update
time.sleep(2)

# Refresh from DB
task.refresh_from_db()

print(f"\nAFTER CHECK:")
print(f"  last_checked: {task.last_checked}")
print(f"  last_status: {task.last_status}")
print(f"  last_result_summary: {task.last_result_summary[:200] if task.last_result_summary else 'None'}")

if task.last_result_summary:
    try:
        summary = json.loads(task.last_result_summary)
        print(f"\n✅ Summary parsed successfully!")
        print(f"  Keys: {list(summary.keys())}")
        
        if 'updates' in summary:
            for date_key, items in summary['updates'].items():
                print(f"\n  Date: {date_key}")
                for item in items:
                    slots = item.get('slots', [])
                    print(f"    Ticket: {item.get('name')}")
                    print(f"    Slots: {slots[:10]}{'...' if len(slots) > 10 else ''} ({len(slots)} total)")
    except Exception as e:
        print(f"❌ Error parsing summary: {e}")
else:
    print(f"\n❌ Still no last_result_summary after check!")

print(f"\n{'='*80}\n")
