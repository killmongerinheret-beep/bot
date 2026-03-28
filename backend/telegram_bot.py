"""
Telegram Bot for Vatican Monitor Management
State managed via context.user_data['step'] - no ConversationHandler state confusion.
"""
import os
import sys
import logging
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember, ChatMemberUpdated
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, ChatMemberHandler, filters
)

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from monitors.models import MonitorTask, Agency, TelegramGroup, User

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set!")


# ── Keyboards ────────────────────────────────────────────────────────────────

def kb_main():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Monitor", callback_data='add')],
        [InlineKeyboardButton("📋 List Monitors", callback_data='list')],
        [InlineKeyboardButton("🗑️ Remove Monitor", callback_data='remove')],
        [InlineKeyboardButton("📊 Status", callback_data='status')],
    ])

def kb_calendar(year: int, month: int):
    """Build a month-view calendar keyboard."""
    import calendar
    today = datetime.now().date()

    # Header: month name + year
    month_name = datetime(year, month, 1).strftime('%B %Y')
    rows = [
        # Navigation row
        [
            InlineKeyboardButton("◀️", callback_data=f'cal:prev:{year}:{month}'),
            InlineKeyboardButton(f"📅 {month_name}", callback_data='cal:ignore'),
            InlineKeyboardButton("▶️", callback_data=f'cal:next:{year}:{month}'),
        ],
        # Day-of-week header
        [InlineKeyboardButton(d, callback_data='cal:ignore') for d in ['Mo','Tu','We','Th','Fr','Sa','Su']],
    ]

    # Fill calendar grid
    cal = calendar.monthcalendar(year, month)
    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data='cal:ignore'))
            else:
                d = datetime(year, month, day).date()
                if d <= today:
                    # Past/today - not selectable
                    row.append(InlineKeyboardButton(f"·{day}", callback_data='cal:ignore'))
                else:
                    date_str = d.strftime('%Y-%m-%d')
                    row.append(InlineKeyboardButton(str(day), callback_data=f'date:{date_str}'))
        rows.append(row)

    rows.append([InlineKeyboardButton("❌ Cancel", callback_data='cancel')])
    return InlineKeyboardMarkup(rows)

def kb_visitors():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(str(i), callback_data=f'vis:{i}') for i in range(1, 6)],
        [InlineKeyboardButton(str(i), callback_data=f'vis:{i}') for i in range(6, 11)],
        [InlineKeyboardButton("❌ Cancel", callback_data='cancel')],
    ])

def kb_ticket():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎫 Standard Entry", callback_data='ticket:standard')],
        [InlineKeyboardButton("👥 Guided Tour",    callback_data='ticket:guided')],
        [InlineKeyboardButton("❌ Cancel",          callback_data='cancel')],
    ])

def kb_tier(plan='free'):
    """Show only tiers available for the agency's plan."""
    rows = [[InlineKeyboardButton("🔔 Notify Only", callback_data='tier:notify')]]
    if plan in ('pro', 'agency'):
        rows.append([InlineKeyboardButton("🔒 Notify + Hold", callback_data='tier:hold')])
    else:
        rows.append([InlineKeyboardButton("🔒 Hold — Pro plan required 🔐", callback_data='tier:locked_hold')])
    if plan == 'agency':
        rows.append([InlineKeyboardButton("🤖 Notify + Hold + Snipe", callback_data='tier:snipe')])
    else:
        rows.append([InlineKeyboardButton("🤖 Snipe — Agency plan required 🔐", callback_data='tier:locked_snipe')])
    rows.append([InlineKeyboardButton("❌ Cancel", callback_data='cancel')])
    return InlineKeyboardMarkup(rows)

def kb_language():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇬🇧 English",  callback_data='lang:ENG')],
        [InlineKeyboardButton("🇮🇹 Italiano", callback_data='lang:ITA')],
        [InlineKeyboardButton("🇫🇷 Français", callback_data='lang:FRA')],
        [InlineKeyboardButton("🇩🇪 Deutsch",  callback_data='lang:DEU')],
        [InlineKeyboardButton("🇪🇸 Español",  callback_data='lang:SPA')],
        [InlineKeyboardButton("❌ Cancel",     callback_data='cancel')],
    ])

def kb_times():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌅 Morning  09:00–12:00", callback_data='time:morning')],
        [InlineKeyboardButton("🌞 Afternoon 12:00–15:00", callback_data='time:afternoon')],
        [InlineKeyboardButton("🌆 Late     15:00–17:00", callback_data='time:late')],
        [InlineKeyboardButton("⏰ All Times",             callback_data='time:all')],
        [InlineKeyboardButton("❌ Cancel",                callback_data='cancel')],
    ])

def kb_confirm():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm", callback_data='confirm')],
        [InlineKeyboardButton("❌ Cancel",  callback_data='cancel')],
    ])

def kb_back():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data='menu')]])


# ── Helpers ──────────────────────────────────────────────────────────────────

async def get_agency(chat_id):
    from asgiref.sync import sync_to_async

    def _lookup():
        group = TelegramGroup.objects.filter(
            chat_id=str(chat_id),
            status='approved',
            agency__isnull=False
        ).select_related('agency').first()
        if group:
            return group.agency
        return Agency.objects.filter(telegram_chat_id=str(chat_id)).first()

    return await sync_to_async(_lookup)()

def summary(ud):
    lang_names = {'ENG':'🇬🇧 English','ITA':'🇮🇹 Italiano','FRA':'🇫🇷 Français','DEU':'🇩🇪 Deutsch','SPA':'🇪🇸 Español'}
    lines = [
        f"📅 Date: {ud.get('date','—')}",
        f"👥 Visitors: {ud.get('visitors','—')}",
        f"🎫 Ticket: {ud.get('ticket_label','—')}",
    ]
    if ud.get('language'):
        lines.append(f"🌍 Language: {lang_names.get(ud['language'], ud['language'])}")
    lines.append(f"⏰ Times: {ud.get('times_label','All Times')}")
    return '\n'.join(lines)


# ── /start ────────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    agency = await get_agency(chat_id)
    if not agency:
        await update.message.reply_text(
            f"⚠️ This chat is not linked to an agency.\n\nChat ID: `{chat_id}`\nContact admin to link it.",
            parse_mode='Markdown'
        )
        return
    context.user_data.clear()
    context.user_data['agency_id'] = agency.id
    context.user_data['agency_name'] = agency.name
    context.user_data['agency_plan'] = agency.plan
    await update.message.reply_text(
        f"🏛️ Vatican Monitor Bot\nAgency: {agency.name}\n\nWhat would you like to do?",
        reply_markup=kb_main()
    )


# ── Master callback handler ───────────────────────────────────────────────────

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from asgiref.sync import sync_to_async
    query = update.callback_query
    await query.answer()
    data = query.data
    ud = context.user_data

    # ── Admin: approve/reject from notification buttons ──
    if data.startswith("admin_approve:") or data.startswith("admin_reject:"):
        admin_ids = [a.strip() for a in os.getenv('ADMIN_TELEGRAM_IDS', '').split(',') if a.strip()]
        if str(update.effective_user.id) not in admin_ids:
            await query.edit_message_text("⛔ Not authorized.")
            return

        action, group_chat_id = data.split(":", 1)

        if action == "admin_reject":
            @sync_to_async
            def do_reject():
                g = TelegramGroup.objects.filter(chat_id=group_chat_id).first()
                if g:
                    g.status = 'rejected'
                    g.save()
                return g
            g = await do_reject()
            await query.edit_message_text(f"❌ Rejected: {g.chat_title if g else group_chat_id}")
            return

        # Approve → show agency list + create new option
        agencies = await sync_to_async(list)(Agency.objects.filter(is_active=True).exclude(plan='system'))
        kb = [[InlineKeyboardButton(f"🏢 {a.name} ({a.plan})", callback_data=f"admin_link:{group_chat_id}:{a.id}")] for a in agencies]
        kb.append([InlineKeyboardButton("➕ Create New Agency", callback_data=f"admin_new_agency:{group_chat_id}")])
        kb.append([InlineKeyboardButton("⏭ Approve without agency", callback_data=f"admin_link:{group_chat_id}:0")])

        group_title = await sync_to_async(lambda: TelegramGroup.objects.filter(chat_id=group_chat_id).values_list('chat_title', flat=True).first())()
        await query.edit_message_text(
            f"✅ Approving: *{group_title}*\n\nLink to which agency?",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    # ── Admin: link group to existing agency ──
    if data.startswith("admin_link:"):
        admin_ids = [a.strip() for a in os.getenv('ADMIN_TELEGRAM_IDS', '').split(',') if a.strip()]
        if str(update.effective_user.id) not in admin_ids:
            await query.edit_message_text("⛔ Not authorized.")
            return
        parts = data.split(":")
        group_chat_id = parts[1]
        agency_id = parts[2]

        @sync_to_async
        def do_link():
            from django.utils import timezone as dj_timezone
            group = TelegramGroup.objects.filter(chat_id=group_chat_id).first()
            if not group:
                return None, None
            group.status = 'approved'
            group.approved_at = dj_timezone.now()
            group.approved_by = str(update.effective_user.id)
            group.notification_enabled = True
            agency = None
            if agency_id != '0':
                agency = Agency.objects.filter(id=int(agency_id)).first()
                group.agency = agency
            group.save()
            return group, agency

        group, agency = await do_link()
        if not group:
            await query.edit_message_text("❌ Group not found.")
            return

        agency_name = agency.name if agency else "No agency"
        await query.edit_message_text(f"✅ *{group.chat_title}* approved → {agency_name}", parse_mode='Markdown')
        try:
            await context.bot.send_message(
                chat_id=group_chat_id,
                text="✅ *Your group has been approved!*\n\nYou will now receive Vatican ticket notifications.",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to notify group: {e}")

        # Offer plan change inline
        if agency:
            plan_kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("🆓 Free",    callback_data=f"admin_setplan:{agency.id}:free"),
                InlineKeyboardButton("⭐ Pro",     callback_data=f"admin_setplan:{agency.id}:pro"),
                InlineKeyboardButton("🏢 Agency",  callback_data=f"admin_setplan:{agency.id}:agency"),
            ]])
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🎯 Set plan for *{agency.name}* (current: `{agency.plan}`)",
                parse_mode='Markdown',
                reply_markup=plan_kb
            )
        return

    # ── Admin: start new agency creation flow ──
    if data.startswith("admin_new_agency:"):
        admin_ids = [a.strip() for a in os.getenv('ADMIN_TELEGRAM_IDS', '').split(',') if a.strip()]
        if str(update.effective_user.id) not in admin_ids:
            await query.edit_message_text("⛔ Not authorized.")
            return
        group_chat_id = data.split(":", 1)[1]
        # Store in user_data and ask for agency name
        ud['admin_creating_agency'] = {'group_chat_id': group_chat_id, 'step': 'name'}
        await query.edit_message_text(
            "➕ *Create New Agency*\n\nStep 1/3 — Send the *agency name*:",
            parse_mode='Markdown'
        )
        return

    # ── Admin: plan selection during agency creation ──
    if data.startswith("admin_agency_plan:"):
        admin_ids = [a.strip() for a in os.getenv('ADMIN_TELEGRAM_IDS', '').split(',') if a.strip()]
        if str(update.effective_user.id) not in admin_ids:
            return
        plan = data.split(":", 1)[1]
        ac = ud.get('admin_creating_agency', {})
        ac['plan'] = plan
        ud['admin_creating_agency'] = ac

        @sync_to_async
        def create_agency_and_user():
            import secrets, hashlib
            from django.utils import timezone as dj_timezone
            agency = Agency.objects.create(
                name=ac['agency_name'],
                api_key=secrets.token_hex(16),
                plan=plan,
                is_active=True
            )
            salt = secrets.token_hex(16)
            hashed = hashlib.sha256((ac['password'] + salt).encode()).hexdigest()
            user = User.objects.create(
                username=ac['username'],
                email=f"{ac['username']}@hydrabot.it",
                password_hash=salt + '$' + hashed,
                agency=agency,
                is_active=True,
                is_admin=True
            )
            # Link group
            group = TelegramGroup.objects.filter(chat_id=ac['group_chat_id']).first()
            if group:
                group.status = 'approved'
                group.approved_at = dj_timezone.now()
                group.approved_by = str(update.effective_user.id)
                group.notification_enabled = True
                group.agency = agency
                group.save()
            return agency, user, group

        agency, user, group = await create_agency_and_user()
        ud.pop('admin_creating_agency', None)

        await query.edit_message_text(
            f"✅ *Agency Created & Group Approved!*\n\n"
            f"🏢 Agency: *{agency.name}* ({plan})\n"
            f"👤 Username: `{user.username}`\n"
            f"🔑 Password: `{ac['password']}`\n"
            f"🔗 Group: {group.chat_title if group else ac['group_chat_id']}\n\n"
            f"Share these credentials with the agency.",
            parse_mode='Markdown'
        )
        try:
            await context.bot.send_message(
                chat_id=ac['group_chat_id'],
                text="✅ *Your group has been approved!*\n\nYou will now receive Vatican ticket notifications.",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to notify group: {e}")
        return

    # ── Admin: change plan for an existing agency ──
    if data.startswith("admin_setplan:"):
        admin_ids = [a.strip() for a in os.getenv('ADMIN_TELEGRAM_IDS', '').split(',') if a.strip()]
        if str(update.effective_user.id) not in admin_ids:
            await query.answer("⛔ Not authorized.", show_alert=True)
            return
        _, agency_id_str, new_plan = data.split(":")

        @sync_to_async
        def do_set_plan():
            a = Agency.objects.filter(id=int(agency_id_str)).first()
            if a:
                a.plan = new_plan
                a.save(update_fields=['plan'])
            return a

        a = await do_set_plan()
        plan_labels = {'free': '🆓 Free', 'pro': '⭐ Pro', 'agency': '🏢 Agency'}
        await query.edit_message_text(
            f"✅ Plan updated: *{a.name}* → {plan_labels.get(new_plan, new_plan)}",
            parse_mode='Markdown'
        )
        return

    # Ensure agency is loaded
    if 'agency_id' not in ud:
        agency = await get_agency(update.effective_chat.id)
        if not agency:
            await query.edit_message_text("⚠️ Chat not linked. Contact admin.")
            return
        ud['agency_id'] = agency.id
        ud['agency_name'] = agency.name
        ud['agency_plan'] = agency.plan

    # ── Menu ──
    if data in ('menu', 'back'):
        ud['step'] = None
        await query.edit_message_text(
            f"🏛️ Vatican Monitor Bot\nAgency: {ud['agency_name']}\n\nWhat would you like to do?",
            reply_markup=kb_main()
        )
        return

    if data == 'cancel':
        ud['step'] = None
        await query.edit_message_text("❌ Cancelled.", reply_markup=kb_back())
        return

    # ── Add flow ──
    if data == 'add':
        ud['step'] = 'date'
        now = datetime.now()
        await query.edit_message_text(
            "📅 Pick a date:",
            reply_markup=kb_calendar(now.year, now.month)
        )
        return

    # Calendar navigation
    if data.startswith('cal:'):
        parts = data.split(':')
        action = parts[1]
        if action == 'ignore':
            return
        year, month = int(parts[2]), int(parts[3])
        if action == 'prev':
            month -= 1
            if month < 1:
                month = 12; year -= 1
        elif action == 'next':
            month += 1
            if month > 12:
                month = 1; year += 1
        await query.edit_message_text(
            "📅 Pick a date:",
            reply_markup=kb_calendar(year, month)
        )
        return

    if data == 'date:manual':
        ud['step'] = 'date_text'
        await query.edit_message_text(
            "✏️ Type the date in YYYY-MM-DD format\nExample: 2026-06-15\n\nOr /cancel to go back."
        )
        return

    if data.startswith('date:'):
        date_val = data.split(':', 1)[1]
        ud['date'] = date_val
        ud['step'] = 'visitors'
        await query.edit_message_text(
            f"✅ Date: {date_val}\n\n👥 How many visitors?",
            reply_markup=kb_visitors()
        )
        return

    if data.startswith('vis:'):
        ud['visitors'] = int(data.split(':')[1])
        ud['step'] = 'ticket'
        await query.edit_message_text(
            f"✅ Date: {ud['date']}\n✅ Visitors: {ud['visitors']}\n\n🎫 Select ticket type:",
            reply_markup=kb_ticket()
        )
        return

    if data == 'ticket:standard':
        ud['ticket_type'] = 0
        ud['ticket_name'] = "Musei Vaticani - Biglietti d'ingresso"
        ud['ticket_label'] = 'Standard Entry'
        ud['language'] = None
        ud['step'] = 'times'
        await query.edit_message_text(
            f"✅ Date: {ud['date']}\n✅ Visitors: {ud['visitors']}\n✅ Ticket: Standard Entry\n\n⏰ Preferred times:",
            reply_markup=kb_times()
        )
        return

    if data == 'ticket:guided':
        ud['ticket_type'] = 1
        ud['ticket_name'] = 'Musei Vaticani - Visite Guidate'
        ud['ticket_label'] = 'Guided Tour'
        ud['step'] = 'language'
        await query.edit_message_text(
            f"✅ Date: {ud['date']}\n✅ Visitors: {ud['visitors']}\n✅ Ticket: Guided Tour\n\n🌍 Select language:",
            reply_markup=kb_language()
        )
        return

    if data.startswith('lang:'):
        lang = data.split(':')[1]
        ud['language'] = lang
        ud['ticket_name'] = f'Musei Vaticani - Visite Guidate ({lang})'
        ud['step'] = 'times'
        await query.edit_message_text(
            f"✅ Date: {ud['date']}\n✅ Visitors: {ud['visitors']}\n✅ Ticket: Guided Tour\n✅ Language: {lang}\n\n⏰ Preferred times:",
            reply_markup=kb_times()
        )
        return

    if data.startswith('time:'):
        slot = data.split(':')[1]
        time_map = {
            'morning':   (['09:00','09:30','10:00','10:30','11:00','11:30'], 'Morning 09:00–12:00'),
            'afternoon': (['12:00','12:30','13:00','13:30','14:00','14:30'], 'Afternoon 12:00–15:00'),
            'late':      (['15:00','15:30','16:00','16:30'],                 'Late 15:00–17:00'),
            'all':       (['09:00','10:00','11:00','12:00','13:00','14:00','15:00','16:00'], 'All Times'),
        }
        times, label = time_map[slot]
        ud['preferred_times'] = times
        ud['times_label'] = label
        ud['step'] = 'tier'
        await query.edit_message_text(
            f"✅ Date: {ud['date']}\n✅ Visitors: {ud['visitors']}\n✅ Ticket: {ud['ticket_label']}\n✅ Times: {label}\n\n🎯 Select monitoring tier:",
            reply_markup=kb_tier(ud.get('agency_plan', 'free'))
        )
        return

    if data.startswith('tier:locked_'):
        locked = data.split('tier:locked_')[1]
        plan_needed = 'Pro' if locked == 'hold' else 'Agency'
        await query.answer(f"🔐 {plan_needed} plan required. Contact admin to upgrade.", show_alert=True)
        return

    if data.startswith('tier:'):
        tier = data.split(':')[1]
        tier_labels = {
            'notify': '🔔 Notify Only',
            'hold':   '🔒 Notify + Hold',
            'snipe':  '🤖 Notify + Hold + Snipe',
        }
        ud['tier'] = tier
        ud['tier_label'] = tier_labels.get(tier, tier)
        ud['step'] = 'confirm'
        await query.edit_message_text(
            f"📋 Confirm New Monitor\n\n{summary(ud)}\n🎯 Tier: {ud['tier_label']}\n\nAdd this monitor?",
            reply_markup=kb_confirm()
        )
        return

    if data == 'confirm':
        await do_create_monitor(query, context)
        return

    # ── List ──
    if data == 'list':
        await do_list(query, context)
        return

    # ── Remove ──
    if data == 'remove':
        await do_remove_menu(query, context)
        return

    if data.startswith('del:'):
        task_id = int(data.split(':')[1])
        await do_delete_task(query, context, task_id)
        return

    # ── Status ──
    if data == 'status':
        await do_status(query, context)
        return


# ── Text message handler (for manual date / custom times) ─────────────────────

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    step = ud.get('step')
    text = update.message.text.strip()

    # ── Admin: agency creation text steps ──
    admin_ids = [a.strip() for a in os.getenv('ADMIN_TELEGRAM_IDS', '').split(',') if a.strip()]
    ac = ud.get('admin_creating_agency')
    if ac and str(update.effective_user.id) in admin_ids:
        ac_step = ac.get('step')

        if ac_step == 'name':
            ac['agency_name'] = text
            ac['step'] = 'username'
            ud['admin_creating_agency'] = ac
            await update.message.reply_text(
                f"✅ Agency name: *{text}*\n\nStep 2/3 — Send the *login username* for this agency:",
                parse_mode='Markdown'
            )
        elif ac_step == 'username':
            # Check if username taken
            from asgiref.sync import sync_to_async
            from monitors.models import User as BotUser
            exists = await sync_to_async(BotUser.objects.filter(username=text).exists)()
            if exists:
                await update.message.reply_text("❌ Username already taken. Choose another:")
                return
            ac['username'] = text
            ac['step'] = 'password'
            ud['admin_creating_agency'] = ac
            await update.message.reply_text(
                f"✅ Username: *{text}*\n\nStep 3/3 — Send the *password*:",
                parse_mode='Markdown'
            )
        elif ac_step == 'password':
            ac['password'] = text
            ac['step'] = 'plan'
            ud['admin_creating_agency'] = ac
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("🆓 Free", callback_data="admin_agency_plan:free"),
                InlineKeyboardButton("⭐ Pro", callback_data="admin_agency_plan:pro"),
                InlineKeyboardButton("🏢 Agency", callback_data="admin_agency_plan:agency"),
            ]])
            await update.message.reply_text(
                f"✅ Password set.\n\nSelect plan:",
                reply_markup=kb
            )
        return

    if step == 'date_text':
        try:
            d = datetime.strptime(text, '%Y-%m-%d')
            if d.date() < datetime.now().date():
                await update.message.reply_text("❌ Date must be in the future. Try again (YYYY-MM-DD):")
                return
            ud['date'] = text
            ud['step'] = 'visitors'
            await update.message.reply_text(
                f"✅ Date: {text}\n\n👥 How many visitors?",
                reply_markup=kb_visitors()
            )
        except ValueError:
            await update.message.reply_text("❌ Invalid format. Use YYYY-MM-DD (e.g. 2026-06-15):")
        return

    # ── Profile setup steps ──
    if step == 'profile_first_name':
        ud['profile']['first_name'] = text
        ud['step'] = 'profile_last_name'
        await update.message.reply_text("Step 2/5 — Send your *last name*:", parse_mode='Markdown')
        return

    if step == 'profile_last_name':
        ud['profile']['last_name'] = text
        ud['step'] = 'profile_email'
        await update.message.reply_text("Step 3/5 — Send your *email address*:", parse_mode='Markdown')
        return

    if step == 'profile_email':
        if '@' not in text:
            await update.message.reply_text("❌ Invalid email. Try again:")
            return
        ud['profile']['email'] = text
        ud['step'] = 'profile_phone'
        await update.message.reply_text("Step 4/5 — Send your *phone number* (e.g. +39 333 1234567):", parse_mode='Markdown')
        return

    if step == 'profile_phone':
        ud['profile']['phone'] = text
        ud['step'] = 'profile_birth_date'
        await update.message.reply_text("Step 5/5 — Send your *date of birth* (YYYY-MM-DD):", parse_mode='Markdown')
        return

    if step == 'profile_birth_date':
        from asgiref.sync import sync_to_async
        from datetime import date as date_type
        try:
            bd = datetime.strptime(text, '%Y-%m-%d').date()
        except ValueError:
            await update.message.reply_text("❌ Invalid format. Use YYYY-MM-DD (e.g. 1990-05-20):")
            return

        profile_data = ud.get('profile', {})
        agency_id = ud.get('agency_id')

        @sync_to_async
        def save_profile():
            from monitors.models import BuyerProfile, Agency
            agency = Agency.objects.get(id=agency_id)
            obj, _ = BuyerProfile.objects.update_or_create(
                agency=agency,
                defaults={
                    'first_name': profile_data['first_name'],
                    'last_name': profile_data['last_name'],
                    'email': profile_data['email'],
                    'phone': profile_data['phone'],
                    'birth_date': bd,
                }
            )
            return obj

        await save_profile()
        ud['step'] = None
        ud.pop('profile', None)
        await update.message.reply_text(
            f"✅ *Buyer profile saved!*\n\n"
            f"👤 {profile_data['first_name']} {profile_data['last_name']}\n"
            f"📧 {profile_data['email']}\n"
            f"📱 {profile_data['phone']}\n"
            f"🎂 {text}\n\n"
            f"Snipe mode will use this info to auto-book tickets.",
            parse_mode='Markdown',
            reply_markup=kb_back()
        )
        return

    # Ignore other text during flow
    if step:
        await update.message.reply_text("Please use the buttons above, or /cancel to stop.")


# ── Actions ───────────────────────────────────────────────────────────────────

async def do_create_monitor(query, context):
    from asgiref.sync import sync_to_async
    ud = context.user_data
    agency_id = ud.get('agency_id')
    date = ud.get('date')
    visitors = ud.get('visitors')
    ticket_type = ud.get('ticket_type', 0)
    ticket_name = ud.get('ticket_name', "Musei Vaticani - Biglietti d'ingresso")
    ticket_label = ud.get('ticket_label', 'Standard Entry')
    language = ud.get('language')
    preferred_times = ud.get('preferred_times', ['09:00','10:00','11:00','12:00','13:00','14:00','15:00','16:00'])

    try:
        agency = await sync_to_async(Agency.objects.get)(id=agency_id)

        # Check duplicate
        existing = await sync_to_async(
            MonitorTask.objects.filter(
                agency=agency, site='vatican',
                dates__contains=[date], visitors=visitors,
                ticket_type=ticket_type, is_active=True
            ).first
        )()
        if existing:
            await query.edit_message_text(
                f"⚠️ Monitor already exists (Task #{existing.id})\n\nDate: {date} · Visitors: {visitors}",
                reply_markup=kb_back()
            )
            return

        tier = ud.get('tier', 'notify')
        task = await sync_to_async(MonitorTask.objects.create)(
            agency=agency,
            site='vatican',
            area_name='Musei Vaticani',
            dates=[date],
            preferred_times=preferred_times,
            visitors=visitors,
            ticket_type=ticket_type,
            ticket_label=ticket_label,
            ticket_name=ticket_name,
            ticket_id=None,
            language=language,
            check_interval=60,
            tier=tier,
            match_strategy='any',
            notification_mode='available_only',
            is_active=True,
            last_status='pending',
            last_result_summary=f"Created via Telegram on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # Trigger immediate check
        try:
            from monitors.tasks import resolve_and_check_task
            await sync_to_async(resolve_and_check_task.delay)(task.id)
        except Exception as e:
            logger.warning(f"Could not trigger immediate check: {e}")

        ud['step'] = None
        await query.edit_message_text(
            f"✅ Monitor created! (Task #{task.id})\n\n{summary(ud)}\n\n🔔 You'll be notified when tickets are available.",
            reply_markup=kb_back()
        )
    except Exception as e:
        logger.error(f"Error creating monitor: {e}")
        await query.edit_message_text(f"❌ Error: {e}", reply_markup=kb_back())


async def do_list(query, context):
    from asgiref.sync import sync_to_async
    agency_id = context.user_data.get('agency_id')
    tasks = await sync_to_async(list)(
        MonitorTask.objects.filter(agency_id=agency_id, site='vatican', is_active=True).order_by('dates')
    )
    if not tasks:
        await query.edit_message_text("📋 No active monitors.", reply_markup=kb_back())
        return
    lines = [f"📋 Active Monitors ({len(tasks)})\n"]
    for t in tasks:
        emoji = "✅" if t.last_status == 'available' else "❌"
        lines.append(f"{emoji} #{t.id} · {t.dates[0] if t.dates else '?'} · {t.visitors}v · {t.last_status or '?'}")
    await query.edit_message_text('\n'.join(lines), reply_markup=kb_back())


async def do_remove_menu(query, context):
    from asgiref.sync import sync_to_async
    agency_id = context.user_data.get('agency_id')
    tasks = await sync_to_async(list)(
        MonitorTask.objects.filter(agency_id=agency_id, site='vatican', is_active=True).order_by('dates')[:10]
    )
    if not tasks:
        await query.edit_message_text("📋 No monitors to remove.", reply_markup=kb_back())
        return
    rows = [[InlineKeyboardButton(
        f"🗑️ #{t.id} · {t.dates[0] if t.dates else '?'} · {t.visitors}v",
        callback_data=f'del:{t.id}'
    )] for t in tasks]
    rows.append([InlineKeyboardButton("🔙 Back", callback_data='menu')])
    await query.edit_message_text("Select monitor to remove:", reply_markup=InlineKeyboardMarkup(rows))


async def do_delete_task(query, context, task_id):
    from asgiref.sync import sync_to_async
    try:
        task = await sync_to_async(MonitorTask.objects.get)(id=task_id)
        date = task.dates[0] if task.dates else '?'
        await sync_to_async(task.delete)()
        await query.edit_message_text(f"✅ Monitor #{task_id} removed (Date: {date})", reply_markup=kb_back())
    except MonitorTask.DoesNotExist:
        await query.edit_message_text("❌ Monitor not found.", reply_markup=kb_back())


async def do_status(query, context):
    from asgiref.sync import sync_to_async
    agency_id = context.user_data.get('agency_id')
    agency_name = context.user_data.get('agency_name', '?')
    tasks = await sync_to_async(list)(MonitorTask.objects.filter(agency_id=agency_id, site='vatican', is_active=True))
    available = sum(1 for t in tasks if t.last_status == 'available')
    sold_out  = sum(1 for t in tasks if t.last_status == 'sold_out')
    await query.edit_message_text(
        f"📊 Status\nAgency: {agency_name}\n\n"
        f"Monitors: {len(tasks)}\n✅ Available: {available}\n❌ Sold Out: {sold_out}\n"
        f"⏳ Other: {len(tasks)-available-sold_out}\n\n⚡ Running 24/7",
        reply_markup=kb_back()
    )


async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['step'] = None
    await update.message.reply_text("❌ Cancelled. Use /start to go back.", reply_markup=kb_back())


async def setprofile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /setprofile — set buyer profile for snipe mode.
    Walks through: first_name → last_name → email → phone → birth_date → done.
    """
    ud = context.user_data
    agency = await get_agency(update.effective_chat.id)
    if not agency:
        await update.message.reply_text("⚠️ Chat not linked to an agency.")
        return
    ud['agency_id'] = agency.id
    ud['agency_name'] = agency.name
    ud['step'] = 'profile_first_name'
    ud['profile'] = {}
    await update.message.reply_text(
        "👤 *Set Buyer Profile* (for Snipe mode)\n\n"
        "This info is used to auto-fill the Vatican booking form.\n\n"
        "Step 1/5 — Send your *first name*:",
        parse_mode='Markdown'
    )


async def holds_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/holds — list all active held slots with payment links."""
    from asgiref.sync import sync_to_async
    agency = await get_agency(update.effective_chat.id)
    if not agency:
        await update.message.reply_text("⚠️ Chat not linked to an agency.")
        return

    @sync_to_async
    def get_holds():
        from monitors.models import HeldSlot
        return list(HeldSlot.objects.filter(
            task__agency=agency, status='held'
        ).order_by('date', 'slot_time', 'visitors')[:30])

    holds = await get_holds()
    if not holds:
        await update.message.reply_text(
            "🔓 No active holds right now.\n\nHolds are created automatically when slots open.",
            reply_markup=kb_back()
        )
        return

    lines = [f"🔒 *Active Holds* ({len(holds)})\n"]
    for h in holds:
        lines.append(
            f"📅 {h.date} {h.slot_time} | 👥 {h.visitors}v | €{h.total_price}\n"
            f"💳 [Pay now]({h.payment_url})\n"
        )
    await update.message.reply_text(
        '\n'.join(lines),
        parse_mode='Markdown',
        disable_web_page_preview=True,
        reply_markup=kb_back()
    )


async def setparticipants_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /setparticipants — upload a .txt or .csv with participant names.

    Format (one per line):
        FirstName LastName
    or CSV:
        FirstName,LastName

    These are used as participantUser list for hold/snipe bookings.
    The representativeUser (billing contact) stays as the stored BuyerProfile.
    """
    agency = await get_agency(update.effective_chat.id)
    if not agency:
        await update.message.reply_text("⚠️ Chat not linked to an agency.")
        return
    context.user_data['agency_id'] = agency.id
    context.user_data['step'] = 'awaiting_participants_file'
    await update.message.reply_text(
        "📋 *Upload Participant List*\n\n"
        "Send a `.txt` or `.csv` file with one name per line:\n\n"
        "`FirstName LastName`\n"
        "`FirstName,LastName`\n\n"
        "These names will be used as the visitors on the Vatican booking form.\n"
        "The billing contact (representativeUser) stays as your saved profile.",
        parse_mode='Markdown'
    )


async def on_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle .txt/.csv participant list uploads."""
    from asgiref.sync import sync_to_async

    ud = context.user_data
    if ud.get('step') != 'awaiting_participants_file':
        return

    doc = update.message.document
    if not doc.file_name.endswith(('.txt', '.csv')):
        await update.message.reply_text("❌ Please send a .txt or .csv file.")
        return

    agency_id = ud.get('agency_id')
    if not agency_id:
        await update.message.reply_text("⚠️ Session expired. Use /start first.")
        return

    # Download file
    file = await context.bot.get_file(doc.file_id)
    raw = await file.download_as_bytearray()
    text = raw.decode('utf-8', errors='ignore')

    # Parse names
    participants = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if ',' in line:
            parts = [p.strip() for p in line.split(',', 1)]
        else:
            parts = line.split(None, 1)
        if len(parts) == 2:
            participants.append({'first_name': parts[0], 'last_name': parts[1]})
        elif len(parts) == 1:
            participants.append({'first_name': parts[0], 'last_name': ''})

    if not participants:
        await update.message.reply_text("❌ No valid names found. Check the format and try again.")
        return

    # Save to BuyerProfile.participants_json (we'll add this field via migration)
    @sync_to_async
    def save_participants():
        from monitors.models import BuyerProfile, Agency
        import json
        agency = Agency.objects.get(id=agency_id)
        profile, _ = BuyerProfile.objects.get_or_create(
            agency=agency,
            defaults={'first_name': 'Agency', 'last_name': 'User', 'email': f'agency{agency_id}@hydrabot.it', 'phone': '+000'}
        )
        profile.participants_json = json.dumps(participants)
        profile.save(update_fields=['participants_json'])
        return len(participants)

    count = await save_participants()
    ud['step'] = None
    preview = '\n'.join(f"  {i+1}. {p['first_name']} {p['last_name']}" for i, p in enumerate(participants[:5]))
    if count > 5:
        preview += f"\n  ... and {count - 5} more"

    await update.message.reply_text(
        f"✅ *{count} participants saved!*\n\n{preview}\n\n"
        f"These names will be used for the next hold/snipe booking.",
        parse_mode='Markdown',
        reply_markup=kb_back()
    )


# ── Group join/leave handler ──────────────────────────────────────────────────

def extract_status_change(chat_member_update: ChatMemberUpdated):
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))
    if status_change is None:
        return None
    old_status, new_status = status_change
    was_member = old_status in [ChatMember.MEMBER, ChatMember.OWNER, ChatMember.ADMINISTRATOR] \
        or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    is_member = new_status in [ChatMember.MEMBER, ChatMember.OWNER, ChatMember.ADMINISTRATOR] \
        or (new_status == ChatMember.RESTRICTED and new_is_member is True)
    return was_member, is_member


async def handle_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from asgiref.sync import sync_to_async
    from django.utils import timezone
    result = extract_status_change(update.my_chat_member)
    if result is None:
        return
    was_member, is_member = result
    chat = update.effective_chat
    user = update.effective_user

    if not was_member and is_member:
        logger.info(f"Bot added to {chat.type}: {chat.title} (ID: {chat.id})")
        group, created = await sync_to_async(TelegramGroup.objects.get_or_create)(
            chat_id=str(chat.id),
            defaults={
                'chat_type': chat.type,
                'chat_title': chat.title,
                'chat_username': chat.username,
                'added_by_user_id': str(user.id),
                'added_by_username': user.username,
                'added_by_first_name': user.first_name,
                'status': 'pending',
                'last_activity': timezone.now()
            }
        )
        if created:
            # Build approve/reject buttons for admin notification
            approve_kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve:{chat.id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject:{chat.id}")
            ]])
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"👋 Vatican Monitor Bot added!\n\n🔒 Pending admin approval.\nGroup ID: `{chat.id}`",
                parse_mode='Markdown'
            )
            # Notify admins with inline approve/reject buttons
            admin_ids = os.getenv('ADMIN_TELEGRAM_IDS', '').split(',')
            for aid in admin_ids:
                if aid.strip():
                    try:
                        await context.bot.send_message(
                            chat_id=aid.strip(),
                            text=f"🔔 *New group approval request*\nGroup: {chat.title}\nID: `{chat.id}`\nAdded by: {user.first_name} (@{user.username})\n\nApprove or reject below:",
                            parse_mode='Markdown',
                            reply_markup=approve_kb
                        )
                    except Exception as e:
                        logger.error(f"Failed to notify admin {aid}: {e}")
    elif was_member and not is_member:
        group = await sync_to_async(TelegramGroup.objects.filter(chat_id=str(chat.id)).first)()
        if group:
            group.status = 'suspended'
            await sync_to_async(group.save)()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Single callback handler handles everything
    app.add_handler(CallbackQueryHandler(on_callback))

    # Commands
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('cancel', cancel_cmd))
    app.add_handler(CommandHandler('setprofile', setprofile_cmd))
    app.add_handler(CommandHandler('setparticipants', setparticipants_cmd))
    app.add_handler(CommandHandler('holds', holds_cmd))

    # Text input (for manual date entry, profile steps)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    # Document upload (participant list)
    app.add_handler(MessageHandler(filters.Document.ALL, on_document))

    # Group join/leave
    app.add_handler(ChatMemberHandler(handle_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))

    logger.info("🤖 Telegram bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
