import requests

url = 'https://tickets.museivaticani.va/api/visit/timeavail'
params = {
    'lang': 'it',
    'visitLang': '',
    'visitTypeId': '165816585',  # Musei Vaticani - Biglietti d'ingresso
    'visitorNum': '1',
    'visitDate': '01/06/2026'
}
headers = {
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://tickets.museivaticani.va/'
}

r = requests.get(url, params=params, headers=headers, timeout=15)
print(f'Status: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    timetable = data.get('timetable', [])
    print(f'Total slots: {len(timetable)}')
    print()
    print('First 10 slots:')
    for slot in timetable[:10]:
        time_val = slot.get('time', 'N/A')
        avail_val = slot.get('availability', 'UNKNOWN')
        id_val = slot.get('id', 'N/A')
        print(f'  {time_val:5} - {avail_val:15} (ID: {id_val})')
    
    available = [s for s in timetable if s.get('availability') == 'AVAILABLE']
    print(f'\nAVAILABLE slots: {len(available)}')
    if available:
        print('First available:')
        print(f'  {available[0].get("time")} (ID: {available[0].get("id")})')
