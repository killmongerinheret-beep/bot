# Vatican Android Agent

Runs on Android in the background. Polls your server for snipe jobs.
When a slot is found, opens Chrome on the phone for checkout.

## What it does
- Holds Vatican slots via recap API (no browser needed for hold)
- Opens Chrome on Android when checkout is needed
- Sends heartbeat so you see it in `/agent status` on Telegram
- Runs 24/7 in background via Termux

## What it does NOT do
- Cannot auto-solve Turnstile on Android (you tap it manually on screen)
- Cannot auto-fill forms on Android Chrome (opens URL, you fill manually)
  → Use Windows agent for fully automated checkout

## Setup (5 minutes)

### Step 1 — Install apps from F-Droid (NOT Play Store)
- **Termux** — https://f-droid.org/packages/com.termux/
- **Termux:API** — https://f-droid.org/packages/com.termux.api/
- **Termux:Boot** — https://f-droid.org/packages/com.termux.boot/ (for auto-start)

### Step 2 — Run setup in Termux
```bash
bash setup_termux.sh
```

### Step 3 — Edit config
```bash
nano ~/vatican_agent/agent_config.json
```
Change `agent_id` to something unique like `android-1`.

### Step 4 — Run
```bash
cd ~/vatican_agent && python main.py --agent android-1
```

### Auto-start on boot
Install **Termux:Boot** from F-Droid. The setup script already created the boot script.
Agent starts automatically when phone boots.

## Keep alive in background
Android kills background processes. To prevent this:
1. Go to Android Settings → Battery → find Termux → set to "Unrestricted"
2. Or use a wake lock: `termux-wake-lock` (run in Termux before starting agent)

## Recommended usage
- Use Android agent for **holding** slots (recap API, no browser)
- Use Windows agent for **paying** (full browser automation, Turnstile auto-solve)
- Run both simultaneously for maximum coverage
