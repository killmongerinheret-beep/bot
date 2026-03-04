# Telegram Bot - Individual Time Selection

## Updated Time Selection Interface

### Time Slot Buttons (08:00 - 17:30, 30-minute intervals)

The bot now shows individual time slot buttons instead of grouped options:

```
⏰ Select Preferred Time

Date: 2026-03-29
Visitors: 1
Ticket: Standard Entry

Choose your preferred time slot:
(Select one time, or use Custom for multiple)

[08:00] [08:30] [09:00]
[09:30] [10:00] [10:30]
[11:00] [11:30] [12:00]
[12:30] [13:00] [13:30]
[14:00] [14:30] [15:00]
[15:30] [16:00] [16:30]
[17:00] [17:30]
[✏️ Custom Times]
[❌ Cancel]
```

### Available Time Slots

**Total: 20 time slots**
- 08:00, 08:30
- 09:00, 09:30
- 10:00, 10:30
- 11:00, 11:30
- 12:00, 12:30
- 13:00, 13:30
- 14:00, 14:30
- 15:00, 15:30
- 16:00, 16:30
- 17:00, 17:30

### How It Works

1. **Single Time Selection**
   - User clicks one time button (e.g., "10:00")
   - Bot sets `preferred_times = ['10:00']`
   - User will be notified when that specific time is available

2. **Custom Times (Multiple)**
   - User clicks "✏️ Custom Times"
   - Bot prompts: "Send your preferred times separated by commas"
   - User types: `09:00, 10:30, 14:00`
   - Bot sets `preferred_times = ['09:00', '10:30', '14:00']`
   - User will be notified when ANY of these times are available

### Example Flow

**Step 1: Select Date**
```
📅 Choose a date:
[Calendar] [Quick Dates]
```

**Step 2: Select Visitors**
```
👥 How many visitors?
[1] [2] [3] [4] [5]
[6] [7] [8] [9] [10]
```

**Step 3: Select Ticket Type**
```
🎫 Select Ticket Type
[🎫 Standard Entry]
[👥 Guided Tour]
```

**Step 4: Select Time** (NEW!)
```
⏰ Select Preferred Time
[08:00] [08:30] [09:00]
[09:30] [10:00] [10:30]
... (all times) ...
[✏️ Custom Times]
```

**Step 5: Confirm**
```
📋 Confirm New Monitor

Date: 2026-03-29
Visitors: 1
Ticket: Standard Entry
Preferred Time: 10:00
Check Interval: 60 seconds

Add this monitor?
[✅ Confirm] [❌ Cancel]
```

### Custom Times Example

When user clicks "✏️ Custom Times":

```
✏️ Custom Times

Send your preferred times separated by commas.
Example: 09:00, 10:30, 14:00

Or send /skip to use all times.
```

User types: `09:00, 10:30, 14:00`

Bot confirms:
```
📋 Confirm New Monitor

Date: 2026-03-29
Visitors: 1
Ticket: Standard Entry
Preferred Time: 09:00, 10:30, 14:00
Check Interval: 60 seconds

Add this monitor?
[✅ Confirm] [❌ Cancel]
```

### Technical Implementation

**Code Changes:**

1. **Generate Time Slots Dynamically**
   ```python
   time_slots = []
   for hour in range(8, 18):
       for minute in ['00', '30']:
           time = f"{hour:02d}:{minute}"
           if time <= "17:30":
               time_slots.append(time)
   ```

2. **Create Keyboard with 3 Buttons Per Row**
   ```python
   keyboard = []
   for i in range(0, len(time_slots), 3):
       row = []
       for time in time_slots[i:i+3]:
           row.append(InlineKeyboardButton(time, callback_data=f'time_{time}'))
       keyboard.append(row)
   ```

3. **Handle Time Selection**
   ```python
   if data.startswith("time_"):
       selected_time = data.replace("time_", "")
       context.user_data['preferred_times'] = [selected_time]
   ```

### Benefits

✅ **Precise Control**: Users select exact time they want
✅ **Visual Clarity**: All available times shown at once
✅ **Flexible**: Single time or multiple via custom
✅ **Mobile-Friendly**: 3 buttons per row fits mobile screens
✅ **Complete Range**: Full Vatican opening hours (08:00-17:30)

### Database Storage

The selected time(s) are stored in the `preferred_times` field as an array:

- Single time: `['10:00']`
- Multiple times: `['09:00', '10:30', '14:00']`
- All times: `['08:00', '09:00', '10:00', ..., '17:00']`

### Notification Behavior

When tickets become available:
- Bot checks ALL time slots
- If ANY of your preferred times are available, you get notified
- Preferred times are highlighted in the notification message
- You'll see which specific times you wanted are now available

## Status

✅ Individual time buttons (08:00-17:30, 30-min intervals)
✅ 3 buttons per row layout
✅ Custom times option for multiple selections
✅ Single time selection supported
✅ Bot restarted with new code

The bot now provides granular time selection with all available Vatican time slots!
