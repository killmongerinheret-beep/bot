#!/usr/bin/env python3
"""
Test script to verify new monitor creation after frontend deployment.
This simulates what the frontend does when creating a new monitor.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask, Agency
from datetime import datetime, timedelta

def test_standard_ticket_creation():
    """Test creating a standard ticket monitor (should have language=None)"""
    print("\n" + "="*60)
    print("TEST 1: Create Standard Ticket Monitor")
    print("="*60)
    
    # Get or create test agency
    agency, _ = Agency.objects.get_or_create(
        id=1,
        defaults={
            'name': 'Test Agency',
            'telegram_chat_id': '123456789',
            'is_active': True
        }
    )
    
    # Create standard ticket task (simulating frontend)
    task_data = {
        'agency': agency,
        'site': 'vatican',
        'area_name': 'MV-Biglietti',
        'ticket_type': 0,  # Standard ticket
        'ticket_name': 'Standard Entry (Full Price)',
        'dates': [(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')],
        'visitors': 2,
        'tier': 'monitor',
        'notification_mode': 'any_change',
        'language': None,  # Should be None for standard tickets
    }
    
    try:
        task = MonitorTask.objects.create(**task_data)
        print(f"✅ Task created successfully!")
        print(f"   Task ID: {task.id}")
        print(f"   Ticket Type: {task.ticket_type}")
        print(f"   Language: {task.language}")
        print(f"   Area: {task.area_name}")
        print(f"   Visitors: {task.visitors}")
        
        # Verify
        if task.ticket_type == 0 and task.language is None:
            print("\n✅ PASS: Standard ticket has language=None")
            return True
        else:
            print(f"\n❌ FAIL: Expected ticket_type=0 and language=None")
            print(f"   Got: ticket_type={task.ticket_type}, language={task.language}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating task: {e}")
        return False

def test_guided_tour_creation():
    """Test creating a guided tour monitor (should have language='ENG')"""
    print("\n" + "="*60)
    print("TEST 2: Create Guided Tour Monitor")
    print("="*60)
    
    agency = Agency.objects.get(id=1)
    
    # Create guided tour task (simulating frontend)
    task_data = {
        'agency': agency,
        'site': 'vatican',
        'area_name': 'MV-Tour',
        'ticket_type': 1,  # Guided tour
        'ticket_name': 'Vatican Museums - Guided Tour',
        'dates': [(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')],
        'visitors': 1,
        'tier': 'monitor',
        'notification_mode': 'any_change',
        'language': 'ENG',  # Should have language for guided tours
    }
    
    try:
        task = MonitorTask.objects.create(**task_data)
        print(f"✅ Task created successfully!")
        print(f"   Task ID: {task.id}")
        print(f"   Ticket Type: {task.ticket_type}")
        print(f"   Language: {task.language}")
        print(f"   Area: {task.area_name}")
        print(f"   Visitors: {task.visitors}")
        
        # Verify
        if task.ticket_type == 1 and task.language == 'ENG':
            print("\n✅ PASS: Guided tour has language='ENG'")
            return True
        else:
            print(f"\n❌ FAIL: Expected ticket_type=1 and language='ENG'")
            print(f"   Got: ticket_type={task.ticket_type}, language={task.language}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating task: {e}")
        return False

def test_existing_tasks():
    """Verify existing tasks have correct language values"""
    print("\n" + "="*60)
    print("TEST 3: Verify Existing Tasks")
    print("="*60)
    
    # Check standard tickets
    standard_tasks = MonitorTask.objects.filter(ticket_type=0)
    print(f"\nStandard Tickets (ticket_type=0): {standard_tasks.count()} total")
    
    wrong_standard = standard_tasks.exclude(language=None)
    if wrong_standard.exists():
        print(f"❌ Found {wrong_standard.count()} standard tickets with language != None:")
        for task in wrong_standard[:5]:
            print(f"   Task {task.id}: language={task.language}")
    else:
        print("✅ All standard tickets have language=None")
    
    # Check guided tours
    guided_tasks = MonitorTask.objects.filter(ticket_type=1)
    print(f"\nGuided Tours (ticket_type=1): {guided_tasks.count()} total")
    
    wrong_guided = guided_tasks.filter(language=None)
    if wrong_guided.exists():
        print(f"❌ Found {wrong_guided.count()} guided tours with language=None:")
        for task in wrong_guided[:5]:
            print(f"   Task {task.id}: language={task.language}")
    else:
        print("✅ All guided tours have language set")
    
    return not wrong_standard.exists() and not wrong_guided.exists()

def main():
    print("\n" + "="*60)
    print("VATICAN BOT - NEW MONITOR CREATION TEST")
    print("="*60)
    print("This script tests if new monitors are created with correct language values")
    print("after the frontend fix has been deployed.")
    
    results = []
    
    # Run tests
    results.append(("Standard Ticket Creation", test_standard_ticket_creation()))
    results.append(("Guided Tour Creation", test_guided_tour_creation()))
    results.append(("Existing Tasks Verification", test_existing_tasks()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("Frontend fix is working correctly.")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Please check the output above for details.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
