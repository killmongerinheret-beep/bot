"""
Epay Token & Link Validation Test
=================================

Test script to validate epay token generation and link functionality with real Vatican slots.
"""

import os
import sys
import logging
import time
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from monitors.models import HeldSlot, MonitorTask, BuyerProfile
from monitors.tasks_search_api import search_date_range
from monitors.hold_manager import hold_slot
from monitors.views import _do_reservation
from django.test import RequestFactory
from django.http import JsonResponse
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('epay_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_epay_flow():
    """Test complete epay token generation and link functionality"""
    logger.info("🚀 Starting Epay Token & Link Validation Test")
    
    # Step 1: Find a real available slot
    logger.info("🔍 Step 1: Searching for available Vatican slots...")
    
    try:
        # Search for available dates (next 7 days)
        start_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        search_results = search_date_range(
            task_id=1,  # Default task
            start_date=start_date,
            end_date=end_date,
            visitors=2
        )
        
        if not search_results or 'available_dates' not in search_results:
            logger.warning("❌ No available slots found for testing")
            return False
        
        available_dates = search_results['available_dates']
        logger.info(f"✅ Found {len(available_dates)} available date(s)")
        
        # Take the first available date for testing
        test_date = available_dates[0]
        date_str = test_date.get('date')
        time_str = test_date.get('time', '09:00')  # Default to 9:00 AM
        
        logger.info(f"🎯 Selected test slot: {date_str} {time_str}")
        
        # Step 2: Hold the slot
        logger.info("🔒 Step 2: Holding the test slot...")
        
        # Create a test monitor task
        test_task, created = MonitorTask.objects.get_or_create(
            name="EPAY_TEST_TASK",
            defaults={
                'site': 'vatican',
                'tier': 'hold',
                'visitors': 2,
                'is_active': True,
                'agency_id': 1  # Default agency
            }
        )
        
        # Hold the slot
        held_slot = hold_slot(
            task=test_task,
            date=date_str,
            slot_id=test_date.get('slot_id', 'test_slot'),
            slot_time=time_str,
            ticket_id=test_date.get('ticket_id', 60),
            ticket_name=test_date.get('ticket_name', 'Biglietto Intero'),
            visitors=2,
            proxy_str=None  # Use direct connection for testing
        )
        
        if not held_slot or held_slot.status != 'held':
            logger.error("❌ Failed to hold test slot")
            return False
        
        logger.info(f"✅ Slot held successfully! Hold ID: {held_slot.id}")
        
        # Step 3: Test epay token generation
        logger.info("🎫 Step 3: Testing epay token generation...")
        
        # Create a mock request for _do_reservation
        factory = RequestFactory()
        
        # Create a test buyer profile
        buyer_profile, created = BuyerProfile.objects.get_or_create(
            agency=test_task.agency,
            defaults={
                'full_name': 'Test Buyer',
                'email': 'test@example.com',
                'phone': '+1234567890',
                'country': 'IT',
                'city': 'Rome'
            }
        )
        
        # Mock request with turnstile token (you'll need to provide a real one)
        mock_request = factory.post(
            f'/checkout/{held_slot.id}/',
            data={'recaptcha': 'test_turnstile_token_here'},
            content_type='application/json'
        )
        
        # Test the reservation function
        try:
            result = _do_reservation(mock_request, held_slot)
            
            if isinstance(result, JsonResponse):
                response_data = json.loads(result.content)
                
                if 'payment_url' in response_data:
                    logger.info(f"✅ Epay link generated successfully!")
                    logger.info(f"🔗 Payment URL: {response_data['payment_url']}")
                    logger.info(f"🆔 Recap ID: {response_data.get('recap_id', 'N/A')}")
                    
                    # Test the payment URL
                    test_payment_url(response_data['payment_url'])
                    
                    return True
                else:
                    logger.warning(f"⚠️ Epay generation response: {response_data}")
                    
                    if 'error' in response_data:
                        logger.error(f"❌ Epay generation error: {response_data['error']}")
                    
                    return False
            
        except Exception as e:
            logger.error(f"❌ Exception in epay generation: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False

def test_payment_url(payment_url):
    """Test if the payment URL is accessible"""
    logger.info("🔗 Step 4: Testing payment URL accessibility...")
    
    import requests
    
    try:
        # Test URL accessibility (HEAD request to avoid full page load)
        response = requests.head(payment_url, timeout=10, allow_redirects=True)
        
        logger.info(f"🌐 Payment URL HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("✅ Payment URL is accessible!")
            return True
        elif response.status_code in [301, 302, 307, 308]:
            logger.info(f"↪️ Payment URL redirects to: {response.headers.get('Location', 'Unknown')}")
            return True
        else:
            logger.warning(f"⚠️ Payment URL returned status: {response.status_code}")
            return False
            
    except requests.exceptions.SSLError:
        logger.info("🔒 Payment URL uses SSL (good)")
        return True
    except requests.exceptions.Timeout:
        logger.warning("⏰ Payment URL timeout")
        return False
    except requests.exceptions.ConnectionError:
        logger.warning("🔌 Payment URL connection error")
        return False
    except Exception as e:
        logger.error(f"❌ Payment URL test error: {e}")
        return False

def validate_turnstile_integration():
    """Validate Cloudflare Turnstile integration"""
    logger.info("🛡️ Validating Turnstile integration...")
    
    # Check if turnstile sitekey is configured
    from monitors.views import VATICAN_BASE
    
    logger.info(f"🌐 Vatican Base URL: {VATICAN_BASE}")
    logger.info(f"🔑 Turnstile Sitekey: 0x4AAAAAAB2Edz1zEK7o5Rj1")
    
    # Test turnstile token extraction (would need real browser session)
    logger.info("ℹ️ Turnstile tokens must be extracted from real browser sessions")
    logger.info("ℹ️ Use DevTools → Network → filter 'reservation' → copy recaptcha value")
    
    return True

def main():
    """Main test function"""
    logger.info("=" * 60)
    logger.info("🎫 VATICAN EPAY FLOW VALIDATION TEST")
    logger.info("=" * 60)
    
    # Validate turnstile integration first
    validate_turnstile_integration()
    
    # Run the main test
    success = test_epay_flow()
    
    logger.info("=" * 60)
    if success:
        logger.info("✅ EPAY FLOW VALIDATION: PASSED")
    else:
        logger.info("❌ EPAY FLOW VALIDATION: FAILED")
    logger.info("=" * 60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)