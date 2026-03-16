#!/usr/bin/env python
"""
Test script for Telegram Multi-Tenant Group Management
Run this to verify the implementation is working correctly
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import TelegramGroup, Agency
from django.utils import timezone


def test_telegram_groups():
    """Test the TelegramGroup model and methods"""
    
    print("=" * 60)
    print("TELEGRAM MULTI-TENANT GROUP MANAGEMENT TEST")
    print("=" * 60)
    print()
    
    # 1. Check if model exists
    print("✓ TelegramGroup model imported successfully")
    print()
    
    # 2. List all groups
    groups = TelegramGroup.objects.all()
    print(f"📊 Total Groups in Database: {groups.count()}")
    print()
    
    if groups.exists():
        print("Groups:")
        for group in groups:
            print(f"  • {group.chat_title} (ID: {group.chat_id})")
            print(f"    Status: {group.status}")
            print(f"    Agency: {group.agency.name if group.agency else 'None'}")
            print(f"    Added by: {group.added_by_first_name}")
            print(f"    Created: {group.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    Is Approved: {group.is_approved()}")
            print()
    else:
        print("  No groups found yet.")
        print("  Add your bot to a Telegram group to test!")
        print()
    
    # 3. Check status distribution
    print("Status Distribution:")
    for status in ['pending', 'approved', 'rejected', 'suspended']:
        count = TelegramGroup.objects.filter(status=status).count()
        print(f"  {status.upper()}: {count}")
    print()
    
    # 4. Check agencies
    agencies = Agency.objects.all()
    print(f"📋 Total Agencies: {agencies.count()}")
    if agencies.exists():
        print("Agencies:")
        for agency in agencies[:5]:
            linked_groups = TelegramGroup.objects.filter(agency=agency).count()
            print(f"  • {agency.name} - {linked_groups} linked groups")
    print()
    
    # 5. Test approval workflow
    print("Testing Approval Workflow:")
    pending_groups = TelegramGroup.objects.filter(status='pending')
    if pending_groups.exists():
        print(f"  Found {pending_groups.count()} pending groups")
        print("  You can approve them via:")
        print("    1. Admin dashboard: http://localhost:3000/admin/telegram-groups")
        print("    2. API: POST /api/v1/telegram-groups/<id>/approve/")
    else:
        print("  No pending groups to approve")
    print()
    
    # 6. Environment check
    print("Environment Check:")
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    admin_ids = os.getenv('ADMIN_TELEGRAM_IDS', '')
    
    print(f"  TELEGRAM_BOT_TOKEN: {'✓ Set' if bot_token else '✗ Missing'}")
    print(f"  ADMIN_TELEGRAM_IDS: {'✓ Set' if admin_ids else '✗ Missing (optional)'}")
    print()
    
    # 7. API endpoints check
    print("API Endpoints Available:")
    print("  GET  /api/v1/telegram-groups/")
    print("  GET  /api/v1/telegram-groups/?status=pending")
    print("  POST /api/v1/telegram-groups/<id>/approve/")
    print("  POST /api/v1/telegram-groups/<id>/reject/")
    print("  POST /api/v1/telegram-groups/<id>/suspend/")
    print()
    
    # 8. Next steps
    print("=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print()
    print("1. Restart telegram_bot container:")
    print("   docker-compose restart telegram_bot")
    print()
    print("2. Add your bot to a Telegram group")
    print()
    print("3. Check the database:")
    print("   python test_telegram_groups.py")
    print()
    print("4. Open admin dashboard:")
    print("   http://localhost:3000/admin/telegram-groups")
    print()
    print("5. Approve the group and test notifications")
    print()
    print("=" * 60)


if __name__ == '__main__':
    try:
        test_telegram_groups()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
