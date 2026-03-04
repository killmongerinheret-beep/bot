import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from monitors.tasks import run_shared_vatican_monitor

def main():
    # Force a standard (ticket_type=0) check for a specific date list
    # Use ISO here to match DB stored format
    dates = ['2026-02-26']
    ticket_type = 0
    language = ""  # ignored for standard
    print(f"⏩ Forcing shared check for dates={dates}, ticket_type={ticket_type}")
    result = run_shared_vatican_monitor(ticket_type, language, dates)
    print(f"Done: {result}")

if __name__ == "__main__":
    main()
