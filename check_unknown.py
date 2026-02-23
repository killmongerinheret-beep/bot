#!/usr/bin/env python3
import json

d = json.load(open('/app/vatican_session.json'))
for date, tickets in d.get('ids_cache', {}).items():
    print(f"\n{date}: {len(tickets)} tickets")
    unknowns = [t for t in tickets if t['name'] == 'Unknown']
    print(f"  Unknown: {len(unknowns)}/{len(tickets)}")
    for t in tickets:
        status = "❌" if t['name'] == 'Unknown' else "✅"
        print(f"  {status} {t['name'][:50]}")
