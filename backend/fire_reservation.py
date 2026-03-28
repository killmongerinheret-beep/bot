"""
Fire reservation using the browser session from HAR.
Vatican uses Cloudflare Turnstile (sitekey: 0x4AAAAAAB2Edz1zEK7o5Rj1)
The reservation response redirects to epay.catholica.va — that URL is the payment link.
"""
import os, sys, django, requests, json, re
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import HeldSlot

BASE = 'https://tickets.museivaticani.va'

# Use Hold #336 — March 26, 11:00, 2 visitors
hold = HeldSlot.objects.get(id=336)
print(f"Hold #{hold.id} | {hold.date} {hold.slot_time} | v={hold.visitors}")
print(f"recapId: {hold.recap_id}")

# ── Paste fresh Turnstile token here ──────────────────────────
# Get it from: Vatican checkout page → DevTools → Network → filter "reservation"
# Copy the "recaptcha" field value
TURNSTILE_TOKEN = ""  # ← paste here

# ── Or use 2captcha auto-solve ─────────────────────────────────
if not TURNSTILE_TOKEN:
    api_key = os.getenv('TWOCAPTCHA_API_KEY')
    if api_key:
        print("Solving Turnstile via 2captcha...")
        import time
        r = requests.post('https://2captcha.com/in.php', data={
            'key': api_key,
            'method': 'turnstile',
            'sitekey': '0x4AAAAAAB2Edz1zEK7o5Rj1',
            'pageurl': f'{BASE}/home/checkout',
            'json': 1,
        }, timeout=10)
        data = r.json()
        if data.get('status') == 1:
            task_id = data['request']
            print(f"Task submitted: {task_id}. Waiting...")
            for _ in range(24):
                time.sleep(5)
                r2 = requests.get('https://2captcha.com/res.php', params={
                    'key': api_key, 'action': 'get', 'id': task_id, 'json': 1
                }, timeout=10)
                res = r2.json()
                if res.get('status') == 1:
                    TURNSTILE_TOKEN = res['request']
                    print(f"✅ Solved: {TURNSTILE_TOKEN[:40]}...")
                    break
                if res.get('request') != 'CAPCHA_NOT_READY':
                    print(f"❌ 2captcha error: {res}")
                    break
        else:
            print(f"❌ 2captcha submit failed: {data}")
    else:
        print("No TWOCAPTCHA_API_KEY and no manual token — cannot proceed")
        sys.exit(1)

if not TURNSTILE_TOKEN:
    print("❌ No Turnstile token available")
    sys.exit(1)

# ── Fire reservation ───────────────────────────────────────────
body = {
    "recaptcha": TURNSTILE_TOKEN,
    "lang": "it",
    "recapId": hold.recap_id,
    "visitorNum": hold.visitors,
    "visitId": hold.slot_id,
    "visitTypeId": int(hold.ticket_id),
    "tickets": [
        {"id": 60, "name": "Biglietto Intero", "price": 20, "quantity": hold.visitors},
        {"id": 61, "name": "Biglietto Ridotto", "price": 10, "quantity": 0},
    ],
    "services": [{"id": 58, "name": "Diritti di Prevendita", "price": 5, "quantity": hold.visitors}],
    "representativeUser": {
        "surname": "Martinez",
        "name": "Elizabeth",
        "gender": "F",
        "country": "Italia",
        "city": "ROMA",
        "birthDate": "2001-06-11T22:00:00.000Z",
        "email": "abiileshlive@gmail.com",
        "confirmEmail": "abiileshlive@gmail.com",
        "telephoneNumber": "3481716428",
        "language": "en",
    },
    "participantUser": [
        {"surname": "Martinez", "name": "Elizabeth", "id": 60, "ticketType": "intero", "services": [58]},
        {"surname": "De Vries", "name": "Gabrielle", "id": 60, "ticketType": "intero", "services": [58]},
    ],
    "gdpr": [{"id": 1, "check": True}, {"id": 3, "check": True}],
}

headers = {
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': f'{BASE}/home/checkout',
    'Origin': BASE,
    'Content-Type': 'application/json',
    'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
}

s = requests.Session()
s.cookies.set('JSESSIONID', hold.jsessionid, domain='tickets.museivaticani.va')
if hold.ticketmv:
    s.cookies.set('ticketmv', hold.ticketmv, domain='tickets.museivaticani.va')

print(f"\nFiring reservation...")
print(f"JSID: {hold.jsessionid[:30]}...")

r = s.post(f'{BASE}/api/visit/reservation', json=body, headers=headers, timeout=20)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    # Vatican response: {"total":"2500","referenceOrder":"...","epay":{"url":"https://epay.catholica.va/...",...}}
    print(f"Response: {r.text[:600]}")

    try:
        data = r.json()
        epay = data.get('epay', {})
        payment_url = epay.get('url', '')

        if payment_url:
            print(f"\n{'='*55}")
            print(f"  ✅ RESERVATION CONFIRMED!")
            print(f"  Reference: {data.get('referenceOrder', '?')}")
            print(f"  Total: €{int(data.get('total', 0)) / 100:.2f}")
            print(f"\n  💳 PAYMENT URL:")
            print(f"  {payment_url}")
            print(f"\n  Open this link in your browser to pay by card.")
            print(f"  No session/cookies needed — it's a clean payment page.")
            print(f"{'='*55}")

            hold.status = 'paying'
            hold.payment_url = payment_url
            hold.save(update_fields=['status', 'payment_url'])
        else:
            print(f"\n  Response keys: {list(data.keys())}")
            print(f"  epay: {epay}")
    except Exception as e:
        print(f"  Parse error: {e}")
        print(f"  Raw: {r.text[:300]}")

elif r.status_code == 500:
    err = r.json().get('message', r.text[:200])
    print(f"❌ {r.status_code}: {err}")
    if 'General Error' in err:
        print("\nLikely cause: Turnstile token expired or session mismatch")
        print("The token must be from the SAME browser session as the recap")
else:
    print(f"❌ {r.status_code}: {r.text[:300]}")
