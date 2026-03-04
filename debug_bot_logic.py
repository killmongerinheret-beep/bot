"""
Debug script to test the bot's availability checking logic
and compare with actual Vatican API responses
"""
import asyncio
import sys
import os
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import MonitorTask
from worker_vatican.hydra_monitor import HydraBot
from datetime import datetime
from asgiref.sync import sync_to_async

async def test_task_checking(task_id):
    """Test the bot's logic for a specific task"""
    
    # Get task from database (use sync_to_async for Django ORM)
    task = await sync_to_async(MonitorTask.objects.get)(id=task_id)
    
    print(f"\n{'='*80}")
    print(f"TESTING TASK {task_id}")
    print(f"{'='*80}")
    print(f"Site: {task.site}")
    print(f"Dates: {task.dates}")
    print(f"Visitors: {task.visitors}")
    print(f"Ticket Type: {task.ticket_type}")
    print(f"Ticket ID (cached): {task.ticket_id}")
    print(f"Ticket Name: {task.ticket_name}")
    print(f"Language: {task.language}")
    print(f"Last Status: {task.last_status}")
    print(f"Last Checked: {task.last_checked}")
    
    # Initialize bot
    bot = HydraBot(use_proxies=True)
    
    # Test each date
    for date_str in task.dates:
        print(f"\n{'-'*80}")
        print(f"CHECKING DATE: {date_str}")
        print(f"{'-'*80}")
        
        # Convert date format if needed
        if '/' in date_str:
            parts = date_str.split('/')
            if len(parts[0]) == 4:  # YYYY/MM/DD
                formatted_date = f"{parts[2]}/{parts[1]}/{parts[0]}"
            else:  # DD/MM/YYYY
                formatted_date = date_str
        elif '-' in date_str:
            parts = date_str.split('-')
            if len(parts[0]) == 4:  # YYYY-MM-DD
                formatted_date = f"{parts[2]}/{parts[1]}/{parts[0]}"
            else:  # DD-MM-YYYY
                formatted_date = f"{parts[0]}/{parts[1]}/{parts[2]}"
        else:
            formatted_date = date_str
        
        print(f"Formatted date for API: {formatted_date}")
        
        async with bot.get_browser() as browser:
            page = await browser.new_page()
            
            try:
                # Step 1: Resolve dynamic IDs
                print(f"\n📍 STEP 1: Resolving dynamic IDs...")
                resolved_ids = await bot.resolve_all_dynamic_ids(
                    page,
                    ticket_type=task.ticket_type,
                    target_date=formatted_date,
                    visitors=task.visitors
                )
                
                print(f"✅ Found {len(resolved_ids)} tickets:")
                for item in resolved_ids:
                    print(f"   - ID: {item['id']}, Name: {item['name']}")
                
                # Step 2: Match ticket by name
                print(f"\n📍 STEP 2: Matching ticket by name...")
                print(f"Looking for: '{task.ticket_name}'")
                
                fresh_id = None
                match_method = None
                
                # Strategy 1: Exact substring match
                for item in resolved_ids:
                    r_name = item.get('name', '').lower()
                    t_name = task.ticket_name.lower()
                    
                    if t_name in r_name or r_name in t_name:
                        if task.ticket_type == 0 and "lunch" in r_name:
                            continue
                        fresh_id = item['id']
                        match_method = "Exact Match"
                        print(f"✅ {match_method}: '{task.ticket_name}' -> ID {fresh_id}")
                        break
                
                # Strategy 2: Keyword matching
                if not fresh_id:
                    keywords = []
                    t_lower = task.ticket_name.lower()
                    
                    if 'musei' in t_lower or 'museum' in t_lower:
                        keywords.extend(['musei', 'museum', 'palazzo', 'specola'])
                    if 'biglietti' in t_lower or 'admission' in t_lower or 'ingresso' in t_lower:
                        keywords.extend(['biglietti', 'ingresso', 'admission'])
                    if 'visita' in t_lower or 'guided' in t_lower or 'tour' in t_lower:
                        keywords.extend(['visita', 'guidata', 'guided', 'tour'])
                    
                    best_match = None
                    best_score = 0
                    
                    for item in resolved_ids:
                        r_name = item.get('name', '').lower()
                        score = sum(1 for kw in keywords if kw in r_name)
                        
                        if task.ticket_type == 0 and any(x in r_name for x in ['lunch', 'pranzo', 'pellegrinaggi']):
                            continue
                        
                        if score > best_score:
                            best_score = score
                            best_match = item['id']
                    
                    if best_match and best_score >= 2:
                        fresh_id = best_match
                        match_method = f"Keyword Match (score: {best_score})"
                        print(f"✅ {match_method}: '{task.ticket_name}' -> ID {fresh_id}")
                
                # Strategy 3: Fallback
                if not fresh_id and task.ticket_type == 0:
                    for item in resolved_ids:
                        r_name = item.get('name', '').lower()
                        if 'biglietti' in r_name or 'ingresso' in r_name:
                            if not any(x in r_name for x in ['lunch', 'pranzo', 'pellegrinaggi', 'gruppi']):
                                fresh_id = item['id']
                                match_method = "Fallback Match"
                                print(f"✅ {match_method}: Using first standard ticket -> ID {fresh_id}")
                                break
                
                if not fresh_id:
                    print(f"❌ NO MATCH FOUND!")
                    print(f"   Falling back to stale ID: {task.ticket_id}")
                    fresh_id = task.ticket_id
                    match_method = "Stale ID (RISKY)"
                
                # Step 3: Check availability via API
                print(f"\n📍 STEP 3: Checking availability via API...")
                print(f"Using ID: {fresh_id}")
                print(f"Visitors: {task.visitors}")
                print(f"Language: {task.language}")
                
                result = await bot.check_via_click(
                    page,
                    ticket_id=fresh_id,
                    ticket_name=task.ticket_name,
                    ticket_index=0,
                    visit_date=formatted_date,
                    visitors=task.visitors
                )
                
                slots = result.get('slots', [])
                detected_lang = result.get('language')
                
                print(f"\n📊 RESULTS:")
                print(f"   Match Method: {match_method}")
                print(f"   Ticket ID Used: {fresh_id}")
                print(f"   Detected Language: {detected_lang}")
                print(f"   Slots Found: {len(slots)}")
                if slots:
                    print(f"   Available Times: {slots[:10]}")  # Show first 10
                    print(f"   Status: AVAILABLE ✅")
                else:
                    print(f"   Status: SOLD OUT ❌")
                
                # Compare with database status
                print(f"\n🔍 COMPARISON:")
                print(f"   Database Status: {task.last_status}")
                print(f"   Actual Status: {'available' if slots else 'sold_out'}")
                if task.last_status != ('available' if slots else 'sold_out'):
                    print(f"   ⚠️ MISMATCH DETECTED!")
                else:
                    print(f"   ✅ Status matches")
                
            except Exception as e:
                print(f"\n❌ ERROR: {e}")
                import traceback
                traceback.print_exc()
            finally:
                await page.close()

async def main():
    """Test multiple tasks"""
    
    # Test the problematic tasks
    test_tasks = [21, 24]  # March 16 and April 22 (both showing sold_out but actually available)
    
    for task_id in test_tasks:
        try:
            await test_task_checking(task_id)
        except Exception as e:
            print(f"\n❌ Failed to test task {task_id}: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(main())
