#!/usr/bin/env python3
"""
Setup Multi-Tenant System
Creates separate agencies for each Telegram group
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def setup_multi_tenant():
    """Setup multi-tenant system with separate agencies"""
    
    from monitors.models import TelegramGroup, Agency, MonitorTask
    from django.utils import timezone
    
    print('🏗️ Setting up Multi-Tenant System')
    print('=' * 40)
    
    # Create separate agencies for each group
    agency1, created1 = Agency.objects.get_or_create(
        name='Vatican Bot Agency 1',
        defaults={
            'api_key': 'agency1_key',
            'telegram_chat_id': '-5077577076',
            'owner_id': 'user1',
            'plan': 'pro',
            'is_active': True
        }
    )
    print(f'Agency 1: {agency1.name} - {"Created" if created1 else "Updated"}')
    
    agency2, created2 = Agency.objects.get_or_create(
        name='Vatican Bot Agency 2', 
        defaults={
            'api_key': 'agency2_key',
            'telegram_chat_id': '-5245239270',
            'owner_id': 'user2',
            'plan': 'pro',
            'is_active': True
        }
    )
    print(f'Agency 2: {agency2.name} - {"Created" if created2 else "Updated"}')
    
    # Update groups to link to their respective agencies
    try:
        group1 = TelegramGroup.objects.get(chat_id='-5077577076')
        group1.agency = agency1
        group1.status = 'approved'
        group1.save()
        print(f'✅ Group 1 ({group1.chat_id}) linked to {agency1.name}')
    except TelegramGroup.DoesNotExist:
        print('❌ Group 1 not found')
    
    try:
        group2 = TelegramGroup.objects.get(chat_id='-5245239270')
        group2.agency = agency2
        group2.status = 'approved'
        group2.save()
        print(f'✅ Group 2 ({group2.chat_id}) linked to {agency2.name}')
    except TelegramGroup.DoesNotExist:
        print('❌ Group 2 not found')
    
    # Create different monitoring tasks for each agency
    print('\n📋 Creating Different Monitoring Tasks for Each Agency')
    
    # Agency 1 Tasks - Standard Entry + Guided Tour
    task1_1, created = MonitorTask.objects.get_or_create(
        agency=agency1,
        site='vatican',
        area_name='Vatican Museums - Standard Entry (Agency 1)',
        defaults={
            'dates': ['15/06/2026', '16/06/2026'],
            'preferred_times': ['09:00', '10:00', '14:00'],
            'visitors': 2,
            'ticket_type': 0,
            'ticket_id': '1684805446',
            'ticket_name': 'Musei Vaticani - Biglietti d\'ingresso',
            'language': None,
            'check_interval': 60,
            'tier': 'monitor',
            'match_strategy': 'any',
            'notification_mode': 'available_only',
            'is_active': True
        }
    )
    print(f'   Task 1.1: {task1_1.area_name} - {"Created" if created else "Exists"}')
    
    task1_2, created = MonitorTask.objects.get_or_create(
        agency=agency1,
        site='vatican',
        area_name='Vatican Museums - Guided Tour ENG (Agency 1)',
        defaults={
            'dates': ['15/06/2026'],
            'preferred_times': ['10:00', '14:00'],
            'visitors': 2,
            'ticket_type': 1,
            'ticket_id': '1594188966',
            'ticket_name': 'Musei Vaticani - Visita Guidata',
            'language': 'ENG',
            'check_interval': 60,
            'tier': 'monitor',
            'match_strategy': 'any',
            'notification_mode': 'available_only',
            'is_active': True
        }
    )
    print(f'   Task 1.2: {task1_2.area_name} - {"Created" if created else "Exists"}')
    
    # Agency 2 Tasks - Different configuration
    task2_1, created = MonitorTask.objects.get_or_create(
        agency=agency2,
        site='vatican',
        area_name='Vatican Museums - Standard Entry (Agency 2)',
        defaults={
            'dates': ['20/06/2026', '21/06/2026', '22/06/2026'],
            'preferred_times': ['08:00', '09:00', '15:00'],
            'visitors': 4,
            'ticket_type': 0,
            'ticket_id': '1684805446',
            'ticket_name': 'Musei Vaticani - Biglietti d\'ingresso',
            'language': None,
            'check_interval': 90,
            'tier': 'monitor',
            'match_strategy': 'any',
            'notification_mode': 'any_change',
            'is_active': True
        }
    )
    print(f'   Task 2.1: {task2_1.area_name} - {"Created" if created else "Exists"}')
    
    task2_2, created = MonitorTask.objects.get_or_create(
        agency=agency2,
        site='vatican',
        area_name='Vatican Museums - Guided Tour ITA (Agency 2)',
        defaults={
            'dates': ['20/06/2026'],
            'preferred_times': ['11:00', '16:00'],
            'visitors': 4,
            'ticket_type': 1,
            'ticket_id': '1594188966',
            'ticket_name': 'Musei Vaticani - Visita Guidata',
            'language': 'ITA',
            'check_interval': 90,
            'tier': 'monitor',
            'match_strategy': 'any',
            'notification_mode': 'any_change',
            'is_active': True
        }
    )
    print(f'   Task 2.2: {task2_2.area_name} - {"Created" if created else "Exists"}')
    
    print('\n📊 Multi-Tenant Setup Complete!')
    print('=' * 40)
    
    # Show final configuration
    print('Agency 1 (Group -5077577076):')
    agency1_tasks = MonitorTask.objects.filter(agency=agency1, is_active=True)
    for task in agency1_tasks:
        print(f'   • {task.area_name}')
        print(f'     Dates: {", ".join(task.dates)}')
        print(f'     Visitors: {task.visitors}')
        print(f'     Language: {task.language or "Standard"}')
    
    print('\nAgency 2 (Group -5245239270):')
    agency2_tasks = MonitorTask.objects.filter(agency=agency2, is_active=True)
    for task in agency2_tasks:
        print(f'   • {task.area_name}')
        print(f'     Dates: {", ".join(task.dates)}')
        print(f'     Visitors: {task.visitors}')
        print(f'     Language: {task.language or "Standard"}')
    
    print(f'\n✅ Total: {agency1_tasks.count()} tasks for Agency 1, {agency2_tasks.count()} tasks for Agency 2')
    
    return True

if __name__ == "__main__":
    success = setup_multi_tenant()
    sys.exit(0 if success else 1)