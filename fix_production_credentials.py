#!/usr/bin/env python3
"""
Fix credentials for the PRODUCTION database agencies you listed.
This will create/reset users for agencies ID 3-14.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import User, Agency

print("=" * 80)
print("FIXING PRODUCTION DATABASE CREDENTIALS")
print("=" * 80)
print()

# The agencies you listed
target_agencies = [
    {'id': 3, 'name': 'Vatican Bot Agency 1', 'username': 'vatican_bot_agency_1'},
    {'id': 4, 'name': 'Vatican Bot Agency 2', 'username': 'wondersofrome'},
    {'id': 6, 'name': 'System Admin', 'username': 'superadmin'},
    {'id': 7, 'name': 'Agency-admin', 'username': None},  # No username listed
    {'id': 9, 'name': 'Tour_guides', 'username': 'Tourguides'},
    {'id': 10, 'name': 'Italy pass', 'username': 'Italypass'},
    {'id': 11, 'name': 'Big bus', 'username': 'bigbus'},
    {'id': 12, 'name': 'Wondersofrome', 'username': 'wondersofrome123'},
    {'id': 13, 'name': 'Mahabur', 'username': 'Bot123'},
    {'id': 14, 'name': 'WOR', 'username': None},  # No username listed
]

print("Checking agencies from your list...\n")

results = []

for target in target_agencies:
    agency_id = target['id']
    expected_name = target['name']
    expected_username = target['username']
    
    # Try to find agency
    try:
        agency = Agency.objects.get(id=agency_id)
        print(f"✅ Found Agency ID {agency_id}: {agency.name}")
        
        # Check if name matches
        if agency.name != expected_name:
            print(f"   ⚠️  Name mismatch: Expected '{expected_name}', got '{agency.name}'")
        
        # Check for existing users
        users = User.objects.filter(agency=agency)
        
        if users.exists():
            print(f"   👥 Existing users: {users.count()}")
            for user in users:
                print(f"      - {user.username}")
                # Reset password
                user.set_password('hydra2026')
                user.is_active = True
                user.save()
                print(f"        ✅ Password reset to: hydra2026")
                
                results.append({
                    'agency_id': agency_id,
                    'agency_name': agency.name,
                    'username': user.username,
                    'password': 'hydra2026',
                    'status': 'reset'
                })
        else:
            print(f"   ⚠️  No users found")
            
            # Create user if username was provided
            if expected_username:
                # Check if username already exists
                if User.objects.filter(username=expected_username).exists():
                    print(f"      ❌ Username '{expected_username}' already exists - skipping")
                else:
                    user = User.objects.create(
                        username=expected_username,
                        email=f"{expected_username}@agency.local",
                        agency=agency,
                        is_active=True,
                        is_admin=True
                    )
                    user.set_password('hydra2026')
                    user.save()
                    print(f"      ✅ Created user: {expected_username}")
                    print(f"         Password: hydra2026")
                    
                    results.append({
                        'agency_id': agency_id,
                        'agency_name': agency.name,
                        'username': expected_username,
                        'password': 'hydra2026',
                        'status': 'created'
                    })
            else:
                # Generate username from agency name
                auto_username = agency.name.lower().replace(' ', '_').replace('-', '_')[:30]
                if User.objects.filter(username=auto_username).exists():
                    auto_username = f"{auto_username}_{agency_id}"
                
                user = User.objects.create(
                    username=auto_username,
                    email=f"{auto_username}@agency.local",
                    agency=agency,
                    is_active=True,
                    is_admin=True
                )
                user.set_password('hydra2026')
                user.save()
                print(f"      ✅ Created user: {auto_username}")
                print(f"         Password: hydra2026")
                
                results.append({
                    'agency_id': agency_id,
                    'agency_name': agency.name,
                    'username': auto_username,
                    'password': 'hydra2026',
                    'status': 'created'
                })
        
        print()
        
    except Agency.DoesNotExist:
        print(f"❌ Agency ID {agency_id} not found in database")
        print(f"   Expected: {expected_name}")
        print()

print("=" * 80)
print("FINAL CREDENTIALS LIST")
print("=" * 80)
print()

for result in results:
    print(f"Agency: {result['agency_name']} (ID: {result['agency_id']})")
    print(f"  Username: {result['username']}")
    print(f"  Password: {result['password']}")
    print(f"  Status: {result['status']}")
    print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()
print(f"✅ Processed {len(results)} accounts")
print(f"🔐 All passwords set to: hydra2026")
print(f"🌐 Login at: https://hydrabot.it")
print()

# Also check ALL agencies in current database
print("=" * 80)
print("ALL AGENCIES IN CURRENT DATABASE")
print("=" * 80)
print()

all_agencies = Agency.objects.all().order_by('id')
print(f"Total agencies: {all_agencies.count()}\n")

for agency in all_agencies:
    users = User.objects.filter(agency=agency)
    print(f"ID {agency.id}: {agency.name} ({agency.plan}) - {users.count()} user(s)")
    for user in users:
        print(f"   - {user.username}")

print()
