#!/usr/bin/env python
"""Fix ticket matching logic for God-Tier headless mode"""

with open('/app/backend/monitors/tasks.py', 'r') as f:
    content = f.read()

# Replace the matching logic
old_matching = '''        # Filter results for the specific ticket we want
        matching_results = [
            r for r in results 
            if ticket_id in r.get('ticket_id', '') or ticket_name.lower() in r.get('ticket_name', '').lower()
        ]'''

new_matching = '''        # Filter results for the specific ticket we want
        # For headless mode: if ticket_id matches, OR if ticket_name is "Unknown" (cached ID)
        # we accept the result since headless already filters by ticket_type
        matching_results = []
        for r in results:
            result_ticket_id = r.get('ticket_id', '')
            result_ticket_name = r.get('ticket_name', '').lower()
            
            # Direct ID match
            if ticket_id in result_ticket_id:
                matching_results.append(r)
            # Name match (for when we have proper names)
            elif ticket_name.lower() in result_ticket_name:
                matching_results.append(r)
            # If result has "Unknown" name but ID is numeric, it might be our ticket
            # Accept it since headless mode already filtered by ticket_type
            elif result_ticket_name in ('unknown', '') and result_ticket_id.isdigit():
                # For standard tickets (ticket_type=0), accept all non-guided results
                # For guided tickets (ticket_type=1), accept all guided results
                # Headless already filtered by this, so we trust the results
                matching_results.append(r)
        
        logger.info(f"🔍 Headless found {len(results)} results, {len(matching_results)} matched ticket filter")'''

content = content.replace(old_matching, new_matching)

with open('/app/backend/monitors/tasks.py', 'w') as f:
    f.write(content)

print("✅ Matching logic patched!")
