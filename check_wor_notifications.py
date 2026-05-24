#!/usr/bin/env python
"""Check WOR Telegram notification history"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.insert(0, 'backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import Agency, MonitorTask, NotificationLog
from django.utils import timezone

# Get WOR agency
wor = Agency.objects.get(name='WOR')

print("="*80)
print("WOR TELEGRAM NOTIFICATION HISTORY")
print("="*80)
print()

# Check if NotificationLog model exists
try:
    # Get notifications from last 24 hours
    yesterday = timezone.now() - timedelta(hours=24)
    notifications = NotificationLog.objects.filter(
        agency=wor,
        created_at__gte=yesterday
    ).order_by('-created_at')
    
    if notifications.exists():
        print(f"📊 Found {notifications.count()} notifications in last 24 hours")
        print()
        
        for notif in notifications[:20]:
            print(f"⏰ {notif.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            print(f"   Type: {notif.notification_type}")
            print(f"   Status: {notif.status}")
            print(f"   Message: {notif.message[:100] if notif.message else 'N/A'}...")
            print()
    else:
        print("⚠️  No notifications found in last 24 hours")
        print()
        
        # Check all-time notifications
        all_notifs = NotificationLog.objects.filter(agency=wor).order_by('-created_at')
        if all_notifs.exists():
            print(f"📊 Found {all_notifs.count()} total notifications (all time)")
            print(f"   Last notification: {all_notifs.first().created_at}")
            print()
            
            print("Last 10 notifications:")
            for notif in all_notifs[:10]:
                print(f"   {notif.created_at.strftime('%Y-%m-%d %H:%M:%S')} - {notif.notification_type} - {notif.status}")
        else:
            print("❌ No notifications found for WOR (ever)")

except Exception as e:
    print(f"⚠️  NotificationLog model not available or error: {e}")
    print()

# Check monitoring task status
print("="*80)
print("MONITORING TASK STATUS")
print("="*80)
print()

tasks = MonitorTask.objects.filter(agency=wor, is_active=True)

if tasks.exists():
    for task in tasks:
        print(f"📋 Task #{task.id}:")
        print(f"   Active: {task.is_active}")
        print(f"   Last checked: {task.last_checked or 'Never'}")
        print(f"   Last status: {task.last_status or 'Unknown'}")
        print(f"   Dates: {', '.join(task.dates)}")
        print(f"   Tier: {task.tier}")
        print()
        
        # Check if task was recently checked
        if task.last_checked:
            time_since = timezone.now() - task.last_checked
            minutes_ago = time_since.total_seconds() / 60
            print(f"   ⏱️  Last check was {minutes_ago:.1f} minutes ago")
            
            if minutes_ago > 5:
                print(f"   ⚠️  WARNING: Task hasn't been checked in {minutes_ago:.1f} minutes")
                print(f"   Expected: Check every {task.check_interval}s")
        else:
            print(f"   ⚠️  WARNING: Task has never been checked")
        print()
else:
    print("❌ No active monitoring tasks for WOR")
    print()

# Check Telegram group configuration
print("="*80)
print("TELEGRAM GROUP CONFIGURATION")
print("="*80)
print()

try:
    from monitors.models import TelegramGroup
    
    groups = TelegramGroup.objects.filter(agency=wor, is_active=True)
    
    if groups.exists():
        print(f"✅ Found {groups.count()} active Telegram group(s) for WOR:")
        for group in groups:
            print(f"   Group: {group.chat_id}")
            print(f"   Title: {group.title or 'N/A'}")
            print(f"   Active: {group.is_active}")
            print()
    else:
        print("⚠️  No active Telegram groups configured for WOR")
        print()
        
        # Check inactive groups
        inactive = TelegramGroup.objects.filter(agency=wor, is_active=False)
        if inactive.exists():
            print(f"   Found {inactive.count()} inactive group(s):")
            for group in inactive:
                print(f"   - {group.chat_id} (Deactivated)")
        else:
            print("   No Telegram groups found for WOR (active or inactive)")
        print()
        print("❌ THIS IS THE PROBLEM: No Telegram group configured!")
        print("   Notifications cannot be sent without a Telegram group")
        
except Exception as e:
    print(f"⚠️  TelegramGroup model not available or error: {e}")

print("="*80)
