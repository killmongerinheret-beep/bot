#!/usr/bin/env python3
"""
Health Check Bot for Vatican Ticket Monitor
Checks if all services are running and sends alerts via Telegram
Can be run by cron or Windows Task Scheduler
"""

import requests
import subprocess
import json
from datetime import datetime
import os
import sys

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8385485516:AAF8GjzusdFNBekC8cJrTk5wGVnZtDdhAhY')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-5245239270')
API_URL = "http://localhost:8000/api/v1/tasks/"

def send_telegram_alert(message):
    """Send alert to Telegram"""
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
        print(f"Failed to send Telegram alert: {e}")
        return False

def check_docker_services():
    """Check if all Docker services are running"""
    try:
        result = subprocess.run(
            ['docker-compose', 'ps', '--format', 'json'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return False, "Docker compose command failed"
        
        # Parse JSON output
        services = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                try:
                    services.append(json.loads(line))
                except:
                    pass
        
        # Check critical services
        critical_services = ['backend', 'worker_vatican', 'beat', 'telegram_bot', 'db', 'redis']
        running_services = [s['Service'] for s in services if s.get('State') == 'running']
        
        missing = [s for s in critical_services if s not in running_services]
        
        if missing:
            return False, f"Services not running: {', '.join(missing)}"
        
        return True, f"All {len(running_services)} services running"
        
    except subprocess.TimeoutExpired:
        return False, "Docker command timeout"
    except Exception as e:
        return False, f"Docker check error: {str(e)}"

def check_api_health():
    """Check if API is responding"""
    try:
        response = requests.get(API_URL, timeout=10)
        if response.status_code == 200:
            tasks = response.json()
            return True, f"API healthy - {len(tasks)} tasks active"
        else:
            return False, f"API returned status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "API not reachable - connection refused"
    except requests.exceptions.Timeout:
        return False, "API timeout"
    except Exception as e:
        return False, f"API check error: {str(e)}"

def check_recent_activity():
    """Check if monitoring tasks ran recently"""
    try:
        response = requests.get(API_URL, timeout=10)
        if response.status_code != 200:
            return False, "Cannot fetch tasks"
        
        tasks = response.json()
        if not tasks:
            return True, "No tasks configured (OK)"
        
        # Check if any task was checked in last 5 minutes
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        recent_checks = []
        
        for task in tasks:
            if task.get('last_checked'):
                last_check = datetime.fromisoformat(task['last_checked'].replace('Z', '+00:00'))
                minutes_ago = (now - last_check).total_seconds() / 60
                if minutes_ago < 5:
                    recent_checks.append(task['id'])
        
        if recent_checks:
            return True, f"{len(recent_checks)} tasks checked in last 5 min"
        else:
            return False, "No tasks checked in last 5 minutes"
            
    except Exception as e:
        return False, f"Activity check error: {str(e)}"

def main():
    """Run all health checks"""
    print(f"\n{'='*60}")
    print(f"Vatican Monitor Health Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    all_ok = True
    issues = []
    
    # Check 1: Docker Services
    print("🔍 Checking Docker services...")
    docker_ok, docker_msg = check_docker_services()
    print(f"   {'✅' if docker_ok else '❌'} {docker_msg}")
    if not docker_ok:
        all_ok = False
        issues.append(f"Docker: {docker_msg}")
    
    # Check 2: API Health
    print("\n🔍 Checking API health...")
    api_ok, api_msg = check_api_health()
    print(f"   {'✅' if api_ok else '❌'} {api_msg}")
    if not api_ok:
        all_ok = False
        issues.append(f"API: {api_msg}")
    
    # Check 3: Recent Activity
    print("\n🔍 Checking recent activity...")
    activity_ok, activity_msg = check_recent_activity()
    print(f"   {'✅' if activity_ok else '❌'} {activity_msg}")
    if not activity_ok:
        all_ok = False
        issues.append(f"Activity: {activity_msg}")
    
    # Summary
    print(f"\n{'='*60}")
    if all_ok:
        print("✅ ALL CHECKS PASSED - System is healthy")
        print(f"{'='*60}\n")
        return 0
    else:
        print("❌ HEALTH CHECK FAILED")
        print(f"{'='*60}\n")
        
        # Send Telegram alert
        alert_message = f"""
🚨 <b>Vatican Monitor Health Alert</b>

<b>Status:</b> UNHEALTHY
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<b>Issues Found:</b>
{chr(10).join(f'• {issue}' for issue in issues)}

<b>Action Required:</b>
Please check the system immediately.
"""
        
        print("📱 Sending Telegram alert...")
        if send_telegram_alert(alert_message):
            print("   ✅ Alert sent successfully")
        else:
            print("   ❌ Failed to send alert")
        
        return 1

if __name__ == '__main__':
    sys.exit(main())
