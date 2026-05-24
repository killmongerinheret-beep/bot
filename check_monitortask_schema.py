#!/usr/bin/env python
"""
Check MonitorTask table schema
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

def check_schema():
    """Check MonitorTask table schema"""
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(monitors_monitortask)")
        columns = cursor.fetchall()
        
        print("=" * 80)
        print("📋 MONITORTASK TABLE COLUMNS:")
        print("=" * 80)
        for col in columns:
            nullable = "NULL" if col[3] == 0 else "NOT NULL"
            default = f" DEFAULT {col[4]}" if col[4] else ""
            print(f"  {col[1]:30} {col[2]:15} {nullable:10}{default}")
        
        # Check for legacy fields
        column_names = [col[1] for col in columns]
        legacy_fields = ['pay_mode', 'checkout_method', 'remote_worker_needed', 
                        'remote_worker_claimed', 'agent_target']
        
        print("\n" + "=" * 80)
        print("🔍 LEGACY FIELD CHECK:")
        print("=" * 80)
        for field in legacy_fields:
            if field in column_names:
                print(f"  ❌ {field} - EXISTS (should be removed)")
            else:
                print(f"  ✅ {field} - NOT FOUND (good)")

if __name__ == '__main__':
    check_schema()
