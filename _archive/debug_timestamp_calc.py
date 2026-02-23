
from datetime import datetime
import time
try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Fallback for Python < 3.9 if needed, though container has 3.11+
    from dateutil.tz import gettz as ZoneInfo

# User Provided URLs
url_guided_feb13 = "https://tickets.museivaticani.va/home/fromtag/1/1769727600000/MV-Visite-Guidate/1"
url_std_feb27 = "https://tickets.museivaticani.va/home/fromtag/2/1770937200000/MV-Biglietti/1" # Assumed date based on user text? User said Feb 13 for first one.

ts_guided = 1769727600000
ts_std = 1770937200000

def check_timestamp(ms, label):
    s = ms / 1000
    dt_utc = datetime.fromtimestamp(s, tz=ZoneInfo("UTC"))
    dt_rome = datetime.fromtimestamp(s, tz=ZoneInfo("Europe/Rome"))
    print(f"--- {label} ({ms}) ---")
    print(f"UTC:  {dt_utc}")
    print(f"Rome: {dt_rome}")
    return dt_utc, dt_rome

print("Analyzing User Provided Timestamps:")
dt_g_utc, dt_g_rome = check_timestamp(ts_guided, "Guided Feb 13?")
dt_s_utc, dt_s_rome = check_timestamp(ts_std, "Std Link 2")

# Current Bot Logic
def bot_logic(date_str):
    rome = ZoneInfo("Europe/Rome")
    if "/" in date_str:
        dt = datetime.strptime(date_str, "%d/%m/%Y")
    else:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    
    # Midnight Rome
    midnight_rome = dt.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=rome)
    ts_rome = int(midnight_rome.timestamp() * 1000)
    
    # Midnight UTC
    dt_utc = dt.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=ZoneInfo("UTC"))
    ts_utc = int(dt_utc.timestamp() * 1000)
    
    return ts_rome, ts_utc, midnight_rome

print("\nComparing with Bot Calculation for Feb 13, 2026:")
ts_rome, ts_utc, dt_rome_obj = bot_logic("13/02/2026")

print(f"Bot (Rome Midnight): {ts_rome} -> {dt_rome_obj}")
print(f"User URL TS:       {ts_guided}")
print(f"Difference:        {ts_rome - ts_guided}")

if ts_rome == ts_guided:
    print("✅ CONCLUSION: Bot Logic (Midnight Rome) MATCHES User URL.")
elif ts_utc == ts_guided:
    print("✅ CONCLUSION: User URL is actually Midnight UTC.")
else:
    print("❌ CONCLUSION: Logic mismatch. Investigating offset...")
    diff_hours = (ts_rome - ts_guided) / 1000 / 3600
    print(f"Offset in hours: {diff_hours}")
