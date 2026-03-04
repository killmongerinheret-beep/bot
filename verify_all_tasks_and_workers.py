#!/usr/bin/env python3
"""
Comprehensive verification of all tasks and workers
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask, Agency
from django.utils import timezone

def main():
    print("=" * 80)
    print("COMPREHENSIVE SYSTEM VERIFICATION")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Check Docker Services
    print(f"\n{'='*80}")
    print("1. DOCKER SERVICES STATUS")
    print("=" * 80)
    
    import subprocess
    try:
        result = subprocess.run(['docker-compose', 'ps'], capture_output=True, text=True, cwd='/app')
        print(result.stdout)
    except Exception as e:
        print(f"❌ Error checking Docker services: {e}")
    
    # 2. Check All Tasks
    print(f"\n{'='*80}")
    print("2. ALL MONITOR TASKS")
    print("=" * 80)
    
    tasks = MonitorTask.objects.all().order_by('id')
    print(f"\nTotal Tasks: {tasks.count()}")
    
    tasks_with_id = 0
    tasks_without_id = 0
    tasks_checked_recently = 0
    tasks_never_checked = 0
    tasks_with_errors = 0
    
    print(f"\n{'ID':<5} {'Date':<12} {'Visitors':<8} {'Ticket ID':<15} {'Status':<10} {'Last Checked':<20}")
    print("-" * 80)
    
    for task in tasks:
        date_str = task.dates[0] if task.dates else 'N/A'
        ticket_id_str = str(task.ticket_id)[:12] if task.ticket_id else 'None'
        status = task.last_status or 'unknown'
        
        if task.last_checked:
            time_ago = timezone.now() - task.last_checked
            if time_ago.total_seconds() < 3600:  # Less than 1 hour
                last_checked = f"{int(time_ago.total_seconds() / 60)}m ago"
                tasks_checked_recently += 1
            else:
                last_checked = task.last_checked.strftime('%Y-%m-%d %H:%M')
        else:
            last_checked = 'Never'
            tasks_never_checked += 1
        
        if task.ticket_id:
            tasks_with_id += 1
        else:
            tasks_without_id += 1
        
        if status == 'error':
            tasks_with_errors += 1
            marker = '❌'
        elif ticket_id_str == 'None':
            marker = '⚠️'
        elif last_checked == 'Never':
            marker = '⏳'
        else:
            marker = '✅'
        
        print(f"{marker} {task.id:<4} {date_str:<12} {task.visitors:<8} {ticket_id_str:<15} {status:<10} {last_checked:<20}")
    
    # 3. Summary Statistics
    print(f"\n{'='*80}")
    print("3. TASK STATISTICS")
    print("=" * 80)
    
    print(f"\n✅ Tasks with ticket_id: {tasks_with_id}/{tasks.count()} ({tasks_with_id/tasks.count()*100:.0f}%)")
    print(f"⚠️  Tasks without ticket_id: {tasks_without_id}/{tasks.count()} ({tasks_without_id/tasks.count()*100:.0f}%)")
    print(f"🕒 Tasks checked recently (<1h): {tasks_checked_recently}/{tasks.count()}")
    print(f"⏳ Tasks never checked: {tasks_never_checked}/{tasks.count()}")
    print(f"❌ Tasks with errors: {tasks_with_errors}/{tasks.count()}")
    
    # Calculate health score
    health_score = (tasks_with_id / tasks.count() * 100) if tasks.count() > 0 else 0
    
    print(f"\n📊 HEALTH SCORE: {health_score:.0f}/100", end=" ")
    if health_score >= 90:
        print("(EXCELLENT ✅)")
    elif health_score >= 75:
        print("(GOOD ✅)")
    elif health_score >= 50:
        print("(FAIR ⚠️)")
    else:
        print("(POOR ❌)")
    
    # 4. Check Celery Queues
    print(f"\n{'='*80}")
    print("4. CELERY QUEUE STATUS")
    print("=" * 80)
    
    try:
        from celery import Celery
        from kombu import Connection
        
        app = Celery('core')
        app.config_from_object('django.conf:settings', namespace='CELERY')
        
        with Connection(app.conf.broker_url) as conn:
            try:
                # Get queue lengths
                queues = ['vatican', 'colosseum', 'celery']
                print(f"\n{'Queue':<15} {'Tasks':<10} {'Status'}")
                print("-" * 40)
                
                for queue_name in queues:
                    try:
                        queue = conn.SimpleQueue(queue_name)
                        qsize = queue.qsize()
                        queue.close()
                        
                        if queue_name == 'vatican' and qsize > 100:
                            status = '⚠️ HIGH'
                        elif queue_name == 'colosseum' and qsize > 50:
                            status = '⚠️ HIGH'
                        elif queue_name == 'celery' and qsize > 200:
                            status = '⚠️ HIGH'
                        else:
                            status = '✅ OK'
                        
                        print(f"{queue_name:<15} {qsize:<10} {status}")
                    except Exception as e:
                        print(f"{queue_name:<15} {'Error':<10} ❌ {str(e)[:20]}")
            except Exception as e:
                print(f"❌ Error checking queues: {e}")
    except Exception as e:
        print(f"❌ Error connecting to Celery: {e}")
    
    # 5. Check Worker Logs
    print(f"\n{'='*80}")
    print("5. RECENT WORKER ACTIVITY")
    print("=" * 80)
    
    try:
        result = subprocess.run(
            ['docker-compose', 'logs', 'worker_vatican', '--tail', '20'],
            capture_output=True, text=True, cwd='/app', timeout=5
        )
        
        # Extract key information
        lines = result.stdout.split('\n')
        recent_tasks = []
        for line in lines:
            if 'Task' in line and 'succeeded' in line:
                recent_tasks.append(line)
        
        if recent_tasks:
            print(f"\n✅ Recent completed tasks ({len(recent_tasks)}):")
            for task in recent_tasks[-5:]:  # Last 5
                # Extract task info
                if 'run_god_tier_vatican_monitor' in task:
                    print(f"   • God-tier check completed")
                elif 'resolve_and_check_task' in task:
                    print(f"   • Task resolution completed")
                elif 'orchestrate_all_tasks' in task:
                    print(f"   • Orchestration completed")
        else:
            print("\n⚠️ No recent task completions found")
    except Exception as e:
        print(f"❌ Error checking worker logs: {e}")
    
    # 6. Identify Issues
    print(f"\n{'='*80}")
    print("6. IDENTIFIED ISSUES")
    print("=" * 80)
    
    issues = []
    
    if tasks_without_id > 0:
        issues.append(f"⚠️  {tasks_without_id} tasks missing ticket_id")
    
    if tasks_never_checked > 0:
        issues.append(f"⏳ {tasks_never_checked} tasks never checked")
    
    if tasks_with_errors > 0:
        issues.append(f"❌ {tasks_with_errors} tasks with errors")
    
    if health_score < 90:
        issues.append(f"📊 Health score below 90% ({health_score:.0f}%)")
    
    if issues:
        print("\n" + "\n".join(issues))
        
        print(f"\n{'='*80}")
        print("7. RECOMMENDED ACTIONS")
        print("=" * 80)
        
        if tasks_without_id > 0:
            print("\n1. Force resolution for tasks without ticket_id:")
            print("   docker-compose exec -T backend python -c \"")
            print("   from monitors.models import MonitorTask")
            print("   from monitors.tasks import resolve_and_check_task")
            print("   tasks = MonitorTask.objects.filter(ticket_id__isnull=True)")
            print("   for task in tasks:")
            print("       resolve_and_check_task.apply_async(args=[task.id], queue='vatican', priority=9)")
            print("   \"")
        
        if tasks_with_errors > 0:
            print("\n2. Reset error tasks:")
            print("   docker-compose exec -T backend python -c \"")
            print("   from monitors.models import MonitorTask")
            print("   MonitorTask.objects.filter(last_status='error').update(last_status='pending', ticket_id=None)")
            print("   \"")
    else:
        print("\n✅ No issues found - system is healthy!")
    
    # 8. Specific Task Details
    print(f"\n{'='*80}")
    print("8. TASKS NEEDING ATTENTION")
    print("=" * 80)
    
    problem_tasks = tasks.filter(ticket_id__isnull=True) | tasks.filter(last_status='error')
    
    if problem_tasks.exists():
        print(f"\nFound {problem_tasks.count()} tasks needing attention:\n")
        for task in problem_tasks:
            print(f"Task #{task.id}:")
            print(f"  Date: {task.dates[0] if task.dates else 'N/A'}")
            print(f"  Ticket: {task.ticket_name}")
            print(f"  ticket_id: {task.ticket_id or 'Missing'}")
            print(f"  Status: {task.last_status}")
            print(f"  Last checked: {task.last_checked or 'Never'}")
            if task.last_result_summary:
                print(f"  Summary: {task.last_result_summary[:100]}")
            print()
    else:
        print("\n✅ All tasks are healthy!")
    
    print("=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
