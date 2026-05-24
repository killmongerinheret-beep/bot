"""
Test: Hold 1 slot via pure API recap, then get a payable link.
Run: python test_hold_and_pay.py

This tests whether a slot held via API recap is actually payable
by someone else opening the epay link on their phone.
"""
import requests
import json
import time
import os
import sys

BASE = 'https://tickets.museivaticani.va'
H_XHR = {
    'Accept': 'application/json, text/plain, */*',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': f'{BASE}/',
    'Origin': BASE,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}
HC = {**H_XHR, 'Content-Type': 'application/json', 'Referer': f'{BASE}/home/checkout'}

VISITORS = 1
ADULTS   = 1
CHILDREN = 0

# ── Step 1: Find open slot ────────────────────────────────────────────────────
print("Step 1: Finding open slot...")
s = requests.Session()
s.get(f'{BASE}/home', headers=H_XHR, timeout=10)

from datetime import datetime, timedelta
slot_found = None
for i in range(1, 120):
    d = (datetime.now() + timedelta(days=i)).strftime('%d/%m/%Y')
    if datetime.strptime(d, '%d/%m/%Y').weekday() == 6:
        continue
    r = s.get(f'{BASE}/api/search/resultPerTag', params={
        'lang': 'it', 'visitorNum': str(VISITORS), 'visitDate': d,
        'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
    }, headers=H_XHR, timeout=8)
    if r.status_code != 200:
        continue
    ticket = next((v for v in r.json().get('visits', [])
                   if 'musei vaticani' in v.get('name', '').lower()
                   and 'ingresso' in v.get('name', '').lower()
                   and v.get('availability') in ('AVAILABLE', 'LOW_AVAILABILITY')), None)
    if not ticket:
        sys.stdout.write(f'\r  Scanning {d}...')
        sys.stdout.flush()
        continue
    tid = ticket['id']
    r2 = s.get(f'{BASE}/api/visit/timeavail', params={
        'lang': 'it', 'visitLang': '', 'visitTypeId': str(tid),
        'visitorNum': str(VISITORS), 'visitDate': d,
    }, headers=H_XHR, timeout=8)
    if r2.status_code != 200:
        continue
    slots = [sl for sl in r2.json().get('timetable', [])
             if sl.get('availability') in ('AVAILABLE', 'LOW_AVAILABILITY')]
    if slots:
        slot_found = {'date': d, 'slot': slots[0], 'ticket_id': tid}
        print(f'\n  Found: {d} {slots[0]["time"]} (slot_id={slots[0]["id"]}, ticket_id={tid})')
        break
    time.sleep(0.1)

if not slot_found:
    print('No open slots found.')
    sys.exit(1)

date     = slot_found['date']
slot_id  = str(slot_found['slot']['id'])
slot_time= slot_found['slot']['time']
tid      = slot_found['ticket_id']

# ── Step 2: Get services ──────────────────────────────────────────────────────
print(f"\nStep 2: Getting services...")
services = []
r_svc = s.get(f'{BASE}/api/visit/services', params={
    'lang': 'it', 'visitId': slot_id, 'visitTypeId': tid, 'visitorNum': str(VISITORS)
}, headers=H_XHR, timeout=8)
if r_svc.status_code == 200:
    services = r_svc.json().get('services', []) or []
    print(f'  Services: {[sv.get("name") for sv in services]}')

# ── Step 3: Recap (HOLD) ──────────────────────────────────────────────────────
print(f"\nStep 3: Calling recap to HOLD slot {slot_id}...")
recap_body = {
    "visitId": slot_id,
    "visitTypeId": int(tid),
    "visitorNum": VISITORS,
    "lang": "it",
    "tickets": [
        {"id": 60, "name": "Biglietto Intero", "price": 20, "quantity": str(ADULTS)},
        {"id": 61, "name": "Biglietto Ridotto", "price": 10, "quantity": str(CHILDREN)},
    ],
    "additionalCosts": {},
    "services": []
}
for svc in services[:1]:
    recap_body["additionalCosts"]["service-0"] = {
        "id": svc.get('id', 58), "name": svc.get('name', 'Diritti di Prevendita'),
        "price": svc.get('price', 5), "quantity": VISITORS
    }
    recap_body["services"].append({
        "id": svc.get('id', 58), "name": svc.get('name', 'Diritti di Prevendita'),
        "price": svc.get('price', 5), "quantity": VISITORS
    })

r_recap = s.post(f'{BASE}/api/visit/recap', json=recap_body, headers=HC, timeout=15)
print(f'  Recap HTTP {r_recap.status_code}')
if r_recap.status_code != 200:
    print(f'  FAILED: {r_recap.text[:300]}')
    sys.exit(1)

recap_data = r_recap.json()
recap_id   = recap_data.get('recapId') or recap_data.get('id') or ''
total      = recap_data.get('total', '?')
jsessionid = s.cookies.get('JSESSIONID', '')
ticketmv   = s.cookies.get('ticketmv', '')
serverid   = s.cookies.get('SERVERID', '')

print(f'  ✅ SLOT HELD!')
print(f'  recap_id  = {recap_id}')
print(f'  total     = €{total}')
print(f'  JSESSIONID= {jsessionid[:20]}...')
print(f'  ticketmv  = {ticketmv}')
print(f'  SERVERID  = {serverid}')

# ── Step 4: Solve Turnstile via 2captcha ─────────────────────────────────────
TWOCAPTCHA_KEY = os.getenv('TWOCAPTCHA_API_KEY', '')
if not TWOCAPTCHA_KEY:
    # Try loading from .env
    try:
        with open('.env') as f:
            for line in f:
                if line.startswith('TWOCAPTCHA_API_KEY='):
                    TWOCAPTCHA_KEY = line.strip().split('=', 1)[1]
    except Exception:
        pass

token = None
if TWOCAPTCHA_KEY:
    print(f"\nStep 4: Solving Turnstile via 2captcha (~30s)...")
    r_sub = requests.post('https://2captcha.com/in.php', data={
        'key': TWOCAPTCHA_KEY,
        'method': 'turnstile',
        'sitekey': '0x4AAAAAAB2Edz1zEK7o5Rj1',
        'pageurl': 'https://tickets.museivaticani.va/home/checkout',
        'action': 'managed',
        'json': 1,
    }, timeout=10)
    task_id = r_sub.json().get('request')
    print(f'  Task ID: {task_id}')
    for attempt in range(24):
        time.sleep(5)
        r_res = requests.get('https://2captcha.com/res.php', params={
            'key': TWOCAPTCHA_KEY, 'action': 'get', 'id': task_id, 'json': 1
        }, timeout=10)
        res = r_res.json()
        if res.get('status') == 1:
            token = res['request']
            print(f'  ✅ Token solved! (len={len(token)})')
            break
        if res.get('request') != 'CAPCHA_NOT_READY':
            print(f'  2captcha error: {res}')
            break
        sys.stdout.write(f'\r  Waiting... {(attempt+1)*5}s')
        sys.stdout.flush()
    print()
else:
    print(f"\nStep 4: No TWOCAPTCHA_API_KEY — skipping Turnstile solve")
    print(f"  (You can still test the hold — just can't complete reservation without token)")

# ── Step 5: Reservation ───────────────────────────────────────────────────────
if token:
    print(f"\nStep 5: Calling reservation...")
    res_body = {
        "recaptcha": token,
        "lang": "it",
        "recapId": recap_id,
        "visitorNum": VISITORS,
        "visitId": slot_id,
        "visitTypeId": int(tid),
        "tickets": [
            {"id": 60, "name": "Biglietto Intero", "price": 20, "quantity": str(ADULTS)},
            {"id": 61, "name": "Biglietto Ridotto", "price": 10, "quantity": str(CHILDREN)},
        ],
        "services": [{"id": 58, "name": "Diritti di Prevendita", "price": 5, "quantity": VISITORS}],
        "representativeUser": {
            "name": "Mario", "surname": "Rossi", "gender": "M",
            "country": "Italy", "city": "Roma", "birthDate": "1990-01-01T00:00:00.000Z",
            "email": "mario.rossi@example.com", "confirmEmail": "mario.rossi@example.com",
            "telephoneNumber": "3401234567", "language": "en"
        },
        "participantUser": [
            {"surname": "Rossi", "name": "Mario", "id": 60, "ticketType": "intero", "services": [58]}
        ],
        "gdpr": [{"id": 1, "check": True}, {"id": 3, "check": True}],
    }
    r_res = s.post(f'{BASE}/api/visit/reservation', json=res_body, headers=HC, timeout=20, allow_redirects=False)
    print(f'  Reservation HTTP {r_res.status_code}')

    if r_res.status_code == 200:
        res_data = r_res.json()
        epay = res_data.get('epay', {})
        epay_url  = epay.get('url', '')
        reference = res_data.get('referenceOrder', '')
        print(f'\n  ✅ RESERVATION COMPLETE!')
        print(f'  Reference : {reference}')
        print(f'  Total     : €{res_data.get("total")}')
        print(f'\n  💳 PAYMENT LINK (open on your phone):')
        print(f'  {epay_url}')
        print(f'\n  Send this link to anyone — they can pay from their phone.')
    else:
        print(f'  FAILED: {r_res.text[:400]}')
else:
    print(f"\nStep 5: Skipped (no Turnstile token)")
    print(f"\n  ✅ HOLD IS ACTIVE — slot {slot_id} is locked for ~55 minutes")
    print(f"  To complete: run with TWOCAPTCHA_API_KEY set, or use /pay command in Telegram")

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"HOLD SUMMARY")
print(f"  Date      : {date} {slot_time}")
print(f"  Slot ID   : {slot_id}")
print(f"  Ticket ID : {tid}")
print(f"  recap_id  : {recap_id}")
print(f"  Total     : €{total}")
print(f"  JSESSIONID: {jsessionid[:30]}...")
print(f"{'='*60}")
print(f"\nThe slot is held for ~55 minutes.")
print(f"Run again to refresh the hold (or use the keepalive loop).")
