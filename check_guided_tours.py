#!/usr/bin/env python
"""
Check for available guided tour slots
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

import requests

def check_guided_tours():
    print("Checking for available guided tour slots...")
    print()
    
    # Check a few dates
    dates = ['29/04/2026', '30/04/2026', '01/05/2026', '02/05/2026', '05/05/2026']
    languages = ['ENG', 'ITA']
    
    found_any = False
    
    for date_str in dates:
        try:
            url = 'https://tickets.museivaticani.va/api/search/resultPerTag'
            params = {
                'lang': 'it',
                'visitorNum': '1',
                'visitDate': date_str,
                'area': '1',
                'who': '',
                'page': '0',
                'tag': 'MV-Visite-Guidate'  # Guided tours
            }
            
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': 'https://tickets.museivaticani.va/'
            }
            
            r = requests.get(url, params=params, headers=headers, timeout=10)
            
            if r.status_code == 200:
                data = r.json()
                visits = data.get('visits', [])
                
                available_tours = []
                for visit in visits:
                    if visit.get('availability') == 'AVAILABLE':
                        available_tours.append({
                            'id': visit.get('id'),
                            'name': visit.get('name', 'Unknown')
                        })
                
                if available_tours:
                    print(f"✅ {date_str}: AVAILABLE GUIDED TOURS!")
                    
                    for tour in available_tours[:3]:  # Check first 3
                        print(f"   - {tour['name']}")
                        
                        # Check time slots for each language
                        jsessionid = r.cookies.get('JSESSIONID', '')
                        
                        for lang in languages:
                            url2 = 'https://tickets.museivaticani.va/api/visit/timeavail'
                            params2 = {
                                'lang': 'it',
                                'visitLang': lang,
                                'visitTypeId': str(tour['id']),
                                'visitorNum': '1',
                                'visitDate': date_str
                            }
                            
                            headers2 = headers.copy()
                            if jsessionid:
                                headers2['Cookie'] = f'JSESSIONID={jsessionid}'
                            
                            r2 = requests.get(url2, params=params2, headers=headers2, timeout=10)
                            
                            if r2.status_code == 200:
                                timetable = r2.json().get('timetable', [])
                                available_slots = [s for s in timetable if s.get('availability') == 'AVAILABLE']
                                if available_slots:
                                    times = [s['time'] for s in available_slots[:5]]
                                    print(f"     [{lang}] Slots: {', '.join(times)}")
                                    found_any = True
                    print()
                else:
                    print(f"❌ {date_str}: No guided tours available")
            else:
                print(f"⚠️  {date_str}: API error {r.status_code}")
                
        except Exception as e:
            print(f"⚠️  {date_str}: Error - {str(e)[:80]}")
    
    if found_any:
        print("\n✅ Found available guided tour slots!")
    else:
        print("\n❌ No available guided tour slots found")

if __name__ == '__main__':
    check_guided_tours()
