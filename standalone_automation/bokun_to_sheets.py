import json
import requests
import gspread
from google.oauth2.service_account import Credentials
import datetime
import os
import time

# Load configuration
CONFIG_FILE = 'config.json'

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def get_bokun_bookings(config):
    """Fetch recent bookings from Bokun"""
    bokun_cfg = config['bokun']
    url = f"{bokun_cfg['api_url']}/booking.json/query"
    
    # Common Bokun API headers
    headers = {
        'X-Bokun-AccessKey': bokun_cfg['access_key'],
        'X-Bokun-SecretKey': bokun_cfg['secret_key'],
        'Content-Type': 'application/json'
    }
    
    # Query for confirmed bookings in the next 30 days
    start_date = datetime.date.today().isoformat()
    end_date = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
    
    query = {
        "status": "CONFIRMED",
        "startDate": start_date,
        "endDate": end_date
    }
    
    print(f"Fetching bookings from Bokun ({start_date} to {end_date})...")
    try:
        response = requests.post(url, headers=headers, json=query)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching from Bokun: {response.status_code} - {response.text}")
            # Try GET if POST fails (depends on API version)
            response = requests.get(url, headers=headers, params=query)
            if response.status_code == 200:
                return response.json()
            return []
    except Exception as e:
        print(f"Bokun API Connection Error: {e}")
        return []

def update_google_sheet(config, bookings):
    """Update Google Sheet with participant data"""
    gs_cfg = config['google_sheets']
    
    if not os.path.exists(gs_cfg['credentials_file']):
        print(f"Error: {gs_cfg['credentials_file']} not found. Please place your Google Service Account JSON file in this folder.")
        return
    
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    try:
        creds = Credentials.from_service_account_file(gs_cfg['credentials_file'], scopes=scopes)
        client = gspread.authorize(creds)
        
        spreadsheet = client.open_by_key(gs_cfg['spreadsheet_id'])
        
        try:
            worksheet = spreadsheet.worksheet(gs_cfg['sheet_name'])
        except gspread.exceptions.WorksheetNotFound:
            print(f"Worksheet '{gs_cfg['sheet_name']}' not found. Creating it...")
            worksheet = spreadsheet.add_worksheet(title=gs_cfg['sheet_name'], rows="100", cols="10")
            # Add headers
            headers = ["First Name", "Last Name", "Email", "Phone", "Birth Date", "Gender", "Booking ID", "Date"]
            worksheet.append_row(headers)

        # Get existing records to avoid duplicates
        existing_records = worksheet.get_all_records()
        existing_booking_ids = set(str(r.get('Booking ID', '')) for r in existing_records)
        
        new_rows = []
        for booking in bookings:
            booking_id = str(booking.get('id', ''))
            if booking_id in existing_booking_ids:
                continue
                
            # Extract participants
            # Note: Bokun data structure varies. This is a common pattern.
            items = booking.get('items', [])
            booking_date = booking.get('startDate', 'N/A')
            
            for item in items:
                passengers = item.get('passengers', [])
                if not passengers:
                    # Fallback to main contact if no passengers
                    contact = booking.get('mainContact', {})
                    if contact:
                        new_rows.append([
                            contact.get('firstName', ''),
                            contact.get('lastName', ''),
                            contact.get('email', ''),
                            contact.get('phoneNumber', ''),
                            contact.get('dateOfBirth', ''),
                            'M',
                            booking_id,
                            booking_date
                        ])
                else:
                    for p in passengers:
                        new_rows.append([
                            p.get('firstName', ''),
                            p.get('lastName', ''),
                            p.get('email', '') or booking.get('mainContact', {}).get('email', ''),
                            p.get('phoneNumber', '') or booking.get('mainContact', {}).get('phoneNumber', ''),
                            p.get('dateOfBirth', ''),
                            'M',
                            booking_id,
                            booking_date
                        ])
        
        if new_rows:
            print(f"Adding {len(new_rows)} new participants to sheet...")
            worksheet.append_rows(new_rows)
            print("Successfully updated Google Sheet.")
        else:
            print("No new participants to add.")
            
    except Exception as e:
        print(f"Google Sheets Error: {e}")

def create_bot_tasks(config, bookings):
    """Create monitoring tasks in the bot for new bookings"""
    bot_cfg = config['bot']
    url = f"{bot_cfg['api_url']}/api/v1/tasks/"
    
    print("Checking if tasks need to be created in the bot...")
    
    for booking in bookings:
        # We only care about Vatican bookings (hypothetically)
        # We'll create a task for each booking date if it doesn't exist
        date = booking.get('startDate') # Format: YYYY-MM-DD
        visitors = booking.get('totalPassengerCount', 1)
        
        if not date:
            continue
            
        task_data = {
            "agency": bot_cfg['agency_id'],
            "site": "vatican",
            "area_name": "Musei Vaticani",
            "dates": [date],
            "preferred_times": ["08:30", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00"],
            "visitors": visitors,
            "adult_count": visitors,
            "child_count": 0,
            "ticket_type": 0, # Regular
            "tier": "snipe", # Auto-pay
            "is_active": True
        }
        
        try:
            # First check if task already exists for this date and agency
            # For simplicity, we'll just try to POST and let the bot handle duplicates or just create them
            response = requests.post(url, json=task_data)
            if response.status_code == 201:
                print(f"Created bot task for {date} ({visitors} visitors)")
            elif response.status_code == 400:
                # Likely already exists or validation error
                pass
        except Exception as e:
            print(f"Bot API Error: {e}")

def main():
    print("--- Bokun to Google Sheets Automation ---")
    try:
        config = load_config()
        bookings = get_bokun_bookings(config)
        
        if bookings:
            print(f"Found {len(bookings)} bookings in Bokun.")
            update_google_sheet(config, bookings)
            create_bot_tasks(config, bookings)
        else:
            print("No bookings found in Bokun.")
            
    except FileNotFoundError:
        print("Error: config.json not found.")
    except Exception as e:
        print(f"Unexpected Error: {e}")

if __name__ == "__main__":
    main()
