#!/usr/bin/env python
"""Patch tasks.py to use enhanced notifications"""

import re

# Read the current tasks.py
with open('/app/backend/monitors/tasks.py', 'r') as f:
    content = f.read()

# Add import for notification_utils at the top (after existing imports)
import_section = """from .models import MonitorTask, CheckResult, Agency, Proxy, SiteCredential

# 1. Clean Imports"""

new_import_section = """from .models import MonitorTask, CheckResult, Agency, Proxy, SiteCredential

# Enhanced Notification Utilities
try:
    from .notification_utils import format_vatican_notification, send_telegram_signal as send_telegram_signal_enhanced
    HAS_ENHANCED_NOTIFICATIONS = True
except ImportError:
    HAS_ENHANCED_NOTIFICATIONS = False

# 1. Clean Imports"""

content = content.replace(import_section, new_import_section)

# Replace the God-Tier notification section
old_god_tier_notification = '''            # ??? Send Telegram notification if should_alert is True
            if should_alert and task.notification_mode != 'silent':
                try:
                    chat_id = task.agency.telegram_chat_id
                    if chat_id:
                        lang_info = f" ({language})" if language else ""
                        message = f"???? *TICKETS JUST OPENED!*\\n\\n"
                        message += f"???? Date: {date}\\n"
                        message += f"???? Ticket: {ticket_name}{lang_info}\\n"
                        message += f"??? Check Method: Ultra-Fast Headless\\n\\n"
                        message += f"??? Available Times ({len(unique_slots)} slots):\\n"
                        
                        for slot in unique_slots[:10]:
                            time_str = slot.get('time', slot) if isinstance(slot, dict) else slot
                            message += f"  ??? {time_str}\\n"
                        
                        if len(unique_slots) > 10:
                            message += f"  ... and {len(unique_slots) - 10} more\\n"
                        
                        message += f"\\n???? Book now!"
                        
                        send_telegram_signal(chat_id, message)
                        logger.info(f"??? TELEGRAM ALERT sent to {task.agency.name}")
                    else:
                        logger.warning(f"?????? No telegram_chat_id for agency {task.agency.name}")
                except Exception as e:
                    logger.error(f"??? Notification failed: {e}")
                    import traceback
                    logger.error(traceback.format_exc())'''

new_god_tier_notification = '''            # ??? Send Telegram notification if should_alert is True
            if should_alert and task.notification_mode != 'silent':
                try:
                    chat_id = task.agency.telegram_chat_id
                    if chat_id:
                        # Use enhanced notification if available
                        if HAS_ENHANCED_NOTIFICATIONS:
                            message = format_vatican_notification(
                                date=date,
                                ticket_name=ticket_name,
                                ticket_id=ticket_id,
                                slots=unique_slots,
                                preferred_times=task.preferred_times,
                                language=language,
                                visitors=task.visitors,
                                check_method="headless" if not use_browser_fallback else "hybrid"
                            )
                            send_telegram_signal_enhanced(chat_id, message)
                        else:
                            # Fallback to simple notification
                            lang_info = f" ({language})" if language else ""
                            message = f"???? *TICKETS JUST OPENED!*\\n\\n"
                            message += f"???? Date: {date}\\n"
                            message += f"???? Ticket: {ticket_name}{lang_info}\\n\\n"
                            message += f"??? Available Times ({len(unique_slots)} slots):\\n"
                            
                            for slot in unique_slots[:10]:
                                time_str = slot.get('time', slot) if isinstance(slot, dict) else slot
                                message += f"  ??? {time_str}\\n"
                            
                            if len(unique_slots) > 10:
                                message += f"  ... and {len(unique_slots) - 10} more\\n"
                            
                            message += f"\\n???? Book now!"
                            send_telegram_signal(chat_id, message)
                        
                        logger.info(f"??? TELEGRAM ALERT sent to {task.agency.name}")
                    else:
                        logger.warning(f"?????? No telegram_chat_id for agency {task.agency.name}")
                except Exception as e:
                    logger.error(f"??? Notification failed: {e}")
                    import traceback
                    logger.error(traceback.format_exc())'''

content = content.replace(old_god_tier_notification, new_god_tier_notification)

# Write back
with open('/app/backend/monitors/tasks.py', 'w') as f:
    f.write(content)

print("✅ tasks.py patched successfully!")
