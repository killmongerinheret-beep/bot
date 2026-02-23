from django.core.management.base import BaseCommand
from monitors.models import Proxy
import os

class Command(BaseCommand):
    help = 'Seed proxies from Webshare and Oxylabs JSON lists'

    def handle(self, *args, **options):
        # 1. Seed from JSON (Oxylabs)
        json_file = 'c:\\Users\\abiil\\Downloads\\travelagent\\travelagentbot\\Proxy lists.json'
        oxylabs_user = "user-abiilesh_2uVXW"
        oxylabs_pass = "Onemillion_777"
        
        added = 0
        if os.path.exists(json_file):
            import json
            with open(json_file, 'r') as f:
                proxies = json.load(f)
                for p in proxies:
                    ip_port = f"{p['entryPoint']}:{p['port']}"
                    Proxy.objects.get_or_create(
                        ip_port=ip_port,
                        username=oxylabs_user,
                        password=oxylabs_pass
                    )
                    added += 1
            self.stdout.write(self.style.SUCCESS(f'Seeded {added} Oxylabs proxies from JSON.'))

        # 2. Seed from Text (Webshare)
        txt_file = 'c:\\Users\\abiil\\Downloads\\travelagent\\travelagentbot\\Webshare 10 proxies.txt'
        if os.path.exists(txt_file):
            txt_added = 0
            with open(txt_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or ':' not in line: continue
                    parts = line.split(':')
                    if len(parts) == 4:
                        Proxy.objects.get_or_create(
                            ip_port=f"{parts[0]}:{parts[1]}",
                            username=parts[2],
                            password=parts[3]
                        )
                        txt_added += 1
            self.stdout.write(self.style.SUCCESS(f'Seeded {txt_added} Webshare proxies from TXT.'))
