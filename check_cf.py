import requests

BASE = 'https://tickets.museivaticani.va'
H = {
    'Accept': 'application/json, text/plain, */*',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': f'{BASE}/',
}
s = requests.Session()

tests = [
    ('GET',  '/home',                          {}),
    ('GET',  '/api/search/resultPerTag',       {'lang':'it','visitorNum':'1','visitDate':'13/05/2026','area':'1','who':'','page':'0','tag':'MV-Biglietti'}),
    ('GET',  '/api/visit/timeavail',           {'lang':'it','visitLang':'','visitTypeId':'785114822','visitorNum':'1','visitDate':'13/05/2026'}),
    ('GET',  '/api/config/isAgency',           {}),
    ('GET',  '/api/visit/services',            {'lang':'it','visitId':'2026*8222','visitTypeId':'785114822','visitorNum':'1'}),
    ('POST', '/api/visit/recap',               {}),   # will 400 without body but shows CF status
    ('POST', '/api/visit/reservation',         {}),   # the one that needs Turnstile
]

print(f"{'Status':<8} {'Cloudflare':<12} {'Endpoint'}")
print("-" * 60)
for method, path, params in tests:
    url = BASE + path
    try:
        if method == 'GET':
            r = s.get(url, params=params, headers=H, timeout=8)
        else:
            r = s.post(url, json={}, headers={**H, 'Content-Type':'application/json'}, timeout=8)
        
        cf_ray = r.headers.get('cf-ray', '')
        cf_cache = r.headers.get('cf-cache-status', '')
        server = r.headers.get('server', '')
        
        has_cf = bool(cf_ray) or 'cloudflare' in server.lower()
        cf_label = "CLOUDFLARE" if has_cf else "none"
        
        print(f"{r.status_code:<8} {cf_label:<12} {path}")
        
        # Check if it's a Turnstile challenge (403 with CF challenge)
        if r.status_code == 403 and 'turnstile' in r.text.lower():
            print(f"         ^^^ TURNSTILE CHALLENGE REQUIRED")
        elif r.status_code == 403:
            print(f"         ^^^ 403 (body: {r.text[:80]})")
            
    except Exception as e:
        print(f"ERROR    {'?':<12} {path} — {e}")
