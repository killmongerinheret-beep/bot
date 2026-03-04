#!/usr/bin/env python
"""
Fix Task #19 - Remove language from standard ticket
"""
import os
import sys
import django

# Setup Django - adjust path for Docker environment
backend_path = '/app/backend' if os.path.exists('/app/backend') else os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask

print("="*60)
print("Fixing Task #19 - Language Configuration")
print("="*60)
print()

# Fix Task #19
try:
    task = MonitorTask.objects.get(id=19)
    
    print(f"Task #19 - Current Configuration:")
    print(f"  ID: {task.id}")
    print(f"  Date: {task.dates[0] if task.dates else 'N/A'}")
    print(f"  Ticket Type: {task.ticket_type} ({'Standard' if task.ticket_type == 0 else 'Guided'})")
    print(f"  Ticket Name: {task.ticket_name}")
    print(f"  Language: {task.language}")
    print(f"  Visitors: {task.visitors}")
    print()
    
    # Check if fix is needed
    if task.ticket_type == 0 and task.language:
        print("⚠️  ISSUE FOUND:")
        print("   Standard tickets (ticket_type=0) should NOT have a language")
        print("   Language is only for guided tours (ticket_type=1)")
        print()
        print("🔧 Applying fix...")
        
        task.language = None
        task.save()
        
        print("✅ FIXED!")
        print()
        print(f"Task #19 - Updated Configuration:")
        print(f"  Language: {task.language} ← Now correct!")
        print()
        print("The bot will now check this task correctly.")
        
    elif task.ticket_type == 1 and not task.language:
        print("⚠️  ISSUE FOUND:")
        print("   Guided tours (ticket_type=1) MUST have a language")
        print()
        print("Please set language to one of: ENG, ITA, FRA, DEU, SPA")
        
    else:
        print("✅ Task configuration is already correct!")
        print("   No changes needed.")
    
    print()
    print("="*60)
    
except MonitorTask.DoesNotExist:
    print("❌ Task #19 not found!")
    print()
    print("Available tasks:")
    for t in MonitorTask.objects.all():
        print(f"  - Task #{t.id}: {t.dates[0] if t.dates else 'N/A'} - {t.ticket_name}")
