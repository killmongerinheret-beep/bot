"""
Check if tasks have last_result_summary with slots for Telegram display
"""
import os
import sys
import django
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask

# Get all active Vatican tasks
tasks = MonitorTask.objects.filter(site='vatican', is_active=True).order_by('-last_checked')

print(f"\n{'='*80}")
print(f"TELEGRAM SLOT DISPLAY CHECK")
print(f"{'='*80}\n")

for task in tasks[:10]:  # Check first 10 tasks
    print(f"Task #{task.id}")
    print(f"  Date: {task.dates[0] if task.dates else 'N/A'}")
    print(f"  Visitors: {task.visitors}")
    print(f"  Ticket: {task.ticket_label or task.ticket_name}")
    print(f"  Status: {task.last_status}")
    print(f"  Last Checked: {task.last_checked}")
    
    # Check last_result_summary
    if task.last_result_summary:
        try:
            summary = json.loads(task.last_result_summary)
            print(f"  ✅ Has last_result_summary")
            
            # Check for slots
            if 'updates' in summary:
                total_slots = 0
                for date_key, items in summary['updates'].items():
                    for item in items:
                        if 'slots' in item:
                            slots = item['slots']
                            total_slots += len(slots)
                            print(f"     Date: {date_key}")
                            print(f"     Slots: {slots[:5]}{'...' if len(slots) > 5 else ''} ({len(slots)} total)")
                
                if total_slots == 0:
                    print(f"  ⚠️ Summary exists but NO SLOTS found")
            else:
                print(f"  ⚠️ Summary exists but no 'updates' key")
                print(f"     Keys: {list(summary.keys())}")
        except Exception as e:
            print(f"  ❌ Error parsing summary: {e}")
    else:
        print(f"  ❌ NO last_result_summary")
    
    print()

print(f"\n{'='*80}\n")
