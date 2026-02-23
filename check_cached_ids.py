#!/usr/bin/env python3
import json

d = json.load(open('/app/vatican_session.json'))
ids = d.get('ids_cache', {}).get('2026-02-27', [])
print(f"Cached IDs for 2026-02-27: {len(ids)} tickets")
for i, t in enumerate(ids[:5], 1):
    print(f"  {i}. ID: {t['id']}, Name: {t['name']}")
