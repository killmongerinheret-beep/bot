#!/usr/bin/env python3
"""
Check all login credentials in the database and test them.
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
print("CHECKING ALL USER LOGIN CREDENTIALS")
print("=" * 80)
print()

users = User.objects.all().select_related('agency')

if not users:
    print("❌ No users found in database!")
    print()
    print("Creating a test user...")
    
    # Create or get first agency
    agency = Agency.objects.filter(is_active=True).first()
    if not agency:
        import secrets
        agency = Agency.objects.create(
            name="Test Agency",
            api_key=secrets.token_hex(16),
            plan='agency',
            is_active=True
        )
        print(f"✅ Created agency: {agency.name}")
    
    # Create test user
    test_user = User.objects.create(
        email="admin@hydrabot.it",
        username="admin",
        full_name="Admin User",
        agency=agency,
        is_active=True,
        is_admin=True,
        is_super_admin=True
    )
    test_user.set_password("admin123")
    test_user.save()
    
    print(f"✅ Created test user:")
    print(f"   Username: admin")
    print(f"   Password: admin123")
    print(f"   Email: admin@hydrabot.it")
    print()
    
    users = [test_user]

print(f"Found {users.count()} user(s):\n")

for user in users:
    print(f"{'='*80}")
    print(f"👤 User: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   Full Name: {user.full_name}")
    print(f"   Agency: {user.agency.name} ({user.agency.plan})")
    print(f"   Active: {'✅' if user.is_active else '❌'}")
    print(f"   Admin: {'✅' if user.is_admin else '❌'}")
    print(f"   Super Admin: {'✅' if user.is_super_admin else '❌'}")
    print(f"   Last Login: {user.last_login or 'Never'}")
    print(f"   Password Hash: {user.password_hash[:50]}...")
    print()
    
    # Test password verification
    test_passwords = ["admin123", "password", "admin", user.username, ""]
    print(f"   Testing common passwords:")
    for pwd in test_passwords:
        if user.check_password(pwd):
            print(f"   ✅ Password is: '{pwd}'")
            break
    else:
        print(f"   ⚠️  Password not in common list - check manually")
    print()

print("=" * 80)
print("HYDRABOT.IT LOGIN INSTRUCTIONS")
print("=" * 80)
print()
print("1. Open: https://hydrabot.it (or your deployed URL)")
print("2. Use the credentials shown above")
print("3. If login fails, check:")
print("   - Is the backend running?")
print("   - Is the database connected?")
print("   - Are you using the correct URL?")
print()
print("To create a new user, run:")
print("   python backend/manage.py shell")
print("   >>> from monitors.models import User, Agency")
print("   >>> agency = Agency.objects.first()")
print("   >>> user = User.objects.create(username='newuser', email='new@example.com', agency=agency)")
print("   >>> user.set_password('yourpassword')")
print("   >>> user.save()")
print()
