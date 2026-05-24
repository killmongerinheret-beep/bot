#!/usr/bin/env python3
"""
Check ALL Telegram groups that receive notifications.
Shows which groups are active, approved, and receiving alerts.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import TelegramGroup, Agency, MonitorTask
from monitors.notification_utils import send_telegram_signal

print("=" * 80)
print("ALL TELEGRAM GROUPS - NOTIFICATION RECIPIENTS")
print("=" * 80)
print()

# Get all Telegram groups
all_groups = TelegramGroup.objects.all().select_related('agency').order_by('agency__name', 'chat_id')

print(f"📱 Total Telegram Groups: {all_groups.count()}\n")

# Group by status
approved_groups = all_groups.filter(status='approved')
pending_groups = all_groups.filter(status='pending')
rejected_groups = all_groups.filter(status='rejected')

print(f"✅ Approved: {approved_groups.count()}")
print(f"⏳ Pending: {pending_groups.count()}")
print(f"❌ Rejected: {rejected_groups.count()}")
print()

print("=" * 80)
print("APPROVED GROUPS (Receiving Notifications)")
print("=" * 80)
print()

if not approved_groups:
    print("⚠️  No approved groups found!")
    print("   Notifications will NOT be sent to any Telegram groups.")
    print()
else:
    for group in approved_groups:
        print(f"{'='*80}")
        print(f"💬 {group.chat_title or 'Unknown Group'}")
        print(f"   Chat ID: {group.chat_id}")
        print(f"   Type: {group.chat_type}")
        print(f"   Agency: {group.agency.name if group.agency else 'None'}")
        print(f"   Notifications: {'✅ ENABLED' if group.notification_enabled else '❌ DISABLED'}")
        print(f"   Created: {group.created_at.strftime('%Y-%m-%d %H:%M')}")
        if group.approved_at:
            print(f"   Approved: {group.approved_at.strftime('%Y-%m-%d %H:%M')}")
        if group.added_by_username:
            print(f"   Added by: @{group.added_by_username} ({group.added_by_first_name})")
        
        # Check active tasks for this agency
        if group.agency:
            active_tasks = MonitorTask.objects.filter(
                agency=group.agency,
                is_active=True
            ).count()
            print(f"   Active Tasks: {active_tasks}")
        
        print()

print("=" * 80)
print("PENDING GROUPS (Awaiting Approval)")
print("=" * 80)
print()

if not pending_groups:
    print("✅ No pending groups")
    print()
else:
    for group in pending_groups:
        print(f"⏳ {group.chat_title or 'Unknown'} ({group.chat_id})")
        print(f"   Added: {group.created_at.strftime('%Y-%m-%d %H:%M')}")
        if group.added_by_username:
            print(f"   By: @{group.added_by_username}")
        print()

print("=" * 80)
print("TEST NOTIFICATION")
print("=" * 80)
print()

if approved_groups.exists():
    test = input("Send test notification to all approved groups? (yes/no): ")
    
    if test.lower() == 'yes':
        print("\n📤 Sending test notifications...\n")
        
        test_message = """
🧪 <b>Test Notification</b>

This is a test message from the Vatican Bot system.

✅ If you received this, notifications are working correctly!

🎫 <b>System Status:</b>
• Bot: Online
• Monitoring: Active
• Notifications: Enabled

<i>Sent at: {}</i>
""".format(os.popen('date /t & time /t').read().strip() if os.name == 'nt' else os.popen('date').read().strip())
        
        success_count = 0
        fail_count = 0
        
        for group in approved_groups:
            if group.notification_enabled:
                print(f"Sending to: {group.chat_title} ({group.chat_id})...")
                try:
                    result = send_telegram_signal(group.chat_id, test_message)
                    if result:
                        print(f"   ✅ Success")
                        success_count += 1
                    else:
                        print(f"   ❌ Failed")
                        fail_count += 1
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    fail_count += 1
            else:
                print(f"Skipping: {group.chat_title} (notifications disabled)")
        
        print()
        print(f"📊 Results: {success_count} sent, {fail_count} failed")
        print()
    else:
        print("❌ Test cancelled")
        print()
else:
    print("⚠️  No approved groups to test")
    print()

print("=" * 80)
print("NOTIFICATION FLOW")
print("=" * 80)
print()
print("How notifications work:")
print()
print("1. Monitor detects available slot")
print("2. System checks for approved Telegram groups linked to task's agency")
print("3. Sends notification to ALL approved groups with notifications enabled")
print("4. Group members receive message with booking link")
print()
print("Current notification recipients:")
for group in approved_groups.filter(notification_enabled=True):
    print(f"   ✅ {group.chat_title} → {group.agency.name if group.agency else 'No Agency'}")
print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()
print(f"Total Groups: {all_groups.count()}")
print(f"Receiving Notifications: {approved_groups.filter(notification_enabled=True).count()}")
print(f"Agencies with Groups: {approved_groups.values('agency').distinct().count()}")
print()

# Show agencies WITHOUT Telegram groups
agencies_without_groups = Agency.objects.exclude(
    id__in=approved_groups.values_list('agency_id', flat=True)
).filter(is_active=True)

if agencies_without_groups.exists():
    print("⚠️  Agencies WITHOUT Telegram groups (won't receive notifications):")
    for agency in agencies_without_groups:
        print(f"   - {agency.name}")
    print()
    print("   To add a group: Add the bot to a Telegram group, then admin approves via /pending")
    print()

print("=" * 80)
print("ADMIN COMMANDS")
print("=" * 80)
print()
print("To manage groups via Telegram bot:")
print()
print("  /pending     - View pending group requests")
print("  /groups      - List all approved groups")
print("  /status      - Check bot status")
print()
print(f"Bot Token: {os.getenv('TELEGRAM_BOT_TOKEN', 'Not set')[:20]}...")
print(f"Admin IDs: {os.getenv('ADMIN_TELEGRAM_IDS', 'Not set')}")
print()
