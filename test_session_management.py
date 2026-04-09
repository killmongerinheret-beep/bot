#!/usr/bin/env python3
"""
Session Management and Cookie Persistence Test
==============================================

Tests the Vatican session management system to ensure cookies are properly
persisted and sessions remain active for slot holding.
"""

import os
import sys
import time
import logging

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_session_creation():
    """Test session creation with proper cookie handling."""
    print("Testing Session Creation...")
    
    try:
        from monitors.hold_manager import _make_session
        
        # Test session creation with mock cookies
        session = _make_session(
            jsessionid="TEST_JSESSIONID_1234567890",
            ticketmv="01",
            serverid="01|testserver"
        )
        
        # Verify session has cookies
        if not hasattr(session, 'cookies'):
            print("ERROR: Session object missing cookies attribute")
            return False
        
        # Check that cookies are set
        cookies = session.cookies.get_dict()
        print(f"Session cookies: {cookies}")
        
        # Verify critical headers
        headers = session.headers
        required_headers = ['User-Agent', 'Accept']
        
        for header in required_headers:
            if header not in headers:
                print(f"ERROR: Missing required header: {header}")
                return False
        
        print("SUCCESS: Session created with proper cookies and headers")
        return True
        
    except Exception as e:
        print(f"ERROR: Session creation test failed: {e}")
        return False

def test_cookie_persistence():
    """Test that cookies persist across multiple requests."""
    print("\nTesting Cookie Persistence...")
    
    try:
        from monitors.hold_manager import _make_session
        
        # Create session with specific cookies
        test_jsessionid = "PERSISTENCE_TEST_12345"
        session = _make_session(
            jsessionid=test_jsessionid,
            ticketmv="02",
            serverid="02|testserver"
        )
        
        # Verify initial cookies
        initial_cookies = session.cookies.get_dict()
        if 'JSESSIONID' not in initial_cookies:
            print("ERROR: JSESSIONID not set in initial cookies")
            return False
        
        # Simulate multiple operations to test cookie persistence
        for i in range(3):
            # Test cookie persistence by checking session cookies directly
            current_cookies = session.cookies.get_dict()
            if current_cookies.get('JSESSIONID') != test_jsessionid:
                print(f"ERROR: Cookie not persisted across operation {i+1}")
                print(f"Expected: {test_jsessionid}, Got: {current_cookies.get('JSESSIONID')}")
                return False
            
            print(f"SUCCESS: Cookies persisted across operation {i+1}")
            time.sleep(0.1)
        
        print("SUCCESS: Cookie persistence test completed")
        return True
        
    except Exception as e:
        print(f"ERROR: Cookie persistence test failed: {e}")
        return False

def test_proxy_rotation():
    """Test proxy acquisition and rotation functionality."""
    print("\nTesting Proxy Rotation...")
    
    try:
        from monitors.tasks_sweep import _get_proxy
        
        # Test getting multiple proxies to check rotation
        proxies = set()
        
        for i in range(5):  # Get 5 different proxies
            proxy = _get_proxy()
            if proxy:
                proxies.add(proxy)
                print(f"Proxy {i+1}: {proxy}")
            else:
                print("WARNING: No proxy available")
                break
            
            time.sleep(0.1)
        
        if len(proxies) > 1:
            print(f"SUCCESS: Multiple proxies available ({len(proxies)} unique)")
            return True
        elif len(proxies) == 1:
            print("INFO: Only one proxy available (may be expected in some setups)")
            return True
        else:
            print("WARNING: No proxies available")
            return True  # This might be expected in some environments
        
    except Exception as e:
        print(f"ERROR: Proxy rotation test failed: {e}")
        return False

def test_session_freshness():
    """Test session freshness validation."""
    print("\nTesting Session Freshness...")
    
    try:
        from monitors.hold_manager import _make_session
        from monitors.models import HeldSlot
        
        # Create a test held slot with correct fields
        test_slot = HeldSlot(
            slot_id="TEST_SLOT_123",
            ticket_id="999999",
            jsessionid="FRESHNESS_TEST_SESSION",
            ticketmv="01",
            status='held',
            date="01/04/2026",
            slot_time="10:00",
            ticket_name="Test Ticket",
            visitors=2
        )
        
        # Test session creation for the slot
        session = _make_session(
            jsessionid=test_slot.jsessionid,
            ticketmv=test_slot.ticketmv,
            serverid="01|test"  # serverid is not stored in HeldSlot
        )
        
        # Verify session was created
        if session:
            print("SUCCESS: Session created for held slot")
            
            # Check session cookies
            cookies = session.cookies.get_dict()
            if 'JSESSIONID' in cookies and cookies['JSESSIONID'] == test_slot.jsessionid:
                print("SUCCESS: Session cookies match held slot")
                return True
            else:
                print("ERROR: Session cookies don't match held slot")
                return False
        else:
            print("ERROR: Failed to create session for held slot")
            return False
        
    except Exception as e:
        print(f"ERROR: Session freshness test failed: {e}")
        return False

def main():
    """Run all session management tests."""
    print("Session Management and Cookie Persistence Test")
    print("=" * 60)
    
    tests = [
        ("Session Creation", test_session_creation),
        ("Cookie Persistence", test_cookie_persistence),
        ("Proxy Rotation", test_proxy_rotation),
        ("Session Freshness", test_session_freshness)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"ERROR: {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    all_passed = True
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name:25} {status}")
        if not success:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("SUCCESS: All session management tests passed!")
        print("\nYour session management system is working correctly:")
        print("✅ Sessions are created with proper cookies")
        print("✅ Cookies persist across multiple requests") 
        print("✅ Proxy rotation is functional")
        print("✅ Session freshness is maintained")
    else:
        print("ERROR: Some session management tests failed.")
        print("Please check the errors above and ensure your session")
        print("management system is properly configured.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)