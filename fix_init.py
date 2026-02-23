#!/usr/bin/env python
import re

with open('/root/travelagentbot/docker-compose.yml', 'r') as f:
    content = f.read()

# Add init: true to services that run Chrome or spawn processes
services_needing_init = [
    'worker_vatican',
    'worker_colosseum', 
    'solver',
    'harvester'
]

for service in services_needing_init:
    # Find the service block and add init after the service name
    old = f"  {service}:"
    new = f"  {service}:\n    init: true"
    content = content.replace(old, new)
    print(f"Added init: true to {service}")

with open('/root/travelagentbot/docker-compose.yml', 'w') as f:
    f.write(content)

print("\nDone! Restart containers to apply.")
