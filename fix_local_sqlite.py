#!/usr/bin/env python
"""
Fix local SQLite database by removing legacy fields
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

def remove_legacy_fields():
    """Remove legacy fields from MonitorTask table"""
    print("=" * 80)
    print("🔧 REMOVING LEGACY FIELDS FROM SQLITE")
    print("=" * 80)
    
    # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
    with connection.cursor() as cursor:
        # Clean up any previous failed attempts
        cursor.execute("DROP TABLE IF EXISTS monitors_monitortask_new")
        
        # Get current data
        cursor.execute("SELECT * FROM monitors_monitortask")
        rows = cursor.fetchall()
        
        # Get column names
        cursor.execute("PRAGMA table_info(monitors_monitortask)")
        columns = cursor.fetchall()
        
        # Filter out legacy columns
        legacy_fields = ['pay_mode', 'checkout_method', 'remote_worker_needed', 
                        'remote_worker_claimed', 'agent_target']
        
        keep_columns = [col for col in columns if col[1] not in legacy_fields]
        keep_column_names = [col[1] for col in keep_columns]
        
        print(f"\n📋 Keeping {len(keep_columns)} columns:")
        for col in keep_columns:
            print(f"  ✅ {col[1]}")
        
        print(f"\n🗑️  Removing {len(legacy_fields)} legacy columns:")
        for field in legacy_fields:
            print(f"  ❌ {field}")
        
        # Create new table without legacy fields
        print("\n🔨 Creating new table structure...")
        cursor.execute("""
            CREATE TABLE monitors_monitortask_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site VARCHAR(50) NOT NULL,
                area_name VARCHAR(255) NOT NULL,
                dates TEXT NOT NULL,
                preferred_times TEXT NOT NULL,
                visitors INTEGER NOT NULL,
                ticket_type INTEGER NOT NULL,
                language VARCHAR(10),
                match_strategy VARCHAR(20) NOT NULL,
                notification_mode VARCHAR(20) NOT NULL,
                is_active BOOLEAN NOT NULL,
                last_checked DATETIME,
                last_status VARCHAR(50) NOT NULL,
                last_result_summary TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                agency_id BIGINT NOT NULL,
                check_interval INTEGER NOT NULL,
                ticket_id VARCHAR(255),
                ticket_label VARCHAR(255),
                ticket_name VARCHAR(300),
                tier VARCHAR(20) NOT NULL,
                participants_json TEXT,
                adult_count INTEGER NOT NULL,
                child_count INTEGER NOT NULL,
                FOREIGN KEY (agency_id) REFERENCES monitors_agency(id)
            )
        """)
        
        # Copy data (excluding legacy columns)
        if rows:
            print(f"\n📦 Copying {len(rows)} existing tasks...")
            
            # Get indices of columns to keep
            old_column_names = [col[1] for col in columns]
            keep_indices = [old_column_names.index(name) for name in keep_column_names]
            
            # Prepare insert statement
            placeholders = ','.join(['?' for _ in keep_column_names])
            insert_sql = f"INSERT INTO monitors_monitortask_new ({','.join(keep_column_names)}) VALUES ({placeholders})"
            
            # Copy each row using raw cursor
            import sqlite3
            db_path = os.path.join(os.path.dirname(__file__), 'backend', 'db.sqlite3')
            conn = sqlite3.connect(db_path)
            raw_cursor = conn.cursor()
            
            for row in rows:
                new_row = tuple([row[i] for i in keep_indices])
                raw_cursor.execute(insert_sql, new_row)
            
            conn.commit()
            conn.close()
        
        # Drop old table and rename new one
        print("\n🔄 Replacing old table...")
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.execute("DROP TABLE monitors_monitortask")
        cursor.execute("ALTER TABLE monitors_monitortask_new RENAME TO monitors_monitortask")
        cursor.execute("PRAGMA foreign_keys=ON")
        
        # Recreate indices
        print("\n📇 Creating indices...")
        cursor.execute("CREATE INDEX monitors_monitortask_agency_id_idx ON monitors_monitortask(agency_id)")
        cursor.execute("CREATE INDEX monitors_monitortask_ticket_id_idx ON monitors_monitortask(ticket_id)")
        
        print("\n✅ Done! Legacy fields removed.")

def main():
    print("\n" + "=" * 80)
    print("🔍 FIX LOCAL SQLITE DATABASE")
    print("=" * 80)
    
    remove_legacy_fields()
    
    print("\n" + "=" * 80)
    print("✅ DATABASE FIXED!")
    print("=" * 80)
    print("\nYou can now run: python test_extension_flow_august.py")

if __name__ == '__main__':
    main()
