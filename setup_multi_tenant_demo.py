#!/usr/bin/env python3
"""
Setup Multi-Tenant Demo Data
Creates multiple agencies with users and tasks to demonstrate isolation
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import Agency, User, MonitorTask, TelegramGroup
import hashlib
import secrets

def create_password_hash(password):
    """Create secure password hash"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{password_hash}:{salt}"

def main():
    print("=" * 80)
    print("SETUP MULTI-TENANT DEMO DATA")
    print("=" * 80)
    
    # Create agencies
    agencies_data = [
        {"name": "Alpha Travel Agency", "plan": "premium"},
        {"name": "Beta Tours & Travel", "plan": "standard"},
        {"name": "Gamma Vacation Services", "plan": "premium"},
    ]
    
    agencies = []
    for agency_data in agencies_data:
        agency, created = Agency.objects.get_or_create(
            name=agency_data["name"],
            defaults={
                "plan": agency_data["plan"],
                "is_active": True
            }
        )
        agencies.append(agency)
        status = "✅ Created" if created else "ℹ️  Exists"
        print(f"{status} Agency: {agency.name} (ID: {agency.id})")
    
    print()
    
    # Create users for each agency
    users_data = [
        {"username": "alpha_travel", "email": "alpha@travel.com", "password": "alpha123", "agency_idx": 0},
        {"username": "beta_tours", "email": "beta@tours.com", "password": "beta123", "agency_idx": 1},
        {"username": "gamma_vacation", "email": "gamma@vacation.com", "password": "gamma123", "agency_idx": 2},
    ]
    
    users = []
    for user_data in users_data:
        agency = agencies[user_data["agency_idx"]]
        user, created = User.objects.get_or_create(
            username=user_data["username"],
            defaults={
                "email": user_data["email"],
                "password_hash": create_password_hash(user_data["password"]),
                "full_name": f"{agency.name} Admin",
                "agency": agency,
                "is_active": True,
                "is_admin": True
            }
        )
        users.append(user)
        status = "✅ Created" if created else "ℹ️  Exists"
        print(f"{status} User: {user.username} → {agency.name}")
        if created:
            print(f"    Password: {user_data['password']} (CHANGE AFTER LOGIN)")
    
    print()
    
    # Create sample tasks for each agency
    today = datetime.now()
    
    tasks_data = [
        # Alpha Travel Agency tasks
        {
            "agency_idx": 0,
            "ticket_name": "Musei Vaticani - Biglietti d'ingresso",
            "ticket_type": 0,
            "language": None,
            "dates": [(today + timedelta(days=7)).strftime("%d/%m/%Y"), (today + timedelta(days=14)).strftime("%d/%m/%Y")],
            "visitors": 2,
            "preferred_times": ["09:00", "10:30"]
        },
        {
            "agency_idx": 0,
            "ticket_name": "Musei Vaticani - Visita Guidata",
            "ticket_type": 1,
            "language": "ENG",
            "dates": [(today + timedelta(days=10)).strftime("%d/%m/%Y")],
            "visitors": 4,
            "preferred_times": ["14:00", "15:30"]
        },
        
        # Beta Tours & Travel tasks
        {
            "agency_idx": 1,
            "ticket_name": "Musei Vaticani - Biglietti d'ingresso",
            "ticket_type": 0,
            "language": None,
            "dates": [(today + timedelta(days=5)).strftime("%d/%m/%Y"), (today + timedelta(days=12)).strftime("%d/%m/%Y")],
            "visitors": 1,
            "preferred_times": ["11:00", "16:00"]
        },
        {
            "agency_idx": 1,
            "ticket_name": "Musei Vaticani - Visita Guidata",
            "ticket_type": 1,
            "language": "ITA",
            "dates": [(today + timedelta(days=8)).strftime("%d/%m/%Y")],
            "visitors": 3,
            "preferred_times": ["10:00"]
        },
        
        # Gamma Vacation Services tasks
        {
            "agency_idx": 2,
            "ticket_name": "Musei Vaticani - Visita Guidata",
            "ticket_type": 1,
            "language": "FRA",
            "dates": [(today + timedelta(days=6)).strftime("%d/%m/%Y"), (today + timedelta(days=13)).strftime("%d/%m/%Y")],
            "visitors": 2,
            "preferred_times": ["09:30", "14:30"]
        },
    ]
    
    print("=== CREATING TASKS ===")
    for task_data in tasks_data:
        agency = agencies[task_data["agency_idx"]]
        
        # Check if similar task exists
        existing = MonitorTask.objects.filter(
            agency=agency,
            ticket_name=task_data["ticket_name"],
            ticket_type=task_data["ticket_type"],
            language=task_data["language"]
        ).first()
        
        if existing:
            print(f"ℹ️  Task exists: {agency.name} - {task_data['ticket_name']}")
            continue
        
        task = MonitorTask.objects.create(
            agency=agency,
            site='vatican',
            area_name='Musei Vaticani',
            dates=task_data["dates"],
            preferred_times=task_data["preferred_times"],
            visitors=task_data["visitors"],
            ticket_type=task_data["ticket_type"],
            ticket_name=task_data["ticket_name"],
            language=task_data["language"],
            check_interval=300,  # 5 minutes
            tier='monitor',
            match_strategy='any',
            notification_mode='available_only',
            is_active=True
        )
        
        lang_info = f" ({task_data['language']})" if task_data['language'] else ""
        print(f"✅ Created: {agency.name} - {task_data['ticket_name']}{lang_info}")
    
    print()
    print("=" * 80)
    print("MULTI-TENANT DEMO DATA SUMMARY")
    print("=" * 80)
    
    # Summary
    for i, agency in enumerate(agencies):
        user = users[i] if i < len(users) else None
        tasks = MonitorTask.objects.filter(agency=agency)
        
        print(f"\n🏢 {agency.name}")
        print(f"   Plan: {agency.plan}")
        if user:
            print(f"   👤 Login: {user.username} / {users_data[i]['password']}")
        print(f"   📋 Tasks: {tasks.count()}")
        
        for task in tasks:
            lang_info = f" ({task.language})" if task.language else ""
            print(f"      • {task.ticket_name}{lang_info} - {len(task.dates)} dates")
    
    print()
    print("=" * 80)
    print("TESTING INSTRUCTIONS")
    print("=" * 80)
    print()
    print("1. Go to: https://bot-front-beta.vercel.app")
    print()
    print("2. Test Multi-Tenant Isolation:")
    print()
    print("   Login as Alpha Travel:")
    print("   Username: alpha_travel")
    print("   Password: alpha123")
    print("   → Should see 2 tasks (Standard + Guided ENG)")
    print()
    print("   Logout and login as Beta Tours:")
    print("   Username: beta_tours") 
    print("   Password: beta123")
    print("   → Should see 2 different tasks (Standard + Guided ITA)")
    print()
    print("   Logout and login as Gamma Vacation:")
    print("   Username: gamma_vacation")
    print("   Password: gamma123")
    print("   → Should see 1 task (Guided FRA)")
    print()
    print("3. Verify Isolation:")
    print("   - Each user sees only their agency's tasks")
    print("   - Cannot see other agencies' data")
    print("   - Can create/delete only their own tasks")
    print()
    print("=" * 80)
    print("✅ SETUP COMPLETE - READY FOR TESTING")
    print("=" * 80)

if __name__ == "__main__":
    main()