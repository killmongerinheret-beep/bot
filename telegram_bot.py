"""
Telegram Bot for Vatican Monitor Management
Allows users to add/remove/list monitors via Telegram
"""
import os
import sys
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from monitors.models import MonitorTask, Agency

from telegram_bot_calendar import (
    TelegramCalendar, 
    create_quick_dates_keyboard, 
    create_visitors_keyboard
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
SELECTING_ACTION, SELECTING_DATE_METHOD, ENTERING_DATE, ENTERING_VISITORS, SELECTING_TICKET, SELECTING_TIMES, CONFIRMING = range(7)

# Get bot token from environment
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set!")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - show main menu"""
    from asgiref.sync import sync_to_async
    
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Try to find agency by chat_id (use sync_to_async for Django ORM)
    agency = await sync_to_async(Agency.objects.filter(telegram_chat_id=str(chat_id)).first)()
    
    if not agency:
        await update.message.reply_text(
            f"👋 Welcome {user.first_name}!\n\n"
            f"⚠️ Your Telegram chat is not linked to an agency yet.\n\n"
            f"Please contact the admin to link your chat ID: `{chat_id}`\n\n"
            f"Or use the web dashboard to set up your account.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Store agency in context
    context.user_data['agency'] = agency
    
    keyboard = [
        [InlineKeyboardButton("➕ Add Monitor", callback_data='add')],
        [InlineKeyboardButton("📋 List Monitors", callback_data='list')],
        [InlineKeyboardButton("🗑️ Remove Monitor", callback_data='remove')],
        [InlineKeyboardButton("📊 Status", callback_data='status')],
        [InlineKeyboardButton("❓ Help", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Welcome {user.first_name}!\n\n"
        f"🏛️ Vatican Monitor Bot\n"
        f"Agency: {agency.name}\n\n"
        f"What would you like to do?",
        reply_markup=reply_markup
    )
    
    return SELECTING_ACTION


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    action = query.data
    
    if action == 'add':
        # Show date selection options
        keyboard = create_quick_dates_keyboard()
        await query.edit_message_text(
            "➕ Add New Monitor\n\n"
            "📅 Choose a date:\n\n"
            "• Click a quick date below\n"
            "• Or use the calendar\n"
            "• Or type manually",
            reply_markup=keyboard
        )
        return SELECTING_DATE_METHOD
    
    elif action == 'list':
        await list_monitors(query, context)
        return ConversationHandler.END
    
    elif action == 'remove':
        await show_remove_options(query, context)
        return ConversationHandler.END
    
    elif action == 'status':
        await show_status(query, context)
        return ConversationHandler.END
    
    elif action == 'help':
        await show_help(query, context)
        return ConversationHandler.END


async def list_monitors(query, context: ContextTypes.DEFAULT_TYPE):
    """List all active monitors"""
    from asgiref.sync import sync_to_async
    
    agency = context.user_data.get('agency')
    if not agency:
        await query.edit_message_text("❌ Agency not found. Please /start again.")
        return
    
    tasks = await sync_to_async(list)(
        MonitorTask.objects.filter(
            agency=agency,
            site='vatican',
            is_active=True
        ).order_by('dates')
    )
    
    if not tasks:
        await query.edit_message_text(
            "📋 No active monitors found.\n\n"
            "Use /start to add your first monitor!"
        )
        return
    
    message = f"📋 Your Active Monitors ({len(tasks)})\n\n"
    
    for task in tasks:
        date = task.dates[0] if task.dates else 'N/A'
        status_emoji = "✅" if task.last_status == 'available' else "❌" if task.last_status == 'sold_out' else "⏳"
        
        # Get available slots from last_result_summary if available
        slots_info = ""
        if task.last_result_summary:
            try:
                import json
                summary = json.loads(task.last_result_summary)
                if 'updates' in summary:
                    for date_key, items in summary['updates'].items():
                        for item in items:
                            if item.get('slots'):
                                slots = item['slots'][:5]  # Show first 5 slots
                                slots_str = ', '.join(slots)
                                if len(item['slots']) > 5:
                                    slots_str += f" (+{len(item['slots'])-5} more)"
                                slots_info = f"\n   Slots: {slots_str}"
                                break
            except:
                pass
        
        message += (
            f"{status_emoji} Task #{task.id}\n"
            f"   Date: {date}\n"
            f"   Visitors: {task.visitors}\n"
            f"   Ticket: {task.ticket_label or 'Standard'}\n"
            f"   Status: {task.last_status}{slots_info}\n"
            f"   Last Check: {task.last_checked.strftime('%H:%M') if task.last_checked else 'Never'}\n\n"
        )
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)


async def show_remove_options(query, context: ContextTypes.DEFAULT_TYPE):
    """Show monitors that can be removed"""
    from asgiref.sync import sync_to_async
    
    agency = context.user_data.get('agency')
    if not agency:
        await query.edit_message_text("❌ Agency not found. Please /start again.")
        return
    
    tasks = await sync_to_async(list)(
        MonitorTask.objects.filter(
            agency=agency,
            site='vatican',
            is_active=True
        ).order_by('dates')[:10]
    )
    
    if not tasks:
        await query.edit_message_text(
            "📋 No active monitors to remove.\n\n"
            "Use /start to go back."
        )
        return
    
    keyboard = []
    for task in tasks:
        date = task.dates[0] if task.dates else 'N/A'
        keyboard.append([
            InlineKeyboardButton(
                f"🗑️ {date} ({task.visitors}v)",
                callback_data=f'remove_{task.id}'
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data='back')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🗑️ Select a monitor to remove:",
        reply_markup=reply_markup
    )


async def remove_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove a specific monitor"""
    from asgiref.sync import sync_to_async
    
    query = update.callback_query
    await query.answer()
    
    task_id = int(query.data.split('_')[1])
    
    try:
        task = await sync_to_async(MonitorTask.objects.get)(id=task_id)
        date = task.dates[0] if task.dates else 'N/A'
        visitors = task.visitors
        await sync_to_async(task.delete)()
        
        await query.edit_message_text(
            f"✅ Monitor removed successfully!\n\n"
            f"Date: {date}\n"
            f"Visitors: {visitors}\n\n"
            f"Use /start to manage more monitors."
        )
    except MonitorTask.DoesNotExist:
        await query.edit_message_text(
            "❌ Monitor not found. It may have been already removed.\n\n"
            "Use /start to go back."
        )


async def show_status(query, context: ContextTypes.DEFAULT_TYPE):
    """Show system status"""
    from asgiref.sync import sync_to_async
    
    agency = context.user_data.get('agency')
    if not agency:
        await query.edit_message_text("❌ Agency not found. Please /start again.")
        return
    
    tasks = await sync_to_async(list)(
        MonitorTask.objects.filter(agency=agency, site='vatican', is_active=True)
    )
    total_tasks = len(tasks)
    available_count = len([t for t in tasks if t.last_status == 'available'])
    sold_out_count = len([t for t in tasks if t.last_status == 'sold_out'])
    unknown_count = len([t for t in tasks if t.last_status == 'unknown'])
    
    message = (
        f"📊 System Status\n\n"
        f"Agency: {agency.name}\n"
        f"Plan: {agency.plan.upper()}\n\n"
        f"📋 Monitors: {total_tasks}\n"
        f"✅ Available: {available_count}\n"
        f"❌ Sold Out: {sold_out_count}\n"
        f"⏳ Checking: {unknown_count}\n\n"
        f"🔄 Check Interval: 60 seconds\n"
        f"📡 Proxies: 14 active\n"
        f"⚡ Status: Running 24/7"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)


async def show_help(query, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    message = (
        "❓ Help - Vatican Monitor Bot\n\n"
        "📋 Commands:\n"
        "/start - Main menu\n"
        "/add - Add new monitor\n"
        "/list - List all monitors\n"
        "/status - Show system status\n"
        "/cancel - Cancel current operation\n\n"
        "➕ Adding Monitors:\n"
        "1. Click 'Add Monitor'\n"
        "2. Select date (calendar or quick pick)\n"
        "3. Select number of visitors\n"
        "4. Confirm\n\n"
        "🔔 Notifications:\n"
        "You'll receive alerts when tickets become available!\n\n"
        "📊 Dashboard:\n"
        "Visit the web dashboard for detailed view."
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)


async def handle_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle date selection from calendar or quick picks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Quick date selection
    if data.startswith("quick_day_"):
        date_str = data.replace("quick_day_", "")
        context.user_data['date'] = date_str
        
        # Show visitors selection
        keyboard = create_visitors_keyboard()
        await query.edit_message_text(
            f"✅ Date: {date_str}\n\n"
            f"👥 How many visitors?",
            reply_markup=keyboard
        )
        return ENTERING_VISITORS
    
    # Show calendar
    elif data == "quick_calendar":
        cal = TelegramCalendar()
        keyboard = cal.create_calendar()
        await query.edit_message_text(
            "📅 Select a date:\n\n"
            "• Tap a day to select\n"
            "• Use ◀️ ▶️ to change month",
            reply_markup=keyboard
        )
        return SELECTING_DATE_METHOD
    
    # Type manually
    elif data == "quick_type":
        await query.edit_message_text(
            "📝 Type the date\n\n"
            "Format: YYYY-MM-DD\n"
            "Example: 2026-04-15\n\n"
            "Or send /cancel to go back."
        )
        return ENTERING_DATE
    
    # Calendar navigation
    elif data.startswith("cal_"):
        cal = TelegramCalendar()
        action, result = cal.process_selection(data)
        
        if action == "ignore":
            return SELECTING_DATE_METHOD
        
        elif action == "cancel":
            keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='back')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Cancelled. Use /start to go back to menu.",
                reply_markup=reply_markup
            )
            return ConversationHandler.END
        
        elif action == "change":
            # Update calendar
            await query.edit_message_text(
                "📅 Select a date:\n\n"
                "• Tap a day to select\n"
                "• Use ◀️ ▶️ to change month",
                reply_markup=result
            )
            return SELECTING_DATE_METHOD
        
        elif action == "selected":
            # Date selected
            context.user_data['date'] = result
            
            # Show visitors selection
            keyboard = create_visitors_keyboard()
            await query.edit_message_text(
                f"✅ Date: {result}\n\n"
                f"👥 How many visitors?",
                reply_markup=keyboard
            )
            return ENTERING_VISITORS
    
    # Cancel
    elif data == "quick_cancel":
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "❌ Cancelled. Use /start to go back to menu.",
            reply_markup=keyboard
        )
        return ConversationHandler.END
    
    return SELECTING_DATE_METHOD


async def handle_visitors_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle visitors selection from keyboard"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "visitors_cancel":
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "❌ Cancelled. Use /start to go back to menu.",
            reply_markup=keyboard
        )
        return ConversationHandler.END
    
    if data.startswith("visitors_"):
        visitors = int(data.replace("visitors_", ""))
        context.user_data['visitors'] = visitors
        
        # Show ticket selection
        keyboard = [
            [InlineKeyboardButton("🎫 Standard Entry", callback_data='ticket_standard')],
            [InlineKeyboardButton("👥 Guided Tour", callback_data='ticket_guided')],
            [InlineKeyboardButton("❌ Cancel", callback_data='visitors_cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎫 Select Ticket Type\n\n"
            f"Date: {context.user_data.get('date')}\n"
            f"Visitors: {visitors}\n\n"
            f"Choose ticket type:",
            reply_markup=reply_markup
        )
        return SELECTING_TICKET
    
    return ENTERING_VISITORS


async def handle_ticket_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ticket type selection"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "visitors_cancel":
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "❌ Cancelled. Use /start to go back to menu.",
            reply_markup=reply_markup
        )
        return ConversationHandler.END
    
    if data == "ticket_standard":
        context.user_data['ticket_type'] = 0
        context.user_data['ticket_name'] = 'Musei Vaticani - Biglietti d\'ingresso'
        context.user_data['ticket_label'] = 'Standard Entry'
        context.user_data['language'] = None
    elif data == "ticket_guided":
        context.user_data['ticket_type'] = 1
        context.user_data['ticket_name'] = 'Musei Vaticani - Visite Guidate'
        context.user_data['ticket_label'] = 'Guided Tour'
        context.user_data['language'] = 'ENG'  # Default to English
    
    # Show time selection with specific time slots
    # Generate time slots from 08:00 to 17:30 with 30-minute intervals
    time_slots = []
    for hour in range(8, 18):
        for minute in ['00', '30']:
            time = f"{hour:02d}:{minute}"
            if time <= "17:30":
                time_slots.append(time)
    
    # Create keyboard with 3 buttons per row
    keyboard = []
    for i in range(0, len(time_slots), 3):
        row = []
        for time in time_slots[i:i+3]:
            row.append(InlineKeyboardButton(time, callback_data=f'time_{time}'))
        keyboard.append(row)
    
    # Add custom times and cancel buttons
    keyboard.append([InlineKeyboardButton("✏️ Custom Times", callback_data='time_custom')])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data='visitors_cancel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"⏰ Select Preferred Time\n\n"
        f"Date: {context.user_data.get('date')}\n"
        f"Visitors: {context.user_data.get('visitors')}\n"
        f"Ticket: {context.user_data.get('ticket_label')}\n\n"
        f"Choose your preferred time slot:\n"
        f"(Select one time, or use Custom for multiple)",
        reply_markup=reply_markup
    )
    return SELECTING_TIMES


async def handle_time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle time selection"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "visitors_cancel":
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "❌ Cancelled. Use /start to go back to menu.",
            reply_markup=reply_markup
        )
        return ConversationHandler.END
    
    # Handle custom times
    if data == "time_custom":
        await query.edit_message_text(
            f"✏️ Custom Times\n\n"
            f"Send your preferred times separated by commas.\n"
            f"Example: 09:00, 10:30, 14:00\n\n"
            f"Or send /skip to use all times."
        )
        return SELECTING_TIMES
    
    # Handle specific time selection (format: time_HH:MM)
    if data.startswith("time_"):
        selected_time = data.replace("time_", "")
        context.user_data['preferred_times'] = [selected_time]
        time_label = selected_time
    else:
        # Fallback to all times
        context.user_data['preferred_times'] = ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00']
        time_label = "All Times"
    
    # Show confirmation
    date = context.user_data.get('date')
    visitors = context.user_data.get('visitors')
    ticket_label = context.user_data.get('ticket_label')
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data='confirm_add')],
        [InlineKeyboardButton("❌ Cancel", callback_data='cancel_add')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📋 Confirm New Monitor\n\n"
        f"Date: {date}\n"
        f"Visitors: {visitors}\n"
        f"Ticket: {ticket_label}\n"
        f"Preferred Time: {time_label}\n"
        f"Check Interval: 60 seconds\n\n"
        f"Add this monitor?",
        reply_markup=reply_markup
    )
    return CONFIRMING


async def receive_custom_times(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive custom time preferences"""
    times_str = update.message.text.strip()
    
    # Parse times
    times = [t.strip() for t in times_str.split(',')]
    
    # Validate times (basic check)
    valid_times = []
    for t in times:
        if ':' in t and len(t) >= 4:
            valid_times.append(t)
    
    if not valid_times:
        await update.message.reply_text(
            "❌ Invalid time format.\n\n"
            "Please send times like: 09:00, 10:30, 14:00\n"
            "Or send /skip to use all times."
        )
        return SELECTING_TIMES
    
    context.user_data['preferred_times'] = valid_times
    
    # Show confirmation
    date = context.user_data.get('date')
    visitors = context.user_data.get('visitors')
    ticket_label = context.user_data.get('ticket_label')
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data='confirm_add')],
        [InlineKeyboardButton("❌ Cancel", callback_data='cancel_add')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📋 Confirm New Monitor\n\n"
        f"Date: {date}\n"
        f"Visitors: {visitors}\n"
        f"Ticket: {ticket_label}\n"
        f"Preferred Times: {', '.join(valid_times)}\n"
        f"Check Interval: 60 seconds\n\n"
        f"Add this monitor?",
        reply_markup=reply_markup
    )
    return CONFIRMING


async def show_help(query, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    message = (
        "❓ Help - Vatican Monitor Bot\n\n"
        "📋 Commands:\n"
        "/start - Main menu\n"
        "/add - Add new monitor\n"
        "/list - List all monitors\n"
        "/status - Show system status\n"
        "/cancel - Cancel current operation\n\n"
        "➕ Adding Monitors:\n"
        "1. Click 'Add Monitor'\n"
        "2. Enter date (YYYY-MM-DD)\n"
        "3. Enter number of visitors\n"
        "4. Confirm\n\n"
        "🔔 Notifications:\n"
        "You'll receive alerts when tickets become available!\n\n"
        "📊 Dashboard:\n"
        "Visit the web dashboard for detailed view."
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)


async def receive_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and validate date"""
    date_str = update.message.text.strip()
    
    # Validate date format
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Check if date is in the future
        if date_obj.date() < datetime.now().date():
            await update.message.reply_text(
                "❌ Date must be in the future.\n\n"
                "Please send a valid date (YYYY-MM-DD) or /cancel"
            )
            return ENTERING_DATE
        
        # Store date in context
        context.user_data['date'] = date_str
        
        await update.message.reply_text(
            f"✅ Date: {date_str}\n\n"
            f"How many visitors?\n"
            f"Enter a number (1-10):"
        )
        return ENTERING_VISITORS
        
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid date format.\n\n"
            "Please use YYYY-MM-DD format.\n"
            "Example: 2026-04-15\n\n"
            "Or send /cancel to go back."
        )
        return ENTERING_DATE


async def receive_visitors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and validate visitor count"""
    try:
        visitors = int(update.message.text.strip())
        
        if visitors < 1 or visitors > 10:
            await update.message.reply_text(
                "❌ Visitors must be between 1 and 10.\n\n"
                "Please enter a valid number or /cancel"
            )
            return ENTERING_VISITORS
        
        # Store visitors in context
        context.user_data['visitors'] = visitors
        
        # Show confirmation
        date = context.user_data.get('date')
        
        keyboard = [
            [InlineKeyboardButton("✅ Confirm", callback_data='confirm_add')],
            [InlineKeyboardButton("❌ Cancel", callback_data='cancel_add')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📋 Confirm New Monitor\n\n"
            f"Date: {date}\n"
            f"Visitors: {visitors}\n"
            f"Ticket: Standard Entry\n"
            f"Check Interval: 60 seconds\n\n"
            f"Add this monitor?",
            reply_markup=reply_markup
        )
        return CONFIRMING
        
    except ValueError:
        await update.message.reply_text(
            "❌ Please enter a valid number (1-10) or /cancel"
        )
        return ENTERING_VISITORS


async def confirm_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and create the monitor"""
    from asgiref.sync import sync_to_async
    
    query = update.callback_query
    await query.answer()
    
    if query.data == 'cancel_add':
        await query.edit_message_text(
            "❌ Cancelled. Use /start to go back to menu."
        )
        return ConversationHandler.END
    
    # Get data from context
    agency = context.user_data.get('agency')
    date = context.user_data.get('date')
    visitors = context.user_data.get('visitors')
    ticket_type = context.user_data.get('ticket_type', 0)
    ticket_name = context.user_data.get('ticket_name', 'Musei Vaticani - Biglietti d\'ingresso')
    ticket_label = context.user_data.get('ticket_label', 'Standard Entry')
    language = context.user_data.get('language', None)
    preferred_times = context.user_data.get('preferred_times', ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00'])
    
    if not all([agency, date, visitors]):
        await query.edit_message_text(
            "❌ Error: Missing data. Please /start again."
        )
        return ConversationHandler.END
    
    # Check if monitor already exists
    existing = await sync_to_async(
        MonitorTask.objects.filter(
            agency=agency,
            site='vatican',
            dates__contains=[date],
            visitors=visitors,
            ticket_type=ticket_type,
            is_active=True
        ).first
    )()
    
    if existing:
        await query.edit_message_text(
            f"⚠️ Monitor already exists!\n\n"
            f"Task #{existing.id}\n"
            f"Date: {date}\n"
            f"Visitors: {visitors}\n"
            f"Ticket: {ticket_label}\n\n"
            f"Use /start to manage monitors."
        )
        return ConversationHandler.END
    
    # ✅ NEW: Resolve fresh ticket_id before creating task
    await query.edit_message_text(
        f"⏳ Creating monitor...\n\n"
        f"Resolving fresh ticket ID from Vatican website..."
    )
    
    ticket_id = None
    try:
        # Import HydraBot to resolve dynamic IDs
        import asyncio
        from worker_vatican.hydra_monitor import HydraBot
        
        async def resolve_ticket_id():
            bot = HydraBot(use_proxies=True)
            async with bot.get_browser() as browser:
                page = await browser.new_page()
                
                # Convert date format: YYYY-MM-DD -> DD/MM/YYYY
                if '-' in date:
                    year, month, day = date.split('-')
                    date_formatted = f"{day}/{month}/{year}"
                else:
                    date_formatted = date
                
                # Resolve all IDs for this date
                resolved_ids = await bot.resolve_all_dynamic_ids(
                    page,
                    ticket_type=ticket_type,
                    target_date=date_formatted,
                    visitors=visitors
                )
                
                await page.close()
                
                # Match ticket by name (same logic as in tasks.py)
                for item in resolved_ids:
                    r_name = item.get('name', '').lower()
                    t_name = ticket_name.lower()
                    
                    # Exact match
                    if t_name in r_name or r_name in t_name:
                        if ticket_type == 0 and "lunch" in r_name:
                            continue
                        return item['id']
                
                # Keyword match fallback
                keywords = []
                t_lower = ticket_name.lower()
                
                if 'musei' in t_lower:
                    keywords.extend(['musei', 'vaticani', 'aree', 'museali'])  # ✅ FIXED: Added 'aree', 'museali'
                elif 'palazzo' in t_lower:
                    keywords.extend(['palazzo', 'papale'])
                elif 'specola' in t_lower:
                    keywords.extend(['specola', 'vaticana'])
                
                if 'biglietti' in t_lower or 'admission' in t_lower or 'ingresso' in t_lower:
                    keywords.extend(['biglietti', 'ingresso'])
                if 'visita' in t_lower or 'guided' in t_lower or 'tour' in t_lower:
                    keywords.extend(['visita', 'guidata'])
                
                best_match = None
                best_score = 0
                
                for item in resolved_ids:
                    r_name = item.get('name', '').lower()
                    score = sum(1 for kw in keywords if kw in r_name)
                    
                    # CRITICAL: Venue exclusions
                    if 'musei' in t_lower and 'palazzo' in r_name:
                        continue
                    if 'palazzo' in t_lower and 'musei' in r_name:
                        continue
                    
                    if ticket_type == 0 and any(x in r_name for x in ['lunch', 'pranzo', 'pellegrinaggi']):
                        continue
                    
                    if score > best_score:
                        best_score = score
                        best_match = item['id']
                
                if best_match and best_score >= 2:
                    return best_match
                
                # Final fallback: first standard ticket
                if ticket_type == 0:
                    for item in resolved_ids:
                        r_name = item.get('name', '').lower()
                        # ✅ IMPROVED: Also check for "aree museali" and "ingresso" patterns
                        if any(x in r_name for x in ['biglietti', 'ingresso', 'aree museali', 'museali']):
                            # ✅ CRITICAL: Exclude wrong venues
                            if not any(x in r_name for x in ['lunch', 'pranzo', 'pellegrinaggi', 'gruppi', 'palazzo', 'specola']):
                                return item['id']
                
                return None
        
        # Run async resolution
        ticket_id = await resolve_ticket_id()
        
        if ticket_id:
            logger.info(f"✅ Resolved fresh ticket_id: {ticket_id} for {ticket_name}")
        else:
            logger.warning(f"⚠️ Could not resolve ticket_id for {ticket_name}, creating task without ID")
        
    except Exception as e:
        logger.error(f"❌ Error resolving ticket_id: {e}")
        # Continue without ticket_id - task will use legacy path
    
    # Create new monitor
    try:
        task = await sync_to_async(MonitorTask.objects.create)(
            agency=agency,
            site='vatican',
            area_name='Musei Vaticani',
            dates=[date],
            preferred_times=preferred_times,
            visitors=visitors,
            ticket_type=ticket_type,
            ticket_label=ticket_label,
            ticket_id=ticket_id,  # ✅ Now set with fresh ID
            ticket_name=ticket_name,
            language=language,
            check_interval=60,
            tier='monitor',
            match_strategy='any',
            notification_mode='available_only',
            is_active=True
        )
        
        await query.edit_message_text(
            f"✅ Monitor created successfully!\n\n"
            f"Task #{task.id}\n"
            f"Date: {date}\n"
            f"Visitors: {visitors}\n"
            f"Ticket: {ticket_label}\n"
            f"Ticket ID: {ticket_id or 'Will resolve on first check'}\n"
            f"Preferred Times: {', '.join(preferred_times[:3])}{'...' if len(preferred_times) > 3 else ''}\n\n"
            f"🔔 You'll receive alerts when tickets become available!\n\n"
            f"The bot will start checking within 60 seconds.\n\n"
            f"Use /start to manage more monitors."
        )
        
    except Exception as e:
        logger.error(f"Error creating monitor: {e}")
        await query.edit_message_text(
            f"❌ Error creating monitor: {str(e)}\n\n"
            f"Please try again or contact support."
        )
    
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation"""
    await update.message.reply_text(
        "❌ Cancelled. Use /start to go back to menu."
    )
    return ConversationHandler.END


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to main menu"""
    query = update.callback_query
    await query.answer()
    
    agency = context.user_data.get('agency')
    
    keyboard = [
        [InlineKeyboardButton("➕ Add Monitor", callback_data='add')],
        [InlineKeyboardButton("📋 List Monitors", callback_data='list')],
        [InlineKeyboardButton("🗑️ Remove Monitor", callback_data='remove')],
        [InlineKeyboardButton("📊 Status", callback_data='status')],
        [InlineKeyboardButton("❓ Help", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🏛️ Vatican Monitor Bot\n"
        f"Agency: {agency.name if agency else 'Unknown'}\n\n"
        f"What would you like to do?",
        reply_markup=reply_markup
    )
    
    return SELECTING_ACTION


def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation handler for adding monitors
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_ACTION: [
                CallbackQueryHandler(button_handler),
                CallbackQueryHandler(back_to_menu, pattern='^back$'),
                CallbackQueryHandler(remove_monitor, pattern='^remove_\\d+$')
            ],
            SELECTING_DATE_METHOD: [
                CallbackQueryHandler(back_to_menu, pattern='^back$'),
                CallbackQueryHandler(handle_date_selection),
                CommandHandler('cancel', cancel)
            ],
            ENTERING_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_date),
                CommandHandler('cancel', cancel)
            ],
            ENTERING_VISITORS: [
                CallbackQueryHandler(back_to_menu, pattern='^back$'),
                CallbackQueryHandler(handle_visitors_selection),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_visitors),
                CommandHandler('cancel', cancel)
            ],
            SELECTING_TICKET: [
                CallbackQueryHandler(back_to_menu, pattern='^back$'),
                CallbackQueryHandler(handle_ticket_selection),
                CommandHandler('cancel', cancel)
            ],
            SELECTING_TIMES: [
                CallbackQueryHandler(back_to_menu, pattern='^back$'),
                CallbackQueryHandler(handle_time_selection),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_custom_times),
                CommandHandler('skip', handle_time_selection),
                CommandHandler('cancel', cancel)
            ],
            CONFIRMING: [
                CallbackQueryHandler(back_to_menu, pattern='^back$'),
                CallbackQueryHandler(confirm_add)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('add', start))
    application.add_handler(CommandHandler('list', start))
    application.add_handler(CommandHandler('status', start))
    
    # Start the bot
    logger.info("🤖 Telegram bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
