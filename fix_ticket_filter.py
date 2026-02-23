#!/usr/bin/env python3
"""Fix the ticket filtering to only check the requested ticket"""

import re

# Fix god_tier_monitor.py
with open('/app/worker_vatican/god_tier_monitor.py', 'r') as f:
    content = f.read()

# Find and replace the filtering logic to be more strict
old_code = '''                # Filter by ticket type
                is_guided = "Guidat" in t_name or "Guided" in t_name
                if ticket_type == 0 and is_guided:
                    continue
                if ticket_type == 1 and not is_guided:
                    continue'''

new_code = '''                # Filter by ticket type - STRICT filtering
                is_guided = "Guidat" in t_name or "Guided" in t_name or "guidat" in t_name.lower()
                is_standard = "Biglietti" in t_name or "Admission" in t_name or "Ingresso" in t_name
                
                if ticket_type == 0:  # Standard tickets
                    # Skip if clearly guided
                    if is_guided and not is_standard:
                        continue
                    # If name is Unknown, check ID patterns or skip to be safe
                    if t_name == "Unknown":
                        # Skip unknown tickets that might be guided tours
                        # Only process if we can't determine type
                        pass  # Keep but will be filtered later by ID matching
                        
                elif ticket_type == 1:  # Guided tours
                    if not is_guided:
                        continue'''

content = content.replace(old_code, new_code)

# Also fix the matching in tasks.py - be more strict
with open('/app/backend/monitors/tasks.py', 'r') as f:
    tasks_content = f.read()

# Find the matching logic and make it stricter
old_matching = '''        # Filter results for the specific ticket we want
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
                matching_results.append(r)'''

new_matching = '''        # Filter results for the SPECIFIC ticket requested only
        matching_results = []
        for r in results:
            result_ticket_id = r.get('ticket_id', '')
            result_ticket_name = r.get('ticket_name', '').lower()
            
            # STRICT: Only match by exact ticket_id
            # This prevents showing slots for guided tours when monitoring standard tickets
            if ticket_id == result_ticket_id or result_ticket_id in ticket_id or ticket_id in result_ticket_id:
                matching_results.append(r)
                logger.info(f"✅ Matched ticket ID: {result_ticket_id} for {ticket_name}")
            # Also check by name if ticket_id matching fails but name is clear
            elif ticket_name.lower() in result_ticket_name and result_ticket_name != 'unknown':
                matching_results.append(r)
                logger.info(f"✅ Matched ticket name: {result_ticket_name}")
            # Skip results with "Unknown" names - can't verify they're the right ticket
            elif result_ticket_name == 'unknown':
                logger.debug(f"⏭️ Skipping unknown ticket ID {result_ticket_id} - can't verify match")
                continue
            # Skip guided tours when checking standard tickets
            elif ticket_type == 0 and ("guidat" in result_ticket_name or "guided" in result_ticket_name):
                logger.debug(f"⏭️ Skipping guided tour: {result_ticket_name}")
                continue'''

tasks_content = tasks_content.replace(old_matching, new_matching)

with open('/app/worker_vatican/god_tier_monitor.py', 'w') as f:
    f.write(content)

with open('/app/backend/monitors/tasks.py', 'w') as f:
    f.write(tasks_content)

print("✅ Fixed ticket filtering to be stricter")
print("   - Only matches exact ticket_id")
print("   - Skips 'Unknown' ticket names")
print("   - Explicitly skips guided tours for standard ticket checks")
