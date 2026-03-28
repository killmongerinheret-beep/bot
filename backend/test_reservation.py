"""
Test reservation call on the most recent active hold.
Shows exact Vatican error message.
"""
import os, sys, django, requests, json
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import HeldSlot, BuyerProfile

BASE = 'https://tickets.museivaticani.va'

# Get most recent held slot
hold = HeldSlot.objects.filter(status='held').order_by('-hold_started_at').first()
if not hold:
    print("No active holds")
    sys.exit(0)

print(f"Hold #{hold.id} | {hold.date} {hold.slot_time} | v={hold.visitors}")
print(f"JSID: {hold.jsessionid[:30]}...")
print(f"recapId: {hold.recap_id}")
print(f"slot_id: {hold.slot_id}")
print(f"ticket_id: {hold.ticket_id}")

# Step 1: Check if session is still alive
print("\n--- Keepalive check ---")
s = requests.Session()
s.cookies.set('JSESSIONID', hold.jsessionid, domain='tickets.museivaticani.va')
if hold.ticketmv:
    s.cookies.set('ticketmv', hold.ticketmv, domain='tickets.museivaticani.va')

r = s.get(f'{BASE}/api/config/isAgency', headers={
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0',
    'Referer': f'{BASE}/',
}, timeout=10)
print(f"isAgency: {r.status_code} | {r.text[:100]}")

# Step 2: Re-check timeavail to see if slot still exists
print("\n--- Timeavail check ---")
r2 = s.get(f'{BASE}/api/visit/timeavail', params={
    'lang': 'it', 'visitLang': '',
    'visitTypeId': hold.ticket_id,
    'visitorNum': str(hold.visitors),
    'visitDate': hold.date,
}, headers={'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0', 'Referer': f'{BASE}/'}, timeout=10)
print(f"Timeavail: {r2.status_code}")
if r2.status_code == 200:
    slots = r2.json().get('timetable', [])
    for sl in slots:
        if sl.get('availability') != 'SOLD_OUT':
            marker = ' ← OUR SLOT' if sl.get('id') == hold.slot_id else ''
            print(f"  {sl['time']} | {sl.get('availability')} | id={sl.get('id')}{marker}")

# Step 3: Try reservation with empty recaptcha
print("\n--- Reservation attempt (no recaptcha) ---")
profile = BuyerProfile.objects.filter(agency=hold.task.agency).first()
if not profile:
    print("No buyer profile — create one first")
    sys.exit(1)

body = {
    "recaptcha": "",
    "lang": "it",
    "recapId": hold.recap_id or '',
    "visitorNum": hold.visitors,
    "visitId": hold.slot_id,
    "visitTypeId": int(hold.ticket_id),
    "tickets": [{"id": 60, "name": "Biglietto Intero", "price": 20, "quantity": hold.visitors}],
    "services": [{"id": 58, "name": "Diritti di Prevendita", "price": 5, "quantity": hold.visitors}],
    "representativeUser": profile.to_representative_user(),
    "participantUser": profile.to_participant_list(hold.visitors),
    "gdpr": [{"id": 1, "check": True}, {"id": 3, "check": True}],
}

headers = {
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': f'{BASE}/home/checkout',
    'Origin': BASE,
    'Content-Type': 'application/json',
}

r3 = s.post(f'{BASE}/api/visit/reservation', json=body, headers=headers, timeout=20)
print(f"Status: {r3.status_code}")
print(f"Response: {r3.text[:600]}")

if r3.status_code == 200:
    data = r3.json()
    print(f"\n✅ SUCCESS!")
    print(f"Keys: {list(data.keys())}")
    # Look for payment URL
    for key in ['redirectUrl', 'paymentUrl', 'url', 'urlPayment', 'redirect']:
        if key in data:
            print(f"  {key}: {data[key]}")
