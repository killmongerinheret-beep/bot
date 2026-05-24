"""
Simplified Vatican Monitor Tasks using Search API
=================================================
Ultra-fast, reliable monitoring using Vatican's search API directly.
No browser automation needed - 10x faster than previous implementation.
"""

import logging
import json
import os
import requests
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
from .models import MonitorTask, CheckResult
from .notification_utils import format_vatican_notification, send_telegram_signal

logger = logging.getLogger(__name__)

# Import the new search API monitor
try:
    from worker_vatican.search_api_monitor import VaticanSearchAPIMonitor
except ImportError:
    VaticanSearchAPIMonitor = None
    logger.error("❌ VaticanSearchAPIMonitor not found!")


def get_proxy_str(site='vatican'):
    """Pick a random active proxy. No DB writes — read-only."""
    from .models import Proxy
    from django.db import models
    from django.utils import timezone

    now = timezone.now()
    proxy_obj = (
        Proxy.objects.filter(is_active=True)
        .filter(models.Q(cooldown_until__isnull=True) | models.Q(cooldown_until__lte=now))
        .order_by('?')
        .first()
    )
    if not proxy_obj:
        # All on cooldown — pick earliest
        proxy_obj = Proxy.objects.filter(is_active=True).order_by('cooldown_until').first()
    if not proxy_obj:
        return None, None

    user = proxy_obj.username or ''
    if 'oxylabs' in proxy_obj.ip_port.lower() and user:
        import random
        user = f"{user}-session-{random.randint(10000, 99999)}"

    if user and proxy_obj.password:
        return f"http://{user}:{proxy_obj.password}@{proxy_obj.ip_port}", proxy_obj
    return f"http://{proxy_obj.ip_port}", proxy_obj


def report_proxy_status(proxy_obj, success=True):
    """No-op — skip DB writes for speed."""
    pass


@shared_task(name="run_search_api_vatican_monitor", queue="vatican")
def run_search_api_vatican_monitor(date, ticket_id, ticket_name, language, task_ids, visitors=2):
    """
    🚀 ULTRA-FAST: Vatican monitor using search API directly.
    No browser automation - 10x faster and more reliable.
    
    ✅ WITH AUTOMATIC PROXY ROTATION ON RATE LIMIT
    
    Args:
        date: DD/MM/YYYY format
        ticket_id: Vatican ticket ID (may be stale - will be resolved fresh)
        ticket_name: Human-readable name for matching
        language: Language code (ENG/ITA/etc.) or None for standard tickets
        task_ids: List of MonitorTask IDs interested in this combo
        visitors: Number of visitors
    
    Returns:
        Status message string
    """
    try:
        logger.info(f"🚀 SEARCH API CHECK: {date} | {ticket_name} | Lang: {language} | Visitors: {visitors} | Agencies: {len(task_ids)}")
        
        if not VaticanSearchAPIMonitor:
            logger.error("❌ VaticanSearchAPIMonitor not available")
            return "Skipped: Monitor not available"
        
        # ✅ PROXY ROTATION: Try up to 3 different proxies if rate limited
        max_retries = 3
        for attempt in range(max_retries):
            # Get proxy for this check
            proxy_str, proxy_obj = get_proxy_str('vatican')
            
            if proxy_str:
                logger.info(f"🔄 Attempt {attempt + 1}/{max_retries} using proxy: {proxy_obj.ip_port if proxy_obj else 'direct'}")
            else:
                logger.warning(f"⚠️ No proxies available, using direct IP (attempt {attempt + 1}/{max_retries})")

            # Initialize monitor
            monitor = VaticanSearchAPIMonitor(proxy_str=proxy_str)

            # Determine ticket type
            ticket_type = 1 if language else 0
            
            # Perform check
            try:
                success, slots, resolved_ticket_id = monitor.check_ticket(
                    target_date=date,
                    ticket_name=ticket_name,
                    visitors=visitors,
                    ticket_type=ticket_type,
                    language=language
                )
                
                # ✅ SUCCESS - No rate limiting, break retry loop
                if not success:
                    logger.warning(f"⚠️ Check returned no result for {ticket_name} - treating as sold_out")
                    status = 'sold_out'
                    slots = []
                    resolved_ticket_id = ticket_id
                else:
                    status = 'available' if slots else 'sold_out'
                    if slots:
                        logger.info(f"✅ {len(slots)} slots for {ticket_name} {date}")
                
                # Success - break retry loop
                break
                
            except requests.exceptions.Timeout as e:
                logger.error(f"⚠️ RATE LIMITED on attempt {attempt + 1}: {e}")
                
                # ✅ COOLDOWN PROXY: Mark this proxy as rate limited
                if proxy_obj:
                    proxy_obj.cooldown_until = timezone.now() + timedelta(minutes=15)
                    proxy_obj.save()
                    logger.info(f"🔒 Proxy {proxy_obj.ip_port} on cooldown for 15 minutes")
                
                # If this was the last attempt, skip result save
                if attempt == max_retries - 1:
                    logger.error(f"❌ All {max_retries} proxies failed for {ticket_name} - skipping")
                    return f"Rate limited: All proxies exhausted"
                
                # Otherwise, retry with next proxy
                logger.info(f"🔄 Retrying with different proxy...")
                continue
                
            except Exception as e:
                logger.error(f"❌ Monitor exception: {e}")
                logger.warning(f"⚠️ Skipping result save for {ticket_name} due to exception - will retry")
                return f"Error: {str(e)}"
        
        # Process results for all interested agencies
        tasks = MonitorTask.objects.filter(id__in=task_ids).select_related('agency')
        
        for task in tasks:
            task.last_checked = timezone.now()
            task.last_status = status
            
            # ✅ STATE CHANGE DETECTION using Redis
            # Key uses task.id + date only (stable - ticket_id can be None or change)
            state_key = f"ticket_state:{task.id}:{date}"
            previous_state = cache.get(state_key)
            
            # Handle Redis Bytes vs String mismatch
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
                    'effective_ticket_id': resolved_ticket_id,
                    'ticket_name': ticket_name,
                    'language': language,
                    'slots': slots,
                    'state_changed': status_changed_to_open,
                    'previous_state': previous_state,
                    'is_first_check': is_first_check,
                    'check_method': 'search_api'
                }
            )
            
            # ✅ Save slots to last_result_summary for Telegram display
            try:
                summary_data = {
                    "updates": {
                        date: [{
                            'id': resolved_ticket_id or ticket_id,
                            'name': ticket_name,
                            'slots': slots
                        }]
                    },
                    "last_updated": str(timezone.now())
                }
                task.last_result_summary = json.dumps(summary_data)
            except Exception as e:
                logger.error(f"Failed to save result summary: {e}")
            
            task.save()
            
            # ✅ SMART NOTIFICATION: Only alert on state CHANGE (closed → open)
            should_alert = status_changed_to_open and not is_first_check
            # For snipe tasks: ALWAYS try to hold when slots are available (not just on state change)
            # This handles the case where the task was created when slots were already open
            is_snipe = task.tier in ('hold', 'snipe')
            should_trigger_hold = is_now_available and (status_changed_to_open or is_first_check or is_snipe)
            
            # ── Pure state machine: notify only on CLOSED → OPEN transition ──
            should_alert = status_changed_to_open and not is_first_check

            if is_first_check and is_now_available:
                logger.info(f"ℹ️ Baseline {date}: already open — no alert")
            elif status_changed_to_open and not is_first_check:
                logger.info(f"🔔 {date}: CLOSED → OPEN — alerting")
            elif not is_now_available:
                logger.debug(f"🔒 {date}: closed")
            else:
                logger.debug(f"ℹ️ {date}: still open — no alert")
            
            # ✅ AUTO-HOLD: Grab the slot immediately when it opens
            if should_trigger_hold and slots and task.tier in ('hold', 'snipe'):
                try:
                    from .tasks_hold import auto_hold_slot
                    preferred = task.preferred_times or []
                    match_strategy = getattr(task, 'match_strategy', 'any') or 'any'

                    slot_dicts = []
                    for s in slots:
                        if isinstance(s, dict):
                            slot_dicts.append(s)
                        else:
                            slot_dicts.append({'time': s, 'id': None})

                    available_times = [str(s.get('time') or '') for s in slot_dicts]
                    if preferred:
                        if match_strategy == 'all' and not all(t in available_times for t in preferred):
                            logger.info(f"⏭️ Skipping auto-hold: not all preferred times available for task #{task.id}")
                        else:
                            slot_dicts = [s for s in slot_dicts if (s.get('time') in preferred)]
                            slot_dicts.sort(key=lambda x: preferred.index(x.get('time')) if x.get('time') in preferred else 9999)

                    if slot_dicts:
                        best = slot_dicts[0]
                        slot_time = best.get('time')
                        slot_id = best.get('id')
                        if slot_id:
                            # Cooldown by task+date+time (not slot_id — Vatican rotates IDs)
                            # 55 min = Vatican hold duration, prevents re-firing while held
                            hold_cooldown_key = f"hold_cooldown:{task.id}:{date}:{slot_time}"
                            if cache.get(hold_cooldown_key):
                                logger.info(f"⏳ SUPPRESSED HOLD: cooldown active for task #{task.id} {date} {slot_time}")
                            else:
                                cache.set(hold_cooldown_key, "sent", timeout=3300)  # 55 min
                                auto_hold_slot.delay(
                                    task_id=task.id,
                                    date=date,
                                    slot_id=slot_id,
                                    slot_time=slot_time,
                                    ticket_id=str(resolved_ticket_id or ticket_id or ''),
                                    ticket_name=ticket_name,
                                    visitors=task.visitors,
                                )
                                logger.info(f"🎯 Auto-hold triggered for {date} {slot_time} (task #{task.id})")
                except Exception as e:
                    logger.error(f"❌ Auto-hold trigger failed: {e}")

            # Send Telegram notification only if should_alert passed all checks
            if should_alert and task.notification_mode != 'silent':
                try:
                    from .notification_utils import format_vatican_notification, send_telegram_signal
                    from .models import TelegramGroup

                    # Get all approved groups for this agency
                    approved_groups = TelegramGroup.objects.filter(
                        agency=task.agency,
                        status='approved',
                        notification_enabled=True
                    )

                    targets = list(approved_groups.values_list('chat_id', flat=True))
                    if not targets and task.agency.telegram_chat_id:
                        targets = [task.agency.telegram_chat_id]

                    if not targets:
                        logger.warning(f"⚠️ No approved groups for agency {task.agency.name}")
                        continue

                    message = format_vatican_notification(
                        date=date,
                        ticket_name=ticket_name,
                        ticket_id=str(resolved_ticket_id or ticket_id),
                        slots=slots,
                        preferred_times=task.preferred_times if hasattr(task, 'preferred_times') else None,
                        language=language,
                        visitors=task.visitors,
                        check_method="search_api"
                    )

                    sent_count = 0
                    for chat_id in targets:
                        # ── Per-group dedup key: only one notification per group per date ──
                        group_sent_key = f"notified:{chat_id}:{date}"
                        if cache.get(group_sent_key):
                            logger.info(f"⏭️ Already notified {chat_id} for {date} — skipping")
                            continue
                        if send_telegram_signal(chat_id, message):
                            cache.set(group_sent_key, True, timeout=86400 * 7)  # until date passes
                            sent_count += 1

                    logger.info(f"✅ TELEGRAM ALERT sent to {sent_count} groups for {task.agency.name}")

                except Exception as e:
                    logger.error(f"❌ Notification failed for task {task.id}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
        
        logger.info(f"✅ Completed check for {date}/{ticket_id} - Checked {len(task_ids)} agencies")
        return f"Checked {ticket_name} - Found {len(slots)} slots - Alerts sent: {sum(1 for t in tasks if status_changed_to_open)}"
        
    except Exception as e:
        logger.error(f"❌ Search API monitor failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return f"Failed: {str(e)}"


@shared_task(name="instant_sniper_scan", queue="vatican")
def instant_sniper_scan():
    """High-frequency orchestrator alias for the sniper engine."""
    return orchestrate_vatican_tasks_search_api()


@shared_task(name="orchestrate_vatican_tasks_search_api", queue="vatican")
def orchestrate_vatican_tasks_search_api():
    """
    🎯 ORCHESTRATOR: Groups tasks by (date, ticket_id, language, visitors) and dispatches checks.
    Uses the new search API monitor for all checks.
    """
    try:
        logger.info("🎯 ORCHESTRATOR: Starting Vatican task orchestration (Search API)")
        
        # Get all active Vatican tasks
        # ✅ Prefetch Telegram groups to avoid N+1 queries
        tasks = MonitorTask.objects.filter(
            site='vatican',
            is_active=True
        ).select_related('agency').prefetch_related('agency__telegram_groups')
        
        if not tasks.exists():
            logger.info("ℹ️ No active Vatican tasks found")
            return "No active tasks"
        
        # ✅ FIX BUG #2: Group by ticket_name instead of stale ticket_id
        # Vatican changes IDs frequently, so grouping by ID causes duplicate checks
        task_groups = {}
        for task in tasks:
            # Iterate through each date in the task's dates list
            dates_list = task.dates if isinstance(task.dates, list) else [task.dates]
            
            for raw_date in dates_list:
                # ✅ Normalize date format + skip past/invalid dates
                from monitors.tasks import normalize_date
                date = normalize_date(raw_date)
                if not date:
                    continue  # skip past or invalid dates silently

                # ✅ FIXED: Group by ticket_name (stable) instead of ticket_id (changes daily)
                key = (date, task.ticket_name, task.language, task.visitors)
                if key not in task_groups:
                    task_groups[key] = {
                        'date': date,
                        'ticket_id': task.ticket_id,  # Keep for reference, but don't use for grouping
                        'ticket_name': task.ticket_name,
                        'language': task.language,
                        'visitors': task.visitors,
                        'task_ids': []
                    }
                task_groups[key]['task_ids'].append(task.id)
        
        logger.info(f"📊 Found {len(tasks)} tasks grouped into {len(task_groups)} unique checks")

        # ✅ SEED: Pre-populate Redis state as 'closed' for any task+date with no entry.
        # This prevents is_first_check=True from silently swallowing the first open event
        # after a worker restart or Redis flush.
        seeded = 0
        for group in task_groups.values():
            for tid in group['task_ids']:
                key = f"ticket_state:{tid}:{group['date']}"
                if cache.get(key) is None:
                    cache.set(key, 'closed', timeout=86400 * 7)
                    seeded += 1
        if seeded:
            logger.info(f"🌱 Seeded {seeded} missing Redis states as 'closed'")

        # Dispatch checks
        dispatched = 0
        for group in task_groups.values():
            try:
                run_search_api_vatican_monitor.delay(
                    date=group['date'],
                    ticket_id=group['ticket_id'],
                    ticket_name=group['ticket_name'],
                    language=group['language'],
                    task_ids=group['task_ids'],
                    visitors=group['visitors']
                )
                dispatched += 1
                logger.info(f"✅ Dispatched: {group['date']} | {group['ticket_name']} | {len(group['task_ids'])} agencies")
            except Exception as e:
                logger.error(f"❌ Failed to dispatch check: {e}")
        
        logger.info(f"🎯 ORCHESTRATOR: Dispatched {dispatched}/{len(task_groups)} checks")
        return f"Dispatched {dispatched} checks for {len(tasks)} tasks"
        
    except Exception as e:
        logger.error(f"❌ Orchestration failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return f"Orchestration failed: {str(e)}"
