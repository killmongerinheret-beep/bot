"""
Check if a recapped slot is still held.
A slot held via recap shows as SOLD_OUT in timeavail — that's how you know it's locked.
"""
import requests, sys

BASE = 'https://tickets.museivaticani.va'
H = {'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest',
     'Referer': f'{BASE}/', 'User-Agent': 'Mozilla/5.0'}

# From the last test_hold_and_pay.py run — update these if you ran it again
DATE      = '14/05/2026'
SLOT_ID   = '2026*8243'
SLOT_TIME = '15:30'
TICKET_ID = '667047496'
VISITORS  = 1
JSESSIONID = 'C41C8278A40A63DA98B6B4B016D035'  # from last run (partial)

s = requests.Session()

# ── Method 1: timeavail — slot shows SOLD_OUT if still held ──────────────────
print(f"Checking hold status for {DATE} {SLOT_TIME} (slot_id={SLOT_ID})...")
print()

# Get fresh ticket_id first (Vatican changes IDs)
r = s.get(f'{BASE}/api/search/resultPerTag', params={
    'lang': 'it', 'visitorNum': str(VISITORS), 'visitDate': DATE,
    'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
}, headers=H, timeout=8)

if r.status_code == 200:
    ticket = next((v for v in r.json().get('visits', [])
                   if 'musei vaticani' in v.get('name', '').lower()
                   and 'ingresso' in v.get('name', '').lower()), None)
    if ticket:
        TICKET_ID = str(ticket['id'])
        print(f"Fresh ticket_id: {TICKET_ID}")

# Check timeavail
r2 = s.get(f'{BASE}/api/visit/timeavail', params={
    'lang': 'it', 'visitLang': '', 'visitTypeId': TICKET_ID,
    'visitorNum': str(VISITORS), 'visitDate': DATE,
}, headers=H, timeout=8)

if r2.status_code != 200:
    print(f"timeavail failed: {r2.status_code}")
    sys.exit(1)

timetable = r2.json().get('timetable', [])
print(f"\nAll slots for {DATE}:")
print(f"{'Time':<8} {'Status':<20} {'Slot ID'}")
print("-" * 50)

our_slot = None
for sl in timetable:
    t    = sl.get('time', '?')
    avail = sl.get('availability', '?')
    sid  = sl.get('id', '?')
    marker = " ← OUR SLOT" if str(sid) == SLOT_ID else ""
    print(f"{t:<8} {avail:<20} {sid}{marker}")
    if str(sid) == SLOT_ID:
        our_slot = sl

print()
if our_slot:
    avail = our_slot.get('availability', '')
    if avail == 'SOLD_OUT':
        print(f"✅ SLOT IS STILL HELD — shows SOLD_OUT (your recap is locking it)")
        print(f"   Nobody else can book this slot while your session is active.")
    elif avail in ('AVAILABLE', 'LOW_AVAILABILITY'):
        print(f"❌ SLOT IS RELEASED — shows {avail}")
        print(f"   Your recap expired or was never set. Run test_hold_and_pay.py again.")
    else:
        print(f"⚠️  Slot status: {avail}")
else:
    # Slot ID not found — Vatican may have changed the slot ID
    # Check if the time slot exists at all
    time_slot = next((sl for sl in timetable if sl.get('time') == SLOT_TIME), None)
    if time_slot:
        avail = time_slot.get('availability', '?')
        new_id = time_slot.get('id', '?')
        print(f"⚠️  Slot ID changed (Vatican rotates IDs)")
        print(f"   Time {SLOT_TIME} now has id={new_id}, status={avail}")
        if avail == 'SOLD_OUT':
            print(f"   ✅ Still SOLD_OUT — likely still your hold")
        else:
            print(f"   ❌ Now {avail} — hold may have expired")
    else:
        print(f"⚠️  Time slot {SLOT_TIME} not found in timetable at all")
        print(f"   Date may be fully sold out or Vatican removed this time slot")

# ── Method 2: ping recap again to extend hold ─────────────────────────────────
print()
extend = input("Extend hold now (call recap again)? [y/n]: ").strip().lower()
if extend == 'y':
    recap_body = {
        "visitId": SLOT_ID,
        "visitTypeId": int(TICKET_ID),
        "visitorNum": VISITORS,
        "lang": "it",
        "tickets": [
            {"id": 60, "name": "Biglietto Intero", "price": 20, "quantity": "1"},
            {"id": 61, "name": "Biglietto Ridotto", "price": 10, "quantity": "0"},
        ],
        "additionalCosts": {
            "service-0": {"id": 58, "name": "Diritti di Prevendita", "price": 5, "quantity": 1}
        },
        "services": [{"id": 58, "name": "Diritti di Prevendita", "price": 5, "quantity": 1}]
    }
    HC = {**H, 'Content-Type': 'application/json', 'Origin': BASE}
    r3 = s.post(f'{BASE}/api/visit/recap', json=recap_body, headers=HC, timeout=10)
    print(f"Recap HTTP {r3.status_code}")
    if r3.status_code == 200:
        d = r3.json()
        print(f"✅ Hold extended! recap_id={d.get('recapId') or d.get('id')}, total=€{d.get('total')}")
    else:
        print(f"❌ Recap failed: {r3.text[:200]}")
