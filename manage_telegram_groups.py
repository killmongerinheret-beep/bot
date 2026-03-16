#!/usr/bin/env python3
"""
Telegram Groups Management Script
Simple CLI tool to manage Telegram groups via API
"""

import requests
import json
import sys
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"

def list_groups(status=None):
    """List all groups or filter by status"""
    url = f"{API_BASE}/telegram-groups/"
    if status:
        url += f"?status={status}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            groups = response.json()
            
            if not groups:
                print(f"📭 No groups found" + (f" with status '{status}'" if status else ""))
                return []
            
            print(f"📋 Found {len(groups)} groups" + (f" with status '{status}'" if status else "") + ":")
            print("=" * 80)
            
            for group in groups:
                created = datetime.fromisoformat(group['created_at'].replace('Z', '+00:00'))
                
                print(f"🆔 ID: {group['id']}")
                print(f"📱 Title: {group['chat_title']}")
                print(f"🔗 Chat ID: {group['chat_id']}")
                print(f"📊 Status: {group['status'].upper()}")
                print(f"👤 Added by: {group['added_by']['first_name']}" + 
                      (f" (@{group['added_by']['username']})" if group['added_by'].get('username') else ""))
                print(f"📅 Created: {created.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if group.get('agency'):
                    print(f"🏢 Agency: {group['agency']['name']}")
                
                if group.get('rejection_reason'):
                    print(f"❌ Rejection reason: {group['rejection_reason']}")
                
                print("-" * 40)
            
            return groups
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return []

def approve_group(group_id, agency_id=None):
    """Approve a group"""
    url = f"{API_BASE}/telegram-groups/{group_id}/approve/"
    data = {}
    if agency_id:
        data['agency_id'] = agency_id
    
    try:
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        if response.status_code == 200:
            result = response.json()
            print("✅ Group approved successfully!")
            print(f"   Group: {result['group']['chat_title']}")
            print(f"   Status: {result['group']['status']}")
            return result
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None

def reject_group(group_id, reason):
    """Reject a group"""
    url = f"{API_BASE}/telegram-groups/{group_id}/reject/"
    data = {'reason': reason}
    
    try:
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        if response.status_code == 200:
            result = response.json()
            print("✅ Group rejected successfully!")
            print(f"   Group: {result['group']['chat_title']}")
            print(f"   Status: {result['group']['status']}")
            return result
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None

def suspend_group(group_id, reason="Suspended by admin"):
    """Suspend a group"""
    url = f"{API_BASE}/telegram-groups/{group_id}/suspend/"
    data = {'reason': reason}
    
    try:
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        if response.status_code == 200:
            result = response.json()
            print("✅ Group suspended successfully!")
            print(f"   Group: {result['group']['chat_title']}")
            print(f"   Status: {result['group']['status']}")
            return result
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None

def list_agencies():
    """List all agencies"""
    url = f"{API_BASE}/agencies/"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            agencies = response.json()
            print(f"🏢 Found {len(agencies)} agencies:")
            for agency in agencies:
                print(f"   ID: {agency['id']} - {agency['name']}")
            return agencies
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return []

def interactive_mode():
    """Interactive management mode"""
    print("🤖 Telegram Groups Management")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. List all groups")
        print("2. List pending groups")
        print("3. List approved groups")
        print("4. Approve a group")
        print("5. Reject a group")
        print("6. Suspend a group")
        print("7. List agencies")
        print("8. Exit")
        
        choice = input("\nEnter your choice (1-8): ").strip()
        
        if choice == '1':
            list_groups()
        
        elif choice == '2':
            list_groups('pending')
        
        elif choice == '3':
            list_groups('approved')
        
        elif choice == '4':
            groups = list_groups('pending')
            if groups:
                try:
                    group_id = int(input("\nEnter group ID to approve: "))
                    agencies = list_agencies()
                    if agencies:
                        agency_choice = input("Enter agency ID (or press Enter to skip): ").strip()
                        agency_id = int(agency_choice) if agency_choice else None
                    else:
                        agency_id = None
                    approve_group(group_id, agency_id)
                except ValueError:
                    print("❌ Invalid ID")
        
        elif choice == '5':
            groups = list_groups('pending')
            if groups:
                try:
                    group_id = int(input("\nEnter group ID to reject: "))
                    reason = input("Enter rejection reason: ").strip()
                    if reason:
                        reject_group(group_id, reason)
                    else:
                        print("❌ Reason is required")
                except ValueError:
                    print("❌ Invalid ID")
        
        elif choice == '6':
            groups = list_groups('approved')
            if groups:
                try:
                    group_id = int(input("\nEnter group ID to suspend: "))
                    reason = input("Enter suspension reason (optional): ").strip()
                    suspend_group(group_id, reason or "Suspended by admin")
                except ValueError:
                    print("❌ Invalid ID")
        
        elif choice == '7':
            list_agencies()
        
        elif choice == '8':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice")

def main():
    """Main function"""
    if len(sys.argv) == 1:
        # Interactive mode
        interactive_mode()
    else:
        # Command line mode
        command = sys.argv[1].lower()
        
        if command == 'list':
            status = sys.argv[2] if len(sys.argv) > 2 else None
            list_groups(status)
        
        elif command == 'approve':
            if len(sys.argv) < 3:
                print("Usage: python manage_telegram_groups.py approve <group_id> [agency_id]")
                return
            group_id = int(sys.argv[2])
            agency_id = int(sys.argv[3]) if len(sys.argv) > 3 else None
            approve_group(group_id, agency_id)
        
        elif command == 'reject':
            if len(sys.argv) < 4:
                print("Usage: python manage_telegram_groups.py reject <group_id> <reason>")
                return
            group_id = int(sys.argv[2])
            reason = ' '.join(sys.argv[3:])
            reject_group(group_id, reason)
        
        elif command == 'suspend':
            if len(sys.argv) < 3:
                print("Usage: python manage_telegram_groups.py suspend <group_id> [reason]")
                return
            group_id = int(sys.argv[2])
            reason = ' '.join(sys.argv[3:]) if len(sys.argv) > 3 else "Suspended by admin"
            suspend_group(group_id, reason)
        
        elif command == 'agencies':
            list_agencies()
        
        else:
            print("Usage:")
            print("  python manage_telegram_groups.py                    # Interactive mode")
            print("  python manage_telegram_groups.py list [status]      # List groups")
            print("  python manage_telegram_groups.py approve <id> [agency_id]")
            print("  python manage_telegram_groups.py reject <id> <reason>")
            print("  python manage_telegram_groups.py suspend <id> [reason]")
            print("  python manage_telegram_groups.py agencies           # List agencies")

if __name__ == "__main__":
    main()