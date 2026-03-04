"""
Telegram Calendar Helper
Provides inline calendar for date selection
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
import calendar

class TelegramCalendar:
    """
    Inline calendar for Telegram bots
    """
    
    def __init__(self, year=None, month=None):
        self.year = year or datetime.now().year
        self.month = month or datetime.now().month
    
    def create_calendar(self, year=None, month=None):
        """
        Create an inline keyboard with calendar
        """
        year = year or self.year
        month = month or self.month
        
        # Month name
        month_name = calendar.month_name[month]
        
        # Create keyboard
        keyboard = []
        
        # Header row: Month Year
        keyboard.append([
            InlineKeyboardButton("◀️", callback_data=f"cal_prev_{year}_{month}"),
            InlineKeyboardButton(f"{month_name} {year}", callback_data="cal_ignore"),
            InlineKeyboardButton("▶️", callback_data=f"cal_next_{year}_{month}")
        ])
        
        # Days of week header
        keyboard.append([
            InlineKeyboardButton(day, callback_data="cal_ignore")
            for day in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        ])
        
        # Calendar days
        month_calendar = calendar.monthcalendar(year, month)
        for week in month_calendar:
            row = []
            for day in week:
                if day == 0:
                    # Empty day
                    row.append(InlineKeyboardButton(" ", callback_data="cal_ignore"))
                else:
                    # Check if date is in the past
                    date = datetime(year, month, day)
                    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    
                    if date < today:
                        # Past date - show but disabled
                        row.append(InlineKeyboardButton(
                            f"·{day}·",
                            callback_data="cal_ignore"
                        ))
                    else:
                        # Future date - selectable
                        row.append(InlineKeyboardButton(
                            str(day),
                            callback_data=f"cal_day_{year}_{month}_{day}"
                        ))
            keyboard.append(row)
        
        # Footer: Cancel button
        keyboard.append([
            InlineKeyboardButton("❌ Cancel", callback_data="cal_cancel")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    def process_selection(self, data):
        """
        Process calendar callback data
        Returns: (action, date_str or None)
        """
        parts = data.split('_')
        
        if data == "cal_ignore":
            return ("ignore", None)
        
        elif data == "cal_cancel":
            return ("cancel", None)
        
        elif data.startswith("cal_prev_"):
            # Previous month
            year = int(parts[2])
            month = int(parts[3])
            
            if month == 1:
                month = 12
                year -= 1
            else:
                month -= 1
            
            return ("change", self.create_calendar(year, month))
        
        elif data.startswith("cal_next_"):
            # Next month
            year = int(parts[2])
            month = int(parts[3])
            
            if month == 12:
                month = 1
                year += 1
            else:
                month += 1
            
            return ("change", self.create_calendar(year, month))
        
        elif data.startswith("cal_day_"):
            # Day selected
            year = int(parts[2])
            month = int(parts[3])
            day = int(parts[4])
            
            date_str = f"{year}-{month:02d}-{day:02d}"
            return ("selected", date_str)
        
        return ("ignore", None)


def create_quick_dates_keyboard():
    """
    Create keyboard with quick date options (next 7 days, next month, etc.)
    """
    today = datetime.now()
    
    keyboard = []
    
    # Quick options row 1
    keyboard.append([
        InlineKeyboardButton("📅 Calendar", callback_data="quick_calendar"),
        InlineKeyboardButton("📝 Type Date", callback_data="quick_type")
    ])
    
    # Next 7 days
    row = []
    for i in range(1, 8):
        date = today + timedelta(days=i)
        day_name = date.strftime("%a")[:2]  # Mo, Tu, We...
        row.append(InlineKeyboardButton(
            f"{day_name} {date.day}",
            callback_data=f"quick_day_{date.strftime('%Y-%m-%d')}"
        ))
        
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    # Popular future dates
    keyboard.append([
        InlineKeyboardButton("Next Week", callback_data=f"quick_day_{(today + timedelta(days=7)).strftime('%Y-%m-%d')}"),
        InlineKeyboardButton("2 Weeks", callback_data=f"quick_day_{(today + timedelta(days=14)).strftime('%Y-%m-%d')}")
    ])
    
    keyboard.append([
        InlineKeyboardButton("1 Month", callback_data=f"quick_day_{(today + timedelta(days=30)).strftime('%Y-%m-%d')}"),
        InlineKeyboardButton("2 Months", callback_data=f"quick_day_{(today + timedelta(days=60)).strftime('%Y-%m-%d')}")
    ])
    
    # Cancel
    keyboard.append([
        InlineKeyboardButton("❌ Cancel", callback_data="quick_cancel")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def create_visitors_keyboard():
    """
    Create keyboard for selecting number of visitors
    """
    keyboard = []
    
    # 1-6 visitors (most common)
    keyboard.append([
        InlineKeyboardButton("1", callback_data="visitors_1"),
        InlineKeyboardButton("2", callback_data="visitors_2"),
        InlineKeyboardButton("3", callback_data="visitors_3")
    ])
    
    keyboard.append([
        InlineKeyboardButton("4", callback_data="visitors_4"),
        InlineKeyboardButton("5", callback_data="visitors_5"),
        InlineKeyboardButton("6", callback_data="visitors_6")
    ])
    
    # 7-10 visitors (less common)
    keyboard.append([
        InlineKeyboardButton("7", callback_data="visitors_7"),
        InlineKeyboardButton("8", callback_data="visitors_8"),
        InlineKeyboardButton("9", callback_data="visitors_9"),
        InlineKeyboardButton("10", callback_data="visitors_10")
    ])
    
    # Cancel
    keyboard.append([
        InlineKeyboardButton("❌ Cancel", callback_data="visitors_cancel")
    ])
    
    return InlineKeyboardMarkup(keyboard)
