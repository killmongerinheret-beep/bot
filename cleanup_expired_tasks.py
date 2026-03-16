#!/usr/bin/env python3
"""
Automatic Task Cleanup - Vatican Ticket Monitor
Deletes monitoring tasks when their target date has passed
Can be run manually or scheduled via cron/Task Scheduler
"""

import requests
import os
from datetime import datetime, timedelta, timezone
import sys

# Configuration
API_URL = "http://localhost:8000/api/v1/tasks/"
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8385485516:AAF8GjzusdFNBekC8cJrTk5wGVnZtDdhAhY')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-5245239270')

def send_telegram_message(message):
    """Send notification to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")
        return False

def parse_date(date_str):
    """Parse date string in DD/MM/YYYY format"""
    try:
        return datetime.strptime(date_str, '%d/%m/%Y')
    except:
        return None

def get_all_tasks():
    """Fetch all monitoring tasks from API"""
    try:
        response = requests.get(API_URL, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch tasks: HTTP {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        return []

def delete_task(task_id):
    """Delete a task by ID"""
    try:
        response = requests.delete(f"{API_URL}{task_id}/", timeout=10)
        return response.status_code in [200, 204]
    except Exception as e:
        print(f"Error deleting task {task_id}: {e}")
        return False

def cleanup_expired_tasks():
    """Main cleanup function"""
    print(f"\n{'='*60}")
    print(f"Task Cleanup - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Get current date (midnight today)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Fetch all tasks
    print("📋 Fetching all monitoring tasks...")
    tasks = get_all_tasks()
    
    if not tasks:
        print("   ℹ️  No tasks found or API unavailable")
        return 0
    
    print(f"   ✅ Found {len(tasks)} task(s)\n")
    
    # Check each task
    expired_tasks = []
    active_tasks = []
    
    for task in tasks:
        task_id = task.get('id')
        target_date = task.get('target_date')
        agency_name = task.get('agency_name', 'Unknown')
        ticket_name = task.get('ticket_name', 'Unknown ticket')
        
        if not target_date:
            print(f"   ⚠️  Task {task_id}: No target date - skipping")
            continue
        
        # Parse the target date
        task_date = parse_date(target_date)
        if not task_date:
            print(f"   ⚠️  Task {task_id}: Invalid date format '{target_date}' - skipping")
            continue
        
        # Check if expired (date has passed)
        if task_date < today:
            days_ago = (today - task_date).days
            expired_tasks.append({
                'id': task_id,
                'date': target_date,
                'days_ago': days_ago,
                'agency': agency_name,
                'ticket': ticket_name
            })
            print(f"   🗑️  Task {task_id}: {target_date} - EXPIRED ({days_ago} days ago)")
        else:
            days_until = (task_date - today).days
            active_tasks.append({
                'id': task_id,
                'date': target_date,
                'days_until': days_until,
                'ticket': ticket_name
            })
            print(f"   ✅ Task {task_id}: {target_date} - Active ({days_until} days remaining)")
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Active tasks: {len(active_tasks)}")
    print(f"  Expired tasks: {len(expired_tasks)}")
    print(f"{'='*60}\n")
    
    # Delete expired tasks
    if expired_tasks:
        print("🗑️  Deleting expired tasks...\n")
        deleted_count = 0
        failed_count = 0
        
        for task in expired_tasks:
            print(f"   Deleting task {task['id']} ({task['date']})...")
            if delete_task(task['id']):
                print(f"   ✅ Deleted successfully")
                deleted_count += 1
            else:
                print(f"   ❌ Failed to delete")
                failed_count += 1
        
        print(f"\n{'='*60}")
        print(f"Cleanup Results:")
        print(f"  ✅ Deleted: {deleted_count}")
        if failed_count > 0:
            print(f"  ❌ Failed: {failed_count}")
        print(f"{'='*60}\n")
        
        # Send Telegram notification
        if deleted_count > 0:
            message = f"""
🗑️ <b>Expired Tasks Cleaned Up</b>

<b>Deleted:</b> {deleted_count} task(s)
<b>Remaining:</b> {len(active_tasks)} active task(s)

<b>Deleted Tasks:</b>
{chr(10).join(f'• {t["date"]} - {t["ticket"]} ({t["days_ago"]} days ago)' for t in expired_tasks[:5])}
"""
            if len(expired_tasks) > 5:
                message += f"\n... and {len(expired_tasks) - 5} more"
            
            if active_tasks:
                message += f"\n\n<b>Active Tasks:</b>\n"
                message += "\n".join(f'• {t["date"]} - {t["ticket"]} ({t["days_until"]} days)' for t in active_tasks[:3])
                if len(active_tasks) > 3:
                    message += f"\n... and {len(active_tasks) - 3} more"
            
            print("📱 Sending Telegram notification...")
            if send_telegram_message(message):
                print("   ✅ Notification sent\n")
            else:
                print("   ⚠️  Failed to send notification\n")
        
        return deleted_count
    else:
        print("✅ No expired tasks to delete\n")
        
        # Show upcoming tasks
        if active_tasks:
            print("📅 Upcoming tasks:")
            for task in sorted(active_tasks, key=lambda x: x['days_until'])[:5]:
                print(f"   • {task['date']} - {task['ticket']} ({task['days_until']} days)")
            print()
        
        return 0

if __name__ == '__main__':
    try:
        deleted = cleanup_expired_tasks()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n⚠️  Cleanup interrupted by user\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        sys.exit(1)
