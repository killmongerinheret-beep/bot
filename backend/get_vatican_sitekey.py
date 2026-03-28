import requests, re

r = requests.get('https://tickets.museivaticani.va/home/checkout',
    headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
print(f"Status: {r.status_code} | Size: {len(r.text)}")

# Find reCAPTCHA site keys
keys = re.findall(r'["\']?(6[A-Za-z0-9_-]{39})["\']?', r.text)
print(f"Site keys in HTML: {list(set(keys))}")

render = re.findall(r'render=([A-Za-z0-9_-]{40,})', r.text)
print(f"Render keys: {render}")

# Also check the main JS bundle
js_urls = re.findall(r'src="(/[^"]+\.js)"', r.text)
print(f"\nJS bundles: {js_urls[:5]}")
