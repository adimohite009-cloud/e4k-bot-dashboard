# ============================================================
# bot/attack_bot.py — Robber Baron Attack Logic
#
# This is the BRAIN of the bot.
# It follows a state machine to:
#   1. Open the world map
#   2. Find Robber Baron castles
#   3. Click them, launch attack, send troops
#   4. Wait and repeat
#
# Writes REAL stats to stats.json after every attack
# so the dashboard shows live accurate data.
# ============================================================

import time
import os
import sys
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from bot import adb, screen

# ============================================================
# REAL STATS — written to stats.json so the dashboard reads
# live data instead of fake hardcoded numbers
# ============================================================
STATS_FILE = "stats.json"

_session_stats = {
    "running": True,
    "attacks_sent": 0,
    "attacks_won": 0,
    "attacks_failed": 0,
    "troops_lost": 0,
    "uptime_seconds": 0,
    "last_attack": None,
    "last_target": None,
    "adb_connected": False,
    "session_start": datetime.now().isoformat(),
}
_session_start_time = time.time()


def update_stats(**kwargs):
    """Update and save stats to stats.json so dashboard reads live data."""
    _session_stats.update(kwargs)
    _session_stats["uptime_seconds"] = int(time.time() - _session_start_time)
    try:
        os.makedirs("logs", exist_ok=True)
        with open(STATS_FILE, "w") as f:
            json.dump(_session_stats, f, indent=2)
    except Exception as e:
        print(f"   ⚠️  Could not write stats: {e}")


# ============================================================
# Asset paths — template images OpenCV looks for on screen
# ============================================================
ASSETS = {
    "map_button":           "assets/map_button.png",
    "robber_baron":         "assets/robber_baron_icon.png",
    "attack_button":        "assets/attack_button.png",
    "send_troops_button":   "assets/send_troops_button.png",
    "max_troops_button":    "assets/max_troops_button.png",
    "close_button":         "assets/close_button.png",
    "back_button":          "assets/back_button.png",
}


# ============================================================
# LOGGING
# ============================================================
def log(message):
    """Print AND save to log file with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    os.makedirs("logs", exist_ok=True)
    with open(config.LOG_FILE, "a") as f:
        f.write(log_line + "\n")


# ============================================================
# STEP 1: Open World Map
# ============================================================
def open_world_map():
    log("📍 Opening World Map...")
    position = screen.find_on_screen(ASSETS["map_button"])
    if position:
        adb.tap(position[0], position[1])
        time.sleep(2)
        log("✅ World Map opened")
        return True
    else:
        log("❌ Map button not found! Check assets/map_button.png")
        return False


# ============================================================
# STEP 2: Find Robber Baron Castles
# ============================================================
def find_robber_barons():
    log("🔍 Scanning for Robber Baron castles...")
    positions = screen.find_all_on_screen(ASSETS["robber_baron"])
    if positions:
        log(f"✅ Found {len(positions)} Robber Baron(s) on screen")
    else:
        log("⚠️  No Robber Barons visible — will scroll and try again")
    return positions


# ============================================================
# STEP 3: Attack a Single Robber Baron
# ============================================================
def attack_robber_baron(x, y):
    """
    Attacks a Robber Baron castle at (x, y).
    Returns True if attack was sent, False if something failed.
    """
    log(f"⚔️  Attacking Robber Baron at ({x}, {y})...")

    # Click the castle icon
    adb.tap(x, y)
    time.sleep(2)

    # Wait for Attack button
    attack_pos = screen.wait_for_image(ASSETS["attack_button"], timeout=5)
    if not attack_pos:
        log("❌ Attack button not found — skipping")
        adb.press_back()
        return False

    adb.tap(attack_pos[0], attack_pos[1])
    time.sleep(config.ATTACK_POPUP_WAIT)

    # Click Max troops button (optional)
    max_pos = screen.find_on_screen(ASSETS["max_troops_button"])
    if max_pos:
        adb.tap(max_pos[0], max_pos[1])
        time.sleep(1)
        log("   👥 Selected MAX troops")
    else:
        log("   ℹ️  Max button not found — using default troops")

    # Click Send / Confirm
    send_pos = screen.wait_for_image(ASSETS["send_troops_button"], timeout=5)
    if not send_pos:
        log("❌ Send button not found — cancelling")
        adb.press_back()
        adb.press_back()
        return False

    adb.tap(send_pos[0], send_pos[1])
    time.sleep(1)

    log(f"✅ Attack sent to Robber Baron at ({x}, {y})!")
    return True


# ============================================================
# STEP 4: Scroll Map
# ============================================================
def scroll_map():
    log("🗺️  Scrolling map to find more Robber Barons...")
    cx, cy = 640, 360
    for pattern in [(cx, cy, cx+300, cy), (cx, cy, cx-300, cy),
                    (cx, cy, cx, cy+200), (cx, cy, cx, cy-200)]:
        adb.swipe(*pattern, duration_ms=600)
        time.sleep(1.5)


# ============================================================
# MAIN ATTACK LOOP
# ============================================================
def run_attack_loop():
    """
    The main bot loop. Runs until MAX_ATTACKS_PER_SESSION reached.
    Writes real stats to stats.json after every attack so the
    dashboard always shows live, accurate numbers.
    """
    log("=" * 50)
    log("🤖 EMPIRE BOT STARTED — Robber Baron Attack Mode")
    log("=" * 50)

    total_attacks = 0
    total_wins    = 0
    total_failed  = 0

    # Check ADB connection and write to stats
    connected = adb.is_connected()
    update_stats(running=True, adb_connected=connected,
                 attacks_sent=0, attacks_won=0, attacks_failed=0)

    while total_attacks < config.MAX_ATTACKS_PER_SESSION:
        # Check for manual_attack.trigger file (from dashboard button)
        if os.path.exists("manual_attack.trigger"):
            os.remove("manual_attack.trigger")
            log("⚡ Manual attack triggered from dashboard!")

        log(f"\n--- Round {total_attacks + 1} ---")

        if not open_world_map():
            log("⚠️  Could not open map. Retrying in 10s...")
            time.sleep(10)
            continue

        attacks_this_round = 0
        rb_positions = find_robber_barons()

        for (rb_x, rb_y) in rb_positions:
            if total_attacks >= config.MAX_ATTACKS_PER_SESSION:
                break

            success = attack_robber_baron(rb_x, rb_y)
            total_attacks += 1
            attacks_this_round += 1

            if success:
                total_wins += 1
            else:
                total_failed += 1

            # ✅ Write REAL stats after every single attack
            update_stats(
                attacks_sent=total_attacks,
                attacks_won=total_wins,
                attacks_failed=total_failed,
                last_attack=datetime.now().isoformat(),
                last_target=f"Robber Baron at ({rb_x}, {rb_y})",
            )
            time.sleep(2)

        # Scroll and retry if nothing found
        if attacks_this_round == 0:
            scroll_map()
            time.sleep(2)
            rb_positions = find_robber_barons()
            for (rb_x, rb_y) in rb_positions:
                if total_attacks >= config.MAX_ATTACKS_PER_SESSION:
                    break
                success = attack_robber_baron(rb_x, rb_y)
                total_attacks += 1
                if success:
                    total_wins += 1
                else:
                    total_failed += 1
                update_stats(
                    attacks_sent=total_attacks,
                    attacks_won=total_wins,
                    attacks_failed=total_failed,
                    last_attack=datetime.now().isoformat(),
                    last_target=f"Robber Baron at ({rb_x}, {rb_y})",
                )
                time.sleep(2)

        log(f"\n📊 Attacks: {total_attacks}/{config.MAX_ATTACKS_PER_SESSION}")
        log(f"⏳ Waiting {config.ATTACK_INTERVAL_SECONDS}s...")
        time.sleep(config.ATTACK_INTERVAL_SECONDS)

    log("\n🏁 Bot finished! Max attacks reached.")
    log(f"   Total attacks: {total_attacks}")
    update_stats(running=False)
