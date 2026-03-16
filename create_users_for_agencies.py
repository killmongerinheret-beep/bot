#!/usr/bin/env python3
"""
Create initial users for existing agencies
"""
import os
import sys
import django

sys.path.insert(0, 'backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import Agency, User

print("=" * 80)
print("CREATE USERS FOR EXISTING AGENCIES")
print("=" * 80)

agencies = Agency.objects.all()

print(f"\nFound {agencies.count()} agencies\n")

for agency in agencies:
    print(f"\nAgency: {agency.name} (ID: {agency.id})")
    
    # Check if agency already has users
    existing_users = User.objects.filter(agency=agency).count()
    if existing_users > 0:
        print(f"  ✅ Already has {existing_users} user(s)")
        continue
    
    # Create default user for this agency
    username = agency.name.lower().replace(' ', '_').replace("'", '')[:50]
    email = f"{username}@agency.local"
    
    # Check if username/email already exists
    if User.objects.filter(username=username).exists():
        username = f"{username}_{agency.id}"
    if User.objects.filter(email=email).exists():
        email = f"{username}_{agency.id}@agency.local"
    
    # Create user
    user = User.objects.create(
        email=email,
        username=username,
        full_name=f"{agency.name} Admin",
        agency=agency,
        is_admin=True
    )
    
    # Set default password (agency name without spaces)
    default_password = agency.name.replace(' ', '').lower()
    user.set_password(default_password)
    user.save()
    
    print(f"  ✅ Created user:")
    print(f"     Username: {username}")
    print(f"     Email: {email}")
    print(f"     Password: {default_password}")
    print(f"     ⚠️  CHANGE THIS PASSWORD AFTER FIRST LOGIN!")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

all_users = User.objects.all()
print(f"\nTotal users created: {all_users.count()}")
print("\nUser List:")
for user in all_users:
    print(f"  - {user.username} ({user.email}) → {user.agency.name}")

print("\n" + "=" * 80)
print("NEXT STEPS")
print("=" * 80)
print("\n1. Users can now login at: http://localhost:3000")
print("2. Each user should change their password after first login")
print("3. Users can only see their own agency's data")
print("\n" + "=" * 80)
