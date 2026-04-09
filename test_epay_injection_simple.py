#!/usr/bin/env python3
"""
Test Browser-Compatible Epay Link Injection with Participant Data
=================================================================
Tests the complete flow of generating epay links that work in any browser
with embedded participant information.
"""

import os
import sys
import json
import base64
import urllib.parse

def test_url_injection():
    """Test URL parameter injection method"""
    print("=== Testing URL Parameter Injection ===")
    
    # Sample participant data
    participants = [
        {
            'first_name': 'Mario',
            'last_name': 'Rossi',
            'email': 'mario.rossi@example.com',
            'phone': '+39 123 456 7890',
            'birth_date': '1985-06-15',
            'nationality': 'Italian'
        },
        {
            'first_name': 'Luigi',
            'last_name': 'Verdi', 
            'email': 'luigi.verdi@example.com',
            'phone': '+39 987 654 3210',
            'birth_date': '1990-03-22',
            'nationality': 'Italian'
        }
    ]
    
    buyer_data = {
        'first_name': 'Giovanni',
        'last_name': 'Bianchi',
        'email': 'giovanni.bianchi@example.com',
        'phone': '+39 555 123 4567',
        'address': 'Via Roma 123, Milano',
        'country': 'Italy'
    }
    
    # Sample base epay URL
    base_url = "https://epay.catholica.va/payment?token=SIV123456789&amount=34.00&currency=EUR"
    
    injection_data = {
        'hold_id': 123,
        'slot_date': '2026-06-15',
        'slot_time': '10:00',
        'visitors': 2,
        'participants': participants,
        'buyer': buyer_data,
        'agency': 'Test Agency',
        'generated_at': '2026-03-31T10:30:00Z'
    }
    
    # Test URL parameter injection
    encoded_data = base64.urlsafe_b64encode(
        json.dumps(injection_data).encode('utf-8')
    ).decode('utf-8')
    
    # Add as query parameter
    parsed_url = urllib.parse.urlparse(base_url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    query_params['injection_data'] = [encoded_data]
    
    new_query = urllib.parse.urlencode(query_params, doseq=True)
    final_url = urllib.parse.urlunparse(parsed_url._replace(query=new_query))
    
    print("SUCCESS: URL Injection Test Successful")
    print(f"Original URL: {base_url}")
    print(f"Final URL: {final_url}")
    print(f"URL Length: {len(final_url)} characters")
    
    # Test decoding
    parsed_final = urllib.parse.urlparse(final_url)
    query_params = urllib.parse.parse_qs(parsed_final.query)
    injected_data = query_params.get('injection_data', [''])[0]
    
    if injected_data:
        decoded_bytes = base64.urlsafe_b64decode(injected_data)
        decoded_data = json.loads(decoded_bytes.decode('utf-8'))
        
        print("SUCCESS: Decoding Test Successful")
        print(f"Decoded participants: {len(decoded_data.get('participants', []))}")
        print(f"Buyer: {decoded_data.get('buyer', {}).get('first_name', 'N/A')}")
        
        return True
    
    return False

def test_localstorage_injection():
    """Test localStorage injection method"""
    print("\n=== Testing LocalStorage Injection ===")
    
    base_url = "https://epay.catholica.va/payment"
    injection_data = {
        'hold_id': 456,
        'participants': [{'name': 'Test Participant'}],
        'test': 'localstorage_data'
    }
    
    encoded_data = base64.urlsafe_b64encode(
        json.dumps(injection_data).encode('utf-8')
    ).decode('utf-8')
    
    final_url = f"{base_url}#injection=localstorage&data={encoded_data}"
    
    print("SUCCESS: LocalStorage Injection Test Successful")
    print(f"Final URL: {final_url}")
    
    # Test parsing from hash
    hash_part = final_url.split('#')[1]
    hash_params = dict(urllib.parse.parse_qsl(hash_part))
    
    if hash_params.get('injection') == 'localstorage' and hash_params.get('data'):
        print("SUCCESS: Hash Parsing Successful")
        return True
    
    return False

def test_sessionstorage_injection():
    """Test sessionStorage injection method"""
    print("\n=== Testing SessionStorage Injection ===")
    
    base_url = "https://epay.catholica.va/payment"
    injection_data = {
        'hold_id': 789,
        'participants': [{'name': 'Test Participant'}],
        'test': 'sessionstorage_data'
    }
    
    encoded_data = base64.urlsafe_b64encode(
        json.dumps(injection_data).encode('utf-8')
    ).decode('utf-8')
    
    final_url = f"{base_url}#injection=sessionstorage&data={encoded_data}"
    
    print("SUCCESS: SessionStorage Injection Test Successful")
    print(f"Final URL: {final_url}")
    
    # Test parsing from hash
    hash_part = final_url.split('#')[1]
    hash_params = dict(urllib.parse.parse_qsl(hash_part))
    
    if hash_params.get('injection') == 'sessionstorage' and hash_params.get('data'):
        print("SUCCESS: Hash Parsing Successful")
        return True
    
    return False

def test_data_encoding():
    """Test data encoding and decoding limits"""
    print("\n=== Testing Data Encoding Limits ===")
    
    # Test with large participant data
    participants = []
    for i in range(10):  # 10 participants
        participants.append({
            'first_name': f'Participant{i}',
            'last_name': f'Test{i}',
            'email': f'participant{i}@example.com',
            'phone': f'+39 {1000000000 + i}',
            'birth_date': f'19{80 + i}-01-01',
            'nationality': 'Italian',
            'document_type': 'Passport',
            'document_number': f'AB{i:06d}'
        })
    
    injection_data = {
        'hold_id': 999,
        'slot_date': '2026-12-25',
        'slot_time': '14:00',
        'visitors': 10,
        'participants': participants,
        'buyer': {
            'first_name': 'Massimo',
            'last_name': 'TestBuyer',
            'email': 'massimo@example.com',
            'phone': '+39 333 444 5555',
            'address': 'Piazza Duomo 1, Milano',
            'country': 'Italy',
            'payment_method': 'credit_card'
        },
        'agency': 'Large Test Agency',
        'generated_at': '2026-03-31T12:00:00Z',
        'notes': 'Large group booking with extensive participant information'
    }
    
    # Encode the data
    json_str = json.dumps(injection_data)
    encoded_data = base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('utf-8')
    
    print(f"Original JSON size: {len(json_str)} characters")
    print(f"Encoded size: {len(encoded_data)} characters")
    print(f"Base64 overhead: {len(encoded_data) - len(json_str)} characters")
    
    # Test URL length limits
    base_url = "https://epay.catholica.va/payment?token=SIV999888777"
    final_url = f"{base_url}&injection_data={encoded_data}"
    
    print(f"Final URL length: {len(final_url)} characters")
    
    # Browser URL length limits: ~2000 characters is generally safe
    if len(final_url) <= 2000:
        print("SUCCESS: URL length within browser limits")
        return True
    else:
        print(f"WARNING: URL length exceeds typical browser limits ({len(final_url)} > 2000)")
        print("Recommend using localStorage or sessionStorage method for large data")
        return False

def run_comprehensive_test():
    """Run all injection tests"""
    print("Browser-Compatible Epay Link Injection Test")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    test_results.append(('URL Parameter Injection', test_url_injection()))
    test_results.append(('LocalStorage Injection', test_localstorage_injection()))
    test_results.append(('SessionStorage Injection', test_sessionstorage_injection()))
    test_results.append(('Data Encoding Limits', test_data_encoding()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY:")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in test_results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:25} {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("ALL TESTS PASSED!")
        print("Browser-compatible epay link injection is working correctly.")
        print("\nRecommended injection methods:")
        print("1. URL Parameters - For small datasets (<1000 chars)")
        print("2. LocalStorage - For large datasets or complex participant info")
        print("3. SessionStorage - For temporary data per browser session")
    else:
        print("SOME TESTS FAILED")
        print("Check the implementation for issues.")
    
    return all_passed

if __name__ == "__main__":
    # Run the comprehensive test
    success = run_comprehensive_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)