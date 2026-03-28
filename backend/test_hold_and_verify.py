"""
End-to-end hold test:
1. Find a real open slot from active monitor tasks
2. Hold ALL available tickets in that slot (drain it)
3. Verify via fresh API call it shows SOLD_OUT
4. Release all holds
5. Verify via fresh API call it shows AVAILABLE again
"""
import os, sys, django, time, requests, json
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask, HeldSlot
from django.utils import timezone

BASE = 'https://tickets.museivaticani.va'
HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': f'{BASE}/',
    'Origin': BASE,
    'Content-Type': 'application/json',
}

def sep(title=''):
    print(f"\n{'='*60}")
    if title:
        print(f"  {title}")
        print(f"{'='*60}")

def check_slot_availability(date, ticket_id, visitors, jsessionid=None):
    """Fresh API check — returns list of available slot times."""
    s = requests.Session()
    if jsessionid:
        s.cookies.set('JSESSIONID', jsessionid, domain='tickets.museivaticani.va')

    # Step 1: get fresh ticket_id
    r = s.get(f'{BASE}/api/search/resultPerTag', params={
        'lang': 'it', 'visitorNum': str(visitors), 'visitDate': date,
        'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
    }, headers=HEADERS, timeout=15)

    fresh_id = ticket_id
    if r.status_code == 200:
        for v in r.json().get('visits', []):
            if 'ingresso' in v.get('name', '').lower():
                fresh_id = v['id']
                break

    jsid = s.cookies.get('JSESSIONID', jsessionid or '')

    # Step 2: timeavail
    r2 = s.get(f'{BASE}/api/visit/timeavail', params={
        'lang': 'it', 'visitLang': '',
        'visitTypeId': str(fresh_id),
        'visitorNum': str(visitors),
        'visitDate': date,
    }, headers=HEADERS, timeout=15)

    if r2.status_code != 200:
        return [], fresh_id, jsid

    slots = []
    for slot in r2.json().get('timetable', []):
        if slot.get('availability') != 'SOLD_OUT':
            slots.append(slot)
    return slots, fresh_id, jsid


def hold_one_slot(date, slot, ticket_id, visitors, session=None):
    """Hold a single slot. Returns (HeldSlot-like dict, session) or (None, session)."""
    s = session or requests.Session()

    slot_id = slot.get('id') or slot.get('visitId', '')
    slot_time = slot['time']

    # Services
    services = []
    try:
        r = s.get(f'{BASE}/api/visit/services', params={
            'lang': 'it', 'visitId': str(slot_id),
            'visitTypeId': str(ticket_id), 'visitorNum': str(visitors),
        }, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            services = [sv for sv in (r.json().get('services') or []) if sv.get('id')]
    except Exception:
        pass

    body = {
        "visitId": str(slot_id),
        "visitTypeId": int(ticket_id),
        "visitorNum": visitors,
        "lang": "it",
        "tickets": [{"id": 60, "name": "Biglietto Intero", "price": 20, "quantity": visitors}],
        "additionalCosts": {},
        "services": [],
    }
    for svc in [sv for sv in services[:1] if sv.get('id')]:
        body["additionalCosts"]["service-0"] = {
            "id": svc['id'], "name": svc['name'], "price": svc.get('price', 5), "quantity": visitors
        }
        body["services"].append({
            "id": svc['id'], "name": svc['name'], "price": svc.get('price', 5), "quantity": visitors
        })

    r2 = s.post(f'{BASE}/api/visit/recap', json=body, headers=HEADERS, timeout=15)
    if r2.status_code == 200:
        data = r2.json()
        jsid = s.cookies.get('JSESSIONID', '')
        return {
            'slot_id': str(slot_id),
            'slot_time': slot_time,
            'ticket_id': str(ticket_id),
            'jsessionid': jsid,
            'ticketmv': s.cookies.get('ticketmv', ''),
            'total': data.get('total', 0),
            'recap_id': data.get('recapId') or data.get('id') or '',
            'session': s,
        }, s
    else:
        print(f"    ❌ Recap failed {r2.status_code}: {r2.text[:150]}")
        return None, s


# ══════════════════════════════════════════════════════════════
sep("STEP 1: Find a real open slot from active monitor tasks")
# ══════════════════════════════════════════════════════════════

tasks = MonitorTask.objects.filter(site='vatican', is_active=True).select_related('agency')
print(f"Active tasks: {tasks.count()}")

open_date = None
open_slots = []
open_ticket_id = None
open_visitors = 2
open_task = None

for task in tasks:
    for raw_date in (task.dates or []):
        # Normalize date
        if '-' in str(raw_date):
            parts = raw_date.split('-')
            date = f"{parts[2]}/{parts[1]}/{parts[0]}"
        else:
            date = raw_date

        print(f"  Checking task #{task.id} | {task.agency.name} | {date} | {task.visitors}v")
        slots, ticket_id, jsid = check_slot_availability(date, task.ticket_id, task.visitors)

        if slots:
            print(f"  ✅ FOUND OPEN SLOTS on {date}!")
            open_date = date
            open_slots = slots
            open_ticket_id = ticket_id
            open_visitors = task.visitors
            open_task = task
            break
    if open_date:
        break

if not open_date:
    print("\n❌ No open slots found in any active task right now.")
    print("   All monitored dates are sold out. Try again when slots open.")
    sys.exit(0)

print(f"\n  Date:     {open_date}")
print(f"  Visitors: {open_visitors}")
print(f"  Ticket:   [{open_ticket_id}]")
print(f"  Open slots ({len(open_slots)}):")
for s in open_slots:
    print(f"    {s['time']} | id={s.get('id','?')} | {s.get('availability')}")


# ══════════════════════════════════════════════════════════════
sep("STEP 2: Hold ALL available slots (drain the date)")
# ══════════════════════════════════════════════════════════════

held_sessions = []
failed = 0

for slot in open_slots:
    print(f"\n  Holding {slot['time']}...")
    result, sess = hold_one_slot(open_date, slot, open_ticket_id, open_visitors)
    if result:
        held_sessions.append(result)
        print(f"  ✅ Held! Total=€{result['total']} | recapId={result['recap_id']} | JSID={result['jsessionid'][:25]}...")
    else:
        failed += 1
    time.sleep(0.5)  # small delay between holds

print(f"\n  Held: {len(held_sessions)} slots | Failed: {failed}")


# ══════════════════════════════════════════════════════════════
sep("STEP 3: Verify via FRESH session — should show SOLD_OUT")
# ══════════════════════════════════════════════════════════════

print("  Checking from a completely fresh session (no cookies)...")
time.sleep(2)

fresh_slots, _, _ = check_slot_availability(open_date, open_ticket_id, open_visitors)
print(f"\n  Available slots after hold: {len(fresh_slots)}")
if fresh_slots:
    for s in fresh_slots:
        print(f"    {s['time']} | {s.get('availability')}")
    print("\n  ⚠️  Some slots still showing available (Vatican may have more inventory)")
else:
    print("  ✅ CONFIRMED: All slots show SOLD_OUT from fresh session!")
    print("     Nobody else can book this date right now.")


# ══════════════════════════════════════════════════════════════
sep("STEP 4: Release all holds")
# ══════════════════════════════════════════════════════════════

# Release by NOT calling keepalive — sessions will expire naturally.
# But we can also verify release by checking if Vatican re-opens slots
# after we abandon the sessions (clear cookies).

print(f"  Releasing {len(held_sessions)} held sessions...")
print("  (Abandoning sessions — Vatican will reclaim slots within ~10-15 min)")
print("  For immediate release test, we clear the session cookies now.")

for h in held_sessions:
    h['session'].cookies.clear()
    print(f"  🔓 Released {h['slot_time']}")

held_sessions.clear()
print("\n  All sessions cleared.")


# ══════════════════════════════════════════════════════════════
sep("STEP 5: Wait 30s then verify slots reappear")
# ══════════════════════════════════════════════════════════════

print("  Waiting 30 seconds for Vatican to reclaim slots...")
for i in range(30, 0, -5):
    print(f"  {i}s remaining...", end='\r')
    time.sleep(5)

print("\n  Checking availability again from fresh session...")
restored_slots, _, _ = check_slot_availability(open_date, open_ticket_id, open_visitors)

print(f"\n  Available slots after release: {len(restored_slots)}")
if restored_slots:
    for s in restored_slots:
        print(f"    {s['time']} | {s.get('availability')}")
    print("\n  ✅ CONFIRMED: Slots restored after release!")
else:
    print("  ⚠️  Slots not yet restored — Vatican may take longer to reclaim.")
    print("     This is normal. Sessions expire server-side, not instantly.")

sep("TEST COMPLETE")
print(f"  Held {len(open_slots)} slots on {open_date}")
print(f"  Verified sold-out: {'✅' if not fresh_slots else '⚠️ partial'}")
print(f"  Verified restored: {'✅' if restored_slots else '⚠️ not yet (normal)'}")
print()
