#!/usr/bin/env python3
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')
sys.path.insert(0, '/app')
os.chdir('/app')

import django
django.setup()

from monitors.models import Agency

# Get the agency with missing chat ID
agency = Agency.objects.get(name='Agency-wondersoffcity')
print(f"Current Chat ID: {agency.telegram_chat_id or 'NOT SET'}")

# Set the same chat ID as the working agency
agency.telegram_chat_id = '-5245239270'
agency.save()

print(f"✅ Updated Chat ID to: {agency.telegram_chat_id}")
print("Agency-wondersoffcity will now receive Telegram notifications!")
