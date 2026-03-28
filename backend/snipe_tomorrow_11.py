"""
Snipe: March 26, 11:00, 2 visitors — hold + save to DB with keepalive
"""
import os, sys, django, requests
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask, HeldSlot, Agency
from django.utils import timezone

BASE = 'https://tickets.museivaticani.va'
DATE = '26/03/2026'
SLOT_TIME = '11:00'
VISITORS = 2

HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': f'{BASE}/',
    'Origin': BASE,
    'Content-Type': 'application/json',
}

import os as _os
NGROK = _os.getenv('NGROK_DOMAIN', 'hyperkinetic-unsplendorously-jessi.ngrok-free.dev')

print(f"Sniping {DATE} {SLOT_TIME} for {VISITORS} visitors...")

# Fresh session
s = requests.Session()
r = s.get(f'{BASE}/api/search/resultPerTag', params={
    'lang': 'it', 'visitorNum': str(VISITORS), 'visitDate': DATE,
    'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
}, headers=HEADERS, timeout=15)

ticket = next((v for v in r.json().get('visits', [])
               if 'musei vaticani' in v.get('name','').lower()
               and 'ingresso' in v.get('name','').lower()), None)

if not ticket:
    print("❌ No standard entry ticket found")
    sys.exit(1)

ticket_id = ticket['id']
ticket_name = ticket['name']
jsid = s.cookies.get('JSESSIONID', '')
print(f"Ticket: [{ticket_id}] {ticket_name}")
print(f"JSID: {jsid[:30]}...")

# Get timeavail to find slot id
r2 = s.get(f'{BASE}/api/visit/timeavail', params={
    'lang': 'it', 'visitLang': '',
    'visitTypeId': str(ticket_id),
    'visitorNum': str(VISITORS),
    'visitDate': DATE,
}, headers=HEADERS, timeout=15)

slot = next((t for t in r2.json().get('timetable', [])
             if t['time'] == SLOT_TIME), None)

if not slot:
    print(f"❌ Slot {SLOT_TIME} not found in timetable")
    for t in r2.json().get('timetable', []):
        print(f"  {t['time']} | {t.get('availability')}")
    sys.exit(1)

slot_id = slot.get('id', '')
avail = slot.get('availability')
print(f"Slot: {SLOT_TIME} | id={slot_id} | {avail}")

if avail == 'SOLD_OUT':
    print("❌ Slot is SOLD_OUT — cannot hold")
    sys.exit(1)

# Recap (hold)
body = {
    "visitId": str(slot_id),
    "visitTypeId": int(ticket_id),
    "visitorNum": VISITORS,
    "lang": "it",
    "tickets": [{"id": 60, "name": "Biglietto Intero", "price": 20, "quantity": VISITORS}],
    "additionalCosts": {},
    "services": [],
}

r3 = s.post(f'{BASE}/api/visit/recap', json=body, headers=HEADERS, timeout=15)
jsid_after = s.cookies.get('JSESSIONID', jsid)
ticketmv = s.cookies.get('ticketmv', '')

if r3.status_code != 200:
    print(f"❌ Recap failed: {r3.status_code} | {r3.text[:200]}")
    sys.exit(1)

data = r3.json()
total = data.get('total', 0)
recap_id = data.get('recapId', '')
print(f"✅ HELD! €{total} | recapId={recap_id}")

# Save to DB
agency = Agency.objects.exclude(plan='system').first()
task = MonitorTask.objects.filter(agency=agency, site='vatican', is_active=True).first()

if not task:
    # Create a minimal task if none exists
    task = MonitorTask.objects.create(
        agency=agency, site='vatican', area_name='Musei Vaticani',
        dates=[DATE], preferred_times=[SLOT_TIME], visitors=VISITORS,
        ticket_type=0, ticket_name=ticket_name, tier='snipe',
        is_active=True, last_status='available',
    )
    print(f"Created task #{task.id}")

held = HeldSlot.objects.create(
    task=task,
    date=DATE,
    slot_id=str(slot_id),
    slot_time=SLOT_TIME,
    ticket_id=str(ticket_id),
    ticket_name=ticket_name,
    visitors=VISITORS,
    total_price=total,
    jsessionid=jsid_after,
    ticketmv=ticketmv,
    recap_id=recap_id,
    status='held',
    payment_url='',
    notes=f'Manual snipe — {DATE} {SLOT_TIME} {VISITORS}v',
)
held.payment_url = f"https://{NGROK}/api/v1/holds/{held.id}/checkout/"
held.save(update_fields=['payment_url'])

print(f"\n{'='*55}")
print(f"  ✅ SLOT HELD & SAVED TO DB")
print(f"  Hold ID:   #{held.id}")
print(f"  Date:      {DATE} {SLOT_TIME}")
print(f"  Visitors:  {VISITORS}")
print(f"  Total:     €{total}")
print(f"  recapId:   {recap_id}")
print(f"  JSID:      {jsid_after[:35]}...")
print(f"\n  Checkout URL:")
print(f"  {held.payment_url}")
print(f"\n  Keepalive task will ping every 5 min to keep session alive.")
print(f"  Open the checkout URL to generate payment link.")
print(f"{'='*55}")
