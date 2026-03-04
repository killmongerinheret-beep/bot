"""
Add a new test date to verify frontend display
"""
import sys
import os
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask, Agency

def add_test_date():
    """Add a new test date (April 15, 2026) to verify frontend"""
    
    # Get the admin agency
    agency = Agency.objects.filter(name="Agency-admin").first()
    
    if not agency:
        print("❌ Agency-admin not found!")
        return
    
    # Create new task for April 15, 2026 (1 visitor)
    task = MonitorTask.objects.create(
        agency=agency,
        site='vatican',
        area_name='Musei Vaticani',
        dates=['2026-04-15'],
        preferred_times=['09:00', '10:00', '11:00'],
        visitors=1,
        ticket_type=0,
        ticket_label='Standard Entry',
        ticket_id=None,  # Will be resolved dynamically
        ticket_name='Musei Vaticani - Biglietti d\'ingresso',
        language=None,
        check_interval=60,
        tier='monitor',
        match_strategy='any',
        notification_mode='available_only',
        is_active=True
    )
    
    print(f"\n{'='*80}")
    print(f"NEW TEST TASK CREATED")
    print(f"{'='*80}")
    print(f"Task ID: {task.id}")
    print(f"Date: 2026-04-15")
    print(f"Visitors: 1")
    print(f"Ticket: {task.ticket_name}")
    print(f"Status: {task.last_status}")
    print(f"\nThe bot will check this task automatically within 60 seconds.")
    print(f"Check the frontend dashboard to see the status update!")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    add_test_date()
