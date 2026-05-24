#!/usr/bin/env python3
"""
Reset all user passwords to known values for testing.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import User

print("=" * 80)
print("RESETTING ALL USER PASSWORDS")
print("=" * 80)
print()

# Default password for all users
DEFAULT_PASSWORD = "hydra2026"

users = User.objects.all()

print(f"Resetting passwords for {users.count()} users...\n")

credentials = []

for user in users:
    # Reset password
    user.set_password(DEFAULT_PASSWORD)
    user.is_active = True  # Ensure user is active
    user.save()
    
    credentials.append({
        'username': user.username,
        'email': user.email,
        'password': DEFAULT_PASSWORD,
        'agency': user.agency.name,
        'plan': user.agency.plan
    })
    
    print(f"✅ Reset: {user.username}")

print()
print("=" * 80)
print("ALL CREDENTIALS (hydrabot.it login)")
print("=" * 80)
print()

for cred in credentials:
    print(f"Username: {cred['username']}")
    print(f"Password: {cred['password']}")
    print(f"Email:    {cred['email']}")
    print(f"Agency:   {cred['agency']} ({cred['plan']})")
    print("-" * 80)

print()
print("🔐 All passwords have been reset to: hydra2026")
print()
print("Login at: https://hydrabot.it")
print("Or local: http://localhost:3000")
print()
