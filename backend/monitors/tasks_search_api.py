"""
Simplified Vatican Monitor Tasks using Search API
=================================================
Ultra-fast, reliable monitoring using Vatican's search API directly.
No browser automation needed - 10x faster than previous implementation.
"""

import logging
import json
import os
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
    """Helper to select the best proxy using Smart Reputation Logic"""
    from .models import Proxy
    from django.db import models
    
    now = timezone.now()
    
    # Filter proxies that are active AND not cooling down
    valid_proxies = Proxy.objects.filter(is_active=True).filter(
        models.Q(cooldown_until__isnull=True) | models.Q(cooldown_until__lte=now)
    )
    
    # Vatican prefers Oxylabs but can use any proxy
    proxy_obj = valid_proxies.filter(ip_port__icontains='oxylabs').order_by('?').first()
    if not proxy_obj:
        proxy_obj = valid_proxies.order_by('?').first()

    if not proxy_obj:
        # If ALL proxies are on cooldown, pick the one with the earliest cooldown expiry
        emergency_proxy = Proxy.objects.filter(is_active=True).order_by('cooldown_until').first()
        if emergency_proxy:
            logger.warning(f"⚠️ All proxies on cooldown! Using earliest available: {emergency_proxy}")
            proxy_obj = emergency_proxy
        else:
            return None, None

    # Update Last Used
    proxy_obj.last_used = now
    proxy_obj.save(update_fields=['last_used'])

    user = proxy_obj.username
    if 'oxylabs' in proxy_obj.ip_port.lower():
        import random
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
        cooldown_mins = 0
        if proxy_obj.consecutive_failures >= 10:
            cooldown_mins = 120  # 2 hours
        elif proxy_obj.consecutive_failures >= 5:
            cooldown_mins = 30
        elif proxy_obj.consecutive_failures >= 3:
            cooldown_mins = 5
        
        if cooldown_mins > 0:
            proxy_obj.cooldown_until = timezone.now() + timedelta(minutes=cooldown_mins)
            logger.warning(f"⏰ Proxy {proxy_obj} on cooldown for {cooldown_mins}m")
        
        proxy_obj.save()


@shared_task(name="run_search_api_vatican_monitor", queue="vatican")
def run_search_api_vatican_monitor(date, ticket_id, ticket_name, language, task_ids, visitors=2):
    """
    🚀 ULTRA-FAST: Vatican monitor using search API directly.
    No browser automation - 10x faster and more reliable.
    
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
            return "Error: Monitor not available"
        
        # Get proxy
        proxy_str, proxy_obj = get_proxy_str('vatican')
        if proxy_str:
            logger.info(f"🔌 Using proxy: {proxy_str.split('@')[1] if '@' in proxy_str else proxy_str}")
        
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
            
            # Report proxy success
            if proxy_obj:
                report_proxy_status(proxy_obj, success=success)
            
            if not success:
                logger.error(f"❌ Check failed for {ticket_name}")
                status = 'error'
                slots = []
                resolved_ticket_id = ticket_id
            else:
                status = 'available' if slots else 'sold_out'
                logger.info(f"✅ Check successful: {len(slots)} slots found")
            
        except Exception as e:
            logger.error(f"❌ Monitor exception: {e}")
            if proxy_obj:
                report_proxy_status(proxy_obj, success=False)
            status = 'error'
            slots = []
            resolved_ticket_id = ticket_id
        
        # Process results for all interested agencies
        tasks = MonitorTask.objects.filter(id__in=task_ids)
        
        for task in tasks:
            task.last_checked = timezone.now()
            task.last_status = status
            
            # ✅ STATE CHANGE DETECTION using Redis
            state_key = f"ticket_state:{task.id}:{ticket_id}:{date}"
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
                },
                error_message=None if status != 'error' else 'Check failed'
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
            
            # 🛡️ SPAM GUARD: Cooldown key
            alert_cooldown_key = f"alert_cooldown:{task.id}:{ticket_id}:{date}"
            if should_alert and cache.get(alert_cooldown_key):
                logger.info(f"⏳ SUPPRESSED ALERT: Cooldown active for {ticket_name}")
                should_alert = False
            
            # Log state changes
            if is_first_check and is_now_available:
                logger.info(f"ℹ️ First check: {ticket_name} already available - NOT alerting (initial state)")
            elif status_changed_to_open and not is_first_check:
                if should_alert:
                    logger.info(f"🔔 STATE CHANGE: {ticket_name} went from CLOSED → OPEN! Sending Alert.")
                    cache.set(alert_cooldown_key, "sent", timeout=3600)  # 1 Hour Silence
                else:
                    logger.info(f"🔕 STATE CHANGE detected but Alert Suppressed (Cooldown/Muted)")
            elif not is_now_available:
                logger.info(f"🔒 {ticket_name} is CLOSED ({len(slots)} slots)")
            else:
                logger.info(f"ℹ️ {ticket_name} still AVAILABLE - no alert needed")
            
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
                    
                    if approved_groups.exists():
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
                        
                        # Send to all approved groups
                        sent_count = 0
                        for group in approved_groups:
                            if send_telegram_signal(group.chat_id, message):
                                sent_count += 1
                        
                        logger.info(f"✅ TELEGRAM ALERT sent to {sent_count}/{approved_groups.count()} groups for {task.agency.name}")
                    
                    # Fallback: Also send to legacy telegram_chat_id if set
                    elif task.agency.telegram_chat_id:
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
                        
                        success = send_telegram_signal(task.agency.telegram_chat_id, message)
                        if success:
                            logger.info(f"✅ TELEGRAM ALERT sent to legacy chat_id for {task.agency.name}")
                        else:
                            logger.error(f"❌ TELEGRAM ALERT failed for legacy chat_id {task.agency.name}")
                    else:
                        logger.warning(f"⚠️ No approved Telegram groups found for agency {task.agency.name}")
                        
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


@shared_task(name="orchestrate_vatican_tasks_search_api", queue="vatican")
def orchestrate_vatican_tasks_search_api():
    """
    🎯 ORCHESTRATOR: Groups tasks by (date, ticket_id, language, visitors) and dispatches checks.
    Uses the new search API monitor for all checks.
    """
    try:
        logger.info("🎯 ORCHESTRATOR: Starting Vatican task orchestration (Search API)")
        
        # Get all active Vatican tasks
        tasks = MonitorTask.objects.filter(
            site='vatican',
            is_active=True
        ).select_related('agency')
        
        if not tasks.exists():
            logger.info("ℹ️ No active Vatican tasks found")
            return "No active tasks"
        
        # Group tasks by (date, ticket_id, language, visitors)
        task_groups = {}
        for task in tasks:
            # Iterate through each date in the task's dates list
            dates_list = task.dates if isinstance(task.dates, list) else [task.dates]
            
            for date in dates_list:
                key = (date, task.ticket_id, task.language, task.visitors)
                if key not in task_groups:
                    task_groups[key] = {
                        'date': date,
                        'ticket_id': task.ticket_id,
                        'ticket_name': task.ticket_name,
                        'language': task.language,
                        'visitors': task.visitors,
                        'task_ids': []
                    }
                task_groups[key]['task_ids'].append(task.id)
        
        logger.info(f"📊 Found {len(tasks)} tasks grouped into {len(task_groups)} unique checks")
        
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
