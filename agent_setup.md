# Vatican Browser Agent — Setup on Any Computer

## Requirements
- Windows PC with Google Chrome installed
- Python 3.10+

## One-time setup (run once)
```
python -m pip install nodriver requests
```

## Run the agent
```
python local_browser_agent.py --agent my-pc-name
```

Replace `my-pc-name` with any unique name (e.g. `laptop-italy`, `windows-2`).
The name appears in Telegram when picking which machine to use.

## That's it.
The agent connects to the server automatically.
When a snipe triggers, Chrome opens on this machine.
Close the terminal = Chrome closes too.
