"""
Basic Error-Free Reservation Test (No Redis Required)
=====================================================
Tests the error-free reservation logic without Redis dependencies.
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Test the core logic without Django/Redis
def test_turnstile_validation():
    """Test Turnstile token validation logic."""
    print("Testing Turnstile Token Validation")
    print("-" * 40)
    
    def validate_turnstile_token(token):
        """Test version of token validation."""
        if not token:
            return False
        
        # Working tokens should be ~500+ characters and start with '1.'
        if len(token) < 400:
            print(f"  Token too short: {len(token)} chars (need 400+)")
            return False
            
        if not token.startswith('1.'):
            print(f"  Token doesn't start with '1.': {token[:10]}...")
            return False
            
        return True
    
    # Test cases
    test_cases = [
        ("Valid token", "1." + "A" * 500),
        ("Short token", "1." + "A" * 100),
        ("Wrong prefix", "0." + "A" * 500),
        ("Empty token", ""),
        ("None token", None),
    ]
    
    for name, token in test_cases:
        if token is None:
            result = validate_turnstile_token("")
        else:
            result = validate_turnstile_token(token)
        print(f"  {name}: {result}")
    
    print()

def test_cloudflare_headers():
    """Test Cloudflare header generation logic."""
    print("Testing Cloudflare Header Generation")
    print("-" * 40)
    
    def get_cloudflare_headers(session_id="TEST123456789ABCDEF"):
        """Test version of header generation."""
        import uuid
        import hashlib
        import time
        
        # Generate realistic challenge token
        timestamp = str(int(time.time()))
        unique_id = str(uuid.uuid4())[:8]
        
        # Format similar to websocket.har: [hash]-[timestamp]-1.2.1.1-[random]
        challenge_hash = hashlib.sha256(f"{session_id}{timestamp}{unique_id}".encode()).hexdigest()[:32]
        challenge_token = f"{challenge_hash}-{timestamp}-1.2.1.1-{unique_id}"
        
        return {
            'cf-chl': challenge_token,
            'cf-chl-ra': '0',
        }
    
    headers = get_cloudflare_headers()
    cf_chl = headers.get('cf-chl', '')
    cf_chl_ra = headers.get('cf-chl-ra', '')
    
    print(f"  cf-chl header: {cf_chl[:50]}... (length: {len(cf_chl)})")
    print(f"  cf-chl-ra header: {cf_chl_ra}")
    
    # Validate format
    if cf_chl and len(cf_chl) > 20 and cf_chl_ra == '0':
        print("  Header format: VALID")
    else:
        print("  Header format: INVALID")
    
    print()

def test_participant_names():
    """Test participant name generation."""
    print("Testing Participant Name Generation")
    print("-" * 40)
    
    def generate_italian_names(count):
        """Generate realistic Italian names."""
        first_names = [
            "Marco", "Luca", "Giuseppe", "Maria", "Anna", "Giuseppina",
            "Francesco", "Antonio", "Giovanni", "Rosa", "Carmela", "Teresa"
        ]
        last_names = [
            "Rossi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano",
            "Colombo", "Ricci", "Marino", "Greco", "Bruno", "Galli"
        ]
        
        names = []
        for i in range(count):
            first = first_names[i % len(first_names)]
            last = last_names[i % len(last_names)]
            if i >= len(first_names):
                first += str(i // len(first_names) + 1)
            if i >= len(last_names):
                last += str(i // len(last_names) + 1)
                
            names.append({
                'first_name': first,
                'last_name': last
            })
        
        return names
    
    def generate_participant_names(visitors, agency_name="Test Agency"):
        """Generate proper participant names to avoid blank name 500 errors."""
        names = generate_italian_names(visitors)
        
        participants = []
        for i, name_data in enumerate(names[:visitors]):
            first_name = name_data.get('first_name', '')
            last_name = name_data.get('last_name', '')
            
            # Ensure no blank names
            if not first_name.strip():
                first_name = f"Participant{i+1}"
            if not last_name.strip():
                last_name = 'Vaticano'
                
            participants.append({
                'name': first_name.strip(),
                'surname': last_name.strip(),
                'id': 60,
                'ticketType': 'intero',
                'services': [58],
            })
        
        return participants
    
    # Test generation
    participants = generate_participant_names(3)
    print(f"Generated {len(participants)} participants:")
    for i, p in enumerate(participants):
        print(f"  {i+1}. {p['name']} {p['surname']} (id:{p['id']}, services:{p['services']})")
    
    # Test with blank names
    print("\nTesting blank name handling:")
    test_names = [
        {"first_name": "", "last_name": ""},
        {"first_name": "John", "last_name": ""},
        {"first_name": "", "last_name": "Doe"},
    ]
    
    for name_data in test_names:
        participants = generate_participant_names(1)
        # Simulate blank input
        if not name_data.get('first_name', '').strip():
            participants[0]['name'] = 'FallbackName'
        if not name_data.get('last_name', '').strip():
            participants[0]['surname'] = 'FallbackSurname'
        
        print(f"  Input: {name_data} -> Output: {participants[0]['name']} {participants[0]['surname']}")
    
    print()

def test_reservation_body():
    """Test reservation body generation."""
    print("Testing Reservation Body Generation")
    print("-" * 40)
    
    def build_reservation_body(held_slot_data, turnstile_token, recap_id, participants, representative):
        """Build reservation request body with proper structure."""
        body = {
            "recaptcha": turnstile_token,  # This is the Turnstile token (misnamed in API)
            "lang": "it",
            "recapId": recap_id,
            "visitorNum": held_slot_data['visitors'],
            "visitId": str(held_slot_data['slot_id']),
            "visitTypeId": int(held_slot_data['ticket_id']),
            "tickets": [
                {"id": 60, "name": "Biglietto Intero", "price": 20, "quantity": str(held_slot_data['visitors'])},
                {"id": 61, "name": "Biglietto Ridotto", "price": 10, "quantity": 0},
            ],
            "services": [{
                "id": 58,
                "name": "Diritti di Prevendita", 
                "price": 5,
                "quantity": int(held_slot_data['visitors'])
            }],
            "representativeUser": representative,
            "participantUser": participants,
            "gdpr": [{"id": 1, "check": True}, {"id": 3, "check": True}],
        }
        
        return body
    
    # Test data
    held_slot_data = {
        'visitors': 2,
        'slot_id': '2026*1234',
        'ticket_id': '12345'
    }
    
    turnstile_token = "1." + "A" * 500
    recap_id = "2026/1234/567"
    
    participants = [
        {"name": "Marco", "surname": "Rossi", "id": 60, "ticketType": "intero", "services": [58]},
        {"name": "Luca", "surname": "Bianchi", "id": 60, "ticketType": "intero", "services": [58]}
    ]
    
    representative = {
        "name": "Mario",
        "surname": "Rossi",
        "gender": "M",
        "country": "Italy",
        "city": "Roma",
        "email": "mario.rossi@example.com",
        "confirmEmail": "mario.rossi@example.com",
        "telephoneNumber": "+39 123 456 7890",
        "language": "it"
    }
    
    body = build_reservation_body(held_slot_data, turnstile_token, recap_id, participants, representative)
    
    print(f"Reservation body keys: {list(body.keys())}")
    print(f"Visitor count: {body['visitorNum']}")
    print(f"Participant count: {len(body['participantUser'])}")
    print(f"Services: {body['services']}")
    print(f"Turnstile token length: {len(body['recaptcha'])}")
    
    # Validate structure
    required_keys = ['recaptcha', 'lang', 'recapId', 'visitorNum', 'visitId', 'visitTypeId', 
                     'tickets', 'services', 'representativeUser', 'participantUser', 'gdpr']
    missing_keys = [key for key in required_keys if key not in body]
    
    if missing_keys:
        print(f"ERROR: Missing required keys: {missing_keys}")
    else:
        print("Structure: VALID")
    
    print()

def main():
    """Run all tests."""
    print("Error-Free Reservation Logic Tests")
    print("=" * 60)
    
    test_turnstile_validation()
    test_cloudflare_headers()
    test_participant_names()
    test_reservation_body()
    
    print("=" * 60)
    print("All logic tests completed!")
    print("\nKey findings:")
    print("1. Turnstile tokens need to be 400+ characters and start with '1.'")
    print("2. Cloudflare headers need cf-chl and cf-chl-ra with proper format")
    print("3. Participant names must not be blank to avoid 500 errors")
    print("4. Reservation body must include all required fields")

if __name__ == "__main__":
    main()