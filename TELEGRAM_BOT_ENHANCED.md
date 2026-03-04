# Telegram Bot Enhanced - Ticket & Time Selection

## Changes Applied

### New Features Added

1. **Ticket Type Selection**
   - Standard Entry (Musei Vaticani - Biglietti d'ingresso)
   - Guided Tour (Musei Vaticani - Visite Guidate)
   - Automatically sets correct ticket_type, ticket_name, and language

2. **Preferred Time Selection**
   - Morning (09:00-12:00): 09:00, 09:30, 10:00, 10:30, 11:00, 11:30
   - Afternoon (12:00-15:00): 12:00, 12:30, 13:00, 13:30, 14:00, 14:30
   - Late (15:00-17:00): 15:00, 15:30, 16:00, 16:30
   - All Times: 09:00, 10:00, 11:00, 12:00, 13:00, 14:00, 15:00, 16:00
   - Custom Times: User can enter specific times (e.g., "09:00, 10:30, 14:00")

### Updated Flow

**Old Flow:**
1. Select date
2. Enter visitors
3. Confirm (hardcoded standard ticket, generic times)

**New Flow:**
1. Select date (calendar or manual)
2. Select visitors (1-10)
3. **Select ticket type** (Standard or Guided Tour)
4. **Select preferred times** (Morning/Afternoon/Late/All/Custom)
5. Confirm with all details

### Technical Changes

**File: `telegram_bot.py`**

1. **New Conversation States:**
   ```python
   SELECTING_TICKET = 5
   SELECTING_TIMES = 6
   ```

2. **New Handlers:**
   - `handle_ticket_selection()` - Processes ticket type selection
   - `handle_time_selection()` - Processes time preference selection
   - `receive_custom_times()` - Handles custom time input

3. **Updated `confirm_add()` Function:**
   - Now reads ticket_type, ticket_name, ticket_label, language, preferred_times from context
   - Creates monitor with user-selected preferences
   - Shows all details in confirmation message

4. **Updated ConversationHandler:**
   - Added SELECTING_TICKET state with handle_ticket_selection
   - Added SELECTING_TIMES state with handle_time_selection and receive_custom_times

### How It Works

**Ticket Selection:**
```
🎫 Select Ticket Type

Date: 2026-03-29
Visitors: 1

Choose ticket type:
[🎫 Standard Entry] [👥 Guided Tour] [❌ Cancel]
```

**Time Selection:**
```
⏰ Select Preferred Times

Date: 2026-03-29
Visitors: 1
Ticket: Standard Entry

Choose your preferred time slots:
(You'll be notified when ANY slot is available,
but preferred times will be highlighted)

[🌅 Morning (09:00-12:00)]
[🌞 Afternoon (12:00-15:00)]
[🌆 Late (15:00-17:00)]
[⏰ All Times]
[✏️ Custom Times]
[❌ Cancel]
```

**Custom Times:**
```
✏️ Custom Times

Send your preferred times separated by commas.
Example: 09:00, 10:30, 14:00

Or send /skip to use all times.
```

**Final Confirmation:**
```
📋 Confirm New Monitor

Date: 2026-03-29
Visitors: 1
Ticket: Standard Entry
Preferred Times: Morning (09:00-12:00)
Check Interval: 60 seconds

Add this monitor?
[✅ Confirm] [❌ Cancel]
```

### Database Fields Used

- `ticket_type`: 0 (Standard) or 1 (Guided Tour)
- `ticket_name`: Full ticket name for matching
- `ticket_label`: Display name
- `language`: None for standard, 'ENG' for guided tours
- `preferred_times`: Array of time strings (e.g., ['09:00', '10:30', '14:00'])

### Benefits

1. **User Control**: Users can now select exactly what they want
2. **Accurate Monitoring**: Correct ticket type ensures proper checks
3. **Smart Notifications**: Preferred times are highlighted in alerts
4. **Flexibility**: Custom times allow precise preferences
5. **Better UX**: Clear step-by-step flow with visual feedback

### Testing

To test the new features:

1. Start the bot: `/start`
2. Click "➕ Add Monitor"
3. Select a date using calendar
4. Select number of visitors
5. **NEW:** Select ticket type (Standard or Guided Tour)
6. **NEW:** Select preferred times (or enter custom)
7. Confirm and verify task is created with correct details

### Restart Command

```powershell
docker-compose exec -d backend python /app/telegram_bot.py
```

Or use the start script:
```powershell
.\start_telegram_bot.ps1
```

## Status

✅ Ticket selection implemented
✅ Time preference selection implemented
✅ Custom time input supported
✅ Confirmation shows all details
✅ Database fields properly set
✅ Bot restarted with new code

The Telegram bot now provides full control over ticket type and time preferences!
