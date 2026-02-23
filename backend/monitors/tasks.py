import logging
import json
import os
import random
import requests as py_requests
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
from django.db import models
from .models import MonitorTask, CheckResult, Agency, Proxy, SiteCredential

# 1. Clean Imports
logger = logging.getLogger(__name__)

# VaticanPro and ColosseumPro are legacy classes that may not exist
VaticanPro = None
ColosseumPro = None

try:
    from worker_vatican.monitor import VaticanPro
except ImportError:
    logger.warning("⚠️ worker_vatican.monitor.VaticanPro not found (legacy module)")

try:
    from worker_colosseum.monitor import ColosseumPro
except ImportError:
    logger.warning("⚠️ worker_colosseum.monitor.ColosseumPro not found (legacy module)")

try:
    from worker_vatican.hydra_monitor import HydraBot
except ImportError:
    HydraBot = None
    logger.warning("⚠️ HydraBot not found")

try:
    from worker_vatican.god_tier_monitor import GodTierVaticanMonitor
except ImportError:
    GodTierVaticanMonitor = None
    logger.warning("⚠️ GodTierVaticanMonitor not found")

# ✅ GOD-TIER CONFIGURATION
# Set to 'headless' for ultra-fast HTTP mode (10x faster)
# Set to 'browser' for legacy browser mode (slower but more reliable)
# Set to 'hybrid' to try headless first, fallback to browser (recommended)
VATICAN_MONITOR_MODE = os.getenv('VATICAN_MONITOR_MODE', 'hybrid')

logger.info(f"🚀 Vatican Monitor Mode: {VATICAN_MONITOR_MODE}")

def get_proxy_str(site='vatican'):
    """Helper to select the best proxy using Smart Reputation Logic"""
    now = timezone.now()
    
    # Reset expired cooldowns (clean up logic, or just filter)
    # Filter proxies that are active AND not cooling down
    valid_proxies = Proxy.objects.filter(is_active=True).filter(
        models.Q(cooldown_until__isnull=True) | models.Q(cooldown_until__lte=now)
    )
    
    if site == 'colosseum':
        # Colosseum needs high-quality IPs (ISP/Resid)
        proxy_obj = valid_proxies.filter(ip_port__icontains='oxylabs').order_by('?').first()
    else:
        # Vatican is less strict, but still prefer Oxylabs
        proxy_obj = valid_proxies.filter(ip_port__icontains='oxylabs').order_by('?').first()
        if not proxy_obj:
            proxy_obj = valid_proxies.order_by('?').first()

    if not proxy_obj:
        # If ALL proxies are on cooldown, pick the one with the earliest cooldown expiry
        # This prevents 100% downtime if everything is banned
        emergency_proxy = Proxy.objects.filter(is_active=True).order_by('cooldown_until').first()
        if emergency_proxy:
            logger.warning(f"⚠️ All proxies on cooldown! Using earliest available: {emergency_proxy} (Expires: {emergency_proxy.cooldown_until})")
            proxy_obj = emergency_proxy
        else:
            return None, None

    # Update Last Used
    proxy_obj.last_used = now
    proxy_obj.save(update_fields=['last_used'])

    user = proxy_obj.username
    if 'oxylabs' in proxy_obj.ip_port.lower():
        session_id = random.randint(10000, 99999)
        user = f"{proxy_obj.username}-session-{session_id}"
    
    if user and proxy_obj.password:
        return f"http://{user}:{proxy_obj.password}@{proxy_obj.ip_port}", proxy_obj
    else:
        return f"http://{proxy_obj.ip_port}", proxy_obj

def report_proxy_status(proxy_obj, success=True):
    """Update proxy reputation based on result"""
    if not proxy_obj: 
        return
        
    if success:
        if proxy_obj.fail_count > 0:
            proxy_obj.fail_count = 0
            proxy_obj.consecutive_failures = 0
            proxy_obj.cooldown_until = None
            proxy_obj.save()
    else:
        proxy_obj.fail_count += 1
        proxy_obj.consecutive_failures += 1
        
        # Smart Cooldown Logic (Exponential Backoff)
        # 1 fail = 0m, 3 fails = 5m, 5 fails = 30m, 10 fails = 2h
        cooldown_mins = 0
        if proxy_obj.consecutive_failures >= 3:
            cooldown_mins = 5
        if proxy_obj.consecutive_failures >= 5:
            cooldown_mins = 30
        if proxy_obj.consecutive_failures >= 10:
            cooldown_mins = 120
            
        if cooldown_mins > 0:
            proxy_obj.cooldown_until = timezone.now() + timedelta(minutes=cooldown_mins)
            logger.warning(f"🚫 Proxy {proxy_obj} cooling down for {cooldown_mins}m (Failures: {proxy_obj.consecutive_failures})")
            
        proxy_obj.save()

# --- GOD TIER: SESSION MANAGERS ---
@shared_task(name="refresh_colosseum_session", queue="colosseum")
def refresh_colosseum_session():
    """Runs periodically to pre-warm Colosseum cookies and store in Redis"""
    logger.info("🔄 GOD TIER: Refreshing Colosseum Session...")
    try:
        proxy_str, _ = get_proxy_str('colosseum')
        monitor = ColosseumPro(proxy=proxy_str)
        
        # 1. Try Direct API (Bypass Queue)
        # Using a distant date to check access (May 2026)
        monitor.get_availability(2026, 5)
        
        # 2. If API set cookies (e.g. incap/visid), cache them
        if monitor.session.cookies:
            cookies = monitor.session.cookies.get_dict()
            cache.set('colosseum_cookies', cookies, timeout=600)
            logger.info(f"✅ Colosseum Session Cached! ({len(cookies)} cookies)")
            return "Session Refreshed"
        else:
             # Even if no cookies, if API worked (no exception), we are good. 
             # But we can't cache 'nothing', so monitor will default to Direct API anyway.
             return "Verified API Access (No Cookies)"
    except Exception as e:
        logger.error(f"Failed to refresh Colosseum session: {e}")
    return "Failed"

@shared_task(name="refresh_vatican_session", queue="vatican")
def refresh_vatican_session():
    """Runs periodically to pre-warm Vatican cookies and store in Redis"""
    logger.info("🔄 GOD TIER: Refreshing Vatican Session...")
    try:
        proxy_str, _ = get_proxy_str('vatican')
        
        # Check for ANY active credential to use for warming (can use first found)
        creds = SiteCredential.objects.filter(site='vatican', is_active=True).first()
        username = creds.username if creds else None
        password = creds.password if creds else None
        
        monitor = VaticanPro(proxy=proxy_str, username=username, password=password)
        # Force generation
        monitor.generate_trust_cookies()
        
        if monitor.session.cookies:
            cookies = monitor.session.cookies.get_dict()
            cache.set('vatican_cookies', cookies, timeout=600)
            logger.info(f"✅ Vatican Session Cached! ({len(cookies)} cookies)")
            return "Session Refreshed"
    except Exception as e:
        logger.error(f"Failed to refresh Vatican session: {e}")
    return "Failed"


# ✅ NEW: SMART VATICAN MONITOR (Multi-Agency Optimized)
@shared_task(name="run_smart_vatican_monitor", queue="vatican")
def run_smart_vatican_monitor(date, ticket_id, ticket_name, language, task_ids):
    """
    ULTRA-OPTIMIZED: Checks ONE specific (date, ticket_id, language) combo
    and notifies ALL agencies (task_ids) interested in it.
    
    Args:
        date: DD/MM/YYYY format
        ticket_id: Vatican ticket ID (e.g., '929041748')
        ticket_name: Human-readable name
        language: Language code (ENG/ITA/FRA/DEU/SPA) or None for standard tickets
        task_ids: List of MonitorTask IDs interested in this combo
    """
    try:
        logger.info(f"🎯 SMART CHECK: {date} | Ticket: {ticket_id} ({ticket_name}) | Lang: {language} | Agencies: {len(task_ids)}")
        
        from worker_vatican.hydra_monitor import HydraBot
        import asyncio
        
        async def check_ticket():
            bot = HydraBot(use_proxies=True)
            
            async with bot.get_browser() as browser:
                page = await browser.new_page()
                
                try:
                    # Navigate to deep link for this specific ticket/date
                    # Use ticket_type=0 for standard, 1 for guided (determined by language presence)
                    ticket_type = 1 if language else 0
                    
                    # Resolve IDs to get to the page
                    resolved_ids = await bot.resolve_all_dynamic_ids(
                        page,
                        ticket_type=ticket_type,
                        target_date=date,
                        visitors=2
                    )
                    
                    # 💡 DYNAMIC RESOLUTION LOGIC
                    # Ignore the passed 'ticket_id' (it's likely stale).
                    # Find the fresh ID that matches 'ticket_name'.
                    fresh_id = None
                    exact_match = None
                    
                    logger.info(f"🔎 Resolving fresh ID for name '{ticket_name}' among {len(resolved_ids)} candidates...")
                    
                    for item in resolved_ids:
                        # item = {'id': '...', 'name': '...', 'description': '...'}
                        r_name = item.get('name', '').lower()
                        t_name = ticket_name.lower()
                        
                        # 1. Exact contains?
                        if t_name in r_name or r_name in t_name:
                            # Prefer "Admission" loop avoidance if standard
                            if ticket_type == 0 and "lunch" in r_name: continue
                            exact_match = item['id']
                            break
                            
                    if exact_match:
                        fresh_id = exact_match
                        logger.info(f"✅ Dynamic Match: '{ticket_name}' -> ID {fresh_id}")
                    else:
                        # LOG THE CANDIDATES for debugging
                        candidate_names = [i.get('name', '') for i in resolved_ids]
                        logger.warning(f"⚠️ No name match for '{ticket_name}'. Candidates: {candidate_names}")
                        logger.warning(f"Falling back to stale ID {ticket_id} (Risky)")
                        fresh_id = ticket_id # Fallback
                    
                    # Determine ticket index for language detection
                    # For now, we pass 0 - the method will auto-detect language selector
                    ticket_index = 0
                    
                    # ✅ USE ENHANCED CHECK METHOD with FRESH ID
                    result = await bot.check_via_click(
                        page,
                        ticket_id=fresh_id,
                        ticket_name=ticket_name,
                        ticket_index=ticket_index
                    )
                    
                    slots = result.get('slots', [])
                    detected_lang = result.get('language')
                    
                    await page.close()
                    
                    return {
                        'status': 'available' if slots else 'sold_out',
                        'slots': slots,
                        'language_detected': detected_lang
                    }
                    
                except Exception as e:
                    logger.error(f"Check failed: {e}")
                    await page.close()
                    return {
                        'status': 'error',
                        'slots': [],
                        'error': str(e)
                    }
        
        # Run the check
        check_result = asyncio.run(check_ticket())
        
        status = check_result['status']
        slots = check_result['slots']
        detected_lang = check_result.get('language_detected')
        
        # ✅ NOTIFY ALL INTERESTED AGENCIES
        tasks = MonitorTask.objects.filter(id__in=task_ids)
        
        for task in tasks:
            task.last_checked = timezone.now()
            task.last_status = status
            
            # ✅ STATE CHANGE DETECTION using Redis
            # Key format: ticket_state:{task_id}:{ticket_id}:{date}
            state_key = f"ticket_state:{task.id}:{ticket_id}:{date}"
            previous_state = cache.get(state_key)
            
            # 🛡️ DEFENSIVE: Handle Redis Bytes vs String mismatch
            if isinstance(previous_state, bytes):
                previous_state = previous_state.decode('utf-8')

            # Determine if this is a state CHANGE
            is_now_available = len(slots) > 0
            was_previously_available = previous_state == 'available' if previous_state else False
            is_first_check = previous_state is None
            
            # State change: closed → open
            status_changed_to_open = is_now_available and not was_previously_available
            
            # Update cache with current state
            new_state = 'available' if is_now_available else 'closed'
            cache.set(state_key, new_state, timeout=86400 * 7)  # 7 days TTL
            
            # Save result to database (always, for history)
            CheckResult.objects.create(
                task=task,
                status=status,
                details={
                    'date': date,
                    'ticket_id': ticket_id,
                    'ticket_name': ticket_name,
                    'language': language or detected_lang,
                    'slots': slots,
                    'state_changed': status_changed_to_open,
                    'previous_state': previous_state,
                    'is_first_check': is_first_check
                },
                error_message=check_result.get('error')
            )
            
            task.save()
            
            # ✅ SMART NOTIFICATION: Only alert on state CHANGE (closed → open)
            should_alert = status_changed_to_open and not is_first_check
            
            # 🛡️ SPAM GUARD: Cooldown key (Double Protection)
            # Prevent sending same alert for same ticket/date within 60 minutes
            # regardless of state flips (e.g. flaky connection)
            alert_cooldown_key = f"alert_cooldown:{task.id}:{ticket_id}:{date}"
            if should_alert and cache.get(alert_cooldown_key):
                 logger.info(f"⏳ SUPPRESSED ALERT: Cooldown active for {ticket_name}")
                 should_alert = False

            if is_first_check and is_now_available:
                # First check found tickets - log but don't alert (user said so)
                logger.info(f"ℹ️ First check: {ticket_name} already available - NOT alerting (initial state)")
            elif status_changed_to_open and not is_first_check:
                if should_alert:
                    logger.info(f"🔔 STATE CHANGE: {ticket_name} went from CLOSED → OPEN! Sending Alert.")
                    # Set Cooldown
                    cache.set(alert_cooldown_key, "sent", timeout=3600) # 1 Hour Silence
                else:
                    logger.info(f"🔕 STATE CHANGE detected but Alert Suppressed (Cooldown/Muted)")
            elif not is_now_available:
                logger.info(f"🔒 {ticket_name} is CLOSED ({len(slots)} slots)")
            else:
                logger.info(f"ℹ️ {ticket_name} still AVAILABLE - no alert needed")
            
            # Send Telegram notification only if should_alert passed all checks
            if should_alert and task.notification_mode != 'silent':
                try:
                    chat_id = task.agency.telegram_chat_id
                    if chat_id:
                        lang_info = f" ({detected_lang or language})" if (detected_lang or language) else ""
                        message = f"🚨 *TICKETS JUST OPENED!*\n\n"
                        message += f"📅 Date: {date}\n"
                        message += f"🎫 Ticket: {ticket_name}{lang_info}\n\n"
                        message += f"⏰ Available Times ({len(slots)} slots):\n"
                        
                        for slot in slots[:10]:  # First 10 slots
                            message += f"  • {slot}\n"
                        
                        if len(slots) > 10:
                            message += f"  ... and {len(slots) - 10} more\n"
                        
                        message += f"\n🔗 Book now!"
                        
                        send_telegram_signal(chat_id, message)
                        logger.info(f"✅ TELEGRAM ALERT sent to {task.agency.name}")
                except Exception as e:
                    logger.error(f"Notification failed for task {task.id}: {e}")
        
        logger.info(f"✅ Completed check for {date}/{ticket_id} - Checked {len(task_ids)} agencies")
        return f"Checked {ticket_name} - Found {len(slots)} slots - State change alerts sent if applicable"
        
    except Exception as e:
        logger.error(f"Smart monitor failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return f"Failed: {str(e)}"


# ✅ NEW: GOD-TIER HEADLESS MONITOR (Ultra-Fast HTTP Mode)
@shared_task(name="run_god_tier_vatican_monitor", queue="vatican")
def run_god_tier_vatican_monitor(date, ticket_id, ticket_name, language, task_ids, use_browser_fallback=True):
    """
    🚀 ULTRA-FAST: Uses headless HTTP mode (curl_cffi) for 10x speed improvement.
    Only falls back to browser if session is invalid and refresh fails.
    
    Args:
        date: DD/MM/YYYY format
        ticket_id: Vatican ticket ID (e.g., '929041748')
        ticket_name: Human-readable name
        language: Language code (ENG/ITA/FRA/DEU/SPA) or None for standard tickets
        task_ids: List of MonitorTask IDs interested in this combo
        use_browser_fallback: If True, uses HydraBot when headless fails
    """
    import asyncio
    
    try:
        logger.info(f"🚀 GOD-TIER CHECK: {date} | Ticket: {ticket_name} | Lang: {language} | Agencies: {len(task_ids)}")
        
        ticket_type = 1 if language else 0
        languages = [language] if language else ["ITA"]
        
        # Initialize God-Tier Monitor
        monitor = GodTierVaticanMonitor()
        
        # Run headless check
        async def headless_check():
            return await monitor.check_availability_headless(
                date_str=date,
                ticket_type=ticket_type,
                languages=languages
            )
        
        results = asyncio.run(headless_check())
        
        # Filter results for the specific ticket we want
        matching_results = [
            r for r in results 
            if ticket_id in r.get('ticket_id', '') or ticket_name.lower() in r.get('ticket_name', '').lower()
        ]
        
        # If no results and browser fallback is enabled, try browser mode
        if not matching_results and use_browser_fallback:
            logger.warning(f"⚠️ Headless check returned no results, falling back to browser mode")
            # Delegate to the existing smart monitor which uses HydraBot
            return run_smart_vatican_monitor(date, ticket_id, ticket_name, language, task_ids)
        
        # Extract slots from results
        all_slots = []
        for result in matching_results:
            all_slots.extend(result.get('slots', []))
        
        # Deduplicate slots by time
        seen_times = set()
        unique_slots = []
        for slot in all_slots:
            time_key = slot.get('time', slot) if isinstance(slot, dict) else slot
            if time_key not in seen_times:
                seen_times.add(time_key)
                unique_slots.append(slot)
        
        status = 'available' if unique_slots else 'sold_out'
        
        # ✅ NOTIFY ALL INTERESTED AGENCIES (same logic as smart monitor)
        tasks = MonitorTask.objects.filter(id__in=task_ids)
        
        for task in tasks:
            task.last_checked = timezone.now()
            task.last_status = status
            
            # State change detection
            state_key = f"ticket_state:{task.id}:{ticket_id}:{date}"
            previous_state = cache.get(state_key)
            
            if isinstance(previous_state, bytes):
                previous_state = previous_state.decode('utf-8')
            
            is_now_available = len(unique_slots) > 0
            was_previously_available = previous_state == 'available' if previous_state else False
            is_first_check = previous_state is None
            status_changed_to_open = is_now_available and not was_previously_available
            
            new_state = 'available' if is_now_available else 'closed'
            cache.set(state_key, new_state, timeout=86400 * 7)
            
            # Save result
            CheckResult.objects.create(
                task=task,
                status=status,
                details={
                    'date': date,
                    'ticket_id': ticket_id,
                    'ticket_name': ticket_name,
                    'language': language,
                    'slots': unique_slots,
                    'state_changed': status_changed_to_open,
                    'previous_state': previous_state,
                    'is_first_check': is_first_check,
                    'check_method': 'god_tier_headless'
                }
            )
            
            task.save()
            
            # ✅ IMPROVED: Smart notification logic with proper cooldown handling
            should_alert = False
            alert_cooldown_key = f"alert_cooldown:{task.id}:{ticket_id}:{date}"
            
            if is_first_check and is_now_available:
                logger.info(f"ℹ️ First check: {ticket_name} already available - NOT alerting (initial state)")
            elif status_changed_to_open and not is_first_check:
                # State changed from closed to open - this is what we want to alert on!
                if cache.get(alert_cooldown_key):
                    logger.info(f"⏳ SUPPRESSED ALERT: Cooldown active for {ticket_name}")
                    should_alert = False
                else:
                    logger.info(f"🔔 STATE CHANGE: {ticket_name} went from CLOSED → OPEN!")
                    should_alert = True
                    # Set cooldown immediately to prevent duplicate alerts
                    cache.set(alert_cooldown_key, "sent", timeout=3600)
            elif not is_now_available:
                logger.info(f"🔒 {ticket_name} is CLOSED ({len(unique_slots)} slots)")
            else:
                logger.info(f"ℹ️ {ticket_name} still AVAILABLE - no alert needed")
            
            # ✅ Send Telegram notification if should_alert is True
            if should_alert and task.notification_mode != 'silent':
                try:
                    chat_id = task.agency.telegram_chat_id
                    if chat_id:
                        lang_info = f" ({language})" if language else ""
                        message = f"🚨 *TICKETS JUST OPENED!*\n\n"
                        message += f"📅 Date: {date}\n"
                        message += f"🎫 Ticket: {ticket_name}{lang_info}\n"
                        message += f"⚡ Check Method: Ultra-Fast Headless\n\n"
                        message += f"⏰ Available Times ({len(unique_slots)} slots):\n"
                        
                        for slot in unique_slots[:10]:
                            time_str = slot.get('time', slot) if isinstance(slot, dict) else slot
                            message += f"  • {time_str}\n"
                        
                        if len(unique_slots) > 10:
                            message += f"  ... and {len(unique_slots) - 10} more\n"
                        
                        message += f"\n🔗 Book now!"
                        
                        send_telegram_signal(chat_id, message)
                        logger.info(f"✅ TELEGRAM ALERT sent to {task.agency.name}")
                    else:
                        logger.warning(f"⚠️ No telegram_chat_id for agency {task.agency.name}")
                except Exception as e:
                    logger.error(f"❌ Notification failed: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
        
        logger.info(f"✅ God-Tier check complete: {ticket_name} - Found {len(unique_slots)} slots")
        return f"God-Tier Checked {ticket_name} - Found {len(unique_slots)} slots"
        
    except Exception as e:
        logger.error(f"God-Tier monitor failed: {e}")
        # Fallback to browser mode on error
        if use_browser_fallback:
            logger.info("Falling back to browser mode due to error")
            return run_smart_vatican_monitor(date, ticket_id, ticket_name, language, task_ids)
        return f"Failed: {str(e)}"


@shared_task(name="run_shared_vatican_monitor", queue="vatican")

def run_shared_vatican_monitor(ticket_type, language, dates):
    """
    OPTIMIZED: Checks a list of dates for a specific configuration
    and updates ALL matching tasks in the database.
    """
    try:
        # Resolve Pattern Name based on Type
        # Type 0 = Standard -> "Admission"
        # Type 1 = Guided -> "Guided" (or specific name if we had it, but shared monitor is generic)
        name_pattern = "Admission" if ticket_type == 0 else "Guided"
        
        # Use HydraBot for check
        bot = HydraBot(use_proxies=True)
        bot.target_dates = dates
        
        logger.info(f"🐉 HYDRA SHARED: Checking {len(dates)} dates (Type: {ticket_type}, Lang: {language}, Pattern: {name_pattern})")
        
        # Determine language for bot
        bot_lang = language if ticket_type == 1 else "ENG" 
        
        import asyncio
        # Pass name_pattern to bot
        results = asyncio.run(bot.run_once(ticket_type=ticket_type, language=bot_lang, name_pattern=name_pattern))
        
        # Process Results & Update Tasks
        # ... (rest of logic) ...
        # Match date format reliably (Handle ISO vs DD/MM/YYYY)
        # ... (omitted for brevity, keeping existing logic) ...
        
        # Find tasks
        from django.db.models import Q
        # ... (query construction) ...
        
        # Use Q expressions for multiple variants
        # Re-construct query since we are replacing the block
        date_query = Q()
        for d in dates: # Broad query for any date in the batch
             date_query |= Q(dates__icontains=d)
             # Also add variants just in case
             if "-" in d:
                 try:
                     from datetime import datetime
                     dt = datetime.strptime(d, "%Y-%m-%d")
                     date_query |= Q(dates__icontains=dt.strftime("%d/%m/%Y"))
                 except: pass

        matching_tasks = MonitorTask.objects.filter(
            date_query,
            site='vatican', 
            ticket_type=ticket_type,
            is_active=True
        )
        
        if ticket_type == 1:
            matching_tasks = matching_tasks.filter(language__iexact=language)
        
        logger.info(f"📝 Found {matching_tasks.count()} tasks for {dates}...")
        
        # Aggregation
        task_updates = {} 

        for date_str, rich_items in results.items():
            # ... (date format matching logic repeated for specific result key) ...
            target_tasks = matching_tasks # Simplified scope

            for task in target_tasks:
                 # Check if this task cares about this date
                 # This logic is a bit loose in original code (it checked all matching tasks against all results)
                 # We can refine:
                 task_wants_date = False
                 for d in task.dates:
                     if date_str in d or d in date_str: # Simple contains check
                         task_wants_date = True
                         break
                 if not task_wants_date: continue

                 if task.id not in task_updates:
                    task_updates[task.id] = {
                        'task': task,
                        'updates': {}
                    }
                 
                 task_updates[task.id]['updates'][date_str] = rich_items
                 
                 # Dynamic ID update (InMemory only, avoiding persistence trap)
                 if rich_items:
                     best = rich_items[0]
                     # We can update the DB specifically if we want dashboard to show it,
                     # but we should NOT rely on it for dispatch.
                     # User said: "Stop treating ID as Constant".
                     # So let's update it for visibility, but our dispatch logic (orchestrate)
                     # should NOT use it.
                     if task.ticket_id != best['id']:
                         task.ticket_id = best['id']
                         task.ticket_name = best.get('name')
                         # We save it, but we won't use it for dispatch anymore.
                 
                 has_slots = any(len(i['slots']) > 0 for i in rich_items)
                 status = 'available' if has_slots else 'sold_out'
                 
                 task.last_checked = timezone.now()
                 task.last_status = status
                 
                 if status == 'available' or task.last_status != 'available':
                        CheckResult.objects.create(
                            task=task,
                            status=status,
                            details={date_str: rich_items},
                        )
                 task.save()
                 
        # Notifications (same as before)

        # Send Notifications for each Task
        for tid, data in task_updates.items():
            task = data['task']
            updates = data['updates'] # Map: date -> rich_list
            
            # Check if ANY available slots found
            found_any = False
            for d, rich_list in updates.items():
                # rich_list is [{slots:[], ...}, ...]
                for item in rich_list:
                    if item.get('slots'):
                        found_any = True
                        break
                if found_any: break
            
            # SPAM PREVENTION LOGIC
            # We sort keys and hash the content to see if it EXACTLY matches the last notification
            current_hash = "none"
            try:
                import hashlib
                # Create a canonical string representation of updates
                # e.g. "2026-05-25:09:00,09:30|2026-05-26:10:00"
                # Sort dates
                sorted_dates = sorted(updates.keys())
                content_str = ""
                for d in sorted_dates:
                    rich_list = updates[d]
                    # Sort items by name to be deterministic
                    # rich_list.sort(key=lambda x: x.get('name', '')) # Optional
                    
                    for item in rich_list:
                         s_list = item.get('slots', [])
                         if s_list:
                             sorted_slots = sorted(s_list)
                             content_str += f"{d}:{item.get('name')}:{','.join(sorted_slots)}|"
                
                # Create MD5 of this content
                current_hash = hashlib.md5(content_str.encode()).hexdigest()
                
                # Check against last stored hash (we need a place to store it)
                # We can store it in 'last_result_summary' or a new field.
                # Since 'last_result_summary' is JSON, we can add a field there.
                
                prev_summary = {}
                if task.last_result_summary:
                    try:
                        prev_summary = json.loads(task.last_result_summary)
                    except:
                        pass
                
                last_notified_hash = prev_summary.get('_notified_hash')
                
                # If exact duplicate of what we LAST NOTIFIED, skip (unless 'always' mode?)
                # User complaint: "bot is spamming". So we SKIP.
                # Only if found_any is True (we don't spam 'sold_out' anyway usually)
                if found_any and current_hash == last_notified_hash:
                    logger.info(f"🔕 Skipping duplicate notification for Task {task.id} (Hash match)")
                    
                    # Even if we skip, we should probably update the summary with latest time?
                    # But if we update summary, we MUST keep the hash.
                    prev_summary['last_updated'] = str(timezone.now())
                    task.last_result_summary = json.dumps(prev_summary)
                    task.save(update_fields=['last_result_summary'])
                    continue
                
                # Update hash in DB (even if we don't notify below, we should track state)
                # But typically we update it AFTER sending notification.
            except Exception as e:
                logger.error(f"Hash calc failed: {e}")
                current_hash = "error"
            
            if found_any and task.notification_mode != 'silent':
                # Build Message
                msg = f"⛪ *VATICAN FOUND!* ({task.area_name})\n"
                
                # Helper for Link Generation
                def get_vatican_link(d_str, t_type):
                     try:
                         from zoneinfo import ZoneInfo
                         from datetime import datetime
                         rome = ZoneInfo("Europe/Rome")
                         if "/" in d_str:
                             dt = datetime.strptime(d_str, "%d/%m/%Y")
                         else:
                             dt = datetime.strptime(d_str, "%Y-%m-%d")
                         midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=rome)
                         ts = int(midnight.timestamp() * 1000)
                         tag_id = 3 if t_type == 0 else 2
                         tag = "MV-Biglietti" if t_type == 0 else "MV-Visite-Guidate"
                         return f"https://tickets.museivaticani.va/home/fromtag/{tag_id}/{ts}/{tag}/1"
                     except:
                         return "https://tickets.museivaticani.va/"

                user_prefs = task.preferred_times or []
                
                for date, rich_list in updates.items():
                    # Only show if slots exist
                    for item in rich_list:
                         slots = item.get('slots', [])
                         if not slots: continue
                         
                         name = item.get('name', 'Unknown Ticket')
                         # Pass available ID for direct link
                         t_id = item.get('id', task.ticket_id)
                         link = get_vatican_link(date, task.ticket_type, t_id)
                         
                         # Check strictly for preferred times
                         found_prefs = []
                         missing_prefs = []
                         
                         for p in user_prefs:
                             # Check if any slot exactly matches or starts with preference
                             # e.g. "13:30" matches "13:30" or "13:30:00"
                             match = next((s for s in slots if s.startswith(p)), None)
                             if match:
                                 found_prefs.append(match)
                             else:
                                 missing_prefs.append(p)
                         
                         # Construct Message Header based on Preferences
                         if found_prefs:
                             msg += f"✅ **PREFERRED TIME FOUND!**\n"
                             for fp in found_prefs:
                                 msg += f"   • {fp}\n"
                         elif user_prefs:
                             msg += f"❌ Preferred times ({', '.join(missing_prefs)}) are SOLD OUT.\n"
                         
                         msg += f"\n📅 *{date}*: {name}\n"
                         
                         # List all slots (highlighted)
                         formatted_slots = []
                         slots.sort()
                         for s in slots:
                             if s in found_prefs:
                                 formatted_slots.append(f"**{s}**") # Bold
                             else:
                                 formatted_slots.append(s)
                                 
                         slot_str = ", ".join(formatted_slots[:25])
                         if len(formatted_slots) > 25: slot_str += "..."
                         
                         msg += f"⏰ All Slots: {slot_str}\n"
                         msg += f"🔗 [Book Now]({link})\n"
                
                send_telegram_signal(task.agency.telegram_chat_id, msg)
                
            # Update Summary with NEW Hash and Content (Always, if found_any)
            # This ensures dashboard shows latest info AND hash is saved for next comparison.
            if found_any:
                try:
                     summary_data = {
                         "updates": updates,
                         "_notified_hash": current_hash,
                         "last_updated": str(timezone.now())
                     }
                     task.last_result_summary = json.dumps(summary_data)
                     task.save(update_fields=['last_result_summary'])
                except Exception as e:
                    logger.error(f"Failed to save summary: {e}")

        return f"Shared Check Completed and Notified for {len(dates)} dates"

    except Exception as e:
        logger.error(f"Error in run_shared_vatican_monitor: {e}")
        return str(e)

def send_telegram_signal(chat_id, message):
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") 
    if not TOKEN:
        logger.error("No TELEGRAM_BOT_TOKEN configured")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        py_requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=10)
        logger.info(f"Telegram signal sent to {chat_id}")
    except Exception as e:
        logger.error(f"Failed to send Telegram signal: {e}")

@shared_task(name="run_colosseum_monitor", queue="colosseum")
def run_colosseum_monitor(task_id):
    try:
        task = MonitorTask.objects.get(id=task_id)
        agency = task.agency
        
        proxy_str, proxy_obj = get_proxy_str('colosseum')
        
        monitor = ColosseumPro(lang=task.language, proxy=proxy_str)
        if task.area_name and len(task.area_name) == 36:
            monitor.event_guid = task.area_name
        
        logger.info(f"Running Colosseum Pro check for Task {task_id} using proxy {proxy_obj}")
        
        results = monitor.check_dates(task.dates)
        
        prev_status = task.last_status
        status = 'available' if results else 'sold_out'
        CheckResult.objects.create(
            task=task,
            status=status,
            details=results
        )
        
        task.last_checked = timezone.now()
        task.last_status = status
        task.last_result_summary = json.dumps(results)
        task.save()
        
        # Report Success
        report_proxy_status(proxy_obj, success=True)
        
        if (status == 'available' and prev_status != 'available') or (task.notification_mode == 'any_change' and status != prev_status):
            if task.notification_mode != 'silent':
                send_telegram_signal(agency.telegram_chat_id, f"🏛️ COLOSSEUM ALERT: {task.area_name}\n\n" + json.dumps(results, indent=2))
        
        return f"Colosseum check completed for task {task_id}. Status: {status}"
        
    except Exception as e:
        # Report Failure
        report_proxy_status(proxy_obj, success=False)
        
        logger.error(f"Error in run_colosseum_monitor: {e}")
        try:
            task = MonitorTask.objects.get(id=task_id)
            task.last_status = 'error'
            task.last_result_summary = f"Engine Error: {str(e)}"
            task.save()
        except:
            pass
        return str(e)

@shared_task(name="orchestrate_all_tasks")
def orchestrate_all_tasks():
    """
    ✅ ULTRA-OPTIMIZED: Groups tasks by (date, ticket_id, language) for maximum efficiency.
    
    Example: If 5 agencies want the same ticket/date/language, we check ONCE and notify all 5.
    """
    now = timezone.now()
    active_tasks = MonitorTask.objects.filter(is_active=True)
    
    # ✅ NEW GROUPING STRUCTURE
    # Key: (date, ticket_id, language) → List of task IDs
    smart_groups = {}
    
    # OLD GROUPING (for backwards compat with tasks that don't have ticket_id)
    legacy_groups = {}
    
    colosseum_count = 0
    
    for task in active_tasks:
        # User defined interval or default 120s (Optimized)
        interval_seconds = getattr(task, 'check_interval', 120)
        if not interval_seconds or interval_seconds < 60:
            interval_seconds = 60  # Force min 60s
            
        should_run = False
        if not task.last_checked:
            should_run = True
        else:
            elapsed = (now - task.last_checked).total_seconds()
            if elapsed >= interval_seconds:
                should_run = True
                
        if should_run:
            if task.site == 'vatican' and task.dates:
                # ✅ NEW: Use smart grouping if ticket_id is specified
                if task.ticket_id:
                    for date in task.dates:
                        # Format: DD/MM/YYYY
                        # Group by EXACT combo
                        key = (date, task.ticket_id, task.language or None)
                        
                        if key not in smart_groups:
                            smart_groups[key] = {
                                'task_ids': [],
                                'ticket_name': task.ticket_name or 'Unknown Ticket'
                            }
                        
                        smart_groups[key]['task_ids'].append(task.id)
                else:
                    # LEGACY: Old behavior for tasks without ticket_id
                    key = (task.ticket_type, task.language or 'ENG')
                    if key not in legacy_groups:
                        legacy_groups[key] = set()
                    for d in task.dates:
                        legacy_groups[key].add(d)
                        
            elif task.site == 'colosseum':
                # Keep existing per-task logic for Colosseum (It is lightweight API)
                run_colosseum_monitor.apply_async(args=[task.id], countdown=random.randint(5, 30))
                colosseum_count += 1
                
    # ✅ DISPATCH SMART TASKS (New optimized method)
    smart_count = 0
    for (date, ticket_id, language), data in smart_groups.items():
        task_ids = data['task_ids']
        ticket_name = data['ticket_name']
        
        # Jitter for anti-ban
        jitter = random.randint(5, 30)
        
        # ✅ Dispatch based on configured mode
        if VATICAN_MONITOR_MODE == 'headless':
            # Ultra-fast headless mode only (no fallback)
            run_god_tier_vatican_monitor.apply_async(
                args=[date, ticket_id, ticket_name, language, task_ids],
                kwargs={'use_browser_fallback': False},
                countdown=jitter
            )
        elif VATICAN_MONITOR_MODE == 'browser':
            # Legacy browser mode
            run_smart_vatican_monitor.apply_async(
                args=[date, ticket_id, ticket_name, language, task_ids],
                countdown=jitter
            )
        else:  # 'hybrid' (default)
            # Try headless first, fallback to browser if needed
            run_god_tier_vatican_monitor.apply_async(
                args=[date, ticket_id, ticket_name, language, task_ids],
                kwargs={'use_browser_fallback': True},
                countdown=jitter
            )
        
        smart_count += 1
        logger.info(f"📊 Smart Group: {date}/{ticket_id}/{language} → {len(task_ids)} agencies")
    
    # DISPATCH LEGACY TASKS (Backwards compatibility)
    legacy_count = 0
    for (t_type, lang), date_set in legacy_groups.items():
        if not date_set:
            continue
        
        # Chunk dates to avoid overload (max 10 dates per worker)
        all_dates = list(date_set)
        CHUNK_SIZE = 10
        
        for i in range(0, len(all_dates), CHUNK_SIZE):
            chunk = all_dates[i:i + CHUNK_SIZE]
            
            # Jitter for anti-ban
            jitter = random.randint(5, 30)
            
            run_shared_vatican_monitor.apply_async(
                args=[t_type, lang, chunk],
                countdown=jitter
            )
            legacy_count += len(chunk)

    total_checks = smart_count + legacy_count
    logger.info(f"✅ Orchestration Complete: {smart_count} smart checks + {legacy_count} legacy checks + {colosseum_count} Colosseum")
    
    return f"Queued {smart_count} smart checks (multi-agency), {legacy_count} legacy checks, {colosseum_count} Colosseum tasks."
@shared_task(name="cleanup_old_results")
def cleanup_old_results():
    """
    Delete CheckResult records older than 7 days to save space.
    Runs daily via Celery Beat.
    """
    days_to_keep = 7
    cutoff_date = timezone.now() - timedelta(days=days_to_keep)
    
    deleted_count, _ = CheckResult.objects.filter(check_time__lt=cutoff_date).delete()
    
    logger.info(f"🧹 Cleanup: Deleted {deleted_count} results older than {days_to_keep} days.")
    return f"Deleted {deleted_count} old results"

@shared_task(name="cleanup_expired_monitor_tasks")
def cleanup_expired_monitor_tasks():
    """
    Daily Cleanup: Removes dates from the past.
    If a task has no future dates, it is deleted.
    """
    from datetime import datetime
    now_date = timezone.now().date()
    
    tasks = MonitorTask.objects.all()
    cleaned_count = 0
    deleted_count = 0
    
    for task in tasks:
        if not task.dates:
            continue
            
        # Filter dates
        new_dates = []
        changed = False
        
        for d_str in task.dates:
            try:
                # Handle formats
                if "/" in d_str:
                    dt = datetime.strptime(d_str, "%d/%m/%Y").date()
                elif "-" in d_str:
                    dt = datetime.strptime(d_str, "%Y-%m-%d").date()
                else:
                    # Keep invalid formats just in case, or drop?
                    # Let's drop them if we are strict, but maybe better to keep to avoid accidental deletion
                    # Actually, if we can't parse it, we can't check if it's past.
                    # Let's assume valid formats.
                    continue 
                
                if dt >= now_date:
                    new_dates.append(d_str)
                else:
                    changed = True
            except:
                pass 
                
        if changed:
            if not new_dates:
                logger.info(f"🗑️ Task {task.id} has no future dates. Deleting.")
                task.delete()
                deleted_count += 1
            else:
                task.dates = new_dates
                task.save()
                cleaned_count += 1
                
    return f"Cleanup: Updated {cleaned_count} tasks, Deleted {deleted_count} tasks."
