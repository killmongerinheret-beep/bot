import requests

url = 'http://localhost:8000/api/v1/auth/login/'

tests = [
    ('bigbus',               'Bigbus2026!'),
    ('Italypass',            'Italypass2026!'),
    ('Bot123',               'Mahabur2026!'),
    ('Tourguides',           'Tourguides2026!'),
    ('vatican_bot_agency_1', 'Vatican2026!'),
    ('wondersofrome',        'Wonders2026!'),
    ('wondersofrome123',     'Wonders2026!'),
]

print()
print(f"  {'Username':<24} {'Password':<18} {'Result'}")
print('  ' + '-'*70)
all_ok = True
for username, password in tests:
    r = requests.post(url, json={'username': username, 'password': password}, timeout=10)
    d = r.json()
    if r.status_code == 200:
        agency = d['agency']['name']
        print(f"  {username:<24} {password:<18} ✅ OK  (agency: {agency})")
    else:
        all_ok = False
        print(f"  {username:<24} {password:<18} ❌ FAIL  ({d.get('error')})")
print()
print(f"  {'All logins OK ✅' if all_ok else 'Some logins FAILED ❌'}")
print()
