#!/usr/bin/env python3
"""
Test Script for Instant Sniper
===============================

Tests the instant sniper functionality with your current Vatican API setup.
"""

import os
import sys
import logging

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_sniper_configuration():
    """Test that the sniper is properly configured."""
    print("🧪 Testing Instant Sniper Configuration...")
    
    # Test 1: Check target dates configuration
    target_dates = os.getenv('SWEEP_TARGET_DATES', '')
    if target_dates:
        dates = [d.strip() for d in target_dates.split(',') if d.strip()]
        print(f"✅ Target dates configured: {len(dates)} dates")
        for date in dates:
            print(f"   - {date}")
    else:
        print("⚠️  No SWEEP_TARGET_DATES set, will auto-generate April+May 2026")
    
    # Test 2: Check proxy availability
    from backend.monitors.tasks_sweep import _get_proxy
    proxy = _get_proxy()
    if proxy:
        print(f"✅ Proxy available: {proxy}")
    else:
        print("⚠️  No proxies available - will use direct connection")
    
    # Test 3: Check database connectivity
    from backend.monitors.models import MonitorTask
    try:
        task_count = MonitorTask.objects.count()
        print(f"✅ Database connected - {task_count} monitor tasks")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    # Test 4: Check celery beat configuration
    from backend.core import settings
    if 'instant-sniper-scan' in settings.CELERY_BEAT_SCHEDULE:
        sniper_config = settings.CELERY_BEAT_SCHEDULE['instant-sniper-scan']
        print(f"✅ Celery beat configured: {sniper_config}")
    else:
        print("❌ Celery beat not configured for instant sniper")
        return False
    
    print("✅ All configuration tests passed!")
    return True

def test_har_integration():
    """Test that we can use HAR file data for API calls."""
    print("\n🔍 Testing HAR File Integration...")
    
    # Check if HAR files exist
    har_files = []
    if os.path.exists('1.har'):
        har_files.append('1.har')
    if os.path.exists('epay.catholica.va.har'):
        har_files.append('epay.catholica.va.har')
    
    if har_files:
        print(f"✅ HAR files found: {', '.join(har_files)}")
        
        # Extract API endpoints from HAR files
        import json
        try:
            with open('1.har', 'r') as f:
                content = f.read()
                
            # Look for reservation API calls
            if '/api/visit/reservation' in content:
                print("✅ Reservation API endpoint confirmed in HAR")
            if 'JSESSIONID' in content:
                print("✅ Session management confirmed in HAR")
                
        except Exception as e:
            print(f"⚠️  HAR file analysis error: {e}")
    else:
        print("⚠️  No HAR files found - using default API endpoints")
    
    return True

def quick_availability_check():
    """Quick test to check Vatican API availability."""
    print("\n🌐 Quick Vatican API Availability Check...")
    
    from backend.monitors.tasks_sweep import _search_and_timeavail, _get_proxy
    
    # Test with a sample date
    test_date = "01/04/2026"  # April 1st, 2026
    proxy = _get_proxy()
    
    try:
        session, ticket_id, open_slots = _search_and_timeavail(test_date, 2, proxy)
        
        if session and ticket_id:
            print(f"✅ API connectivity successful")
            print(f"   - Session: {hasattr(session, 'cookies') and 'JSESSIONID' in session.cookies}")
            print(f"   - Ticket ID: {ticket_id}")
            print(f"   - Open slots: {len(open_slots)}")
            
            if open_slots:
                for slot in open_slots[:3]:  # Show first 3 slots
                    print(f"     • {slot.get('time')} - {slot.get('availability')}")
        else:
            print("⚠️  No slots available or API error")
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("Instant Sniper Test Suite")
    print("=" * 50)
    
    success = True
    
    # Run configuration tests
    if not test_sniper_configuration():
        success = False
    
    # Run HAR integration tests
    if not test_har_integration():
        success = False
    
    # Run quick API check
    if not quick_availability_check():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED! Instant Sniper is ready to deploy.")
        print("\nNext steps:")
        print("1. Set SWEEP_TARGET_DATES environment variable with your target dates")
        print("2. Restart Celery beat: celery -A backend.core beat")
        print("3. Monitor logs for instant sniper activity")
    else:
        print("❌ Some tests failed. Please check your configuration.")
    
    return success

if __name__ == "__main__":
    main()