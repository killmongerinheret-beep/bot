#!/usr/bin/env python3
"""
Test Multi-Group Telegram Notifications
Sends a test message to all approved groups for the agency
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def test_multi_group_notifications():
    """Test sending notifications to multiple groups"""
    
    from monitors.models import TelegramGroup, Agency
    from monitors.notification_utils import send_telegram_signal
    
    print("🧪 Testing Multi-Group Telegram Notifications")
    print("=" * 50)
    
    # Get the agency
    agency = Agency.objects.first()
    if not agency:
        print("❌ No agency found")
        return
    
    print(f"📋 Agency: {agency.name}")
    
    # Get all approved groups for this agency
    approved_groups = TelegramGroup.objects.filter(
        agency=agency,
        status='approved',
        notification_enabled=True
    )
    
    print(f"📱 Found {approved_groups.count()} approved groups:")
    for group in approved_groups:
        print(f"   - {group.chat_title} ({group.chat_id})")
    
    if not approved_groups.exists():
        print("❌ No approved groups found")
        return
    
    # Create test message
    test_message = """🧪 MULTI-GROUP TEST MESSAGE

📅 Date: 15/06/2026
🎫 Ticket: Vatican Museums - Test Notification
👥 Visitors: 2

⏰ Available Times:
   • 09:00
   • 10:30
   • 14:00

🔗 This is a test of the multi-group notification system.
Both groups should receive this message!

✅ Multi-tenant system working correctly."""
    
    # Send to all approved groups
    sent_count = 0
    failed_count = 0
    
    print(f"\n📤 Sending test message to {approved_groups.count()} groups...")
    
    for group in approved_groups:
        print(f"   Sending to {group.chat_title} ({group.chat_id})...", end=" ")
        
        if send_telegram_signal(group.chat_id, test_message):
            print("✅ SUCCESS")
            sent_count += 1
        else:
            print("❌ FAILED")
            failed_count += 1
    
    print(f"\n📊 Results:")
    print(f"   ✅ Sent successfully: {sent_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📱 Total groups: {approved_groups.count()}")
    
    if sent_count == approved_groups.count():
        print(f"\n🎉 SUCCESS! Multi-group notifications working perfectly!")
        print(f"   Both groups ({', '.join([g.chat_id for g in approved_groups])}) should have received the test message.")
    elif sent_count > 0:
        print(f"\n⚠️ PARTIAL SUCCESS! {sent_count} out of {approved_groups.count()} groups received the message.")
    else:
        print(f"\n❌ FAILED! No groups received the message. Check bot token and group permissions.")
    
    return sent_count == approved_groups.count()

if __name__ == "__main__":
    success = test_multi_group_notifications()
    sys.exit(0 if success else 1)