"""
Bulk add multiple dates for monitoring
"""
import sys
import os
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask, Agency

def add_multiple_dates(dates_list, visitors=1):
    """
    Add multiple dates for monitoring
    
    Args:
        dates_list: List of dates in YYYY-MM-DD format
        visitors: Number of visitors (default: 1)
    """
    
    # Get the admin agency
    agency = Agency.objects.filter(name="Agency-admin").first()
    
    if not agency:
        print("❌ Agency-admin not found!")
        return
    
    print(f"\n{'='*80}")
    print(f"ADDING {len(dates_list)} DATES FOR MONITORING")
    print(f"{'='*80}\n")
    
    created_tasks = []
    
    for date in dates_list:
        # Check if task already exists for this date
        existing = MonitorTask.objects.filter(
            agency=agency,
            site='vatican',
            dates__contains=[date],
            visitors=visitors
        ).first()
        
        if existing:
            print(f"⏭️  {date} - Already exists (Task {existing.id})")
            continue
        
        # Create new task
        task = MonitorTask.objects.create(
            agency=agency,
            site='vatican',
            area_name='Musei Vaticani',
            dates=[date],
            preferred_times=['09:00', '10:00', '11:00', '14:00', '15:00'],
            visitors=visitors,
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
        
        created_tasks.append(task)
        print(f"✅ {date} - Created (Task {task.id})")
    
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Created: {len(created_tasks)} new tasks")
    print(f"Skipped: {len(dates_list) - len(created_tasks)} existing tasks")
    print(f"Total: {len(dates_list)} dates")
    print(f"\nThe bot will start checking these dates within 60 seconds.")
    print(f"Monitor progress: docker-compose logs -f worker_vatican")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    # Example: Add dates for April-May 2026
    example_dates = [
        # April 2026
        '2026-04-01', '2026-04-02', '2026-04-03', '2026-04-05',
        '2026-04-06', '2026-04-07', '2026-04-08', '2026-04-09',
        '2026-04-10', '2026-04-11', '2026-04-12', '2026-04-13',
        '2026-04-14', '2026-04-16', '2026-04-17', '2026-04-18',
        '2026-04-19', '2026-04-20', '2026-04-21', '2026-04-23',
        '2026-04-24', '2026-04-25', '2026-04-26', '2026-04-27',
        '2026-04-28', '2026-04-29', '2026-04-30',
        # May 2026
        '2026-05-01', '2026-05-02', '2026-05-03', '2026-05-04',
        '2026-05-05', '2026-05-06', '2026-05-07', '2026-05-08'
    ]
    
    print("\n📋 EXAMPLE USAGE:")
    print("   This script can add up to 35 dates at once.")
    print("   Edit the 'example_dates' list above to customize.\n")
    
    # Uncomment to run:
    # add_multiple_dates(example_dates, visitors=1)
    
    print("⚠️  Script is in DEMO mode. Edit the file to add your dates.\n")
