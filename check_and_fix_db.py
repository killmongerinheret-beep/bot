#!/usr/bin/env python
"""
Check and fix the database schema for google_sheet_url column
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

def check_column_exists():
    """Check if google_sheet_url column exists"""
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(monitors_agency)")
        columns = cursor.fetchall()
        
        print("=" * 80)
        print("📋 CURRENT AGENCY TABLE COLUMNS:")
        print("=" * 80)
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Check if google_sheet_url exists
        column_names = [col[1] for col in columns]
        if 'google_sheet_url' in column_names:
            print("\n✅ google_sheet_url column EXISTS")
            return True
        else:
            print("\n❌ google_sheet_url column MISSING")
            return False

def add_column():
    """Manually add the google_sheet_url column"""
    print("\n" + "=" * 80)
    print("🔧 ADDING google_sheet_url COLUMN...")
    print("=" * 80)
    
    with connection.cursor() as cursor:
        try:
            cursor.execute("""
                ALTER TABLE monitors_agency 
                ADD COLUMN google_sheet_url VARCHAR(500) NULL
            """)
            print("✅ Column added successfully!")
            return True
        except Exception as e:
            print(f"❌ Error adding column: {e}")
            return False

def main():
    print("\n" + "=" * 80)
    print("🔍 DATABASE SCHEMA CHECK")
    print("=" * 80)
    
    exists = check_column_exists()
    
    if not exists:
        print("\n⚠️  Column is missing. Attempting to add it...")
        if add_column():
            print("\n✅ Database fixed! Verifying...")
            check_column_exists()
        else:
            print("\n❌ Failed to fix database")
            sys.exit(1)
    else:
        print("\n✅ Database schema is correct!")
    
    print("\n" + "=" * 80)
    print("✅ DONE")
    print("=" * 80)

if __name__ == '__main__':
    main()
