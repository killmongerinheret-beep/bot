#!/usr/bin/env python3
import json

d = json.load(open('/app/vatican_session.json'))
print("Cached dates:", list(d.get('ids_cache', {}).keys()))
for date, ids in d.get('ids_cache', {}).items():
    print(f"\n{date}: {len(ids)} tickets")
    unknown_count = sum(1 for t in ids if t['name'] == 'Unknown')
    print(f"  Unknown names: {unknown_count}/{len(ids)}")
    for t in ids[:3]:
        status = "❌" if t['name'] == 'Unknown' else "✅"
        print(f"  {status} ID: {t['id'][:12]}... Name: {t['name'][:50]}")
