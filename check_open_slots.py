#!/usr/bin/env python
"""
Check for open Vatican slots for WOR agency
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from monitors.models import MonitorTask, Agency
import requests

def check_slots():
    # Get WOR agency
    try:
        agency = Agency.objects.get(name='WOR')
    except Agency.DoesNotExist:
        print("WOR agency not found")
        return
    
    # Get one WOR task
    task = MonitorTask.objects.filter(agency=agency, is_active=True).first()
    
    if not task:
        print("No active WOR tasks found")
        return
    
    print(f"Checking {len(task.dates)} dates for WOR agency...")
    print(f"Visitors: {task.visitors}")
    print()
    
    found_any = False
    
    # Check first 15 dates
    for i, date_str in enumerate(task.dates[:15]):
        # Convert to DD/MM/YYYY
        if '-' in date_str:
            year, month, day = date_str.split('-')
            date_formatted = f'{day}/{month}/{year}'
        else:
            date_formatted = date_str
        
        try:
            url = 'https://tickets.museivaticani.va/api/search/resultPerTag'
            params = {
                'lang': 'it',
                'visitorNum': str(task.visitors),
                'visitDate': date_formatted,
                'area': '1',
                'who': '',
                'page': '0',
                'tag': 'MV-Biglietti'
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
                
                available_tickets = []
                for visit in visits:
                    if visit.get('availability') == 'AVAILABLE':
                        available_tickets.append({
                            'id': visit.get('id'),
                            'name': visit.get('name', 'Unknown')
                        })
                
                if available_tickets:
                    print(f"✅ {date_formatted}: AVAILABLE!")
                    for ticket in available_tickets:
                        print(f"   - {ticket['name']} (ID: {ticket['id']})")
                        
                        # Check time slots
                        jsessionid = r.cookies.get('JSESSIONID', '')
                        url2 = 'https://tickets.museivaticani.va/api/visit/timeavail'
                        params2 = {
                            'lang': 'it',
                            'visitLang': '',
                            'visitTypeId': str(ticket['id']),
                            'visitorNum': str(task.visitors),
                            'visitDate': date_formatted
                        }
                        
                        headers2 = headers.copy()
                        if jsessionid:
                            headers2['Cookie'] = f'JSESSIONID={jsessionid}'
                        
                        r2 = requests.get(url2, params=params2, headers=headers2, timeout=10)
                        
                        if r2.status_code == 200:
                            timetable = r2.json().get('timetable', [])
                            available_slots = [s for s in timetable if s.get('availability') == 'AVAILABLE']
                            if available_slots:
                                times = [s['time'] for s in available_slots[:10]]
                                print(f"     Slots: {', '.join(times)}")
                                found_any = True
                    print()
                else:
                    print(f"❌ {date_formatted}: SOLD_OUT")
            else:
                print(f"⚠️  {date_formatted}: API error {r.status_code}")
                
        except Exception as e:
            print(f"⚠️  {date_formatted}: Error - {str(e)[:80]}")
    
    if not found_any:
        print("\n❌ No available slots found in the checked dates")
    else:
        print("\n✅ Found available slots! Check above for details")

if __name__ == '__main__':
    check_slots()
