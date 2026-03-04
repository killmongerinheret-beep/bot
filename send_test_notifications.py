#!/usr/bin/env python
"""
Send Test Notifications for All Tasks
Verifies time slots match preferred times
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask, CheckResult
from monitors.notification_utils import format_vatican_notification
from django.utils import timezone
import json
import requests

print("=" * 80)
print("SENDING TEST NOTIFICATIONS FOR ALL TASKS")
print("=" * 80)
print()

# Get Telegram bot token
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not configured!")
    sys.exit(1)

def send_telegram_message(chat_id, message):
    """Send message via Telegram"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            },
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        print(f"  ❌ Error sending: {e}")
        return False

# Get all active tasks
active_tasks = MonitorTask.objects.filter(is_active=True).order_by('id')

print(f"Found {active_tasks.count()} active tasks")
print()

# Track statistics
total_sent = 0
total_failed = 0
tasks_with_slots = 0
tasks_without_slots = 0
preferred_time_matches = 0
preferred_time_mismatches = 0

for task in active_tasks:
    print(f"Task #{task.id}: {task.ticket_name}")
    print(f"  Date: {task.dates[0] if task.dates else 'None'}")
    print(f"  Visitors: {task.visitors}")
    print(f"  Preferred Times: {task.preferred_times}")
    print(f"  Last Status: {task.last_status}")
    
    # Get chat_id
    chat_id = task.agency.telegram_chat_id
    if not chat_id:
        print(f"  ⚠️ No Telegram chat_id configured")
        print()
        continue
    
    # Get latest check result
    latest_result = CheckResult.objects.filter(task=task).order_by('-check_time').first()
    
    if not latest_result:
        print(f"  ⚠️ No check results found")
        print()
        continue
    
    # Parse details to get slots
    details = latest_result.details
    slots = []
    
    if isinstance(details, dict):
        # Try to extract slots from various formats
        if 'slots' in details:
            slots = details['slots']
        elif 'updates' in details:
            # Format: {"updates": {"date": [{"slots": [...]}]}}
            for date, items in details.get('updates', {}).items():
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict) and 'slots' in item:
                            slots.extend(item['slots'])
    
    # Deduplicate slots
    slots = list(set(slots)) if slots else []
    slots.sort()
    
    print(f"  Available Slots: {len(slots)}")
    
    if slots:
        tasks_with_slots += 1
        print(f"    {', '.join(slots[:10])}{'...' if len(slots) > 10 else ''}")
        
        # Check if preferred times match
        if task.preferred_times:
            matched_times = []
            missing_times = []
            
            for pref_time in task.preferred_times:
                # Check if any slot matches (exact or starts with)
                match = any(slot.startswith(pref_time) for slot in slots)
                if match:
                    matched_times.append(pref_time)
                else:
                    missing_times.append(pref_time)
            
            if matched_times:
                print(f"  ✅ Preferred times found: {', '.join(matched_times)}")
                preferred_time_matches += 1
            if missing_times:
                print(f"  ❌ Preferred times NOT found: {', '.join(missing_times)}")
                preferred_time_mismatches += 1
    else:
        tasks_without_slots += 1
        print(f"    No slots available")
    
    # Create notification message
    try:
        if slots:
            # Format notification
            message = format_vatican_notification(
                date=task.dates[0] if task.dates else 'Unknown',
                ticket_name=task.ticket_name,
                ticket_id=str(task.ticket_id) if task.ticket_id else 'Unknown',
                slots=slots,
                preferred_times=task.preferred_times,
                language=task.language,
                visitors=task.visitors,
                check_method="test"
            )
        else:
            # Send sold out message
            message = f"🔔 *TEST NOTIFICATION*\n\n"
            message += f"📅 Date: {task.dates[0] if task.dates else 'Unknown'}\n"
            message += f"🎫 Ticket: {task.ticket_name}\n"
            message += f"👥 Visitors: {task.visitors}\n"
            message += f"⏰ Preferred Times: {', '.join(task.preferred_times) if task.preferred_times else 'Any'}\n\n"
            message += f"❌ Status: SOLD OUT\n"
            message += f"No slots currently available.\n"
        
        # Add test notification header
        message = f"🧪 *TEST NOTIFICATION* 🧪\n\n" + message
        
        # Send message
        success = send_telegram_message(chat_id, message)
        
        if success:
            print(f"  ✅ Notification sent")
            total_sent += 1
        else:
            print(f"  ❌ Failed to send notification")
            total_failed += 1
            
    except Exception as e:
        print(f"  ❌ Error creating notification: {e}")
        total_failed += 1
    
    print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()

print(f"Total Tasks: {active_tasks.count()}")
print(f"Notifications Sent: {total_sent}")
print(f"Failed: {total_failed}")
print()

print(f"Tasks with Available Slots: {tasks_with_slots}")
print(f"Tasks with No Slots (Sold Out): {tasks_without_slots}")
print()

print(f"Preferred Time Matches: {preferred_time_matches}")
print(f"Preferred Time Mismatches: {preferred_time_mismatches}")
print()

# ============================================================================
# VERIFICATION REPORT
# ============================================================================
print("=" * 80)
print("VERIFICATION REPORT")
print("=" * 80)
print()

print("Time Slot Verification:")
print()

for task in active_tasks:
    if not task.preferred_times:
        continue
    
    # Get latest result
    latest_result = CheckResult.objects.filter(task=task).order_by('-check_time').first()
    if not latest_result:
        continue
    
    # Extract slots
    details = latest_result.details
    slots = []
    
    if isinstance(details, dict):
        if 'slots' in details:
            slots = details['slots']
        elif 'updates' in details:
            for date, items in details.get('updates', {}).items():
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict) and 'slots' in item:
                            slots.extend(item['slots'])
    
    slots = list(set(slots)) if slots else []
    
    if not slots:
        continue
    
    # Check matches
    matched = []
    missing = []
    
    for pref_time in task.preferred_times:
        match = any(slot.startswith(pref_time) for slot in slots)
        if match:
            matched.append(pref_time)
        else:
            missing.append(pref_time)
    
    status_icon = "✅" if len(matched) == len(task.preferred_times) else "⚠️" if matched else "❌"
    
    print(f"{status_icon} Task #{task.id}: {task.dates[0] if task.dates else 'N/A'}")
    print(f"   Preferred: {', '.join(task.preferred_times)}")
    if matched:
        print(f"   ✅ Found: {', '.join(matched)}")
    if missing:
        print(f"   ❌ Missing: {', '.join(missing)}")
    print(f"   Total Slots: {len(slots)}")
    print()

print("=" * 80)
print("COMPLETE")
print("=" * 80)
