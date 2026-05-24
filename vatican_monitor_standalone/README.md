# Vatican Standalone Monitor

Lightweight replacement for `worker_vatican` + `beat` on Hetzner.  
Reads tasks and channels directly from the same Postgres DB as the main bot.  
No Celery, no Redis, no browser — just Search API + Telegram.

## How it fits in

```
Main server (existing)          Hetzner (this)
─────────────────────           ──────────────
telegram_bot  ──writes──▶  Postgres DB  ◀──reads── monitor.py
backend (Django)                              │
                                              ▼
                                    Vatican Search API
                                              │
                                              ▼
                                    Telegram notifications
                                    (all approved channels)
```

The main `telegram_bot` still handles commands (`/add`, `/list`, etc.) and creates tasks.  
This monitor just polls Vatican and sends notifications — independently, on Hetzner.

## Setup

```bash
# On Hetzner
git clone / scp the vatican_monitor_standalone/ folder
cd vatican_monitor_standalone
pip install -r requirements.txt
cp .env.example .env
# Edit .env — point DATABASE_URL at your main Postgres server
python monitor.py
```

## Postgres access from Hetzner

Make sure your main server's Postgres accepts connections from Hetzner's IP.  
In `postgresql.conf`: `listen_addresses = '*'`  
In `pg_hba.conf`: `host ticketbot postgres <hetzner-ip>/32 md5`

Or use an SSH tunnel:
```bash
ssh -L 5432:localhost:5432 user@main-server
# Then set DATABASE_URL=postgres://postgres:postgres@localhost:5432/ticketbot
```

## Run as systemd service

```ini
# /etc/systemd/system/vatican-monitor.service
[Unit]
Description=Vatican Monitor
After=network.target

[Service]
WorkingDirectory=/opt/vatican_monitor_standalone
ExecStart=/usr/bin/python3 monitor.py
Restart=always
RestartSec=10
EnvironmentFile=/opt/vatican_monitor_standalone/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now vatican-monitor
sudo journalctl -u vatican-monitor -f
```

## What it does

- Every 30s: reads all active `MonitorTask` rows from Postgres
- Groups tasks by (date, ticket_type, language, visitors) — one API call per unique combo
- Calls Vatican Search API → timeavail API (same flow as the main bot)
- On first check: establishes baseline, no alert
- On CLOSED→OPEN transition: sends notification to all approved `TelegramGroup` channels for that agency
- 1hr cooldown per task/date to prevent spam
- Updates `last_checked` / `last_status` on each task

## Disabling the main worker_vatican

Once this is running on Hetzner and working, you can stop `worker_vatican` and `beat` on the main server to save RAM:

```bash
docker-compose stop worker_vatican beat
```

The `telegram_bot`, `backend`, `db`, `redis` services still need to run for commands and the web UI.
