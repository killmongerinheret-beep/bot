#!/usr/bin/env python
"""Patch notification to show ALL slots"""

with open('/app/backend/monitors/notification_utils.py', 'r') as f:
    content = f.read()

# Replace the slot display logic to show ALL slots
old_logic = '''    # Add preferred slots first (highlighted)
    if preferred_slots:
        message += f"⭐ *YOUR PREFERRED TIMES:*\\n"
        for slot in preferred_slots[:5]:
            message += f"   ⭐ {slot}\\n"
        if len(preferred_slots) > 5:
            message += f"   ... and {len(preferred_slots) - 5} more preferred\\n"
        message += "\\n"
    
    # Add other available slots
    display_slots = other_slots[:10] if preferred_slots else other_slots[:15]
    message += f"🕐 *Other Available Times* ({len(slots)} total):\\n"
    for slot in display_slots:
        message += f"   • {slot}\\n"
    
    remaining = len(other_slots) - len(display_slots)
    if remaining > 0:
        message += f"   ... and {remaining} more\\n"'''

new_logic = '''    # Add preferred slots first (highlighted)
    if preferred_slots:
        message += f"⭐ *YOUR PREFERRED TIMES:*\\n"
        for slot in preferred_slots:
            message += f"   ⭐ {slot}\\n"
        message += "\\n"
    
    # Add ALL other available slots (no limit)
    if other_slots:
        message += f"🕐 *All Available Times* ({len(slots)} total):\\n"
        for slot in other_slots:
            message += f"   • {slot}\\n"
    else:
        message += f"🕐 *All Available Times* ({len(slots)} total):\\n"
        for slot in slots:
            message += f"   • {slot}\\n"'''

content = content.replace(old_logic, new_logic)

with open('/app/backend/monitors/notification_utils.py', 'w') as f:
    f.write(content)

print("✅ Notification updated to show ALL slots!")
