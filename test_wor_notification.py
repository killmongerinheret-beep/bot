#!/usr/bin/env python
"""
Send a test notification to WOR Bot group
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from monitors.notification_utils import send_telegram_signal, format_vatican_notification

# WOR Bot group chat ID
WOR_CHAT_ID = '-5245239270'

# Create a test notification message
test_message = format_vatican_notification(
    date='01/05/2026',
    ticket_name='Musei Vaticani - Biglietti d\'ingresso',
    ticket_id='TEST123',
    slots=['09:00', '09:30', '10:00', '10:30', '11:00'],
    preferred_times=['09:00', '10:00'],
    language=None,
    visitors=1,
    check_method='manual_test'
)

print("=" * 70)
print("SENDING TEST NOTIFICATION TO WOR BOT GROUP")
print("=" * 70)
print(f"Chat ID: {WOR_CHAT_ID}")
print(f"Group: WOR Bot")
print()
print("Message Preview:")
print("-" * 70)
print(test_message)
print("-" * 70)
print()

# Send the notification
print("Sending...")
result = send_telegram_signal(WOR_CHAT_ID, test_message)

if result:
    print("✅ SUCCESS! Test notification sent to WOR Bot group")
    print()
    print("Check the WOR Bot Telegram group to see the message!")
else:
    print("❌ FAILED! Could not send notification")
    print()
    print("Possible reasons:")
    print("- TELEGRAM_BOT_TOKEN not configured")
    print("- Bot not added to the group")
    print("- Network issue")

print("=" * 70)
