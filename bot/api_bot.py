# ============================================================
# bot/api_bot.py — Headless API Bot (No Emulator Needed!)
#
# This bot talks DIRECTLY to Empire: Four Kingdoms servers
# using HTTP requests — just like your browser/phone does.
# No LDPlayer. No screen. Runs 24/7 on Railway cloud.
#
# HOW IT WORKS:
#   1. Login → Get session token from game server
#   2. Scan world map → Find Robber Baron castles
#   3. Send attack request → Server processes it
#   4. Wait for result → Update stats
#   5. Repeat forever (with smart delays to avoid detection)
# ============================================================

import requests
import json
import time
import os
import sys
import random
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================================
# FILES
# ============================================================
STATS_FILE    = "stats.json"
ACCOUNTS_FILE = "accounts.json"
SESSION_FILE  = "session.json"   # saved session so we don't re-login every time
LOG_FILE      = "logs/attack_log.txt"

os.makedirs("logs", exist_ok=True)

# ============================================================
# GLOBAL SESSION STATE
# ============================================================
_session = requests.Session()   # persistent HTTP session (keeps cookies)
_session_token  = None          # game auth token
_player_id      = None          # your player/castle ID
_server_url     = None          # e.g. https://s1.empire4kingdoms.com
_is_running     = False

# ============================================================
# STATS TRACKING
# ============================================================
_stats = {
    "running":        False,
    "attacks_sent":   0,
    "attacks_won":    0,
    "attacks_failed": 0,
    "troops_lost":    0,
    "uptime_seconds": 0,
    "last_attack":    None,
    "last_target":    None,
    "adb_connected":  False,   # always False — no ADB in API mode!
    "mode":           "api",   # 'api' or 'adb'
    "session_start":  datetime.now().isoformat(),
}

def save_stats():
    """Write current stats to stats.json so dashboard can read it."""
    if _start_time:
        _stats["uptime_seconds"] = int((datetime.now() - _start_time).total_seconds())
    with open(STATS_FILE, "w") as f:
        json.dump(_stats, f, indent=2)

_start_time = None

# ============================================================
# LOGGING
# ============================================================
def log(msg):
    """Print and save a log message."""
    ts  = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ============================================================
# ACCOUNT LOADING
# ============================================================
def load_active_account():
    """Load the active account from accounts.json."""
    if not os.path.exists(ACCOUNTS_FILE):
        log("❌ No accounts found. Add one in the dashboard first!")
        return None
    with open(ACCOUNTS_FILE) as f:
        accounts = json.load(f)
    if not accounts:
        log("❌ No accounts saved. Go to Dashboard → Accounts to add one.")
        return None
    # Use the account marked active, or the first one
    for acc in accounts:
        if acc.get("active"):
            return acc
    return accounts[0]

# ============================================================
# HTTP HELPERS
# ============================================================
def make_request(method, url, data=None, params=None, retries=3):
    """
    Make an HTTP request to the game server with retry logic.
    Mimics a real browser/app to avoid detection.
    """
    # Browser-like headers so server thinks we're a real client
    headers = {
        "User-Agent":      "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
        "Accept":          "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type":    "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With":"XMLHttpRequest",
    }

    # Add session token to headers if we have it
    if _session_token:
        headers["Authorization"] = f"Bearer {_session_token}"

    for attempt in range(retries):
        try:
            if method.upper() == "GET":
                resp = _session.get(url, headers=headers, params=params, timeout=15)
            else:
                resp = _session.post(url, headers=headers, data=data, params=params, timeout=15)

            if resp.status_code == 200:
                return resp
            else:
                log(f"⚠️  Server returned {resp.status_code} (attempt {attempt+1}/{retries})")

        except requests.exceptions.RequestException as e:
            log(f"⚠️  Network error (attempt {attempt+1}/{retries}): {e}")
            time.sleep(2 * (attempt + 1))  # exponential backoff

    log(f"❌ Request failed after {retries} attempts")
    return None

# ============================================================
# GAME API — LOGIN
# ============================================================
def login(account):
    """
    Login to Empire: Four Kingdoms.

    NOTE: The exact endpoint and parameters are captured by
    running tools/capture_traffic.py while logging in normally.
    These are filled in below from the captured traffic.

    Returns: True if login succeeded
    """
    global _session_token, _player_id, _server_url

    log(f"🔐 Logging in as {account['name']} ({account['username']}) on {account['server']}...")

    # ── IMPORTANT ──────────────────────────────────────────
    # These endpoints are discovered by running:
    #   python tools/capture_traffic.py
    # Then logging into your game normally.
    # The tool saves all requests to captured_traffic/
    # ───────────────────────────────────────────────────────

    # Load captured endpoints if available
    endpoint_file = "captured_traffic/login_endpoint.json"
    if os.path.exists(endpoint_file):
        with open(endpoint_file) as f:
            ep = json.load(f)
        login_url = ep.get("url")
        login_params = ep.get("params", {})
    else:
        # Default known Goodgame Empire login endpoint structure
        # (may need updating based on your captured traffic)
        server_map = {
            "INT1": "https://int1.empire4kingdoms.com",
            "INT2": "https://int2.empire4kingdoms.com",
            "US1":  "https://us1.empire4kingdoms.com",
            "DE1":  "https://de1.empire4kingdoms.com",
            # Add more servers as needed
        }
        base_url = server_map.get(account["server"].upper(),
                                  f"https://{account['server'].lower()}.empire4kingdoms.com")
        login_url = f"{base_url}/ajax/login"
        login_params = {}

    payload = {
        "username": account["username"],
        "password": account["password"],
        "server":   account["server"],
        "lang":     "en",
        "platform": "mobile",
    }

    resp = make_request("POST", login_url, data=payload)

    if not resp:
        log("❌ Login request failed — check internet/server URL")
        return False

    try:
        data = resp.json()

        # Extract session token (field names vary by game version)
        token = (data.get("session_id") or
                 data.get("token") or
                 data.get("auth_token") or
                 data.get("sessionId"))

        if token:
            _session_token = token
            _player_id     = data.get("player_id") or data.get("castle_id")
            _server_url    = data.get("server_url", login_url.rsplit("/", 1)[0])
            log(f"✅ Login SUCCESS! Player ID: {_player_id}")
            log(f"   Server: {_server_url}")
            return True
        else:
            log(f"❌ Login failed — no token in response: {str(data)[:200]}")
            return False

    except (json.JSONDecodeError, AttributeError):
        log(f"❌ Could not parse login response: {resp.text[:200]}")
        return False

# ============================================================
# GAME API — WORLD MAP / FIND TARGETS
# ============================================================
def get_robber_baron_targets():
    """
    Scan the world map for Robber Baron castles to attack.

    Returns a list of target dicts with castle_id, level, coords.
    """
    log("🗺️  Scanning world map for Robber Baron castles...")

    endpoint_file = "captured_traffic/worldmap_endpoint.json"
    if os.path.exists(endpoint_file):
        with open(endpoint_file) as f:
            ep = json.load(f)
        url = ep.get("url")
    else:
        url = f"{_server_url}/ajax/worldmap/scan"

    params = {
        "session_id": _session_token,
        "castle_type": "robber_baron",   # filter for robber baron castles
        "radius":      50,               # scan radius around your castle
    }

    resp = make_request("GET", url, params=params)
    if not resp:
        return []

    try:
        data = resp.json()
        targets = data.get("castles", data.get("targets", data.get("results", [])))
        rb_castles = [t for t in targets if _is_robber_baron(t)]
        log(f"   Found {len(rb_castles)} Robber Baron castles")
        return rb_castles
    except:
        log("⚠️  Could not parse world map response")
        return []

def _is_robber_baron(castle_data):
    """Check if a castle entry is a Robber Baron."""
    name = str(castle_data.get("name", "")).lower()
    owner = str(castle_data.get("owner", "")).lower()
    castle_type = str(castle_data.get("type", "")).lower()
    return (
        "robber" in name or
        "baron" in name or
        castle_type in ["robber_baron", "npc", "rb"] or
        owner in ["robber_baron", "npc", ""]
    )

# ============================================================
# GAME API — SEND ATTACK
# ============================================================
def attack_castle(target):
    """
    Send an attack to a Robber Baron castle via the game API.

    Args:
        target: dict with castle_id, level, etc.

    Returns: True if attack was sent successfully
    """
    target_id   = target.get("castle_id") or target.get("id")
    target_name = target.get("name", f"Castle #{target_id}")
    target_level= target.get("level", "?")

    log(f"⚔️  Attacking {target_name} (Level {target_level}, ID: {target_id})")

    endpoint_file = "captured_traffic/attack_endpoint.json"
    if os.path.exists(endpoint_file):
        with open(endpoint_file) as f:
            ep = json.load(f)
        url = ep.get("url")
        payload_template = ep.get("payload", {})
    else:
        url = f"{_server_url}/ajax/attack"
        payload_template = {}

    # Attack payload — exact fields from captured traffic
    payload = {
        "session_id":  _session_token,
        "attacker_id": _player_id,
        "defender_id": target_id,
        "troop_type":  "sword",    # troop type to send
        "troop_count": 100,        # number of troops
        **payload_template,        # merge with captured payload if available
    }

    # Add human-like delay before attacking (avoid bot detection)
    delay = random.uniform(2.0, 5.0)
    log(f"   Waiting {delay:.1f}s before attack (anti-detection delay)...")
    time.sleep(delay)

    resp = make_request("POST", url, data=payload)
    if not resp:
        return False, "Request failed"

    try:
        data = resp.json()
        success = data.get("success") or data.get("ok") or data.get("status") == "ok"
        message = data.get("message", data.get("msg", ""))

        if success:
            log(f"   ✅ Attack sent! {message}")
            return True, message
        else:
            log(f"   ❌ Attack failed: {message}")
            return False, message
    except:
        log(f"   ⚠️  Could not parse attack response: {resp.text[:100]}")
        return False, "Parse error"

# ============================================================
# MAIN BOT LOOP
# ============================================================
def run_bot():
    """
    Main bot loop — runs forever until stopped.
    1. Login
    2. Find Robber Barons
    3. Attack them one by one
    4. Wait between rounds
    5. Repeat
    """
    global _is_running, _start_time

    _is_running = True
    _start_time = datetime.now()
    _stats["running"] = True
    _stats["session_start"] = _start_time.isoformat()
    _stats["mode"] = "api"
    save_stats()

    log("=" * 55)
    log("🤖 E4K API Bot Starting (No Emulator Mode!)")
    log("=" * 55)

    # Load account
    account = load_active_account()
    if not account:
        log("❌ No account configured. Add one in the dashboard.")
        _stats["running"] = False
        save_stats()
        return

    # Login
    if not login(account):
        log("❌ Login failed. Check your username/password in dashboard.")
        _stats["running"] = False
        save_stats()
        return

    log(f"✅ Bot running in API mode — no emulator needed!")
    log(f"   Attacks every ~2 minutes with randomized delays")
    log(f"   Running 24/7 on cloud ☁️")

    # Main attack loop
    while _is_running:
        try:
            log(f"\n{'─'*40}")
            log(f"🔄 Starting attack round #{_stats['attacks_sent'] + 1}")

            # Find targets
            targets = get_robber_baron_targets()

            if not targets:
                log("   No Robber Baron targets found — waiting 5 minutes...")
                time.sleep(300)
                continue

            # Attack each target
            for target in targets[:5]:  # max 5 per round
                if not _is_running:
                    break

                success, msg = attack_castle(target)
                _stats["attacks_sent"] += 1
                _stats["last_attack"]  = datetime.now().isoformat()
                _stats["last_target"]  = target.get("name", f"Castle #{target.get('id')}")

                if success:
                    _stats["attacks_won"] += 1
                else:
                    _stats["attacks_failed"] += 1

                save_stats()

                # Small delay between attacks in same round
                time.sleep(random.uniform(10, 20))

            # Wait before next round (2-3 minutes, randomized)
            wait_seconds = random.randint(120, 180)
            log(f"\n⏳ Round complete. Next round in {wait_seconds // 60}m {wait_seconds % 60}s")
            time.sleep(wait_seconds)

        except KeyboardInterrupt:
            log("\n🛑 Bot stopped by user")
            break
        except Exception as e:
            log(f"⚠️  Unexpected error: {e}")
            log("   Retrying in 60 seconds...")
            time.sleep(60)

    _is_running = False
    _stats["running"] = False
    save_stats()
    log("🔴 Bot stopped.")

def stop_bot():
    """Signal the bot loop to stop."""
    global _is_running
    _is_running = False
    log("🛑 Stop signal received")


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    run_bot()
