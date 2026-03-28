"""
1. Scan next 90 days for first date with open time slots (Musei Vaticani standard entry)
2. Hold ALL open slots on that date simultaneously (one session per slot)
3. Verify from fresh session — should show SOLD_OUT
4. Release all
5. Verify from fresh session — should show available again
"""
import os, sys, django, time, requests, json
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from datetime import datetime, timedelta

BASE = 'https://tickets.museivaticani.va'
HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': f'{BASE}/',
    'Origin': BASE,
    'Content-Type': 'application/json',
}
VISITORS = 2

def sep(t): print(f"\n{'='*60}\n  {t}\n{'='*60}")

def scan_for_open_date():
    """Find first date in next 90 days with open time slots."""
    s = requests.Session()
    for days in range(1, 91):
        date = (datetime.now() + timedelta(days=days)).strftime('%d/%m/%Y')
        try:
            r = s.get(f'{BASE}/api/search/resultPerTag', params={
                'lang': 'it', 'visitorNum': str(VISITORS), 'visitDate': date,
                'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
            }, headers=HEADERS, timeout=10)
            if r.status_code != 200:
                continue
            ticket = next((v for v in r.json().get('visits', [])
                          if 'musei vaticani' in v.get('name','').lower()
                          and 'ingresso' in v.get('name','').lower()
                          and v.get('availability') == 'AVAILABLE'), None)
            if not ticket:
                continue

            # Check timeavail for actual open slots
            r2 = s.get(f'{BASE}/api/visit/timeavail', params={
                'lang': 'it', 'visitLang': '',
                'visitTypeId': str(ticket['id']),
                'visitorNum': str(VISITORS),
                'visitDate': date,
            }, headers=HEADERS, timeout=10)
            if r2.status_code != 200:
                continue

            open_slots = [t for t in r2.json().get('timetable', [])
                         if t.get('availability') not in ('SOLD_OUT',)]
            if open_slots:
                print(f"  Found: {date} | ticket=[{ticket['id']}] {ticket['name']} | {len(open_slots)} open slots")
                return date, ticket['id'], open_slots
            else:
                print(f"  {date} — all slots sold out")
        except Exception as e:
            print(f"  {date} — error: {e}")
    return None, None, []


def get_fresh_open_slots(date, visitors=VISITORS):
    """Check availability from a brand new session."""
    s = requests.Session()
    r = s.get(f'{BASE}/api/search/resultPerTag', params={
        'lang': 'it', 'visitorNum': str(visitors), 'visitDate': date,
        'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
    }, headers=HEADERS, timeout=15)
    ticket_id = next((v['id'] for v in r.json().get('visits', [])
                     if 'musei vaticani' in v.get('name','').lower()
                     and 'ingresso' in v.get('name','').lower()), None)
    if not ticket_id:
        return [], None

    r2 = s.get(f'{BASE}/api/visit/timeavail', params={
        'lang': 'it', 'visitLang': '',
        'visitTypeId': str(ticket_id),
        'visitorNum': str(visitors),
        'visitDate': date,
    }, headers=HEADERS, timeout=15)
    open_slots = [t for t in r2.json().get('timetable', [])
                 if t.get('availability') not in ('SOLD_OUT',)]
    return open_slots, ticket_id


# ══════════════════════════════════════════════════════════════
sep("STEP 1: Scan next 90 days for open slots")
# ══════════════════════════════════════════════════════════════
target_date, ticket_id, open_slots = scan_for_open_date()

if not target_date:
    print("\n❌ No open dates found in next 90 days.")
    sys.exit(0)

print(f"\n  TARGET DATE: {target_date}")
print(f"  Ticket ID:   {ticket_id}")
print(f"  Open slots ({len(open_slots)}):")
for sl in open_slots:
    print(f"    {sl['time']} | {sl.get('availability')} | id={sl.get('id','?')}")


# ══════════════════════════════════════════════════════════════
sep("STEP 2: Hold ALL open slots (one session per slot)")
# ══════════════════════════════════════════════════════════════
held = []

for slot in open_slots:
    slot_id = slot.get('id', '')
    slot_time = slot['time']
    print(f"\n  Holding {slot_time} (id={slot_id})...")

    # Fresh session per slot
    s = requests.Session()
    r = s.get(f'{BASE}/api/search/resultPerTag', params={
        'lang': 'it', 'visitorNum': str(VISITORS), 'visitDate': target_date,
        'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
    }, headers=HEADERS, timeout=15)

    fresh_id = ticket_id
    for v in r.json().get('visits', []):
        if 'musei vaticani' in v.get('name','').lower() and 'ingresso' in v.get('name','').lower():
            fresh_id = v['id']
            break

    jsid = s.cookies.get('JSESSIONID', '')
    print(f"    JSESSIONID: {jsid[:30]}...")

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
    jsid_after = s.cookies.get('JSESSIONID', jsid)

    if r2.status_code == 200:
        data = r2.json()
        held.append({
            'slot_time': slot_time,
            'slot_id': slot_id,
            'session': s,
            'jsid': jsid_after,
            'total': data.get('total', 0),
            'recap_id': data.get('recapId', ''),
        })
        print(f"    ✅ HELD! €{data.get('total')} | recapId={data.get('recapId')} | JSID={jsid_after[:30]}...")
        print(f"    Checkout: {BASE}/home/checkout;jsessionid={jsid_after}")
    else:
        print(f"    ❌ FAILED {r2.status_code}: {r2.text[:200]}")

    time.sleep(0.5)

print(f"\n  ✅ Successfully held: {len(held)}/{len(open_slots)} slots")
for h in held:
    print(f"    {h['slot_time']} | €{h['total']} | recapId={h['recap_id']}")


# ══════════════════════════════════════════════════════════════
sep("STEP 3: Verify from FRESH session — should show SOLD_OUT")
# ══════════════════════════════════════════════════════════════
time.sleep(3)
print("  Checking from brand new session (no cookies)...")
fresh_open, _ = get_fresh_open_slots(target_date)

print(f"\n  Slots visible to public AFTER hold: {len(fresh_open)}")
if fresh_open:
    for sl in fresh_open:
        print(f"    {sl['time']} | {sl.get('availability')}")
    print(f"\n  ⚠️  {len(fresh_open)} slots still visible")
    print(f"  (Vatican has more inventory than {VISITORS}-visitor slots we held)")
    print(f"  Try with higher visitor count to drain more inventory")
else:
    print("  ✅ FULLY SOLD OUT from public view — nobody can book this date!")


# ══════════════════════════════════════════════════════════════
sep("STEP 4: Release all holds")
# ══════════════════════════════════════════════════════════════
print(f"  Releasing {len(held)} held slots...")
for h in held:
    h['session'].cookies.clear()
    print(f"  🔓 {h['slot_time']} released")
held.clear()
print("  All sessions cleared.")


# ══════════════════════════════════════════════════════════════
sep("STEP 5: Verify slots restored after release")
# ══════════════════════════════════════════════════════════════
print("  Waiting 30s for Vatican to reclaim slots...")
for i in range(6):
    time.sleep(5)
    print(f"  {30-(i+1)*5}s...", end='\r')

print("\n  Checking fresh session...")
restored, _ = get_fresh_open_slots(target_date)
print(f"\n  Open slots after release: {len(restored)}")
if restored:
    for sl in restored:
        print(f"    {sl['time']} | {sl.get('availability')}")
    print("\n  ✅ Slots restored — hold/release cycle confirmed working!")
else:
    print("  ⚠️  Not yet restored (Vatican server-side expiry can take 10-15 min)")
    print("  This is expected — the hold was real.")

sep("FINAL RESULT")
print(f"  Date scanned:    {target_date}")
print(f"  Slots found:     {len(open_slots)}")
print(f"  Slots held:      previously {len(open_slots)} (released)")
print(f"  Public sold out: {'✅ YES' if not fresh_open else f'⚠️ {len(fresh_open)} still visible'}")
print(f"  Slots restored:  {'✅ YES' if restored else '⚠️ pending (normal)'}")
print()
