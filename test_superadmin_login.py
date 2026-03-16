#!/usr/bin/env python3
import os
import sys
import django

sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import User

# Test super admin login
username = "superadmin"
password = "HydraAdmin2026!"

try:
    user = User.objects.get(username=username)
    print(f"User found: {user.username}")
    print(f"Email: {user.email}")
    print(f"Is super admin: {user.is_super_admin}")
    print(f"Password hash format: {user.password_hash[:60]}...")
    print(f"Has $ separator: {'$' in user.password_hash}")
    
    # Test password check
    result = user.check_password(password)
    print(f"\nPassword check result: {result}")
    
    if result:
        print("✅ Login would succeed!")
    else:
        print("❌ Login would fail - password check failed")
        
except User.DoesNotExist:
    print(f"❌ User '{username}' not found")
except Exception as e:
    print(f"❌ Error: {e}")
