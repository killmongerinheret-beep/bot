#!/usr/bin/env python3

import os
import sys
import django

# Add the backend directory to Python path
sys.path.append('/app/backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import TelegramGroup, Agency

def check_telegram_groups():
    groups = TelegramGroup.objects.all()
    print('=== TELEGRAM GROUPS ===')
    print(f'Total Groups: {groups.count()}')
    
    for group in groups:
        print(f'Group: {group.chat_title or group.chat_id}')
        print(f'  Chat ID: {group.chat_id}')
        print(f'  Agency: {group.agency.name if group.agency else "None"}')
        print(f'  Status: {group.status}')
        print(f'  Notifications: {group.notification_enabled}')
        print('---')

    agencies = Agency.objects.all()
    print('=== AGENCIES ===')
    for agency in agencies:
        print(f'Agency: {agency.name}')
        print(f'  Legacy Chat ID: {agency.telegram_chat_id}')
        print('---')

if __name__ == '__main__':
    check_telegram_groups()