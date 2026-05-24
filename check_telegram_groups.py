#!/usr/bin/env python3
"""
Check all Telegram groups and their relationship to user accounts.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import TelegramGroup, Agency, User

print("=" * 80)
print("TELEGRAM GROUPS vs USER ACCOUNTS")
print("=" * 80)
print()

# Get all Telegram groups
groups = TelegramGroup.objects.all().select_related('agency')

print(f"📱 Found {groups.count()} Telegram group(s):\n")

for group in groups:
    print(f"{'='*80}")
    print(f"💬 Group: {group.chat_title or 'Unknown'}")
    print(f"   Chat ID: {group.chat_id}")
    print(f"   Type: {group.chat_type}")
    print(f"   Status: {group.status}")
    print(f"   Agency: {group.agency.name if group.agency else 'None'}")
    print(f"   Notifications: {'✅ Enabled' if group.notification_enabled else '❌ Disabled'}")
    print(f"   Created: {group.created_at}")
    if group.approved_at:
        print(f"   Approved: {group.approved_at}")
    if group.added_by_username:
        print(f"   Added by: @{group.added_by_username} ({group.added_by_first_name})")
    print()

print("=" * 80)
print("IMPORTANT: Telegram Groups vs User Accounts")
print("=" * 80)
print()
print("🔍 Key Differences:")
print()
print("1. TELEGRAM GROUPS (TelegramGroup model):")
print("   - Represent Telegram chat groups/channels")
print("   - Used for receiving notifications")
print("   - Linked to an Agency")
print("   - Do NOT have login credentials")
print("   - Created when bot is added to a group")
print()
print("2. USER ACCOUNTS (User model):")
print("   - Represent individual users who can login to hydrabot.it")
print("   - Have username/password for web login")
print("   - Linked to an Agency")
print("   - Can manage tasks via web interface")
print("   - Created manually or via Telegram bot admin commands")
print()
print("3. RELATIONSHIP:")
print("   - Multiple Telegram groups can belong to one Agency")
print("   - Multiple Users can belong to one Agency")
print("   - Telegram groups receive notifications for tasks created by Agency users")
print("   - Users login to web interface, groups receive Telegram messages")
print()

# Show which agencies have both groups and users
print("=" * 80)
print("AGENCIES WITH GROUPS AND USERS")
print("=" * 80)
print()

agencies = Agency.objects.all()

for agency in agencies:
    users = User.objects.filter(agency=agency)
    groups = TelegramGroup.objects.filter(agency=agency, status='approved')
    
    if users.exists() or groups.exists():
        print(f"🏢 {agency.name} ({agency.plan})")
        print(f"   👥 Users: {users.count()}")
        for user in users:
            print(f"      - {user.username} ({user.email})")
        print(f"   💬 Telegram Groups: {groups.count()}")
        for group in groups:
            print(f"      - {group.chat_title} ({group.chat_id})")
        print()

print("=" * 80)
print("CREATING USER ACCOUNTS FOR TELEGRAM GROUPS")
print("=" * 80)
print()
print("If you want to create web login accounts for Telegram group members:")
print()
print("Option 1: Via Telegram Bot (Admin only)")
print("   1. Admin sends /pending to see pending groups")
print("   2. Admin approves group and creates agency")
print("   3. Bot creates username/password automatically")
print()
print("Option 2: Via Django Shell")
print("   python backend/manage.py shell")
print("   >>> from monitors.models import User, Agency")
print("   >>> agency = Agency.objects.get(name='Your Agency')")
print("   >>> user = User.objects.create(")
print("   ...     username='newuser',")
print("   ...     email='user@example.com',")
print("   ...     agency=agency,")
print("   ...     is_active=True")
print("   ... )")
print("   >>> user.set_password('yourpassword')")
print("   >>> user.save()")
print()
print("Option 3: Via API")
print("   curl -X POST http://localhost:8000/api/v1/auth/register \\")
print("     -H 'Content-Type: application/json' \\")
print("     -d '{")
print("       \"username\": \"newuser\",")
print("       \"email\": \"user@example.com\",")
print("       \"password\": \"yourpassword\",")
print("       \"agency_id\": 1")
print("     }'")
print()
