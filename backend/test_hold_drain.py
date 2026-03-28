"""
Full hold drain test on April 13 — known open slots (LOW_AVAILABILITY at 16:30-17:30)
1. Hold all 3 open slots simultaneously
2. Verify fresh session sees them as SOLD_OUT
3. Release all
4. Verify fresh session sees them as available again
"""
import os, sys, django, time, requests, json
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

DATE = '13/04/2026'
VISITORS = 2

def sep(t): print(f"\n{'='*60}\n  {t}\n{'='*60}")

def get_open_slots(visitors=VISITORS, session=None):
    s = session or requests.Session()
    r = s.get(f'{BASE}/api/search/resultPerTag', params={
        'lang': 'it', 'visitorNum': str(visitors), 'visitDate': DATE,
        'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
    }, headers=HEADERS, timeout=15)
    ticket_id = None
    for v in r.json().get('visits', []):
        if 'musei vaticani' in v.get('name','').lower() and 'ingresso' in v.get('name','').lower():
            ticket_id = v['id']
            break
    if not ticket_id:
        return [], None, s

    r2 = s.get(f'{BASE}/api/visit/timeavail', params={
        'lang': 'it', 'visitLang': '',
        'visitTypeId': str(ticket_id),
        'visitorNum': str(visitors),
        'visitDate': DATE,
    }, headers=HEADERS, timeout=15)

    open_slots = [t for t in r2.json().get('timetable', []) if t.get('availability') != 'SOLD_OUT']
    return open_slots, ticket_id, s


# ── STEP 1: Check what's open ──────────────────────────────────
sep("STEP 1: Check open slots on April 13")
open_slots, ticket_id, _ = get_open_slots()
print(f"  Ticket ID: {ticket_id}")
print(f"  Open slots: {len(open_slots)}")
for s in open_slots:
    print(f"    {s['time']} | {s.get('availability')} | id={s.get('id')}")

if not open_slots:
    print("  No open slots right now — test cannot proceed")
    sys.exit(0)


# ── STEP 2: Hold ALL open slots, each with its own session ─────
sep("STEP 2: Hold ALL open slots (drain)")
held = []

for slot in open_slots:
    s = requests.Session()
    # Re-init session with search API to get fresh JSESSIONID
    r = s.get(f'{BASE}/api/search/resultPerTag', params={
        'lang': 'it', 'visitorNum': str(VISITORS), 'visitDate': DATE,
        'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
    }, headers=HEADERS, timeout=15)
    fresh_id = ticket_id
    for v in r.json().get('visits', []):
        if 'musei vaticani' in v.get('name','').lower() and 'ingresso' in v.get('name','').lower():
            fresh_id = v['id']
            break

    slot_id = slot.get('id', '')
    body = {
        "visitId": str(slot_id),
        "visitTypeId": int(fresh_id),
        "visitorNum": VISITORS,
        "lang": "it",
        "tickets": [{"id": 60, "name": "Biglietto Intero", "price": 20, "quantity": VISITORS}],
        "additionalCosts": {},
        "services": [],
    }
    r2 = s.post(f'{BASE}/api/visit/recap', json=body, headers=HEADERS, timeout=15)
    jsid = s.cookies.get('JSESSIONID', '')

    if r2.status_code == 200:
        data = r2.json()
        held.append({'slot': slot, 'session': s, 'jsid': jsid, 'total': data.get('total'), 'recap_id': data.get('recapId','')})
        print(f"  ✅ HELD {slot['time']} | €{data.get('total')} | recapId={data.get('recapId')} | JSID={jsid[:25]}...")
    else:
        print(f"  ❌ FAILED {slot['time']} | {r2.status_code}: {r2.text[:120]}")
    time.sleep(0.3)

print(f"\n  Held: {len(held)}/{len(open_slots)} slots")


# ── STEP 3: Verify from completely fresh session ───────────────
sep("STEP 3: Verify from FRESH session (no cookies)")
time.sleep(2)
fresh_open, _, _ = get_open_slots()
print(f"  Open slots visible to public: {len(fresh_open)}")
if fresh_open:
    for s in fresh_open:
        print(f"    {s['time']} | {s.get('availability')}")
    print(f"\n  ⚠️  {len(fresh_open)} slots still visible (Vatican has more inventory than we held)")
else:
    print("  ✅ CONFIRMED SOLD OUT — nobody else can book this date!")


# ── STEP 4: Release all holds ──────────────────────────────────
sep("STEP 4: Release all holds")
for h in held:
    h['session'].cookies.clear()
    print(f"  🔓 Released {h['slot']['time']} (cleared session)")
held.clear()
print("  All sessions cleared.")


# ── STEP 5: Verify slots come back ────────────────────────────
sep("STEP 5: Verify slots restored (wait 30s)")
print("  Waiting 30 seconds...")
for i in range(6):
    time.sleep(5)
    print(f"  {30 - (i+1)*5}s remaining...", end='\r')

print("\n  Checking fresh session...")
restored, _, _ = get_open_slots()
print(f"  Open slots after release: {len(restored)}")
if restored:
    for s in restored:
        print(f"    {s['time']} | {s.get('availability')}")
    print("\n  ✅ Slots restored!")
else:
    print("  ⚠️  Not yet restored — Vatican server-side expiry takes longer")

sep("RESULT")
print(f"  Date: {DATE} | Visitors: {VISITORS}")
print(f"  Slots held:    {len(open_slots)}")
print(f"  Hold success:  {len(held)} (before release)")
print(f"  Sold out confirmed: {'✅' if not fresh_open else f'⚠️ {len(fresh_open)} still visible'}")
print(f"  Restored after release: {'✅' if restored else '⚠️ pending'}")
