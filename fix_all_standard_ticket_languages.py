#!/usr/bin/env python3
"""
Fix all standard tickets (ticket_type=0) to have language=None
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask

def fix_standard_ticket_languages():
    """Fix all standard tickets to have language=None"""
    
    # Find all standard tickets with non-null language
    standard_tickets_with_lang = MonitorTask.objects.filter(
        site='vatican',
        ticket_type=0  # Standard tickets
    ).exclude(language=None)
    
    count = standard_tickets_with_lang.count()
    
    if count == 0:
        print("✅ No standard tickets with language set found!")
        return
    
    print(f"🔍 Found {count} standard tickets with language set:")
    print()
    
    for task in standard_tickets_with_lang:
        print(f"Task {task.id}:")
        print(f"   Name: {task.ticket_name}")
        print(f"   Dates: {task.dates}")
        print(f"   Language: {task.language} (WRONG - should be None)")
        print(f"   Type: {task.ticket_type}")
        print(f"   Visitors: {task.visitors}")
        print()
    
    # Fix them
    print(f"🔧 Fixing {count} tasks...")
    updated = standard_tickets_with_lang.update(language=None)
    print(f"✅ Fixed {updated} tasks!")
    print()
    
    # Verify
    print("🔍 Verification:")
    remaining = MonitorTask.objects.filter(
        site='vatican',
        ticket_type=0
    ).exclude(language=None).count()
    
    if remaining == 0:
        print("✅ All standard tickets now have language=None")
    else:
        print(f"⚠️  Still {remaining} standard tickets with language set")
    
    # Show all Vatican tasks
    print()
    print("📋 All Vatican Tasks:")
    all_tasks = MonitorTask.objects.filter(site='vatican').order_by('id')
    for task in all_tasks:
        lang_display = task.language if task.language else "None"
        print(f"Task {task.id}: {task.ticket_name[:40]:40} | Type: {task.ticket_type} | Lang: {lang_display:4} | Visitors: {task.visitors}")

if __name__ == '__main__':
    fix_standard_ticket_languages()
