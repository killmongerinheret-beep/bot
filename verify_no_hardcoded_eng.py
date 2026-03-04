#!/usr/bin/env python3
"""
Verify there are no hardcoded 'ENG' defaults for standard tickets
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask

def verify_no_hardcoded_eng():
    """Verify no standard tickets have hardcoded ENG"""
    
    print("="*70)
    print("VERIFICATION: NO HARDCODED 'ENG' FOR STANDARD TICKETS")
    print("="*70)
    print()
    
    # Check all Vatican tasks
    all_vatican_tasks = MonitorTask.objects.filter(site='vatican').order_by('id')
    
    print(f"📊 Total Vatican Tasks: {all_vatican_tasks.count()}")
    print()
    
    # Separate by type
    standard_tickets = all_vatican_tasks.filter(ticket_type=0)
    guided_tours = all_vatican_tasks.filter(ticket_type=1)
    
    print(f"🎫 Standard Tickets (Type 0): {standard_tickets.count()}")
    print(f"🎫 Guided Tours (Type 1): {guided_tours.count()}")
    print()
    
    # Check standard tickets for language
    print("="*70)
    print("STANDARD TICKETS CHECK")
    print("="*70)
    print()
    
    issues_found = False
    
    for task in standard_tickets:
        lang_display = f"'{task.language}'" if task.language else "None"
        status = "✅" if task.language is None else "❌"
        
        print(f"{status} Task {task.id}: {task.ticket_name[:50]:50}")
        print(f"   Language: {lang_display:10} | Visitors: {task.visitors} | Dates: {len(task.dates)}")
        
        if task.language is not None:
            print(f"   ⚠️  WARNING: Standard ticket should have language=None!")
            issues_found = True
        print()
    
    # Check guided tours
    print("="*70)
    print("GUIDED TOURS CHECK")
    print("="*70)
    print()
    
    for task in guided_tours:
        lang_display = f"'{task.language}'" if task.language else "None"
        status = "✅" if task.language is not None else "⚠️ "
        
        print(f"{status} Task {task.id}: {task.ticket_name[:50]:50}")
        print(f"   Language: {lang_display:10} | Visitors: {task.visitors} | Dates: {len(task.dates)}")
        
        if task.language is None:
            print(f"   ⚠️  WARNING: Guided tour should have a language!")
        print()
    
    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()
    
    standard_with_lang = standard_tickets.exclude(language=None).count()
    guided_without_lang = guided_tours.filter(language=None).count()
    
    if standard_with_lang == 0 and guided_without_lang == 0:
        print("✅ ALL TASKS CORRECTLY CONFIGURED!")
        print()
        print("   ✅ All standard tickets have language=None")
        print("   ✅ All guided tours have a language set")
        return True
    else:
        print("❌ ISSUES FOUND:")
        print()
        if standard_with_lang > 0:
            print(f"   ❌ {standard_with_lang} standard tickets have language set (should be None)")
        if guided_without_lang > 0:
            print(f"   ❌ {guided_without_lang} guided tours have no language (should have one)")
        return False

if __name__ == '__main__':
    success = verify_no_hardcoded_eng()
    sys.exit(0 if success else 1)
