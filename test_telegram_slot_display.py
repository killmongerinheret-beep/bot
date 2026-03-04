"""
Test how Telegram bot would display slots for tasks
"""
import os
import sys
import django
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask

# Get tasks with last_result_summary
tasks = MonitorTask.objects.filter(
    site='vatican',
    is_active=True,
    last_result_summary__isnull=False
).order_by('-last_checked')[:5]

print(f"\n{'='*80}")
print(f"TELEGRAM BOT SLOT DISPLAY SIMULATION")
print(f"{'='*80}\n")

for task in tasks:
    date = task.dates[0] if task.dates else 'N/A'
    status_emoji = "✅" if task.last_status == 'available' else "❌" if task.last_status == 'sold_out' else "⏳"
    
    # Get available slots from last_result_summary
    slots_info = ""
    if task.last_result_summary:
        try:
            summary = json.loads(task.last_result_summary)
            if 'updates' in summary:
                for date_key, items in summary['updates'].items():
                    for item in items:
                        if item.get('slots'):
                            slots = item['slots']
                            
                            # Show first 5 slots
                            slots_display = slots[:5]
                            slots_str = ', '.join(slots_display)
                            if len(slots) > 5:
                                slots_str += f" (+{len(slots)-5} more)"
                            slots_info = f"\n   Slots: {slots_str}"
                            break
        except Exception as e:
            slots_info = f"\n   Error: {e}"
    
    message = (
        f"{status_emoji} Task #{task.id}\n"
        f"   Date: {date}\n"
        f"   Visitors: {task.visitors}\n"
        f"   Ticket: {task.ticket_label or 'Standard'}\n"
        f"   Status: {task.last_status}{slots_info}\n"
        f"   Last Check: {task.last_checked.strftime('%H:%M') if task.last_checked else 'Never'}\n"
    )
    
    print(message)

print(f"{'='*80}\n")
