"""
Hold ALL open slots for tomorrow (26/03/2026)
Visitors 1-5 per slot, one fresh session each.
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

TOMORROW = (datetime.now() + timedelta(days=1)).strftime('%d/%m/%Y')
VISITOR_COUNTS = [1, 2, 3, 4, 5]

def sep(t): print(f"\n{'='*60}\n  {t}\n{'='*60}")

def fresh_session_check(date, visitors):
    """Get open slots from a fresh session for given visitor count."""
    s = requests.Session()
    r = s.get(f'{BASE}/api/search/resultPerTag', params={
        'lang': 'it', 'visitorNum': str(visitors), 'visitDate': date,
        'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
    }, headers=HEADERS, timeout=12)
    if r.status_code != 200:
        return s, None, []

    ticket = next((v for v in r.json().get('visits', [])
                  if 'musei vaticani' in v.get('name','').lower()
                  and 'ingresso' in v.get('name','').lower()), None)
    if not ticket:
        return s, None, []

    ticket_id = ticket['id']
    r2 = s.get(f'{BASE}/api/visit/timeavail', params={
        'lang': 'it', 'visitLang': '',
        'visitTypeId': str(ticket_id),
        'visitorNum': str(visitors),
        'visitDate': date,
    }, headers=HEADERS, timeout=12)
    if r2.status_code != 200:
        return s, ticket_id, []

    slots = [t for t in r2.json().get('timetable', [])
             if t.get('availability') not in ('SOLD_OUT',)]
    return s, ticket_id, slots


# ── STEP 1: Scan all visitor counts to see full picture ────────
sep(f"STEP 1: Scan {TOMORROW} — all visitor counts")

all_slots_by_visitors = {}
for v in VISITOR_COUNTS:
    _, tid, slots = fresh_session_check(TOMORROW, v)
    all_slots_by_visitors[v] = {'ticket_id': tid, 'slots': slots}
    print(f"  v={v}: {len(slots)} open slots | ticket_id={tid}")
    for sl in slots:
        print(f"    {sl['time']} | {sl.get('availability')} | id={sl.get('id','?')}")

# Collect unique slot IDs across all visitor counts
all_slot_ids = set()
for v, data in all_slots_by_visitors.items():
    for sl in data['slots']:
        all_slot_ids.add((sl.get('id',''), sl.get('time','')))

print(f"\n  Total unique open slots: {len(all_slot_ids)}")
print(f"  Total hold attempts needed: {len(all_slot_ids)} slots × {len(VISITOR_COUNTS)} visitor counts = {len(all_slot_ids)*len(VISITOR_COUNTS)}")


# ── STEP 2: Hold everything ────────────────────────────────────
sep("STEP 2: Hold ALL slots × ALL visitor counts")

held = []
failed = 0

for slot_id, slot_time in sorted(all_slot_ids, key=lambda x: x[1]):
    print(f"\n  Slot {slot_time} (id={slot_id}):")
    for visitors in VISITOR_COUNTS:
        s, ticket_id, _ = fresh_session_check(TOMORROW, visitors)
        if not ticket_id:
            print(f"    v={visitors}: ❌ no ticket_id")
            failed += 1
            continue

        body = {
            "visitId": str(slot_id),
            "visitTypeId": int(ticket_id),
            "visitorNum": visitors,
            "lang": "it",
            "tickets": [{"id": 60, "name": "Biglietto Intero", "price": 20, "quantity": visitors}],
            "additionalCosts": {},
            "services": [],
        }
        r = s.post(f'{BASE}/api/visit/recap', json=body, headers=HEADERS, timeout=12)
        jsid = s.cookies.get('JSESSIONID', '')

        if r.status_code == 200:
            data = r.json()
            total = data.get('total', 0)
            recap_id = data.get('recapId', '')
            checkout = f"{BASE}/home/checkout;jsessionid={jsid}"
            held.append({
                'slot_time': slot_time, 'slot_id': slot_id,
                'visitors': visitors, 'total': total,
                'recap_id': recap_id, 'jsid': jsid,
                'checkout': checkout, 'session': s,
            })
            print(f"    v={visitors}: ✅ €{total} | recapId={recap_id}")
        else:
            err = r.json().get('message', r.text[:80])
            print(f"    v={visitors}: ❌ {r.status_code} — {err}")
            failed += 1
        time.sleep(0.2)

print(f"\n  ✅ Held: {len(held)} | ❌ Failed: {failed}")


# ── STEP 3: Verify from fresh session ─────────────────────────
sep("STEP 3: Verify from FRESH session (no cookies)")
time.sleep(3)

remaining = {}
for v in VISITOR_COUNTS:
    _, _, slots = fresh_session_check(TOMORROW, v)
    remaining[v] = slots
    print(f"  v={v}: {len(slots)} slots still visible")
    for sl in slots:
        print(f"    {sl['time']} | {sl.get('availability')}")

total_remaining = sum(len(s) for s in remaining.values())
if total_remaining == 0:
    print(f"\n  ✅ FULLY DRAINED — {TOMORROW} shows SOLD_OUT for all visitor counts!")
else:
    print(f"\n  ⚠️  {total_remaining} slot/visitor combos still visible")
    print(f"  (Vatican may have inventory beyond visitor count 5)")


# ── STEP 4: Summary ───────────────────────────────────────────
sep("STEP 4: Held slots summary + checkout links")
print(f"  Date: {TOMORROW}")
print(f"  Total held: {len(held)}\n")

# Group by slot time
from collections import defaultdict
by_slot = defaultdict(list)
for h in held:
    by_slot[h['slot_time']].append(h)

for slot_time in sorted(by_slot.keys()):
    entries = by_slot[slot_time]
    print(f"  ⏰ {slot_time}:")
    for h in entries:
        print(f"    v={h['visitors']} | €{h['total']} | recapId={h['recap_id']}")
        print(f"    💳 {h['checkout']}")

print(f"\n  Sessions are LIVE — slots locked until sessions expire or you pay.")
print(f"  Open any checkout link in browser to complete payment.")
print(f"\n  To release: clear browser cookies or wait ~15 min for Vatican timeout.")

# Keep sessions alive for 2 minutes so you can test the links
print(f"\n  Keeping sessions alive for 2 minutes...")
for i in range(24):
    time.sleep(5)
    # Ping keepalive
    for h in held:
        try:
            h['session'].get(f'{BASE}/api/config/isAgency', headers=HEADERS, timeout=5)
        except Exception:
            pass
    remaining_secs = (24 - i - 1) * 5
    print(f"  {remaining_secs}s remaining...", end='\r')

print(f"\n  Done. Sessions released.")
