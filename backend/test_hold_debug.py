"""
Debug recap — inspect what ticket/service IDs Vatican expects
"""
import os, sys, django, requests, json
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

BASE = 'https://tickets.museivaticani.va'
HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': f'{BASE}/',
    'Origin': BASE,
    'Content-Type': 'application/json',
}

# Use Musei Vaticani standard entry on a date with real availability
DATE = '13/04/2026'
VISITORS = 2

s = requests.Session()

# Step 1: Search
r = s.get(f'{BASE}/api/search/resultPerTag', params={
    'lang': 'it', 'visitorNum': str(VISITORS), 'visitDate': DATE,
    'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
}, headers=HEADERS, timeout=15)

visits = r.json().get('visits', [])
jsid = s.cookies.get('JSESSIONID', '')
print(f"JSESSIONID: {jsid[:30]}...")
print(f"\nTickets for {DATE} ({VISITORS}v):")
for v in visits:
    print(f"  [{v['id']}] {v['name']} | {v.get('availability')}")

# Pick Musei Vaticani standard entry
ticket = next((v for v in visits if 'musei vaticani' in v.get('name','').lower() and 'ingresso' in v.get('name','').lower() and v.get('availability') == 'AVAILABLE'), None)
if not ticket:
    ticket = next((v for v in visits if v.get('availability') == 'AVAILABLE'), None)
if not ticket:
    print("No available ticket"); sys.exit(1)

ticket_id = ticket['id']
print(f"\nSelected: [{ticket_id}] {ticket['name']}")

# Step 2: Timeavail
r2 = s.get(f'{BASE}/api/visit/timeavail', params={
    'lang': 'it', 'visitLang': '',
    'visitTypeId': str(ticket_id),
    'visitorNum': str(VISITORS),
    'visitDate': DATE,
}, headers=HEADERS, timeout=15)

timetable = r2.json().get('timetable', [])
print(f"\nSlots:")
for t in timetable:
    print(f"  {t['time']} | {t.get('availability')} | id={t.get('id','?')}")

slot = next((t for t in timetable if t.get('availability') != 'SOLD_OUT'), None)
if not slot:
    print("No open slot"); sys.exit(1)

slot_id = slot.get('id') or slot.get('visitId', '')
print(f"\nUsing slot: {slot['time']} | id={slot_id}")

# Step 3: Services
r3 = s.get(f'{BASE}/api/visit/services', params={
    'lang': 'it', 'visitId': str(slot_id),
    'visitTypeId': str(ticket_id), 'visitorNum': str(VISITORS),
}, headers=HEADERS, timeout=10)
print(f"\nServices ({r3.status_code}): {r3.text[:400]}")
services_raw = (r3.json().get('services') or []) if r3.status_code == 200 else []

# Step 4: GET recap to see what Vatican expects
print(f"\n--- GET /api/visit/recap ---")
r_get = s.get(f'{BASE}/api/visit/recap', params={
    'lang': 'it', 'visitId': str(slot_id),
    'visitTypeId': str(ticket_id), 'visitorNum': str(VISITORS),
}, headers=HEADERS, timeout=10)
print(f"Status: {r_get.status_code}")
print(r_get.text[:800])

# Step 5: Try recap POST with minimal body first
print(f"\n--- POST /api/visit/recap (minimal) ---")
body_minimal = {
    "visitId": str(slot_id),
    "visitTypeId": int(ticket_id),
    "visitorNum": VISITORS,
    "lang": "it",
    "tickets": [],
    "additionalCosts": {},
    "services": [],
}
r4 = s.post(f'{BASE}/api/visit/recap', json=body_minimal, headers=HEADERS, timeout=15)
print(f"Status: {r4.status_code}")
print(r4.text[:600])

# Step 6: Try with standard ticket IDs
print(f"\n--- POST /api/visit/recap (with ticket id=60) ---")
body_std = {
    "visitId": str(slot_id),
    "visitTypeId": int(ticket_id),
    "visitorNum": VISITORS,
    "lang": "it",
    "tickets": [{"id": 60, "name": "Biglietto Intero", "price": 20, "quantity": VISITORS}],
    "additionalCosts": {},
    "services": [],
}
r5 = s.post(f'{BASE}/api/visit/recap', json=body_std, headers=HEADERS, timeout=15)
print(f"Status: {r5.status_code}")
print(r5.text[:600])

if r5.status_code == 200:
    data = r5.json()
    print(f"\n✅ HOLD SUCCESS!")
    print(f"  Total: €{data.get('total')}")
    print(f"  recapId: {data.get('recapId') or data.get('id')}")
    print(f"  Full response: {json.dumps(data, indent=2)[:500]}")
    print(f"\n  Checkout: {BASE}/home/checkout;jsessionid={s.cookies.get('JSESSIONID','')}")
