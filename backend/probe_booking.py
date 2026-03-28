import os, sys, requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

session = requests.Session()
headers = {
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://tickets.museivaticani.va/'
}

# Get fresh session + slot IDs for June 15
r = session.get('https://tickets.museivaticani.va/api/search/resultPerTag', params={
    'lang': 'it', 'visitorNum': '2', 'visitDate': '15/06/2026',
    'area': '1', 'who': '', 'page': '0', 'tag': 'MV-Biglietti'
}, headers=headers)
ticket = next((t for t in r.json().get('visits', []) if 'ingresso' in t['name']), None)
ticket_id = ticket['id']
print(f"Ticket ID: {ticket_id}")

r2 = session.get('https://tickets.museivaticani.va/api/visit/timeavail', params={
    'lang': 'it', 'visitLang': '', 'visitTypeId': ticket_id,
    'visitorNum': '2', 'visitDate': '15/06/2026'
}, headers=headers)
slots = [s for s in r2.json().get('timetable', []) if s.get('availability') != 'SOLD_OUT']
slot = slots[0]
slot_id = slot['id']
print(f"Slot: {slot}")

# Try booking endpoints
endpoints = [
    ('POST', 'https://tickets.museivaticani.va/api/visit/book',
        {'slotId': slot_id, 'visitorNum': 2, 'lang': 'it'}),
    ('POST', 'https://tickets.museivaticani.va/api/booking/create',
        {'slotId': slot_id, 'visitorNum': 2, 'lang': 'it'}),
    ('GET',  'https://tickets.museivaticani.va/api/visit/reserve',
        {'slotId': slot_id, 'visitorNum': 2, 'lang': 'it'}),
    ('POST', 'https://tickets.museivaticani.va/api/visit/selecttime',
        {'visitTypeId': str(ticket_id), 'slotId': slot_id, 'visitorNum': 2, 'lang': 'it'}),
    ('GET',  'https://tickets.museivaticani.va/api/visit/selecttime',
        {'visitTypeId': str(ticket_id), 'slotId': slot_id, 'visitorNum': 2, 'lang': 'it'}),
    ('POST', 'https://tickets.museivaticani.va/api/cart/addvisit',
        {'visitTypeId': str(ticket_id), 'slotId': slot_id, 'visitorNum': 2, 'lang': 'it'}),
    ('GET',  'https://tickets.museivaticani.va/api/cart',
        {'lang': 'it'}),
    ('POST', 'https://tickets.museivaticani.va/api/visit/addvisit',
        {'visitTypeId': str(ticket_id), 'slotId': slot_id, 'visitorNum': 2, 'lang': 'it', 'visitDate': '15/06/2026'}),
]

print("\n--- Probing endpoints ---")
for method, url, payload in endpoints:
    try:
        if method == 'POST':
            resp = session.post(url, json=payload,
                headers={**headers, 'Content-Type': 'application/json'}, timeout=5)
        else:
            resp = session.get(url, params=payload, headers=headers, timeout=5)
        path = url.split('museivaticani.va')[1]
        print(f"{method} {path}: {resp.status_code} | {resp.text[:200]}")
    except Exception as e:
        print(f"ERROR {url}: {e}")
