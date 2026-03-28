import os, sys, django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from monitors.models import Agency, BuyerProfile
from datetime import date

# Create profile for ALL agencies so any hold can use it
agencies = Agency.objects.exclude(plan='system')

for agency in agencies:
    profile, created = BuyerProfile.objects.update_or_create(
        agency=agency,
        defaults={
            'first_name': 'Aniile',
            'last_name': 'Skear',
            'email': 'killmongerinheret@gmail.com',
            'phone': '3481716429',
            'country': 'India',
            'city': 'Chennai',
            'birth_date': date(1987, 6, 10),
            'gender': 'M',
            'language': 'en',
        }
    )
    print(f"{'Created' if created else 'Updated'}: {agency.name} -> {profile.first_name} {profile.last_name}")

print("\nDone. Update via /setprofile in the bot to change details.")
