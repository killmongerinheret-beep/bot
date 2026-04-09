"""
Turnstile Token — solve on demand only.
No pre-solving pool — tokens are only solved when a snipe actually fires.
Vatican slots are rare; pre-solving wastes 2captcha balance.

One token per reservation. Tokens are valid ~2 minutes.
"""
import logging
import os
import time
import requests

logger = logging.getLogger(__name__)

SITE_KEY = '0x4AAAAAAB2Edz1zEK7o5Rj1'
PAGE_URL = 'https://tickets.museivaticani.va/home/checkout'


def _solve_one_token(api_key: str) -> str | None:
    """Solve a single Turnstile token via 2captcha. Returns token or None."""
    try:
        r = requests.post('https://2captcha.com/in.php', data={
            'key': api_key,
            'method': 'turnstile',
            'sitekey': SITE_KEY,
            'pageurl': PAGE_URL,
            'action': 'managed',
            'json': 1,
        }, timeout=10)
        data = r.json()
        if data.get('status') != 1:
            logger.error(f"2captcha submit failed: {data}")
            return None

        task_id = data['request']
        logger.debug(f"Turnstile task submitted: {task_id}")

        for _ in range(24):  # up to 2 min
            time.sleep(5)
            r2 = requests.get('https://2captcha.com/res.php', params={
                'key': api_key, 'action': 'get', 'id': task_id, 'json': 1
            }, timeout=10)
            res = r2.json()
            if res.get('status') == 1:
                logger.info(f"✅ Turnstile solved (task {task_id})")
                return res['request']
            if res.get('request') != 'CAPCHA_NOT_READY':
                logger.error(f"2captcha error: {res}")
                return None

        logger.error("2captcha timeout")
        return None
    except Exception as e:
        logger.error(f"Turnstile solve exception: {e}")
        return None


def get_token_sync() -> str | None:
    """
    Solve a fresh Turnstile token on demand.
    Called once per snipe — no pool, no waste.
    """
    api_key = os.getenv('TWOCAPTCHA_API_KEY')
    if not api_key:
        logger.error("No TWOCAPTCHA_API_KEY set")
        return None
    logger.info("🔐 Solving Turnstile token (~30s)...")
    return _solve_one_token(api_key)


def return_unused_token(token: str) -> None:
    """No-op — kept for API compatibility. No pool to return to."""
    pass


def pool_size() -> int:
    """Always 0 — no pool."""
    return 0
