"""
Comprehensive System Verification
Analyzes all critical components and identifies potential issues
"""
import os
import sys
import django
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask, CheckResult, Agency

print(f"\n{'='*80}")
print(f"COMPREHENSIVE SYSTEM VERIFICATION")
print(f"{'='*80}\n")

# 1. Check all active tasks
print("1. ACTIVE TASKS ANALYSIS")
print("-" * 80)
tasks = MonitorTask.objects.filter(is_active=True, site='vatican')
print(f"Total active Vatican tasks: {tasks.count()}\n")

# Group by ticket configuration
ticket_configs = {}
for task in tasks:
    key = (task.ticket_type, task.ticket_name, task.language)
    if key not in ticket_configs:
        ticket_configs[key] = []
    ticket_configs[key].append(task)

print("Task configurations:")
for (t_type, t_name, lang), task_list in ticket_configs.items():
    ticket_label = "Standard" if t_type == 0 else "Guided Tour"
    print(f"  {ticket_label}: {t_name} (Lang: {lang or 'None'})")
    print(f"    Tasks: {len(task_list)}")
    
    # Check ticket_id status
    with_id = sum(1 for t in task_list if t.ticket_id)
    without_id = len(task_list) - with_id
    print(f"    With ticket_id: {with_id}, Without: {without_id}")
    
    # Check last_result_summary
    with_summary = sum(1 for t in task_list if t.last_result_summary)
    print(f"    With slot data: {with_summary}/{len(task_list)}")
    print()

# 2. Check for problematic ticket names
print("\n2. TICKET NAME ANALYSIS")
print("-" * 80)
unique_names = set(t.ticket_name for t in tasks if t.ticket_name)
print(f"Unique ticket names: {len(unique_names)}\n")

for name in sorted(unique_names):
    count = tasks.filter(ticket_name=name).count()
    print(f"  '{name}': {count} tasks")
    
    # Check for potential matching issues
    name_lower = name.lower()
    issues = []
    
    if 'musei' in name_lower and 'palazzo' in name_lower:
        issues.append("⚠️ Contains both 'musei' and 'palazzo'")
    
    if 'musei' in name_lower and 'biglietti' not in name_lower and 'ingresso' not in name_lower:
        issues.append("⚠️ Musei without 'biglietti' or 'ingresso'")
    
    if issues:
        for issue in issues:
            print(f"    {issue}")

# 3. Check recent check results
print("\n3. RECENT CHECK RESULTS")
print("-" * 80)
recent_checks = CheckResult.objects.filter(
    task__site='vatican',
    task__is_active=True
).order_by('-check_time')[:20]

print(f"Last 20 checks:\n")
for check in recent_checks:
    task = check.task
    date = task.dates[0] if task.dates else 'N/A'
    slots = check.details.get('slots', []) if check.details else []
    
    print(f"  Task #{task.id} ({date})")
    print(f"    Ticket: {task.ticket_name}")
    print(f"    Status: {check.status}")
    print(f"    Slots: {len(slots)}")
    print(f"    Time: {check.check_time.strftime('%H:%M:%S')}")
    print()

# 4. Check for tasks that might have matching issues
print("\n4. POTENTIAL MATCHING ISSUES")
print("-" * 80)

# Tasks looking for Musei Vaticani
musei_tasks = tasks.filter(ticket_name__icontains='musei')
print(f"Tasks looking for 'Musei Vaticani': {musei_tasks.count()}")

for task in musei_tasks:
    # Check if it has been checked recently
    if not task.last_checked:
        print(f"  ⚠️ Task #{task.id} never checked")
    elif task.last_status == 'error':
        print(f"  ❌ Task #{task.id} has error status")
    elif not task.last_result_summary:
        print(f"  ⚠️ Task #{task.id} missing slot data")

# Tasks looking for Palazzo Papale
palazzo_tasks = tasks.filter(ticket_name__icontains='palazzo')
print(f"\nTasks looking for 'Palazzo Papale': {palazzo_tasks.count()}")

# 5. Check keyword coverage
print("\n5. KEYWORD COVERAGE ANALYSIS")
print("-" * 80)

keywords_to_check = {
    'musei': 0,
    'vaticani': 0,
    'palazzo': 0,
    'papale': 0,
    'biglietti': 0,
    'ingresso': 0,
    'aree': 0,
    'museali': 0,
    'visita': 0,
    'guidata': 0
}

for task in tasks:
    if task.ticket_name:
        name_lower = task.ticket_name.lower()
        for keyword in keywords_to_check:
            if keyword in name_lower:
                keywords_to_check[keyword] += 1

print("Keyword usage in task names:")
for keyword, count in sorted(keywords_to_check.items(), key=lambda x: -x[1]):
    print(f"  '{keyword}': {count} tasks")

# 6. Check for edge cases
print("\n6. EDGE CASE DETECTION")
print("-" * 80)

# Tasks with unusual configurations
edge_cases = []

for task in tasks:
    # Check for missing critical fields
    if not task.ticket_name:
        edge_cases.append(f"Task #{task.id}: Missing ticket_name")
    
    # Check for inconsistent ticket_type and language
    if task.ticket_type == 1 and not task.language:
        edge_cases.append(f"Task #{task.id}: Guided tour without language")
    
    if task.ticket_type == 0 and task.language:
        edge_cases.append(f"Task #{task.id}: Standard ticket with language")
    
    # Check for very old last_checked
    if task.last_checked:
        age = (datetime.now(task.last_checked.tzinfo) - task.last_checked).total_seconds()
        if age > 3600:  # More than 1 hour
            edge_cases.append(f"Task #{task.id}: Not checked in {age/3600:.1f} hours")

if edge_cases:
    for case in edge_cases:
        print(f"  ⚠️ {case}")
else:
    print("  ✅ No edge cases detected")

# 7. Verify matching logic would work
print("\n7. MATCHING LOGIC SIMULATION")
print("-" * 80)

# Simulate what would happen with different ticket names from Vatican
test_cases = [
    ("Musei Vaticani - Biglietti d'ingresso", "musei vaticani"),
    ("Palazzo Papale - Biglietti d'ingresso", "musei vaticani"),
    ("Ingresso AREE MUSEALI Singoli", "musei vaticani"),
    ("Specola Vaticana - Visita Guidata", "musei vaticani"),
]

print("Testing matching logic:\n")
for vatican_name, looking_for in test_cases:
    vatican_lower = vatican_name.lower()
    looking_lower = looking_for.lower()
    
    # Simulate keyword matching
    keywords = ['musei', 'vaticani', 'aree', 'museali', 'biglietti', 'ingresso']
    score = sum(1 for kw in keywords if kw in vatican_lower)
    
    # Check exclusions
    excluded = False
    if 'musei' in looking_lower and 'palazzo' in vatican_lower:
        excluded = True
    
    match_result = "✅ MATCH" if score >= 2 and not excluded else "❌ NO MATCH"
    if excluded:
        match_result = "🚫 EXCLUDED"
    
    print(f"  Vatican: '{vatican_name}'")
    print(f"  Looking for: '{looking_for}'")
    print(f"  Score: {score}, Excluded: {excluded}")
    print(f"  Result: {match_result}\n")

# 8. Summary
print("\n8. SYSTEM HEALTH SUMMARY")
print("=" * 80)

total_tasks = tasks.count()
tasks_with_id = tasks.exclude(ticket_id=None).count()
tasks_with_slots = tasks.exclude(last_result_summary=None).count()
tasks_checked_recently = tasks.filter(last_checked__isnull=False).count()

print(f"Total active tasks: {total_tasks}")
print(f"Tasks with ticket_id: {tasks_with_id} ({tasks_with_id/total_tasks*100:.1f}%)")
print(f"Tasks with slot data: {tasks_with_slots} ({tasks_with_slots/total_tasks*100:.1f}%)")
print(f"Tasks checked at least once: {tasks_checked_recently} ({tasks_checked_recently/total_tasks*100:.1f}%)")

# Overall health score
health_score = (tasks_with_id + tasks_with_slots + tasks_checked_recently) / (total_tasks * 3) * 100

print(f"\n🏥 Overall Health Score: {health_score:.1f}%")

if health_score >= 90:
    print("✅ System is in EXCELLENT health")
elif health_score >= 75:
    print("✅ System is in GOOD health")
elif health_score >= 50:
    print("⚠️ System needs attention")
else:
    print("❌ System has CRITICAL issues")

print(f"\n{'='*80}\n")
