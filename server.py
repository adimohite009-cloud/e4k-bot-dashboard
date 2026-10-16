# ============================================================
# server.py — Flask Web Server (Brain of the Dashboard)
#
# This connects your dashboard to the real bot.
# Run this INSTEAD of main.py to get the web dashboard.
#
# Usage: python server.py
# Then open: http://localhost:5000  (or the Railway URL in cloud)
# ============================================================

import json
import os
import subprocess
import sys
import time
import threading
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder="dashboard")
CORS(app)  # allow dashboard to call API from any origin

# ============================================================
# STATS FILE — bot writes here, dashboard reads from here
# ============================================================
STATS_FILE = "stats.json"
LOG_FILE   = "logs/attack_log.txt"

# The currently running bot process (None if stopped)
bot_process = None
bot_start_time = None


def default_stats():
    """Returns a clean stats object when bot hasn't run yet."""
    return {
        "running": False,
        "attacks_sent": 0,
        "attacks_won": 0,
        "attacks_failed": 0,
        "troops_lost": 0,
        "uptime_seconds": 0,
        "last_attack": None,
        "last_target": None,
        "adb_connected": False,
        "session_start": None,
    }


def read_stats():
    """Read stats.json, return defaults if file missing."""
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                data = json.load(f)
                # Add live uptime if bot is running
                if bot_start_time:
                    data["uptime_seconds"] = int(time.time() - bot_start_time)
                    data["running"] = bot_process is not None and bot_process.poll() is None
                return data
        except Exception:
            pass
    return default_stats()


def write_stats(stats):
    """Write stats to stats.json."""
    os.makedirs("logs", exist_ok=True)
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)


def read_logs(last_n=100):
    """Read last N lines from the log file."""
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return [line.strip() for line in lines[-last_n:] if line.strip()]


# ============================================================
# API ROUTES
# ============================================================

@app.route("/")
def index():
    """Serve the dashboard HTML."""
    return send_from_directory("dashboard", "index.html")


@app.route("/api/stats")
def api_stats():
    """Return real bot stats as JSON."""
    stats = read_stats()
    # Calculate derived stats
    total = stats["attacks_sent"]
    won   = stats["attacks_won"]
    stats["win_rate"] = round((won / total * 100) if total > 0 else 0, 1)

    uptime = stats.get("uptime_seconds", 0)
    h = uptime // 3600
    m = (uptime % 3600) // 60
    stats["uptime_display"] = f"{h:02d}:{m:02d}"

    return jsonify(stats)


@app.route("/api/logs")
def api_logs():
    """Return last 100 log lines."""
    lines = read_logs(100)
    return jsonify({"lines": lines})


@app.route("/api/start", methods=["POST"])
def api_start():
    """Start the attack bot as a background subprocess."""
    global bot_process, bot_start_time

    # If already running, return early
    if bot_process and bot_process.poll() is None:
        return jsonify({"ok": False, "message": "Bot is already running!"})

    # Check if an account is configured
    accounts_file = "accounts.json"
    if not os.path.exists(accounts_file):
        return jsonify({"ok": False, "message": "❌ No account configured! Go to Accounts tab first."})

    # Update stats to show it's starting
    stats = read_stats()
    stats["running"] = True
    stats["mode"]    = "api"   # headless API mode — no emulator!
    stats["session_start"] = datetime.now().isoformat()
    write_stats(stats)

    # Start the API bot (headless — no emulator needed!)
    try:
        bot_process = subprocess.Popen(
            [sys.executable, "bot/api_bot.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        bot_start_time = time.time()

        # Stream bot output to log file in a background thread
        threading.Thread(target=stream_output, args=(bot_process,), daemon=True).start()

        log_event("🚀 API Bot started (no emulator mode — running in cloud!)")
        return jsonify({"ok": True, "message": "🚀 Bot started! No emulator needed — running in cloud!"})
    except Exception as e:
        return jsonify({"ok": False, "message": f"❌ Failed to start bot: {e}"})


@app.route("/api/stop", methods=["POST"])
def api_stop():
    """Stop the running bot."""
    global bot_process

    if bot_process and bot_process.poll() is None:
        bot_process.terminate()
        bot_process = None

        stats = read_stats()
        stats["running"] = False
        write_stats(stats)

        log_event("⏹ Bot stopped by user via dashboard")
        return jsonify({"ok": True, "message": "⏹ Bot stopped."})
    else:
        return jsonify({"ok": False, "message": "Bot is not running."})


@app.route("/api/attack", methods=["POST"])
def api_attack():
    """Trigger a manual attack immediately (writes to a trigger file)."""
    with open("manual_attack.trigger", "w") as f:
        f.write("1")
    log_event("⚔️ Manual attack triggered via dashboard")
    return jsonify({"ok": True, "message": "⚔️ Manual attack queued!"})


@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    """Read or save bot settings."""
    settings_file = "settings.json"

    if request.method == "GET":
        if os.path.exists(settings_file):
            with open(settings_file) as f:
                return jsonify(json.load(f))
        # Return defaults from config.py values
        return jsonify({
            "adb_path": "C:\\LDPlayer\\LDPlayer9\\adb.exe",
            "device_id": "emulator-5554",
            "attack_interval": 120,
            "max_attacks": 30,
            "confidence": 0.80,
            "min_rb_level": 1,
            "max_rb_level": 15,
            "log_file": "logs/attack_log.txt"
        })
    else:
        data = request.get_json()
        with open(settings_file, "w") as f:
            json.dump(data, f, indent=2)
        log_event("⚙️ Settings updated via dashboard")
        return jsonify({"ok": True, "message": "💾 Settings saved!"})


@app.route("/api/clear_logs", methods=["POST"])
def api_clear_logs():
    """Clear the log file."""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write("")
    return jsonify({"ok": True, "message": "🗑️ Logs cleared."})


# ============================================================
# ACCOUNT MANAGEMENT ROUTES
# ============================================================
ACCOUNTS_FILE = "accounts.json"

def load_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE) as f:
            return json.load(f)
    return []

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(accounts, f, indent=2)


@app.route("/api/accounts", methods=["GET"])
def api_get_accounts():
    """Return all saved game accounts (passwords masked)."""
    accounts = load_accounts()
    # Mask passwords for security
    safe = []
    for acc in accounts:
        safe.append({
            "id":         acc.get("id"),
            "name":       acc.get("name"),
            "username":   acc.get("username"),
            "password":   "••••••••",   # never send real password to frontend
            "server":     acc.get("server"),
            "status":     acc.get("status", "disconnected"),
            "last_login": acc.get("last_login"),
            "active":     acc.get("active", False),
        })
    return jsonify({"accounts": safe})


@app.route("/api/accounts", methods=["POST"])
def api_add_account():
    """Add or update a game account."""
    data = request.get_json()
    name     = data.get("name", "My Account")
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    server   = data.get("server", "").strip()

    if not username or not password or not server:
        return jsonify({"ok": False, "message": "❌ Username, password and server are required."})

    accounts = load_accounts()

    # Update if exists, otherwise add
    for acc in accounts:
        if acc["username"] == username:
            acc["password"] = password
            acc["server"]   = server
            acc["name"]     = name
            save_accounts(accounts)
            log_event(f"🔄 Account updated: {name} ({username})")
            return jsonify({"ok": True, "message": f"✅ Account '{name}' updated!"})

    new_acc = {
        "id":         len(accounts) + 1,
        "name":       name,
        "username":   username,
        "password":   password,
        "server":     server,
        "status":     "disconnected",
        "last_login": None,
        "active":     len(accounts) == 0,  # first account is active by default
    }
    accounts.append(new_acc)
    save_accounts(accounts)
    log_event(f"➕ Account added: {name} ({username}) on {server}")
    return jsonify({"ok": True, "message": f"✅ Account '{name}' added!"})


@app.route("/api/accounts/<int:account_id>", methods=["DELETE"])
def api_delete_account(account_id):
    """Delete a game account."""
    accounts = load_accounts()
    accounts = [a for a in accounts if a.get("id") != account_id]
    save_accounts(accounts)
    log_event(f"🗑️ Account #{account_id} deleted")
    return jsonify({"ok": True, "message": "🗑️ Account deleted."})


@app.route("/api/accounts/<int:account_id>/activate", methods=["POST"])
def api_activate_account(account_id):
    """Set an account as the active bot account."""
    accounts = load_accounts()
    for acc in accounts:
        acc["active"] = (acc.get("id") == account_id)
    save_accounts(accounts)
    active = next((a for a in accounts if a.get("active")), None)
    name = active["name"] if active else "Unknown"
    log_event(f"⚡ Active account switched to: {name}")
    return jsonify({"ok": True, "message": f"⚡ Now using: {name}"})


# ============================================================
# HELPERS
# ============================================================

def log_event(message):
    """Append a timestamped message to the log file."""
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def stream_output(process):
    """Read bot subprocess output and write to log file."""
    for line in process.stdout:
        line = line.strip()
        if line:
            os.makedirs("logs", exist_ok=True)
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")


# ============================================================
# START SERVER
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 E4K Bot Dashboard Server")
    print("=" * 50)
    print()

    # Create initial stats file if missing
    if not os.path.exists(STATS_FILE):
        write_stats(default_stats())
    os.makedirs("logs", exist_ok=True)

    # Detect if running on cloud (Railway sets PORT env var)
    port = int(os.environ.get("PORT", 5000))
    is_cloud = "PORT" in os.environ

    if is_cloud:
        print(f"☁️  Running on CLOUD (Railway) — port {port}")
        print(f"   Your dashboard URL: check Railway dashboard")
    else:
        print(f"🖥️  Running LOCALLY")
        print(f"   Open your dashboard: http://localhost:{port}")
        print(f"   Or from phone (same WiFi): http://<your-pc-ip>:{port}")
    print()
    print("Press CTRL+C to stop the server.")
    print()

    app.run(host="0.0.0.0", port=port, debug=False)
