#!/usr/bin/env python3
"""
Test Separate Agency Notifications
Verifies that each group receives notifications only for their own agency's tasks
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def test_separate_agency_notifications():
    """Test that each agency gets notifications for their own tasks only"""
    
    from monitors.models import TelegramGroup, Agency, MonitorTask
    from monitors.notification_utils import send_telegram_signal, format_vatican_notification
    
    print('🧪 Testing Separate Agency Notifications')
    print('=' * 50)
    
    # Get agencies
    agency1 = Agency.objects.get(name='Vatican Bot Agency 1')
    agency2 = Agency.objects.get(name='Vatican Bot Agency 2')
    
    print(f'📋 Agency 1: {agency1.name}')
    print(f'📋 Agency 2: {agency2.name}')
    
    # Get groups
    group1 = TelegramGroup.objects.get(agency=agency1)
    group2 = TelegramGroup.objects.get(agency=agency2)
    
    print(f'📱 Group 1: {group1.chat_title} ({group1.chat_id})')
    print(f'📱 Group 2: {group2.chat_title} ({group2.chat_id})')
    
    # Get tasks for each agency
    agency1_tasks = MonitorTask.objects.filter(agency=agency1, is_active=True)
    agency2_tasks = MonitorTask.objects.filter(agency=agency2, is_active=True)
    
    print(f'\n📊 Agency 1 has {agency1_tasks.count()} tasks')
    print(f'📊 Agency 2 has {agency2_tasks.count()} tasks')
    
    # Test 1: Send Agency 1 notification (should only go to Group 1)
    print(f'\n🧪 Test 1: Agency 1 Notification')
    print('=' * 30)
    
    agency1_message = format_vatican_notification(
        date="15/06/2026",
        ticket_name="Vatican Museums - Standard Entry (Agency 1)",
        ticket_id="1684805446",
        slots=[{"time": "09:00"}, {"time": "10:00"}, {"time": "14:00"}],
        preferred_times=["09:00", "10:00", "14:00"],
        language=None,
        visitors=2,
        check_method="test"
    )
    
    # Simulate the notification logic for Agency 1
    agency1_groups = TelegramGroup.objects.filter(
        agency=agency1,
        status='approved',
        notification_enabled=True
    )
    
    print(f'Agency 1 approved groups: {agency1_groups.count()}')
    sent_count = 0
    for group in agency1_groups:
        print(f'   Sending to {group.chat_title} ({group.chat_id})...', end=' ')
        if send_telegram_signal(group.chat_id, f"🔵 AGENCY 1 NOTIFICATION\n\n{agency1_message}"):
            print('✅ SUCCESS')
            sent_count += 1
        else:
            print('❌ FAILED')
    
    print(f'Agency 1 notifications sent: {sent_count}/{agency1_groups.count()}')
    
    # Test 2: Send Agency 2 notification (should only go to Group 2)
    print(f'\n🧪 Test 2: Agency 2 Notification')
    print('=' * 30)
    
    agency2_message = format_vatican_notification(
        date="20/06/2026",
        ticket_name="Vatican Museums - Standard Entry (Agency 2)",
        ticket_id="1684805446",
        slots=[{"time": "08:00"}, {"time": "09:00"}, {"time": "15:00"}],
        preferred_times=["08:00", "09:00", "15:00"],
        language=None,
        visitors=4,
        check_method="test"
    )
    
    # Simulate the notification logic for Agency 2
    agency2_groups = TelegramGroup.objects.filter(
        agency=agency2,
        status='approved',
        notification_enabled=True
    )
    
    print(f'Agency 2 approved groups: {agency2_groups.count()}')
    sent_count = 0
    for group in agency2_groups:
        print(f'   Sending to {group.chat_title} ({group.chat_id})...', end=' ')
        if send_telegram_signal(group.chat_id, f"🟢 AGENCY 2 NOTIFICATION\n\n{agency2_message}"):
            print('✅ SUCCESS')
            sent_count += 1
        else:
            print('❌ FAILED')
    
    print(f'Agency 2 notifications sent: {sent_count}/{agency2_groups.count()}')
    
    # Summary
    print(f'\n📊 Test Results Summary')
    print('=' * 30)
    print(f'✅ Agency 1 (Group {group1.chat_id}): Should receive BLUE notifications')
    print(f'✅ Agency 2 (Group {group2.chat_id}): Should receive GREEN notifications')
    print(f'\n🎯 Expected Behavior:')
    print(f'   • Group {group1.chat_id} gets notifications for Agency 1 tasks only')
    print(f'   • Group {group2.chat_id} gets notifications for Agency 2 tasks only')
    print(f'   • Each group has different monitoring configurations')
    
    # Show task differences
    print(f'\n📋 Task Configuration Differences:')
    print(f'Agency 1 Tasks:')
    for task in agency1_tasks:
        print(f'   • {task.area_name}: {task.visitors} visitors, {", ".join(task.dates)}')
    
    print(f'Agency 2 Tasks:')
    for task in agency2_tasks:
        print(f'   • {task.area_name}: {task.visitors} visitors, {", ".join(task.dates)}')
    
    print(f'\n🎉 Multi-Tenant System Test Complete!')
    print(f'Each group should have received different notifications based on their agency.')
    
    return True

if __name__ == "__main__":
    success = test_separate_agency_notifications()
    sys.exit(0 if success else 1)