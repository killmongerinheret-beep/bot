#!/usr/bin/env python3
"""
Try to find an API endpoint that returns ticket IDs
"""
import sys
import os
import asyncio

sys.path.insert(0, 'worker_vatican')

from curl_cffi.requests import AsyncSession

async def test_apis():
    # Try different API endpoints
    endpoints = [
        "https://tickets.museivaticani.va/api/visit/types",
        "https://tickets.museivaticani.va/api/visit/types?lang=it",
        "https://tickets.museivaticani.va/api/visittype",
        "https://tickets.museivaticani.va/api/visittype/list",
        "https://tickets.museivaticani.va/api/visit/available",
    ]
    
    async with AsyncSession(verify=False, impersonate="chrome120") as session:
        for url in endpoints:
            print(f"\nTrying: {url}")
            try:
                response = await session.get(url, timeout=10)
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"  Response type: {type(data)}")
                        if isinstance(data, list):
                            print(f"  Items: {len(data)}")
                            if data:
                                print(f"  First item keys: {data[0].keys() if isinstance(data[0], dict) else 'not a dict'}")
                        elif isinstance(data, dict):
                            print(f"  Keys: {data.keys()}")
                    except:
                        print(f"  Not JSON, length: {len(response.text)}")
            except Exception as e:
                print(f"  Error: {e}")

if __name__ == '__main__':
    asyncio.run(test_apis())
