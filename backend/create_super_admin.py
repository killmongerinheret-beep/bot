#!/usr/bin/env python3
"""
Create Super Admin User
Creates a super admin user for accessing the admin panel
"""

import os
import sys
import django
import hashlib
import secrets

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import User, Agency

def create_password_hash(password):
    """Create secure password hash matching User model format"""
    salt = secrets.token_hex(16)
    password_with_salt = f"{password}{salt}"
    password_hash = hashlib.sha256(password_with_salt.encode()).hexdigest()
    return f"{salt}${password_hash}"

def main():
    print("=" * 80)
    print("CREATE SUPER ADMIN USER")
    print("=" * 80)
    
    # Super admin credentials
    username = "superadmin"
    email = "admin@hydrasnipe.it"
    password = "HydraAdmin2026!"
    
    # Check if super admin already exists
    if User.objects.filter(username=username).exists():
        print(f"⚠️  Super admin '{username}' already exists!")
        
        # Ask if we should update password
        update = input("Update password? (y/N): ").lower().strip()
        if update == 'y':
            user = User.objects.get(username=username)
            user.password_hash = create_password_hash(password)
            user.is_super_admin = True
            user.is_active = True
            user.save()
            print("✅ Password updated successfully!")
        else:
            print("ℹ️  No changes made.")
        
        print(f"\n🔑 Super Admin Credentials:")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"   URL: http://localhost:3000/admin")
        return
    
    # Get or create a system agency for super admin
    system_agency, created = Agency.objects.get_or_create(
        name="System Administration",
        defaults={
            "plan": "system",
            "is_active": True
        }
    )
    
    if created:
        print(f"✅ Created system agency: {system_agency.name}")
    else:
        print(f"ℹ️  Using existing system agency: {system_agency.name}")
    
    # Create super admin user
    super_admin = User.objects.create(
        username=username,
        email=email,
        password_hash=create_password_hash(password),
        full_name="System Administrator",
        agency=system_agency,
        is_active=True,
        is_admin=True,
        is_super_admin=True  # Special flag for super admin
    )
    
    print(f"✅ Created super admin user: {username}")
    
    print("\n" + "=" * 80)
    print("SUPER ADMIN CREATED SUCCESSFULLY")
    print("=" * 80)
    
    print(f"\n🔑 Super Admin Credentials:")
    print(f"   Username: {username}")
    print(f"   Password: {password}")
    print(f"   Email: {email}")
    
    print(f"\n🌐 Access URLs:")
    print(f"   Local: http://localhost:3000/admin")
    print(f"   Production: https://bot-front-beta.vercel.app/admin")
    
    print(f"\n🛡️  Permissions:")
    print(f"   ✅ View all agencies")
    print(f"   ✅ Manage all users")
    print(f"   ✅ View all tasks")
    print(f"   ✅ System statistics")
    print(f"   ✅ Create/edit/delete agencies")
    print(f"   ✅ Reset user passwords")
    
    print(f"\n⚠️  SECURITY NOTES:")
    print(f"   • Change the password after first login")
    print(f"   • Keep credentials secure")
    print(f"   • Super admin has full system access")
    print(f"   • Use only for administrative tasks")
    
    print("\n" + "=" * 80)
    print("READY TO USE ADMIN PANEL")
    print("=" * 80)

if __name__ == "__main__":
    main()