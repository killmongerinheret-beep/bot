import urllib.request
import urllib.error

url = "http://localhost:8000/api/v1/vatican/tickets/?date=26/02/2026"
print(f"Fetching {url}...")
try:
    with urllib.request.urlopen(url, timeout=120) as response:
        print("Success:")
        print(response.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}:")
    print(e.read().decode())
except Exception as e:
    print(f"Error: {e}")
