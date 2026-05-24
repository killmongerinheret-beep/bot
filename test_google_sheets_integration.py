#!/usr/bin/env python3
"""
Test Google Sheets Integration
================================
This script tests fetching participant data from Google Sheets.

Prerequisites:
1. Google Service Account JSON file at /app/google_credentials.json
2. Google Sheet shared with service account email
3. Sheet has worksheet named "Vatican_Participants"
4. Sheet has columns: First Name, Last Name, Email, Phone, Birth Date, Gender, Notes

Usage:
    docker-compose exec backend python test_google_sheets_integration.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from services.google_sheets_service import get_sheets_service
from monitors.models import Agency

def test_sheets_service():
    """Test Google Sheets service"""
    print("\n" + "=" * 80)
    print("🧪 TESTING GOOGLE SHEETS INTEGRATION")
    print("=" * 80)
    
    # Check if service account file exists
    service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', '/app/google_credentials.json')
    print(f"\n📁 Checking for service account file...")
    print(f"   Path: {service_account_file}")
    
    if os.path.exists(service_account_file):
        print(f"   ✅ Service account file found")
    else:
        print(f"   ❌ Service account file NOT found")
        print(f"\n⚠️  To enable Google Sheets integration:")
        print(f"   1. Create a Google Cloud service account")
        print(f"   2. Download the JSON key file")
        print(f"   3. Place it at: {service_account_file}")
        print(f"   4. Share your Google Sheet with the service account email")
        return False
    
    # Initialize service
    print(f"\n🔧 Initializing Google Sheets service...")
    service = get_sheets_service()
    
    if not service.client:
        print(f"   ❌ Failed to initialize Google Sheets client")
        return False
    
    print(f"   ✅ Google Sheets client initialized")
    
    # Test with agency
    print(f"\n🏢 Testing with agencies...")
    agencies = Agency.objects.all()
    
    if not agencies.exists():
        print(f"   ⚠️  No agencies found in database")
        return False
    
    for agency in agencies:
        print(f"\n   Agency: {agency.name} (ID: {agency.id})")
        
        sheet_url = getattr(agency, 'google_sheet_url', None)
        if not sheet_url:
            print(f"      ⚠️  No Google Sheet URL configured")
            continue
        
        print(f"      Sheet URL: {sheet_url}")
        
        # Fetch participants
        print(f"      📥 Fetching participants...")
        participants = service.get_participants_for_agency(agency.id)
        
        if participants:
            print(f"      ✅ Found {len(participants)} participants:")
            for i, p in enumerate(participants[:5], 1):  # Show first 5
                print(f"         {i}. {p['first_name']} {p['last_name']} ({p.get('email', 'no email')})")
            
            if len(participants) > 5:
                print(f"         ... and {len(participants) - 5} more")
        else:
            print(f"      ❌ No participants found")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)
    return True

def test_direct_sheet_url():
    """Test with a direct sheet URL"""
    print("\n" + "=" * 80)
    print("🧪 TESTING DIRECT SHEET URL")
    print("=" * 80)
    
    # Prompt for sheet URL
    print("\n📝 Enter your Google Sheet URL:")
    print("   (or press Enter to skip)")
    sheet_url = input("   URL: ").strip()
    
    if not sheet_url:
        print("   ⏭️  Skipped")
        return
    
    service = get_sheets_service()
    
    if not service.client:
        print("   ❌ Google Sheets client not initialized")
        return
    
    print(f"\n📥 Fetching participants from sheet...")
    participants = service.get_participants_from_sheet(sheet_url)
    
    if participants:
        print(f"✅ Found {len(participants)} participants:")
        for i, p in enumerate(participants, 1):
            print(f"   {i}. {p['first_name']} {p['last_name']}")
            print(f"      Email: {p.get('email', 'N/A')}")
            print(f"      Phone: {p.get('phone', 'N/A')}")
            print(f"      Birth Date: {p.get('birth_date', 'N/A')}")
            print()
    else:
        print("❌ No participants found")
        print("\n⚠️  Make sure:")
        print("   1. Sheet is shared with service account email")
        print("   2. Sheet has worksheet named 'Vatican_Participants'")
        print("   3. Sheet has columns: First Name, Last Name, Email, Phone, Birth Date, Gender")

def main():
    """Main test function"""
    try:
        # Test with agencies
        test_sheets_service()
        
        # Test with direct URL (optional)
        # test_direct_sheet_url()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
