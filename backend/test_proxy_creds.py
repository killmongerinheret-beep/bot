"""Test both sets of Oxylabs credentials"""
import os, sys, requests
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django; django.setup()

creds = [
    ('user-wondersofcity_fJQUF', 'Me=millionare1111'),
    ('customer-abiildonea-cc-it', 'Pzzzap4D_country-it'),
]

for user, pwd in creds:
    for port in [8001, 8009]:
        proxy = f"http://{user}:{pwd}@isp.oxylabs.io:{port}"
        try:
            r = requests.get('https://ip.oxylabs.io', proxies={'https': proxy}, timeout=8)
            print(f"✅ {user[:25]}... port={port} → IP={r.text.strip()}")
            break
        except Exception as e:
            print(f"❌ {user[:25]}... port={port} → {e.__class__.__name__}: {str(e)[:60]}")
