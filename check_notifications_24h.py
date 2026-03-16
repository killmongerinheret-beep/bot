#!/usr/bin/env python3
"""
Check Telegram Notifications Sent in Last 24 Hours
==================================================
Analyzes check results to see how many notifications were sent.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import CheckResult, MonitorTask
from django.utils import timezone
from datetime import timedelta

def check_notifications():
    """Check notifications sent in last 24 hours"""
    
    print("=" * 80)
    print("TELEGRAM NOTIFICATIONS - LAST 24 HOURS")
    print("=" * 80)
    
    # Get cutoff time (24 hours ago)
    cutoff = timezone.now() - timedelta(hours=24)
    
    # Get all check results in last 24 hours
    results = CheckResult.objects.filter(check_time__gte=cutoff).order_by('-check_time')
    
    print(f"\n📊 Total checks performed: {results.count()}")
    
    # Count state changes (these trigger notifications)
    state_changes = []
    for result in results:
        if result.details and result.details.get('state_changed') == True:
            state_changes.append(result)
    
    print(f"🔔 Notifications sent (state changes): {len(state_changes)}")
    
    if state_changes:
        print("\n" + "=" * 80)
        print("NOTIFICATION DETAILS:")
        print("=" * 80)
        
        for i, result in enumerate(state_changes[:20], 1):  # Show first 20
            task = result.task
            details = result.details or {}
            
            # Get slots
            slots = details.get('slots', [])
            if isinstance(slots, str):
                slots = slots.split()
            
            date = details.get('date', 'N/A')
            ticket_name = details.get('ticket_name', task.ticket_name or 'Unknown')
            
            print(f"\n{i}. {result.check_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Date: {date}")
            print(f"   Ticket: {ticket_name}")
            print(f"   Visitors: {task.visitors}")
            print(f"   Slots Found: {len(slots)}")
            print(f"   Previous State: {details.get('previous_state', 'unknown')}")
            print(f"   New State: available")
            if slots:
                print(f"   First 5 slots: {', '.join(slots[:5])}")
        
        if len(state_changes) > 20:
            print(f"\n... and {len(state_changes) - 20} more notifications")
    
    # Check for available tickets (current state)
    print("\n" + "=" * 80)
    print("CURRENT STATUS:")
    print("=" * 80)
    
    tasks = MonitorTask.objects.filter(is_active=True)
    
    for task in tasks:
        latest = CheckResult.objects.filter(task=task).order_by('-check_time').first()
        
        if latest:
            details = latest.details or {}
            slots = details.get('slots', [])
            if isinstance(slots, str):
                slots = slots.split()
            
            date = task.dates[0] if task.dates else 'N/A'
            
            print(f"\n📋 Task #{task.id}: {task.ticket_name}")
            print(f"   Date: {date}")
            print(f"   Visitors: {task.visitors}")
            print(f"   Last Checked: {latest.check_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Status: {latest.status}")
            print(f"   Slots Available: {len(slots)}")
            if slots:
                print(f"   Available Times: {', '.join(slots[:10])}")
                if len(slots) > 10:
                    print(f"   ... and {len(slots) - 10} more")
    
    # Check Redis cooldown keys
    print("\n" + "=" * 80)
    print("NOTIFICATION COOLDOWNS (Spam Protection):")
    print("=" * 80)
    
    from django.core.cache import cache
    
    cooldown_count = 0
    for task in tasks:
        for date in task.dates:
            key = f"alert_cooldown:{task.id}:{task.ticket_id}:{date}"
            if cache.get(key):
                cooldown_count += 1
                print(f"   🔒 Task #{task.id} ({date}) - Cooldown active (1 hour)")
    
    if cooldown_count == 0:
        print("   ✅ No active cooldowns - ready to send notifications")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Total checks in 24h: {results.count()}")
    print(f"🔔 Notifications sent: {len(state_changes)}")
    print(f"🔒 Active cooldowns: {cooldown_count}")
    print(f"📋 Active tasks: {tasks.count()}")
    
    # Calculate notification rate
    if results.count() > 0:
        notification_rate = (len(state_changes) / results.count()) * 100
        print(f"📊 Notification rate: {notification_rate:.1f}%")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_notifications()
