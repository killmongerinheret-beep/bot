"""
Test backend API to see what data is being returned
"""
import requests
import json

# Test local backend
url = "http://localhost:8000/api/v1/tasks/"

try:
    response = requests.get(url, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nTotal tasks: {len(data)}")
        
        if data:
            print(f"\nFirst task:")
            task = data[0]
            print(json.dumps(task, indent=2))
    else:
        print(f"\nError: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
