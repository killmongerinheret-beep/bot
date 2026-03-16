#!/usr/bin/env python3
"""
Simple Vatican Monitoring Runner
Runs the Vatican monitoring tasks directly without Celery Beat
"""

import os
import sys
import django
import time
from datetime import datetime

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def run_monitoring():
    """Run Vatican monitoring tasks"""
    try:
        from monitors.tasks import orchestrate_all_tasks
        
        print(f"🚀 Starting Vatican monitoring at {datetime.now()}")
        result = orchestrate_all_tasks()
        print(f"✅ Monitoring result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Monitoring failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_monitoring()
    sys.exit(0 if success else 1)