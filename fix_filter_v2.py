#!/usr/bin/env python3
"""Fix the ticket filtering to match by ID even with Unknown names"""

# Fix tasks.py - allow matching by ticket_id even with Unknown names
with open('/app/backend/monitors/tasks.py', 'r') as f:
    content = f.read()

# Find the new matching logic and fix it
old_matching = '''        # Filter results for the SPECIFIC ticket requested only
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

new_matching = '''        # Filter results for the SPECIFIC ticket requested only
        matching_results = []
        for r in results:
            result_ticket_id = r.get('ticket_id', '')
            result_ticket_name = r.get('ticket_name', '').lower()
            
            # Match by ticket_id (primary method)
            # This works even if name is "Unknown" - we trust the ID from the cache
            if ticket_id == result_ticket_id:
                matching_results.append(r)
                logger.info(f"✅ Matched exact ticket ID: {result_ticket_id}")
            elif result_ticket_id in ticket_id or ticket_id in result_ticket_id:
                matching_results.append(r)
                logger.info(f"✅ Matched partial ticket ID: {result_ticket_id}")
            # Also check by name if it's not Unknown
            elif ticket_name.lower() in result_ticket_name and result_ticket_name != 'unknown':
                matching_results.append(r)
                logger.info(f"✅ Matched ticket name: {result_ticket_name}")
            # If name is Unknown but ID is different, skip (can't verify)
            elif result_ticket_name == 'unknown' and ticket_id != result_ticket_id:
                logger.debug(f"⏭️ Skipping unknown ticket ID {result_ticket_id} - doesn't match requested {ticket_id}")
                continue
            # Skip guided tours when checking standard tickets (unless ID matches)
            elif ticket_type == 0 and ("guidat" in result_ticket_name or "guided" in result_ticket_name):
                logger.debug(f"⏭️ Skipping guided tour: {result_ticket_name}")
                continue'''

content = content.replace(old_matching, new_matching)

with open('/app/backend/monitors/tasks.py', 'w') as f:
    f.write(content)

print("✅ Fixed ticket filtering v2")
print("   - Matches by exact ticket_id even with Unknown names")
print("   - Only skips Unknown if ID doesn't match")
print("   - Still skips guided tours for standard ticket checks")
