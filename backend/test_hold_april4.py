"""
Test hold: April 4, 5 visitors, 14:30, all adults (standard entry)
"""
import os, sys, django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import requests
import json

BASE = 'https://tickets.museivaticani.va'
DATE = '13/04/2026'
VISITORS = 2
TARGET_TIME = '09:00'

HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': f'{BASE}/',
    'Origin': BASE,
}

s = requests.Session()

print(f"{'='*55}")
print(f"  HOLD TEST — {DATE} | {VISITORS} visitors | {TARGET_TIME}")
print(f"{'='*55}\n")

# ── STEP 1: Search API → fresh ticket ID + JSESSIONID ──
print("STEP 1: Search API...")
r = s.get(f'{BASE}/api/search/resultPerTag', params={
    'lang': 'it',
    'visitorNum': str(VISITORS),
    'visitDate': DATE,
    'area': '1',
    'who': '',
    'page': '0',
    'tag': 'MV-Biglietti'
}, headers=HEADERS, timeout=15)

print(f"  Status: {r.status_code}")
if r.status_code != 200:
    print(f"  ERROR: {r.text[:200]}")
    sys.exit(1)

data = r.json()
visits = data.get('visits', [])
jsessionid = s.cookies.get('JSESSIONID', '')
print(f"  JSESSIONID: {jsessionid[:30]}...")
print(f"  Tickets found: {len(visits)}")

# Find standard entry ticket
ticket = None
for v in visits:
    name = v.get('name', '').lower()
    print(f"    - [{v['id']}] {v.get('name')} | avail={v.get('availability')}")
    if 'ingresso' in name and ticket is None:
        ticket = v

if not ticket:
    print("\n  No standard entry ticket found — trying first available")
    ticket = visits[0] if visits else None

if not ticket:
    print("  FATAL: No tickets at all for this date/visitor combo")
    sys.exit(1)

ticket_id = ticket['id']
ticket_name = ticket.get('name', '')
print(f"\n  Selected: [{ticket_id}] {ticket_name}")

# ── STEP 2: Time availability ──
print(f"\nSTEP 2: Time availability for {TARGET_TIME}...")
r2 = s.get(f'{BASE}/api/visit/timeavail', params={
    'lang': 'it',
    'visitLang': '',
    'visitTypeId': str(ticket_id),
    'visitorNum': str(VISITORS),
    'visitDate': DATE,
}, headers=HEADERS, timeout=15)

print(f"  Status: {r2.status_code}")
if r2.status_code != 200:
    print(f"  ERROR: {r2.text[:200]}")
    sys.exit(1)

timetable = r2.json().get('timetable', [])
print(f"  Slots returned: {len(timetable)}")

target_slot = None
for slot in timetable:
    avail = slot.get('availability', 'UNKNOWN')
    marker = ' ← TARGET' if slot['time'] == TARGET_TIME else ''
    print(f"    {slot['time']} | {avail}{marker}")
    if slot['time'] == TARGET_TIME:
        target_slot = slot

if not target_slot:
    print(f"\n  {TARGET_TIME} not found — available slots above")
    # Pick first available
    for slot in timetable:
        if slot.get('availability') != 'SOLD_OUT':
            target_slot = slot
            print(f"  Falling back to first available: {slot['time']}")
            break

if not target_slot:
    print("  FATAL: No available slots")
    sys.exit(1)

slot_id = target_slot.get('id') or target_slot.get('visitId') or f"{DATE.replace('/','')}{target_slot['time'].replace(':','')}"
slot_time = target_slot['time']
print(f"\n  Using slot: {slot_time} | id={slot_id}")

# ── STEP 3: Services ──
print(f"\nSTEP 3: Fetching services...")
r3 = s.get(f'{BASE}/api/visit/services', params={
    'lang': 'it',
    'visitId': str(slot_id),
    'visitTypeId': str(ticket_id),
    'visitorNum': str(VISITORS),
}, headers=HEADERS, timeout=10)
print(f"  Status: {r3.status_code}")
services = []
if r3.status_code == 200:
    services = r3.json().get('services', [])
    for svc in services:
        print(f"    Service: [{svc.get('id')}] {svc.get('name')} €{svc.get('price')}")

# ── STEP 4: Recap (HOLD) ──
print(f"\nSTEP 4: RECAP (holding slot)...")
recap_body = {
    "visitId": str(slot_id),
    "visitTypeId": int(ticket_id),
    "visitorNum": VISITORS,
    "lang": "it",
    "tickets": [{"id": 60, "name": "Biglietto Intero", "price": 20, "quantity": VISITORS}],
    "additionalCosts": {},
    "services": [],
}
# Add pre-sale fee
for svc in services[:1]:
    recap_body["additionalCosts"]["service-0"] = {
        "id": svc['id'], "name": svc['name'], "price": svc['price'], "quantity": VISITORS
    }
    recap_body["services"].append({
        "id": svc['id'], "name": svc['name'], "price": svc['price'], "quantity": VISITORS
    })

recap_headers = {**HEADERS, 'Content-Type': 'application/json'}
r4 = s.post(f'{BASE}/api/visit/recap', json=recap_body, headers=recap_headers, timeout=15)
print(f"  Status: {r4.status_code}")
print(f"  Response: {r4.text[:500]}")

if r4.status_code == 200:
    recap_data = r4.json()
    total = recap_data.get('total', '?')
    recap_id = recap_data.get('recapId') or recap_data.get('id') or '?'
    jsessionid_final = s.cookies.get('JSESSIONID', jsessionid)
    ticketmv = s.cookies.get('ticketmv', '')

    print(f"\n{'='*55}")
    print(f"  ✅ SLOT HELD SUCCESSFULLY!")
    print(f"  Date:      {DATE}")
    print(f"  Time:      {slot_time}")
    print(f"  Visitors:  {VISITORS}")
    print(f"  Total:     €{total}")
    print(f"  Recap ID:  {recap_id}")
    print(f"  JSESSIONID: {jsessionid_final[:40]}...")
    print(f"  ticketmv:  {ticketmv}")
    print(f"\n  Payment URL:")
    print(f"  {BASE}/home/checkout;jsessionid={jsessionid_final}")
    print(f"{'='*55}")

    # Save session for keepalive test
    with open('/tmp/test_hold_session.json', 'w') as f:
        json.dump({
            'jsessionid': jsessionid_final,
            'ticketmv': ticketmv,
            'slot_id': str(slot_id),
            'ticket_id': str(ticket_id),
            'date': DATE,
            'slot_time': slot_time,
            'visitors': VISITORS,
            'total': str(total),
            'recap_id': str(recap_id),
        }, f, indent=2)
    print(f"\n  Session saved to /tmp/test_hold_session.json")
else:
    print(f"\n  ❌ RECAP FAILED: {r4.status_code}")
    print(f"  {r4.text[:300]}")
