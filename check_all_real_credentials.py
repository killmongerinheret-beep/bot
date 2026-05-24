#!/usr/bin/env python3
"""
Check ALL agencies and users in the REAL database.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import User, Agency, TelegramGroup

print("=" * 80)
print("COMPLETE DATABASE AUDIT - ALL AGENCIES & USERS")
print("=" * 80)
print()

# Get ALL agencies
agencies = Agency.objects.all().order_by('id')

print(f"🏢 Found {agencies.count()} agencies in database:\n")

all_credentials = []

for agency in agencies:
    print(f"{'='*80}")
    print(f"ID: {agency.id}")
    print(f"🏢 Agency: {agency.name}")
    print(f"   Plan: {agency.plan}")
    print(f"   Active: {'✅' if agency.is_active else '❌'}")
    print(f"   API Key: {agency.api_key[:20]}..." if agency.api_key else "   API Key: None")
    
    # Get users for this agency
    users = User.objects.filter(agency=agency)
    print(f"   👥 Users: {users.count()}")
    
    if users.count() == 0:
        print(f"      ⚠️  NO USERS - Cannot login to web interface!")
    else:
        for user in users:
            print(f"      - Username: {user.username}")
            print(f"        Email: {user.email or '(none)'}")
            print(f"        Active: {'✅' if user.is_active else '❌'}")
            print(f"        Admin: {'✅' if user.is_admin else '❌'}")
            print(f"        Super Admin: {'✅' if user.is_super_admin else '❌'}")
            
            all_credentials.append({
                'agency_id': agency.id,
                'agency_name': agency.name,
                'plan': agency.plan,
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active
            })
    
    # Get Telegram groups for this agency
    groups = TelegramGroup.objects.filter(agency=agency)
    print(f"   💬 Telegram Groups: {groups.count()}")
    for group in groups:
        status_icon = '✅' if group.status == 'approved' else '⏳' if group.status == 'pending' else '❌'
        print(f"      {status_icon} {group.chat_title} ({group.chat_id}) - {group.status}")
    
    print()

print("=" * 80)
print("AGENCIES WITHOUT USERS (CANNOT LOGIN)")
print("=" * 80)
print()

agencies_without_users = []
for agency in agencies:
    if not User.objects.filter(agency=agency).exists():
        agencies_without_users.append(agency)
        print(f"⚠️  {agency.name} (ID: {agency.id}) - NO USERS")

if not agencies_without_users:
    print("✅ All agencies have at least one user")

print()
print("=" * 80)
print("RESET ALL PASSWORDS TO: hydra2026")
print("=" * 80)
print()

confirm = input("Do you want to reset ALL user passwords to 'hydra2026'? (yes/no): ")

if confirm.lower() == 'yes':
    print("\n🔄 Resetting passwords...\n")
    
    all_users = User.objects.all()
    for user in all_users:
        user.set_password('hydra2026')
        user.is_active = True  # Ensure active
        user.save()
        print(f"✅ Reset: {user.username} ({user.agency.name})")
    
    print(f"\n✅ Reset {all_users.count()} passwords to: hydra2026")
    
    print("\n" + "=" * 80)
    print("ALL LOGIN CREDENTIALS")
    print("=" * 80)
    print()
    
    for cred in all_credentials:
        if cred['is_active']:
            print(f"Agency: {cred['agency_name']} (ID: {cred['agency_id']}, Plan: {cred['plan']})")
            print(f"  Username: {cred['username']}")
            print(f"  Password: hydra2026")
            print(f"  Email: {cred['email'] or '(none)'}")
            print()
    
    print("=" * 80)
    print("CREATE USERS FOR AGENCIES WITHOUT USERS")
    print("=" * 80)
    print()
    
    if agencies_without_users:
        create = input(f"Create default users for {len(agencies_without_users)} agencies? (yes/no): ")
        
        if create.lower() == 'yes':
            for agency in agencies_without_users:
                # Create username from agency name
                username = agency.name.lower().replace(' ', '_').replace('-', '_')[:30]
                
                # Check if username exists
                if User.objects.filter(username=username).exists():
                    username = f"{username}_{agency.id}"
                
                user = User.objects.create(
                    username=username,
                    email=f"{username}@agency.local",
                    agency=agency,
                    is_active=True,
                    is_admin=True
                )
                user.set_password('hydra2026')
                user.save()
                
                print(f"✅ Created user: {username} for {agency.name}")
                print(f"   Password: hydra2026")
                print()
else:
    print("\n❌ Password reset cancelled")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print()
print(f"Total Agencies: {agencies.count()}")
print(f"Total Users: {User.objects.count()}")
print(f"Total Telegram Groups: {TelegramGroup.objects.count()}")
print()
print("Login URL: https://hydrabot.it")
print("All passwords: hydra2026")
print()
