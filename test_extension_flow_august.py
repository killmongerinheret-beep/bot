#!/usr/bin/env python3
"""
Test Extension Flow - Create Test Slots for August
===================================================
Creates fake available slots in the database so you can test the extension
without waiting for real Vatican tickets.

Usage:
    python test_extension_flow_august.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import Agency, MonitorTask, BuyerProfile
from django.utils import timezone
from datetime import datetime, timedelta
import json

def create_test_agency():
    """Create or get test agency"""
    # Check if google_sheet_url field exists
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(monitors_agency)")
        columns = [row[1] for row in cursor.fetchall()]
        has_google_sheet_url = 'google_sheet_url' in columns
    
    defaults = {
        'api_key': 'test-key-123',
        'plan': 'pro',
        'is_active': True,
        'telegram_chat_id': '123456789'  # Replace with your test chat ID
    }
    
    # Only add google_sheet_url if column exists
    if has_google_sheet_url:
        defaults['google_sheet_url'] = 'https://docs.google.com/spreadsheets/d/TEST_SHEET/edit'
    
    agency, created = Agency.objects.get_or_create(
        name="Test Agency",
        defaults=defaults
    )
    
    if created:
        print(f"✅ Created test agency: {agency.name} (ID: {agency.id})")
    else:
        print(f"✅ Using existing test agency: {agency.name} (ID: {agency.id})")
    
    return agency


def create_test_buyer_profile(agency):
    """Create or get test buyer profile with participants"""
    profile, created = BuyerProfile.objects.get_or_create(
        agency=agency,
        defaults={
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '+39 123456789',
            'country': 'Italia',
            'city': 'Roma',
            'birth_date': '1990-01-15',
            'gender': 'M',
            'language': 'en',
            'participants_json': json.dumps([
                {
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'email': 'john.doe@example.com',
                    'phone': '+39 123456789',
                    'birth_date': '1990-01-15'
                },
                {
                    'first_name': 'Jane',
                    'last_name': 'Doe',
                    'email': 'jane.doe@example.com',
                    'phone': '+39 987654321',
                    'birth_date': '1992-03-20'
                }
            ])
        }
    )
    
    if created:
        print(f"✅ Created test buyer profile: {profile.first_name} {profile.last_name}")
    else:
        print(f"✅ Using existing buyer profile: {profile.first_name} {profile.last_name}")
    
    return profile


def create_test_tasks(agency, num_tasks=5):
    """Create test monitoring tasks for August"""
    print(f"\n📋 Creating {num_tasks} test tasks for August...")
    
    # Start from August 1, 2026
    base_date = datetime(2026, 8, 1)
    
    tasks = []
    for i in range(num_tasks):
        date = base_date + timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')  # Use YYYY-MM-DD format for dates JSON field
        
        # Check if task already exists (by ticket_name containing TEST)
        existing_tasks = MonitorTask.objects.filter(
            agency=agency,
            ticket_name__icontains='TEST'
        )
        
        # Check if any existing task has this date
        existing = None
        for task in existing_tasks:
            if date_str in task.dates:
                existing = task
                break
        
        if existing:
            print(f"   ⏭️  Task already exists: {date_str} (ID: {existing.id})")
            tasks.append(existing)
            continue
        
        task = MonitorTask.objects.create(
            agency=agency,
            site='vatican',
            area_name='Vatican Museums',
            dates=[date_str],  # JSON array of dates
            preferred_times=['09:00', '10:00', '14:00'],
            visitors=2,
            adult_count=2,
            child_count=0,
            ticket_type=0,  # Standard ticket
            ticket_name=f'TEST - Vatican Museums - Standard Entry {i+1}',
            ticket_id=None,  # Will be resolved dynamically
            language=None,
            check_interval=60,
            tier='snipe',
            match_strategy='any',
            notification_mode='available_only',
            is_active=True
        )
        
        print(f"   ✅ Created task {i+1}: {date_str} (ID: {task.id})")
        tasks.append(task)
    
    return tasks



def create_test_available_slots(tasks):
    """Create fake available slots for testing extension"""
    from monitors.models import HeldSlot
    
    print(f"\n🎫 Creating test available slots...")
    
    slots = []
    for i, task in enumerate(tasks):
        # Create 2-3 slots per task
        num_slots = 2 if i % 2 == 0 else 3
        
        for j in range(num_slots):
            time = f"{9 + j:02d}:00"
            
            # Check if slot already exists
            existing = HeldSlot.objects.filter(
                task=task,
                date=task.dates[0],
                slot_time=time,
                status='held'
            ).first()
            
            if existing:
                print(f"   ⏭️  Slot already exists: {task.dates[0]} {time}")
                slots.append(existing)
                continue
            
            slot = HeldSlot.objects.create(
                task=task,
                date=task.dates[0],
                slot_id=f"2026*{8000 + i * 10 + j}",
                slot_time=time,
                ticket_id='2129030053',  # Fake ticket ID
                ticket_name='Vatican Museums - Standard Entry',
                visitors=task.visitors,
                adult_count=task.adult_count,
                child_count=task.child_count,
                total_price=34.00,
                jsessionid='TEST_SESSION_' + str(i),
                ticketmv='TEST_TICKET_' + str(i),
                recap_id=f'2026/{8000 + i}/{j}',
                status='held',
                hold_started_at=timezone.now(),
                last_keepalive_at=timezone.now(),
                payment_ready=False,
                notes=json.dumps({
                    'test': True,
                    'created_by': 'test_script',
                    'serverid': 'TEST_SERVER'
                })
            )
            
            print(f"   ✅ Created slot: {task.dates[0]} {time} (ID: {slot.id})")
            slots.append(slot)
    
    return slots


def print_summary(agency, tasks, slots):
    """Print test setup summary"""
    print("\n" + "="*80)
    print("🎉 TEST SETUP COMPLETE!")
    print("="*80)
    
    print(f"\n📊 Summary:")
    print(f"   Agency: {agency.name} (ID: {agency.id})")
    print(f"   Tasks: {len(tasks)}")
    print(f"   Available Slots: {len(slots)}")
    
    print(f"\n📅 Test Dates:")
    for task in tasks:
        task_slots = [s for s in slots if s.task == task]
        times = [s.slot_time for s in task_slots]
        print(f"   {task.dates[0]}: {len(task_slots)} slots at {', '.join(times)}")
    
    print(f"\n🔧 Extension Configuration:")
    print(f"   Backend URL: http://localhost:8000")
    print(f"   Agency ID: {agency.id}")
    print(f"   Backend Listener: ON")
    
    print(f"\n🧪 Testing Steps:")
    print(f"   1. Configure extension with Agency ID: {agency.id}")
    print(f"   2. Enable Backend Listener Mode")
    print(f"   3. Extension will detect {len(slots)} available slots")
    print(f"   4. Extension will open {min(len(slots), 10)} incognito windows")
    print(f"   5. Watch the magic happen! 🎉")
    
    print(f"\n📝 API Endpoint to Test:")
    print(f"   GET http://localhost:8000/api/v1/available-slots/?agency_id={agency.id}")
    
    print(f"\n🗑️  To Clean Up After Testing:")
    print(f"   python test_extension_flow_august.py --cleanup")
    
    print("\n" + "="*80)


def cleanup_test_data():
    """Clean up test data"""
    print("\n🗑️  Cleaning up test data...")
    
    # Delete test agency and all related data
    test_agency = Agency.objects.filter(name="Test Agency").first()
    
    if not test_agency:
        print("   ℹ️  No test agency found")
        return
    
    # Count related objects
    tasks = MonitorTask.objects.filter(agency=test_agency)
    slots = HeldSlot.objects.filter(task__agency=test_agency)
    profile = BuyerProfile.objects.filter(agency=test_agency)
    
    print(f"   Found:")
    print(f"   - {tasks.count()} tasks")
    print(f"   - {slots.count()} slots")
    print(f"   - {profile.count()} buyer profiles")
    
    # Delete
    slots.delete()
    tasks.delete()
    profile.delete()
    test_agency.delete()
    
    print(f"   ✅ Cleaned up all test data")


def main():
    """Main function"""
    import sys
    
    # Check for cleanup flag
    if '--cleanup' in sys.argv:
        cleanup_test_data()
        return
    
    print("="*80)
    print("🧪 TEST EXTENSION FLOW - AUGUST SLOTS")
    print("="*80)
    
    # Create test data
    agency = create_test_agency()
    profile = create_test_buyer_profile(agency)
    tasks = create_test_tasks(agency, num_tasks=5)
    slots = create_test_available_slots(tasks)
    
    # Print summary
    print_summary(agency, tasks, slots)


if __name__ == '__main__':
    main()
